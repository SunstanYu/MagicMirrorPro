"""
流式录音和识别模块 - 合并唤醒、录音、流式识别
"""
import sounddevice as sd
import queue
import numpy as np
import json
import time
import threading
from typing import Optional
from vosk import Model, KaldiRecognizer
from google.cloud import speech
from asr.models import ASRResult
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class StreamingRecorder:
    """流式录音和识别器 - 集成唤醒词检测和流式识别"""
    
    def __init__(self, wake_word: str = "hello", on_wake_word_detected=None):
        """初始化流式录音器
        
        Args:
            wake_word: 唤醒词
            on_wake_word_detected: 唤醒词检测回调函数，检测到唤醒词时调用
        """
        self.wake_word = wake_word.lower()
        self.sample_rate = config.AUDIO_SAMPLE_RATE
        self.block_size = 8000
        self.volume_gain = 10.0
        self.device_id = 1
        self.on_wake_word_detected = on_wake_word_detected
        
        # 初始化 Vosk 模型
        try:
            model_path = config.VOSK_MODEL_PATH
            if not model_path.exists():
                raise ValueError(f"Vosk 模型路径不存在: {model_path}")
            self.vosk_model = Model(str(model_path))
            self.vosk_rec = KaldiRecognizer(self.vosk_model, self.sample_rate)
            self.vosk_rec.SetWords(True)  # 启用单词级别的识别
            logger.info(f"✅ Vosk 模型加载成功: {model_path}")
        except Exception as e:
            logger.error(f"❌ Vosk 模型加载失败: {e}")
            raise
        
        # 初始化 Google ASR 客户端
        try:
            self.google_client = speech.SpeechClient.from_service_account_file(
                str(config.GOOGLE_ASR_CREDENTIALS_PATH)
            )
            logger.info("✅ Google ASR 客户端初始化成功")
        except Exception as e:
            logger.error(f"❌ Google ASR 客户端初始化失败: {e}")
            raise
        
        # 状态变量
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self._wake_word_detection_active = False  # 唤醒词检测激活标志
        
        # Google 流式识别相关变量（用于类方法访问）
        self._google_queue = None
        self._streaming_active = False
        self._final_result = None
        self._last_recognition_time = None
        self._recognition_started = False
        self._streaming_config = None
        
        # 音频流和设备信息（在初始化时设置）
        self._audio_stream = None
        self._device_info = None
        self._actual_sample_rate = self.sample_rate
        self._channels = 1
        self._needs_resample = False
        
        # 初始化并启动音频流
        self._init_audio_stream()
        
        logger.info("✅ 流式录音器初始化完成")
    
    def _init_audio_stream(self):
        """初始化并启动音频流（在初始化时调用，保持一直运行）"""
        try:
            # 列出所有可用设备（用于调试）
            all_devices = sd.query_devices()
            logger.info("📋 可用音频输入设备:")
            for i, dev in enumerate(all_devices):
                if dev.get('max_input_channels', 0) > 0:
                    logger.info(f"  设备 {i}: {dev['name']} (输入通道: {dev.get('max_input_channels', 0)})")
            
            # 尝试使用指定设备
            try:
                self._device_info = sd.query_devices(self.device_id)
                self._actual_sample_rate = int(self._device_info['default_samplerate'])
                max_input_channels = self._device_info.get('max_input_channels', 0)
                
                if max_input_channels < 1:
                    logger.warning(f"⚠️ 设备 {self.device_id} 不支持输入，尝试使用默认设备")
                    self._device_info = None
                else:
                    self._channels = 1  # 使用单声道
                    logger.info(f"✅ 使用设备 {self.device_id}: {self._device_info['name']} (采样率: {self._actual_sample_rate}Hz, 通道: {self._channels})")
            except Exception as e:
                logger.warning(f"⚠️ 获取设备 {self.device_id} 信息失败: {e}，使用默认设备")
                self._device_info = None
                # 使用默认设备时，尝试获取默认采样率
                try:
                    default_device = sd.query_devices(kind='input')
                    self._actual_sample_rate = int(default_device['default_samplerate'])
                except:
                    self._actual_sample_rate = self.sample_rate
            
            self._needs_resample = (self._actual_sample_rate != self.sample_rate)
            
            # 启动音频流（保持一直运行）
            self._audio_stream = sd.InputStream(
                device=self.device_id if self._device_info else None,
                samplerate=self._actual_sample_rate,
                blocksize=self.block_size,
                dtype="int16",
                channels=self._channels,
                callback=self.audio_callback
            )
            self._audio_stream.start()
            logger.info("✅ 音频流已启动并保持运行")
            
        except Exception as e:
            logger.error(f"❌ 初始化音频流失败: {e}")
            raise
    
    def audio_callback(self, indata, frames, time, status):
        """音频采集回调"""
        if status:
            logger.warning(f"⚠️ 音频状态: {status}")
        
        # 处理多声道音频，取第一个声道
        if indata.ndim > 1:
            audio_chunk = indata[:, 0].copy()
        else:
            audio_chunk = indata.copy()
        
        if audio_chunk.dtype != np.int16:
            if audio_chunk.dtype in [np.float32, np.float64]:
                audio_chunk = (audio_chunk * 32767).astype(np.int16)
            else:
                audio_chunk = audio_chunk.astype(np.int16)
        
        # 实时放大音量
        audio_float = audio_chunk.astype(np.float32) * self.volume_gain
        audio_chunk = np.clip(audio_float, -32768, 32767).astype(np.int16)
        
        self.audio_queue.put(audio_chunk.tobytes())
    
    def _detect_wake_word(self, audio_data: bytes) -> bool:
        """检测唤醒词"""
        try:
            # 检查完整结果
            if self.vosk_rec.AcceptWaveform(audio_data):
                result = json.loads(self.vosk_rec.Result())
                text = result.get('text', '').strip().lower()
                if text:
                    logger.info(f"🔍 Vosk 完整结果: {text}")
                if self.wake_word in text:
                    logger.info(f"✅ 在完整结果中检测到唤醒词 '{self.wake_word}'")
                    return True
            
            # 检查部分结果
            partial = json.loads(self.vosk_rec.PartialResult())
            partial_text = partial.get('partial', '').strip().lower()
            if partial_text:
                logger.info(f"🔍 Vosk 部分结果: {partial_text}")
            if self.wake_word in partial_text:
                logger.info(f"✅ 在部分结果中检测到唤醒词 '{self.wake_word}'")
                return True
        except Exception as e:
            logger.warning(f"⚠️ 唤醒词检测异常: {e}")
        return False
    
    def _resample_audio(self, data: bytes, actual_rate: int) -> bytes:
        """降采样音频"""
        audio_chunk = np.frombuffer(data, dtype=np.int16)
        step_ratio = actual_rate / self.sample_rate
        
        if abs(step_ratio - round(step_ratio)) < 0.001:
            step = int(round(step_ratio))
            audio_chunk = audio_chunk[::step]
        else:
            try:
                from scipy import signal
                new_length = int(len(audio_chunk) * (self.sample_rate / actual_rate))
                audio_chunk = signal.resample(audio_chunk, new_length).astype(np.int16)
            except ImportError:
                return data
        return audio_chunk.tobytes()
    
    def _save_asr_result(self, result: ASRResult):
        """保存识别结果到文件"""
        try:
            if not result.text:
                return
            
            with open(config.ASR_RESULT_FILE, "w", encoding="utf-8") as f:
                f.write(result.text + "\n")
            
            logger.info(f"💾 识别结果已保存: {result.text}")
        except Exception as e:
            logger.error(f"❌ 保存识别结果失败: {e}")
    
    def _generate_google_requests(self):
        """生成音频请求的生成器"""
        try:
            while self._streaming_active:
                try:
                    audio_data = self._google_queue.get(timeout=0.1)
                    yield speech.StreamingRecognizeRequest(audio_content=audio_data)
                except queue.Empty:
                    continue
        except GeneratorExit:
            pass
    
    def _send_audio_to_google(self, data):
        """发送音频数据到 Google API（添加到队列）"""
        if self._google_queue is not None:
            self._google_queue.put(data)
    
    def _process_google_responses(self):
        """处理识别响应（在独立线程中运行）"""
        try:
            responses = self.google_client.streaming_recognize(
                config=self._streaming_config,
                requests=self._generate_google_requests()
            )
            
            for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript.strip()
                
                if result.is_final:
                    if transcript:
                        logger.info(f"📝 识别到句子: {transcript}")
                        self._recognition_started = True
                        self._final_result = ASRResult(
                            text=transcript,
                            confidence=result.alternatives[0].confidence if hasattr(result.alternatives[0], 'confidence') else 0.0,
                            language_code="en-US"
                        )
                        # 直接保存识别结果
                        self._save_asr_result(self._final_result)
                        self._last_recognition_time = time.time()
                        # 识别到最终结果后，立即停止识别流程，让 record_and_transcribe() 更快返回
                        self._streaming_active = False
                        logger.info("✅ 识别到最终结果，停止识别流程")
                else:
                    if transcript:
                        self._recognition_started = True
                        self._last_recognition_time = time.time()
        except Exception as e:
            logger.error(f"❌ Google 流式识别错误: {e}")
    
    def record_and_transcribe(self) -> Optional[ASRResult]:
        """
        完整的录音和识别流程：等待唤醒词 -> 流式识别
        音频流已经在初始化时启动，这里只进行唤醒词检测和识别逻辑
        只处理一次唤醒和识别，然后返回结果（由调用者决定是否继续循环）
        
        Returns:
            ASRResult: 最终识别结果，如果没有识别到则返回 None
        """
        if not self._audio_stream or not self._audio_stream.active:
            logger.error("❌ 音频流未运行，无法进行识别")
            return None
        
        logger.info(f"🎯 等待唤醒词 '{self.wake_word}'...")
        self.is_recording = True
        self._wake_word_detection_active = True
        
        try:
            # 重置 Vosk 识别器状态（开始新的识别会话）
            self.vosk_rec = KaldiRecognizer(self.vosk_model, self.sample_rate)
            self.vosk_rec.SetWords(True)
            
            wake_word_detected = False
            
            # 第一步：等待唤醒词（持续循环直到检测到）
            logger.info(f"🎤 正在监听，请说 '{self.wake_word}'...")
            
            while self.is_recording and not wake_word_detected:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                    if self._needs_resample:
                        data = self._resample_audio(data, self._actual_sample_rate)
                    
                    # 检测唤醒词
                    if self._detect_wake_word(data):
                        wake_word_detected = True
                        logger.info(f"✅ 检测到唤醒词 '{self.wake_word}'")
                        # 调用唤醒词检测回调
                        if self.on_wake_word_detected:
                            try:
                                self.on_wake_word_detected()
                            except Exception as e:
                                logger.warning(f"⚠️ 唤醒词回调执行失败: {e}")
                        break
                except queue.Empty:
                    continue
            
            if not wake_word_detected:
                # 如果停止录音但未检测到唤醒词，返回 None
                return None
            
            # 检测到唤醒词后，给用户一点时间准备说话
            logger.info("✅ 检测到唤醒词，准备开始识别...")
            
            # 第二步：Google 流式识别
            logger.info("🔊 开始 Google 流式识别，请说话...")
            self._google_queue = queue.Queue()
            self._final_result = None
            self._last_recognition_time = None
            self._streaming_active = True
            self._recognition_started = False
            
            # Google 流式识别配置
            recognition_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            self._streaming_config = speech.StreamingRecognitionConfig(
                config=recognition_config,
                interim_results=True,
            )
            
            # 启动识别线程
            recognition_thread = threading.Thread(target=self._process_google_responses, daemon=True)
            recognition_thread.start()
            
            # 持续录音并发送到 Google
            INITIAL_WAIT_DURATION = 5.0  # 初始等待时间（秒），给用户时间开始说话
            NO_RECOGNITION_DURATION = 3.0  # 无识别内容持续时间（秒）
            start_time = time.time()
            
            while self.is_recording and self._streaming_active:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                    if self._needs_resample:
                        data = self._resample_audio(data, self._actual_sample_rate)
                    
                    # 发送音频数据到 Google API
                    self._send_audio_to_google(data)
                    
                    # 如果还没开始识别到内容，检查初始等待时间
                    if not self._recognition_started:
                        elapsed = time.time() - start_time
                        if elapsed >= INITIAL_WAIT_DURATION:
                            logger.info("⏹️ 初始等待时间结束，未检测到语音，停止识别")
                            self._streaming_active = False
                            break
                    else:
                        # 如果已经开始识别，检查是否长时间无新内容
                        if self._last_recognition_time is not None:
                            if time.time() - self._last_recognition_time >= NO_RECOGNITION_DURATION:
                                logger.info("⏹️ 长时间无识别内容，停止识别")
                                self._streaming_active = False
                                break
                except queue.Empty:
                    continue
            
            # 等待识别线程完成
            recognition_thread.join(timeout=2.0)
            
            # 返回识别结果（如果有）
            return self._final_result if (self._final_result and self._final_result.text) else None
                
        except Exception as e:
            logger.error(f"❌ 录音识别错误: {e}")
            return None
        finally:
            self.is_recording = False
            self._wake_word_detection_active = False
    
    def stop(self):
        """停止录音和关闭音频流"""
        self.is_recording = False
        self._wake_word_detection_active = False
        
        if self._audio_stream and self._audio_stream.active:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
                logger.info("⏹️ 音频流已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 关闭音频流时出错: {e}")
        
        logger.info("⏹️ 停止录音")

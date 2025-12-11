"""
主应用类 - 状态机和模块协调
"""
import os
import shutil
import time
import threading
import pygame
from typing import Optional, Dict, Any

from core.state import AppState
from io_audio.player import AudioPlayer
from io_audio.streaming_recorder import StreamingRecorder
from asr.models import ASRResult
from nlu.pattern_nlu import PatternNLU
from nlu.models import Intent
from nlu.llm_client import LLMClient
from actions.registry import ActionRegistry
from tts.tts_client import TTSClient
from tts.models import TTSResult
from ui.ui_manager import UIManager
from utils.logger import setup_logger
from utils.weather_client import WeatherClient
from webrtc_integration import WebRTCIntegration
import config

logger = setup_logger(__name__)


class AssistantApp:
    """语音 AI 助手主应用类"""
    
    def __init__(self):
        """初始化应用和所有模块"""
        logger.info("📦 初始化应用模块...")
        
        # 初始化状态
        self.state = AppState.IDLE
        self.running = True
        
        # 初始化各模块
        self.player = AudioPlayer()
        
        # 流式录音器（集成唤醒词检测和流式识别）
        self.streaming_recorder = StreamingRecorder(wake_word="hello")
        
        # NLU 模块 - 仅使用基于模式匹配的 NLU
        self.pattern_nlu = PatternNLU()
        
        # LLM 客户端 - 用于普通聊天生成回复
        self.llm_client = LLMClient()
        
        # 动作注册表
        self.action_registry = ActionRegistry()
        
        # TTS 客户端
        self.tts_client = TTSClient()
        
        # UI 管理器
        self.ui_manager = UIManager()
        
        # 天气客户端 - 只在启动时获取一次天气数据
        self.weather_client = WeatherClient()
        self.current_weather: Optional[Dict[str, Any]] = None
        
        # 初始化天气数据（程序启动时获取一次，作为今日天气）
        self._update_weather()
        
        # 临时数据存储
        self.current_asr_result: Optional[ASRResult] = None
        self.current_intent: Optional[Intent] = None
        self.current_tts_result: Optional[TTSResult] = None
        
        # 后台任务线程控制
        self._background_task: Optional[threading.Thread] = None
        self._task_lock = threading.Lock()
        
        # 唤醒词检测标志（用于主线程更新 UI）
        self._wake_word_detected = threading.Event()
        
        # 监听状态超时控制
        self._listening_start_time: Optional[float] = None
        self._listening_timeout = 5.0  # 5秒超时
        
        # 播放状态标志，避免重复启动播放任务
        self._speaking_handled = False
        
        # 音乐动作引用（用于控制音乐播放）
        self._music_action = None
        
        # 新闻数据（用于 NEWS 状态）
        self._news_data: Optional[Dict[str, Any]] = None
        self._is_news_action = False  # 标记是否是 news 动作
        self._news_index = 0  # 当前播放的新闻索引
        self._news_tts_generating = False  # 是否正在生成 TTS
        self._current_news_tts_result: Optional[TTSResult] = None  # 当前待播放的新闻 TTS
        self._last_news_index = -1  # 上一次的新闻索引，用于判断是否需要更新 UI
        self._news_ui_initialized = False  # 标记新闻 UI 是否已初始化
        # 新闻TTS文件路径（两个文件交替使用）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._news_tts_file_index = 0  # 当前使用的文件索引（0或1）
        self._news_tts_file_0 = os.path.join(project_root, "temp", "audio", "news_tts_0.wav")
        self._news_tts_file_1 = os.path.join(project_root, "temp", "audio", "news_tts_1.wav")
        
        # 设置唤醒词检测回调
        self.streaming_recorder.on_wake_word_detected = self._on_wake_word_detected
        
        # WebRTC 通话集成
        # 证书文件在 MagicMirrorPro/webrtc/certs 目录下
        project_root = os.path.dirname(os.path.dirname(__file__))
        cert_file = os.path.join(project_root, 'webrtc', 'certs', 'cert.pem')
        key_file = os.path.join(project_root, 'webrtc', 'certs', 'key.pem')
        use_https = os.path.exists(cert_file) and os.path.exists(key_file)
        
        if use_https:
            logger.info(f"✅ 检测到 SSL 证书文件，将使用 HTTPS")
        else:
            logger.warning(f"⚠️ 未检测到 SSL 证书文件，将使用 HTTP")
        
        self.webrtc = WebRTCIntegration(
            host='0.0.0.0',
            port=8080,
            use_https=use_https,
            cert_file=cert_file if use_https else None,
            key_file=key_file if use_https else None,
            on_call_start=self._on_call_start,
            on_call_end=self._on_call_end
        )
        # 启动 WebRTC 服务器（后台线程）
        self.webrtc.start()
        
        logger.info("✅ 应用初始化完成")
    
    def run(self):
        """运行主循环"""
        logger.info("🔄 进入主循环...")
        clock = pygame.time.Clock()
        
        while self.running:
            # 处理 pygame 事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        # ESC 或 Q 键：退出程序
                        logger.info("⌨️ 检测到退出键，正在退出程序...")
                        # self.cleanup()
                        self.running = False
                        return
                    elif event.key == pygame.K_RETURN:
                        # 回车键：在 MUSIC 或 NEWS 状态下停止播放并返回 IDLE
                        if self.state == AppState.MUSIC:
                            logger.info("⌨️ 检测到回车键，停止音乐播放并返回空闲状态...")
                            if self._music_action:
                                self._music_action.stop()
                            self._music_action = None
                            # 先停止所有后台任务
                            self._stop_background_tasks()
                            # 重置 streaming_recorder 状态，确保能够重新开始监听
                            self._reset_streaming_recorder()
                            self.state = AppState.IDLE
                            self._set_idle_ui()
                            self._clear_state_data()
                        elif self.state == AppState.NEWS:
                            # NEWS 状态时按回车，停止播放并返回 IDLE
                            logger.info("⌨️ 检测到回车键，停止新闻播报并返回空闲状态...")
                            self.player.stop()
                            # 先停止所有后台任务
                            self._stop_background_tasks()
                            # 重置 streaming_recorder 状态，确保能够重新开始监听
                            self._reset_streaming_recorder()
                            self.state = AppState.IDLE
                            self._speaking_handled = False
                            self._is_news_action = False
                            self._news_data = None
                            self._news_index = 0
                            self._last_news_index = -1
                            self._news_ui_initialized = False
                            self._news_tts_generating = False
                            if hasattr(self, '_current_news_tts_result'):
                                self._current_news_tts_result = None
                            self._set_idle_ui()
                            self._clear_state_data()
            
            # 状态机更新（非阻塞，耗时操作在后台线程）
            try:
                self._update_state()
            except Exception as e:
                logger.error(f"❌ [主循环] _update_state() 异常: {e}", exc_info=True)
            
            # 更新 UI（在主线程，不阻塞）
            try:
                self.ui_manager.update()
            except Exception as e:
                logger.error(f"❌ [主循环] ui_manager.update() 异常: {e}", exc_info=True)
            
            # 控制帧率
            clock.tick(60)
        
        # 主循环退出后清理资源
        logger.info("🔄 主循环已退出，开始清理资源...")
        self.cleanup()
    
    def _update_state(self):
        """根据当前状态执行相应逻辑"""
        # 通话状态优先级最高
        if self.state == AppState.CALLING:
            # 通话状态，不处理其他逻辑
            self._handle_calling()
        elif self.state == AppState.IDLE:
            # 空闲状态，等待 Vosk 唤醒词
            self._handle_idle()
        elif self.state == AppState.LISTENING:
            # 录音和识别状态（集成唤醒词检测和流式识别）
            self._handle_listening()
        elif self.state == AppState.THINKING:
            # LLM 处理状态
            self._handle_thinking()
        elif self.state == AppState.ACTING:
            # 执行动作状态
            self._handle_acting()
        elif self.state == AppState.CHATTING:
            # 聊天状态
            self._handle_chatting()
        elif self.state == AppState.SPEAKING:
            # TTS 播放状态
            self._handle_speaking()
        elif self.state == AppState.MUSIC:
            # 音乐播放状态
            self._handle_music()
        elif self.state == AppState.NEWS:
            # 新闻播报状态
            self._handle_news()
        else:
            logger.warning(f"⚠️ [状态机] 未知状态: {self.state}")
        
    
    def _handle_idle(self):
        """处理空闲状态 - 后台等待唤醒词，UI 保持空闲状态"""        
        # 检查是否已有后台任务在运行
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                # 检查是否有唤醒词检测事件
                if self._wake_word_detected.is_set():
                    self.state = AppState.LISTENING
                    self.ui_manager.set_mode("listening", {"show_appearing": True})
                    self._listening_start_time = time.time()  # 记录开始监听的时间
                    self._wake_word_detected.clear()
                return
        
        with self._task_lock:
            self._background_task = threading.Thread(target=self._waiting_task, daemon=True)
            self._background_task.start()
    
    def _waiting_task(self):
        """等待唤醒词和识别的后台任务 - 只在 IDLE 状态下循环等待唤醒词"""
        import time
        
        # 持续循环，只在 IDLE 状态下等待唤醒词
        # 当检测到唤醒词后，状态变为 LISTENING，但继续等待识别完成
        # 识别完成后，状态会变为 THINKING（成功）或 IDLE（失败），然后退出循环
        while self.running:
            # 检查状态，如果状态不是 IDLE 或 LISTENING，立即退出循环（包括 CALLING 状态）
            if self.state != AppState.IDLE and self.state != AppState.LISTENING:
                break
            
            try:
                # 完整的录音和识别流程（等待唤醒词 + 流式识别）
                # 注意：即使状态变为 LISTENING，也要等待 record_and_transcribe() 完成
                final_result = self.streaming_recorder.record_and_transcribe()
                                
                if final_result and final_result.text:
                    self.current_asr_result = final_result
                    logger.info(f"✅ 最终识别结果: {self.current_asr_result.text}")
                    # 清除监听开始时间
                    self._listening_start_time = None
                    # 直接进入思考状态（退出循环）
                    self.state = AppState.THINKING
                    break
                else:
                    # 如果当前状态是 LISTENING（超时），需要回到 IDLE
                    if self.state == AppState.LISTENING:
                        self.state = AppState.IDLE
                        # 清除监听开始时间
                        self._listening_start_time = None
                        # 确保 UI 是空闲状态
                        self._set_idle_ui()
                        # 继续循环，等待下一个唤醒词
                        time.sleep(0.1)
                    elif self.state == AppState.IDLE:
                        # 在 IDLE 状态下未识别到内容，继续等待下一个唤醒词
                        self._listening_start_time = None
                        # 确保 UI 是空闲状态
                        self._set_idle_ui()
                        # 短暂延迟，避免立即重复调用
                        time.sleep(0.1)
                    else:
                        # 状态已改变，退出循环
                        break
                    
            except Exception as e:
                logger.error(f"❌ 录音识别失败: {e}", exc_info=True)
                # 发生错误时，检查状态
                with self._task_lock:
                    self.state = self.state
                
                # 如果状态不是 IDLE 或 LISTENING，退出循环
                if self.state != AppState.IDLE and self.state != AppState.LISTENING:
                    break
                
                # 发生错误时，短暂等待后继续循环（如果还在 IDLE 状态）
                time.sleep(0.5)
                self._listening_start_time = None
                # 如果状态是 LISTENING，回到 IDLE
                if self.state == AppState.LISTENING:
                    self.state = AppState.IDLE
                # 再次检查状态
                self.state = self.state
                
                # 如果状态不是 IDLE，退出循环
                if self.state != AppState.IDLE:
                    break
                # 确保 UI 是空闲状态
                self._set_idle_ui()
        
        # 任务结束，清理引用
        with self._task_lock:
            self._background_task = None
        logger.info("🛑 监听任务已结束")
        logger.info(f"✅ 当前状态: {self.state}")
    
    def _set_idle_ui(self):
        """设置空闲 UI"""
        # 使用启动时获取的天气数据（如果可用）
        weather_data = self.current_weather or {
            "temperature": -5,
            "condition": "cloudy",
            "location": "Ithaca,US"
        }
        self.ui_manager.set_mode("idle", data={"weather": weather_data})
    
    def _on_call_start(self):
        """通话开始回调（在 WebRTC 线程中调用）"""
        logger.info("📞 收到通话请求，切换到通话状态...")
        
        # 先设置状态为 CALLING，让 _waiting_task 立即退出
        self.state = AppState.CALLING
        
        # 停止当前的音频输入（streaming_recorder）
        try:
            if hasattr(self.streaming_recorder, 'stop'):
                self.streaming_recorder.stop()
        except:
            pass
        
        # 等待后台任务退出（最多等待 1 秒）
        import time
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                logger.info("⏳ 等待监听任务退出...")
                # 等待任务退出
                for _ in range(10):
                    time.sleep(0.1)
                    if not self._background_task.is_alive():
                        break
                if self._background_task.is_alive():
                    logger.warning("⚠️ 监听任务未及时退出，但继续切换状态")
        
        # 切换到通话状态 UI（确保状态已经是 CALLING）
        with self._task_lock:
            if self.state == AppState.CALLING:
                self.ui_manager.set_mode("calling")
                logger.info("✅ 已切换到通话状态 UI")
            else:
                logger.warning(f"⚠️ 状态已改变为 {self.state}，不切换 UI")
    
    def _on_call_end(self):
        """通话结束回调（在 WebRTC 线程中调用）"""
        logger.info("📞 通话结束，返回空闲状态...")
        
        # 重新启动 streaming_recorder 的音频流（因为通话时被停止了）
        try:
            # 确保旧的音频流已关闭
            if hasattr(self.streaming_recorder, '_audio_stream') and self.streaming_recorder._audio_stream:
                try:
                    if self.streaming_recorder._audio_stream.active:
                        self.streaming_recorder._audio_stream.stop()
                        self.streaming_recorder._audio_stream.close()
                except:
                    pass
            
            # 重新初始化音频流
            if hasattr(self.streaming_recorder, '_init_audio_stream'):
                logger.info("🔄 重新启动音频流...")
                self.streaming_recorder._init_audio_stream()
                logger.info("✅ 音频流已重新启动")
        except Exception as e:
            logger.error(f"❌ 重新启动音频流失败: {e}", exc_info=True)
        
        # 切换回空闲状态
        self.state = AppState.IDLE
        self._set_idle_ui()
        # streaming_recorder 的音频流已重新启动，_handle_idle() 会自动启动 _waiting_task
    
    def _handle_calling(self):
        """处理通话状态 - 保持通话 UI，不处理其他逻辑"""
        # 通话状态时，不处理其他逻辑，只保持 UI 显示
        pass
    
    def _update_weather(self) -> None:
        """获取天气数据（程序启动时调用一次，作为今日天气）"""
        try:
            logger.info("🌤️ 正在获取今日天气数据...")
            weather_data = self.weather_client.get_weather()
            
            # 格式化天气数据供 UI 使用
            self.current_weather = {
                "temperature": weather_data.get("temperature", 22),
                "condition": weather_data.get("condition", "sunny"),
                "location": weather_data.get("location", "Current Location")
            }
            
            logger.info(f"✅ 今日天气数据已获取: {self.current_weather['location']} - {self.current_weather['temperature']}°C - {self.current_weather['condition']}")
            
            # 更新空闲 UI（如果已经初始化）
            if self.ui_manager:
                self._set_idle_ui()
            
        except Exception as e:
            logger.error(f"❌ 获取天气数据失败: {e}", exc_info=True)
            # 使用默认天气数据
            self.current_weather = {
                "temperature": 22,
                "condition": "sunny",
                "location": "Current Location"
            }
    
    def _on_wake_word_detected(self):
        """唤醒词检测回调（在后台线程中调用）"""
        logger.info("🔔 唤醒词检测回调被触发")
        # 设置事件标志，主线程会在 _handle_idle 中检查并更新 UI
        self._wake_word_detected.set()
    

    def _handle_listening(self):
        """处理录音和识别状态 - 流式识别（唤醒词已检测到）"""
        # 这个状态表示已经检测到唤醒词，正在进行流式识别
        # 实际的识别工作已经在后台任务（_waiting_task）中继续执行
        # 检查是否已有识别结果（即使 record_and_transcribe() 还没返回）
        if hasattr(self.streaming_recorder, '_final_result') and self.streaming_recorder._final_result:
            if self.streaming_recorder._final_result.text:
                # 已经有识别结果，不检查超时，等待 _waiting_task 处理
                logger.info(f"✅ 检测到识别结果: {self.streaming_recorder._final_result.text}，等待处理...")
                return
        
        # 检查超时：如果5秒内没有识别到语句，返回空闲状态
        if self._listening_start_time is not None:
            elapsed = time.time() - self._listening_start_time
            if elapsed >= self._listening_timeout:
                logger.warning(f"⏱️ 监听超时（{elapsed:.1f}秒），未识别到语句，返回空闲状态")
                # 设置 is_recording = False 来让 record_and_transcribe() 返回
                self.streaming_recorder.is_recording = False
                self.streaming_recorder._streaming_active = False
                self.state = AppState.IDLE
                self._listening_start_time = None
                # 恢复空闲 UI
                self._set_idle_ui()
                # _waiting_task 会检测到状态变为 IDLE，继续循环等待下一个唤醒词
    
    def _thinking_task(self):
        """意图识别任务 - 仅使用基于模式匹配的 NLU"""
        logger.info("🔍 [思考任务] 开始意图识别...")
        logger.info(f"🔍 [思考任务] 当前识别结果: {self.current_asr_result.text if self.current_asr_result else 'None'}")
        try:
            user_text = self.current_asr_result.text
            logger.info(f"🔍 [思考任务] 用户文本: {user_text}")
            
            # 使用模式匹配识别意图
            pattern_intent = self.pattern_nlu.recognize(user_text)
            
            if pattern_intent:
                logger.info(f"✅ 模式匹配识别到动作: {pattern_intent.action_name}")
                self.current_intent = pattern_intent
                # 如果是预定义动作，进入执行状态
                if pattern_intent.intent_type == "predefined_action":
                    self.state = AppState.ACTING
                else:
                    self.state = AppState.CHATTING
            else:
                # 如果没有识别到预定义动作，作为普通聊天处理，调用 LLM 生成回复
                logger.info("💬 未识别到预定义动作，调用 LLM 生成回复...")
                try:
                    llm_response = self.llm_client.ask(user_text)
                    reply_text = llm_response.text
                    logger.info(f"✅ LLM 生成回复: {reply_text[:50]}...")
                    self.current_intent = Intent(
                        intent_type="chat",
                        reply_text=reply_text,
                        confidence=0.5
                    )
                    self.state = AppState.CHATTING
                except Exception as e:
                    logger.error(f"❌ LLM 生成回复失败: {e}", exc_info=True)
                    # 如果 LLM 调用失败，使用默认回复
                    self.current_intent = Intent(
                        intent_type="chat",
                        reply_text="Sorry, I don't understand your meaning.",
                        confidence=0.5
                    )
                    self.state = AppState.CHATTING
                
        except Exception as e:
            logger.error(f"❌ 意图识别失败: {e}", exc_info=True)
            self.state = AppState.IDLE
        finally:
            with self._task_lock:
                self._background_task = None
    
    def _handle_thinking(self):
        """处理 LLM 思考状态（在后台线程执行）"""
        # 检查是否已有后台任务在运行
        with self._task_lock:
            logger.info(f"🔍 [思考任务] 当前背景任务: {self._background_task}")
            if self._background_task and self._background_task.is_alive():
                return  # 任务已在运行，跳过
        
        # 切换到思考 UI，传递识别到的文字
        recognized_text = self.current_asr_result.text if self.current_asr_result else ""
        self.ui_manager.set_mode("thinking", data={"text": recognized_text})
        
        # 启动后台任务
        with self._task_lock:
            logger.info(f"✅ 启动后台任务: {self._background_task}")
            self._background_task = threading.Thread(target=self._thinking_task, daemon=True)
            self._background_task.start()
    
    def _handle_acting(self):
        """处理预定义动作执行"""
        if not self.current_intent:
            logger.error("❌ [ACTING] current_intent 为 None，无法执行动作")
            self.state = AppState.IDLE
            return
        
        logger.info(f"⚙️ [ACTING] 执行动作: {self.current_intent.action_name}")
        action = self.action_registry.get_action(self.current_intent.action_name)
        if action:
            result = action.execute(self.current_intent.action_params)
            
            # 如果是音乐动作，切换到音乐播放状态
            if self.current_intent.action_name == "music":
                logger.info("🎵 [ACTING] 准备播放音乐，停止并重置音频流...")
                if result.get("success"):
                    # 在播放音乐前，停止所有后台任务和音频流
                    self._stop_background_tasks()
                    # 停止 streaming_recorder 的音频流，释放音频设备
                    self._stop_audio_stream_for_music()
                    # 等待一小段时间确保设备释放
                    import time
                    time.sleep(0.2)
                    logger.info("✅ [ACTING] 音频流已停止，开始播放音乐")
                    
                    # 保存音乐动作引用，用于后续控制
                    self._music_action = action
                    # 切换到音乐 UI，传递音乐信息
                    self.ui_manager.set_mode("music", data=result["data"])
                    # 直接进入 MUSIC 状态，不播放 TTS
                    self.state = AppState.MUSIC
                    logger.info(f"🎵 [ACTING] 已切换到 MUSIC 状态，音乐信息: {result['data']}")
                    return
                else:
                    # 音乐播放失败，使用 talking UI 显示错误信息
                    reply_text = result.get("reply_text", "Failed to play music")
                    self.ui_manager.set_mode("talking", data={"text": reply_text})
                    self.current_tts_result = self.tts_client.synthesize(reply_text)
                    self.state = AppState.SPEAKING
                    return
            
            # 如果是新闻动作，切换到新闻播报UI
            if self.current_intent.action_name == "news":
                # 保存新闻数据，用于后续 NEWS 状态
                self._news_data = result.get("data", {})
                self._is_news_action = True
                # self.ui_manager.set_mode("news", data=result["data"])
                # 使用result中的reply_text设置talking UI（英文），而不是current_intent.reply_text（中文）
                reply_text = result.get("reply_text", "I found some news headlines for you.")
                self.ui_manager.set_mode("talking", data={"text": reply_text})
                # 使用预生成的语音文件（跳过 TTS）
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                preset_audio_path = os.path.join(project_root, "resources", "news_headlines.wav")
                self.current_tts_result = TTSResult(
                        audio_path=preset_audio_path,
                        duration=None,
                        format="wav",
                        sample_rate=16000
                    )
                logger.info(f"✅ 使用预生成的新闻回复语音: {preset_audio_path}")
                self.state = AppState.SPEAKING
                return
            else:
                # 其他动作不是 news
                self._is_news_action = False
                # 其他动作使用 talking UI
                result["action_name"] = self.current_intent.action_name
                # 切换到 talking UI，传递回复文字
                reply_text = result.get("reply_text", "Mission accomplished")
                self.ui_manager.set_mode("talking", data={"text": reply_text})
                # 使用预生成的语音文件（跳过 TTS）
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                preset_audio_path = os.path.join(project_root, "resources", "mission_accomplished.wav")
                self.current_tts_result = TTSResult(
                        audio_path=preset_audio_path,
                        duration=None,
                        format="wav",
                        sample_rate=16000
                )
                logger.info(f"✅ 使用预生成的动作完成回复语音: {preset_audio_path}")
                self.state = AppState.SPEAKING
                return
        else:
            reply_text = "Sorry, I don't understand this action"
            # 切换到 talking UI，传递回复文字
            self.ui_manager.set_mode("talking", data={"text": reply_text})
            # 生成 TTS（错误情况仍使用 TTS）
            self.current_tts_result = self.tts_client.synthesize(reply_text)
            self.state = AppState.SPEAKING
    
    def _handle_chatting(self):
        """处理聊天状态 - 直接切换到 talking UI"""
        logger.info("💬 处理聊天回复...")
        # 切换到 talking UI，传递回复文字
        reply_text = self.current_intent.reply_text if self.current_intent else ""
        self.ui_manager.set_mode("talking", data={"text": reply_text})
        # 生成 TTS
        self.current_tts_result = self.tts_client.synthesize(self.current_intent.reply_text)
        self.state = AppState.SPEAKING
    
    def _handle_music(self):
        """处理音乐播放状态"""
        # 检查音乐是否还在播放
        if self._music_action and self._music_action.is_playing():
            # 音乐正在播放，保持 MUSIC 状态
            return
        else:
            # 音乐播放结束，回到空闲状态
            logger.info("✅ 音乐播放完成，回到空闲状态")
            self._music_action = None
            # 重置 streaming_recorder 状态
            self._reset_streaming_recorder()
            self.state = AppState.IDLE
            self._set_idle_ui()
            self._clear_state_data()
    
    def _handle_news(self):
        """处理新闻播报状态 - 逐条生成和播放"""
        # 第一次处理 NEWS 状态，初始化
        if not self._speaking_handled:
            if not self._news_data:
                logger.warning("⚠️ 没有新闻数据，回到空闲状态")
                self.state = AppState.IDLE
                self._is_news_action = False
                self._reset_streaming_recorder()
                self._set_idle_ui()
                self._clear_state_data()
                return
            
            titles = self._news_data.get("titles", [])
            if not titles:
                logger.warning("⚠️ 没有新闻标题，回到空闲状态")
                self.state = AppState.IDLE
                self._is_news_action = False
                self._news_data = None
                self._reset_streaming_recorder()
                self._set_idle_ui()
                self._clear_state_data()
                return
            
            # 初始化新闻索引
            self._news_index = 0
            self._last_news_index = -1
            self._news_ui_initialized = False
            self._speaking_handled = True
            logger.info(f"📰 开始播报 {len(titles)} 条新闻...")
        
        # 获取新闻标题列表
        titles = self._news_data.get("titles", [])
        if not titles:
            logger.warning("⚠️ 没有新闻标题，回到空闲状态")
            self.state = AppState.IDLE
            self._is_news_action = False
            self._news_data = None
            self._reset_streaming_recorder()
            self._set_idle_ui()
            self._clear_state_data()
            return
        
        # 检查是否所有新闻都已播放完成
        if self._news_index >= len(titles):
            logger.info("✅ 所有新闻播报完成，回到空闲状态")
            self._speaking_handled = False
            self._is_news_action = False
            self._news_data = None
            self._news_index = 0
            self._last_news_index = -1
            self._news_ui_initialized = False
            if hasattr(self, '_current_news_tts_result'):
                self._current_news_tts_result = None
            self.state = AppState.IDLE
            with self._task_lock:
                if self._background_task:
                    self._background_task = None
            self._reset_streaming_recorder()
            self._set_idle_ui()
            self._clear_state_data()
            return
        
        # 只在首次进入或新闻索引变化时更新 UI
        if not self._news_ui_initialized or self._news_index != self._last_news_index:
            current_title = titles[self._news_index]
            # 更新 UI 数据，显示当前正在播放的新闻
            ui_data = {
                "titles": titles,
                "current_index": self._news_index,
                "current_title": current_title
            }
            if not self._news_ui_initialized:
                # 首次进入，设置 UI 模式
                self.ui_manager.set_mode("news", data=ui_data)
                self._news_ui_initialized = True
            else:
                # 新闻索引变化，只更新数据
                if hasattr(self.ui_manager.current_screen, 'update'):
                    self.ui_manager.current_screen.update(ui_data)
            self._last_news_index = self._news_index
        
        # 检查是否正在播放
        is_playing = self.player.is_playing_audio()
        
        # 如果正在播放，检查是否需要生成下一条的 TTS
        # if is_playing:
        #     # 如果当前正在播放，且还没有开始生成下一条的 TTS，则开始生成
        #     if not self._news_tts_generating and self._news_index + 1 < len(titles):
        #         # 在后台线程中生成下一条新闻的 TTS
        #         next_title = titles[self._news_index + 1]
        #         logger.info(f"🔊 开始生成下一条新闻的 TTS (索引={self._news_index + 1}): {next_title[:50]}...")
        #         self._news_tts_generating = True
        #         with self._task_lock:
        #             if not (self._background_task and self._background_task.is_alive()):
        #                 self._background_task = threading.Thread(
        #                     target=self._news_tts_task, 
        #                     args=(next_title,),
        #                     daemon=True
        #                 )
        #                 self._background_task.start()
        #     return
        
        # 如果没有在播放，检查是否有待播放的 TTS
        if hasattr(self, '_current_news_tts_result') and self._current_news_tts_result:
            # 如果当前索引的 TTS 已生成，开始播放
            # logger.info(f"🎵 开始播放第 {self._news_index + 1}/{len(titles)} 条新闻...")
            with self._task_lock:
                if not (self._background_task and self._background_task.is_alive()):
                    self._background_task = threading.Thread(
                        target=self._news_playing_task,
                        daemon=True
                    )
                    self._background_task.start()
            return
        
        # 如果当前索引的 TTS 还没有生成，开始生成
        if not self._news_tts_generating:
            current_title = titles[self._news_index]
            logger.info(f"🔊 开始生成第 {self._news_index + 1}/{len(titles)} 条新闻的 TTS: {current_title[:50]}...")
            self._news_tts_generating = True
            with self._task_lock:
                if not (self._background_task and self._background_task.is_alive()):
                    self._background_task = threading.Thread(
                        target=self._news_tts_task,
                        args=(current_title,),
                        daemon=True
                    )
                    self._background_task.start()
    
    def _news_tts_task(self, news_text: str):
        """新闻 TTS 生成后台任务 - 简单生成一条新闻的 TTS"""
        try:
            # 计算下一个文件路径（交替使用）
            next_file_index = 1 - self._news_tts_file_index  # 0变1，1变0
            next_file_path = self._news_tts_file_0 if next_file_index == 0 else self._news_tts_file_1
            
            # 在后台线程中生成 TTS（使用默认路径）
            tts_result = self.tts_client.synthesize(news_text)
            
            # 检查文件是否存在
            if not os.path.exists(tts_result.audio_path):
                logger.warning(f"⚠️ TTS 文件不存在: {tts_result.audio_path}")
                self._news_tts_generating = False
                return
            
            # 复制到下一个文件路径（避免与播放冲突）
            shutil.copy(tts_result.audio_path, next_file_path)
            logger.info(f"✅ 新闻 TTS 生成完成，已保存到: {next_file_path}")
            
            # 更新TTS结果，使用新的文件路径
            tts_result.audio_path = next_file_path
            
            # TTS 生成完成，保存为当前TTS
            self._current_news_tts_result = tts_result
            self._news_tts_file_index = next_file_index  # 更新文件索引
            self._news_tts_generating = False
            
            with self._task_lock:
                self._background_task = None
        except Exception as e:
            logger.error(f"❌ 新闻 TTS 生成失败: {e}", exc_info=True)
            self._news_tts_generating = False
            with self._task_lock:
                self._background_task = None
    
    def _news_playing_task(self):
        """新闻播报音频播放后台任务 - 播放单条新闻"""
        try:
            # 使用当前新闻的 TTS 结果
            if not hasattr(self, '_current_news_tts_result') or not self._current_news_tts_result:
                logger.warning("⚠️ 没有待播放的新闻 TTS，跳过")
                return
            
            current_index_before = self._news_index
            logger.debug(f"🔍 _news_playing_task 开始播放: 索引={current_index_before}")
            
            # 在后台线程中阻塞播放音频
            self.player.play(self._current_news_tts_result.audio_path, blocking=True)
            
            # 播放完成后，清理当前 TTS 结果，索引加1，准备播放下一条
            logger.info(f"✅ 第 {current_index_before + 1} 条新闻播放完成，索引从 {current_index_before} 更新为 {current_index_before + 1}")
            self._current_news_tts_result = None
            self._news_index += 1
            logger.debug(f"🔍 播放完成后的状态: 新索引={self._news_index}")
            # 如果已有预生成的 TTS，会在主线程中自动使用
            # 注意：不在这里更新状态，让主线程检测到播放完成后继续处理下一条
        except Exception as e:
            logger.error(f"❌ 新闻播报失败: {e}", exc_info=True)
            # 播放失败，跳到下一条
            self._current_news_tts_result = None
            self._news_index += 1
        finally:
            with self._task_lock:
                self._background_task = None
    
    def _handle_speaking(self):
        """处理 TTS 播放状态 - 切换到 talking UI"""
        # 如果已经处理过，只检查播放状态
        if self._speaking_handled:
            # 检查是否已有播放任务在运行
            with self._task_lock:
                if self._background_task and self._background_task.is_alive():
                    # 如果正在播放，检查是否播放完成
                    if not self.player.is_playing_audio():
                        # 播放完成，检查是否是 news 动作
                        if self._is_news_action:
                            # news 动作，进入 NEWS 状态
                            logger.info("✅ 新闻初始回复播放完成，进入 NEWS 状态")
                            self.state = AppState.NEWS
                            self._speaking_handled = False
                        else:
                            # 其他动作，回到空闲状态
                            logger.info("✅ 音频播放完成，回到空闲状态")
                            self.state = AppState.IDLE
                            self._speaking_handled = False
                            self._reset_streaming_recorder()
                            self._set_idle_ui()
                            self._clear_state_data()
                        with self._task_lock:
                            self._background_task = None
                else:
                    # 任务已结束但状态还是 SPEAKING，可能是异常情况
                    if not self.player.is_playing_audio():
                        logger.warning("⚠️ 播放任务已结束但状态未更新")
                        if self._is_news_action:
                            # news 动作，进入 NEWS 状态
                            self.state = AppState.NEWS
                            self._speaking_handled = False
                        else:
                            # 其他动作，回到空闲状态
                            self.state = AppState.IDLE
                            self._speaking_handled = False
                            self._reset_streaming_recorder()
                            self._set_idle_ui()
                            self._clear_state_data()
            return
        
        # 第一次处理 SPEAKING 状态
        logger.info("🔊 TTS 文件已生成...")
        logger.info(f"📁 TTS 文件路径: {self.current_tts_result.audio_path}")
        
        # 切换到 talking UI，传递回复文字（如果还没有设置）
        # 注意：news动作已经在_handle_acting中设置了UI，这里跳过避免覆盖
        if not self._is_news_action and self.current_intent and self.current_intent.reply_text:
            self.ui_manager.set_mode("talking", data={"text": self.current_intent.reply_text})
        
        # 检查文件是否存在
        if os.path.exists(self.current_tts_result.audio_path):
            file_size = os.path.getsize(self.current_tts_result.audio_path)
            logger.info(f"✅ TTS 文件已保存，大小: {file_size / 1024:.2f} KB")
        else:
            logger.warning(f"⚠️ TTS 文件不存在: {self.current_tts_result.audio_path}")
            # 文件不存在，直接回到空闲状态
            self.state = AppState.IDLE
            self._speaking_handled = False
            self._reset_streaming_recorder()
            self._set_idle_ui()
            self._clear_state_data()
            return
        
        # 检查是否已有播放任务在运行
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                # 已有任务在运行，标记为已处理
                self._speaking_handled = True
                return
        
        # 启动后台任务播放音频
        logger.info("🎵 开始播放音频...")
        self._speaking_handled = True
        with self._task_lock:
            self._background_task = threading.Thread(target=self._playing_task, daemon=True)
            self._background_task.start()
    
    def _playing_task(self):
        """音频播放后台任务"""
        try:
            # 在后台线程中阻塞播放音频
            self.player.play(self.current_tts_result.audio_path, blocking=True)
            # 播放完成后，检查是否是 news 动作
            if self._is_news_action:
                # news 动作，进入 NEWS 状态
                logger.info("✅ 新闻初始回复播放完成，进入 NEWS 状态")
                self.state = AppState.NEWS
                self._speaking_handled = False
            else:
                # 其他动作，回到空闲状态
                logger.info("✅ 音频播放完成，回到空闲状态")
                self.state = AppState.IDLE
                self._speaking_handled = False
                # 注意：在后台线程中不能直接调用 _reset_streaming_recorder()，因为可能涉及音频流操作
                # 主线程会在 _handle_speaking() 中检测到状态变化并处理
                self._set_idle_ui()
                # 清理临时数据（不调用 _reset_state，因为会尝试 join 当前线程）
                self._clear_state_data()
        except Exception as e:
            logger.error(f"❌ 音频播放失败: {e}", exc_info=True)
            if self._is_news_action:
                # news 动作，即使失败也进入 NEWS 状态
                self.state = AppState.NEWS
                self._speaking_handled = False
            else:
                # 其他动作，回到空闲状态
                self.state = AppState.IDLE
                self._speaking_handled = False
                # 注意：在后台线程中不能直接调用 _reset_streaming_recorder()，因为可能涉及音频流操作
                # 主线程会在 _handle_speaking() 中检测到状态变化并处理
                self._set_idle_ui()
                # 清理临时数据（不调用 _reset_state，因为会尝试 join 当前线程）
                self._clear_state_data()
        finally:
            with self._task_lock:
                self._background_task = None
    
    def _clear_state_data(self):
        """清理临时数据（不等待后台任务）"""
        self.current_asr_result = None
        self.current_intent = None
        self.current_tts_result = None
        
        # 清理视频资源（如果 ListeningScreen 有 cleanup 方法）
        if hasattr(self.ui_manager, 'screens'):
            listening_screen = self.ui_manager.screens.get("listening")
            if listening_screen and hasattr(listening_screen, 'cleanup'):
                listening_screen.cleanup()
    
    def _stop_background_tasks(self):
        """停止所有后台任务（不等待）"""
        logger.info("🛑 停止所有后台任务...")
        # 设置 streaming_recorder 的停止标志，让 record_and_transcribe() 能够退出
        if hasattr(self.streaming_recorder, 'is_recording'):
            self.streaming_recorder.is_recording = False
        if hasattr(self.streaming_recorder, '_wake_word_detection_active'):
            self.streaming_recorder._wake_word_detection_active = False
        if hasattr(self.streaming_recorder, '_streaming_active'):
            self.streaming_recorder._streaming_active = False
        
        # 清理后台任务引用（不等待，让任务自己检测状态变化并退出）
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                logger.info("⚠️ 后台任务仍在运行，将等待其检测状态变化后退出...")
                # 不调用 join()，让任务自己检测状态变化并退出
            self._background_task = None
    
    def _stop_audio_stream_for_music(self):
        """停止 streaming_recorder 的音频流，释放音频设备供音乐播放使用"""
        logger.info("🛑 [音乐播放] 停止 streaming_recorder 的音频流...")
        try:
            if hasattr(self.streaming_recorder, '_audio_stream') and self.streaming_recorder._audio_stream:
                if self.streaming_recorder._audio_stream.active:
                    logger.info("🛑 [音乐播放] 正在停止音频流...")
                    self.streaming_recorder._audio_stream.stop()
                    self.streaming_recorder._audio_stream.close()
                    logger.info("✅ [音乐播放] streaming_recorder 音频流已关闭")
                else:
                    logger.info("ℹ️ [音乐播放] streaming_recorder 音频流未活动，无需关闭")
            else:
                logger.warning("⚠️ [音乐播放] streaming_recorder 没有 _audio_stream 属性或为 None")
        except Exception as e:
            logger.error(f"❌ [音乐播放] 停止 streaming_recorder 音频流失败: {e}", exc_info=True)
    
    def _reset_streaming_recorder(self):
        """重置 streaming_recorder 状态，确保能够重新开始监听"""
        logger.info("🔄 重置 streaming_recorder 状态...")
        try:
            # 确保录音标志被清除
            if hasattr(self.streaming_recorder, 'is_recording'):
                self.streaming_recorder.is_recording = False
            if hasattr(self.streaming_recorder, '_wake_word_detection_active'):
                self.streaming_recorder._wake_word_detection_active = False
            if hasattr(self.streaming_recorder, '_streaming_active'):
                self.streaming_recorder._streaming_active = False
            
            # 确保音频流是活动的（如果被关闭了，重新初始化）
            if hasattr(self.streaming_recorder, '_audio_stream'):
                if not self.streaming_recorder._audio_stream or not self.streaming_recorder._audio_stream.active:
                    logger.info("🔄 音频流未活动，重新初始化...")
                    self.streaming_recorder._init_audio_stream()
                    logger.info("✅ 音频流已重新初始化")
                else:
                    logger.info("✅ 音频流正常活动")
            else:
                logger.warning("⚠️ streaming_recorder 没有 _audio_stream 属性")
            
            # 清空累积的音频缓冲，避免历史音频影响下一次唤醒速度
            if hasattr(self.streaming_recorder, 'clear_audio_buffer'):
                self.streaming_recorder.clear_audio_buffer()
        except Exception as e:
            logger.error(f"❌ 重置 streaming_recorder 失败: {e}", exc_info=True)
    
    def cleanup(self):
        """清理所有资源并退出程序"""
        logger.info("🧹 开始清理资源...")
        
        # 设置运行标志为 False，让所有循环退出
        self.running = False
        
        # 停止所有后台任务
        self._stop_background_tasks()
        
        # 停止音频播放
        try:
            self.player.stop()
        except Exception as e:
            logger.error(f"❌ 停止音频播放失败: {e}", exc_info=True)
        
        # 停止音乐播放
        if self._music_action:
            try:
                self._music_action.stop()
            except Exception as e:
                logger.error(f"❌ 停止音乐播放失败: {e}", exc_info=True)
        
        # 停止 streaming_recorder
        try:
            if hasattr(self.streaming_recorder, '_audio_stream') and self.streaming_recorder._audio_stream:
                if self.streaming_recorder._audio_stream.active:
                    self.streaming_recorder._audio_stream.stop()
                    self.streaming_recorder._audio_stream.close()
        except Exception as e:
            logger.error(f"❌ 停止音频流失败: {e}", exc_info=True)
        
        # 停止 WebRTC 服务器
        try:
            if hasattr(self, 'webrtc'):
                self.webrtc.stop()
        except Exception as e:
            logger.error(f"❌ 停止 WebRTC 服务器失败: {e}", exc_info=True)
        
        # 等待后台任务退出（最多等待 2 秒）
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                logger.info("⏳ 等待后台任务退出...")
                self._background_task.join(timeout=2.0)
                if self._background_task.is_alive():
                    logger.warning("⚠️ 后台任务未能在 2 秒内退出")
        
        logger.info("✅ 资源清理完成")
    
    def _reset_state(self):
        """重置状态，清理临时数据（在主线程中调用，可以等待后台任务）"""
        self._clear_state_data()
        
        # 注意：不再等待后台任务，因为 _waiting_task 应该自己检测状态变化并退出
        # 如果等待，可能会导致卡死（特别是当 _waiting_task 在 record_and_transcribe() 中等待时）

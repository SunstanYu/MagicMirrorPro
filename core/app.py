"""
主应用类 - 状态机和模块协调
"""
import time
import threading
import pygame
from typing import Optional

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
        
        # 初始化空闲屏幕的天气数据
        initial_weather = {
            "temperature": 22,
            "condition": "sunny",
            "location": "Current Location"
        }
        self.ui_manager.set_mode("idle", data={"weather": initial_weather})
        
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
        
        # 设置唤醒词检测回调
        self.streaming_recorder.on_wake_word_detected = self._on_wake_word_detected
        
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
                    if event.key == pygame.K_SPACE:
                        logger.info("⌨️ 检测到空格键，退出程序...")
                        self.running = False
            
            # 状态机更新（非阻塞，耗时操作在后台线程）
            self._update_state()
            
            # 更新 UI（在主线程，不阻塞）
            self.ui_manager.update()
            
            # 控制帧率
            clock.tick(60)
    
    def _update_state(self):
        """根据当前状态执行相应逻辑"""
        if self.state == AppState.IDLE:
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
    
    def _handle_idle(self):
        """处理空闲状态 - 后台等待唤醒词，UI 保持空闲状态"""
        # 检查是否已有后台任务在运行
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                # 检查是否有唤醒词检测事件
                if self._wake_word_detected.is_set():
                    logger.info("🎤 检测到唤醒词，切换到监听状态...")
                    self.state = AppState.LISTENING
                    self.ui_manager.set_mode("listening")
                    self._listening_start_time = time.time()  # 记录开始监听的时间
                    self._wake_word_detected.clear()
                return
        
        # 启动后台任务等待唤醒词（UI 保持 idle 状态）
        logger.info("🎤 后台开始监听，等待唤醒词（UI 保持空闲状态）...")
        
        with self._task_lock:
            self._background_task = threading.Thread(target=self._waiting_task, daemon=True)
            self._background_task.start()
    
    def _waiting_task(self):
        """等待唤醒词和识别的后台任务 - 只在 IDLE 状态下循环等待唤醒词"""
        logger.info("🔄 开始持续监听循环...")
        import time
        
        # 持续循环，只在 IDLE 状态下等待唤醒词
        # 当检测到唤醒词后，状态变为 LISTENING，但继续等待识别完成
        # 识别完成后，状态会变为 THINKING（成功）或 IDLE（失败），然后退出循环
        while self.running:
            # 如果状态不是 IDLE 或 LISTENING，退出循环
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
                    # 未识别到内容
                    # 如果当前状态是 LISTENING（超时），需要回到 IDLE
                    if self.state == AppState.LISTENING:
                        logger.info("🔄 监听超时，返回空闲状态...")
                        self.state = AppState.IDLE
                        # 清除监听开始时间
                        self._listening_start_time = None
                        # 确保 UI 是空闲状态
                        self._set_idle_ui()
                        # 继续循环，等待下一个唤醒词
                        time.sleep(0.1)
                    elif self.state == AppState.IDLE:
                        # 在 IDLE 状态下未识别到内容，继续等待下一个唤醒词
                        logger.info("🔄 未识别到内容，继续等待下一个唤醒词...")
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
                # 发生错误时，短暂等待后继续循环（如果还在 IDLE 状态）
                time.sleep(0.5)
                self._listening_start_time = None
                # 如果状态是 LISTENING，回到 IDLE
                if self.state == AppState.LISTENING:
                    self.state = AppState.IDLE
                # 如果状态不是 IDLE，退出循环
                if self.state != AppState.IDLE:
                    break
                # 确保 UI 是空闲状态
                self._set_idle_ui()
        
        # 任务结束，清理引用
        with self._task_lock:
            self._background_task = None
        logger.info("🛑 监听任务已结束")
    
    def _set_idle_ui(self):
        """设置空闲 UI"""
        initial_weather = {
            "temperature": 22,
            "condition": "sunny",
            "location": "Current Location"
        }
        self.ui_manager.set_mode("idle", data={"weather": initial_weather})
    
    def _on_wake_word_detected(self):
        """唤醒词检测回调（在后台线程中调用）"""
        logger.info("🔔 唤醒词检测回调被触发")
        # 设置事件标志，主线程会在 _handle_idle 中检查并更新 UI
        self._wake_word_detected.set()
    
    def _thinking_task(self):
        """意图识别任务 - 仅使用基于模式匹配的 NLU"""
        logger.info("🔍 开始意图识别...")
        try:
            user_text = self.current_asr_result.text
            
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
    
    def _handle_thinking(self):
        """处理 LLM 思考状态（在后台线程执行）"""
        # 检查是否已有后台任务在运行
        with self._task_lock:
            if self._background_task and self._background_task.is_alive():
                return  # 任务已在运行，跳过
        
        # 启动后台任务
        with self._task_lock:
            self._background_task = threading.Thread(target=self._thinking_task, daemon=True)
            self._background_task.start()
    
    def _handle_acting(self):
        """处理预定义动作执行"""
        logger.info(f"⚙️ 执行动作: {self.current_intent.action_name}")
        action = self.action_registry.get_action(self.current_intent.action_name)
        if action:
            result = action.execute(self.current_intent.action_params)
            
            # 如果是新闻动作，切换到新闻播报UI
            if self.current_intent.action_name == "news":
                self.ui_manager.set_mode("news", data=result["data"])
                # 准备 TTS
                reply_text = result.get("reply_text", "Here are the news headlines")
            else:
                # 其他动作使用 Action UI
                result["action_name"] = self.current_intent.action_name
                self.ui_manager.set_mode("action", data=result)
                # 准备 TTS
                reply_text = result.get("reply_text", "Mission accomplished")
        else:
            reply_text = "Sorry, I don't understand this action"
        
        # 生成 TTS
        self.current_tts_result = self.tts_client.synthesize(reply_text)
        self.state = AppState.SPEAKING
    
    def _handle_chatting(self):
        """处理聊天状态 - 直接切换到 talking UI"""
        logger.info("💬 处理聊天回复...")
        # 切换到 talking UI（与 speaking 状态使用相同的 UI）
        self.ui_manager.set_mode("talking")
        # 生成 TTS
        self.current_tts_result = self.tts_client.synthesize(self.current_intent.reply_text)
        self.state = AppState.SPEAKING
    
    def _handle_speaking(self):
        """处理 TTS 播放状态 - 切换到 talking UI"""
        # 如果已经处理过，只检查播放状态
        if self._speaking_handled:
            # 检查是否已有播放任务在运行
            with self._task_lock:
                if self._background_task and self._background_task.is_alive():
                    # 如果正在播放，检查是否播放完成
                    if not self.player.is_playing_audio():
                        # 播放完成，回到空闲状态
                        logger.info("✅ 音频播放完成，回到空闲状态")
                        self.state = AppState.IDLE
                        self._speaking_handled = False
                        self._set_idle_ui()
                        self._reset_state()
                        with self._task_lock:
                            self._background_task = None
                else:
                    # 任务已结束但状态还是 SPEAKING，可能是异常情况，回到空闲状态
                    if not self.player.is_playing_audio():
                        logger.warning("⚠️ 播放任务已结束但状态未更新，回到空闲状态")
                        self.state = AppState.IDLE
                        self._speaking_handled = False
                        self._set_idle_ui()
                        self._reset_state()
            return
        
        # 第一次处理 SPEAKING 状态
        logger.info("🔊 TTS 文件已生成...")
        logger.info(f"📁 TTS 文件路径: {self.current_tts_result.audio_path}")
        
        # 切换到 talking UI
        self.ui_manager.set_mode("talking")
        
        # 检查文件是否存在
        import os
        if os.path.exists(self.current_tts_result.audio_path):
            file_size = os.path.getsize(self.current_tts_result.audio_path)
            logger.info(f"✅ TTS 文件已保存，大小: {file_size / 1024:.2f} KB")
        else:
            logger.warning(f"⚠️ TTS 文件不存在: {self.current_tts_result.audio_path}")
            # 文件不存在，直接回到空闲状态
            self.state = AppState.IDLE
            self._speaking_handled = False
            self._set_idle_ui()
            self._reset_state()
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
            # 播放完成后，回到空闲状态
            logger.info("✅ 音频播放完成，回到空闲状态")
            self.state = AppState.IDLE
            self._speaking_handled = False
            self._set_idle_ui()
            # 清理临时数据（不调用 _reset_state，因为会尝试 join 当前线程）
            self._clear_state_data()
        except Exception as e:
            logger.error(f"❌ 音频播放失败: {e}", exc_info=True)
            self.state = AppState.IDLE
            self._speaking_handled = False
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
    
    def _reset_state(self):
        """重置状态，清理临时数据（在主线程中调用，可以等待后台任务）"""
        self._clear_state_data()
        
        # 等待后台任务完成（只在主线程中调用时有效）
        import threading
        if threading.current_thread() is threading.main_thread():
            with self._task_lock:
                if self._background_task and self._background_task.is_alive():
                    # 检查是否是当前线程（避免 join 自己）
                    if self._background_task is not threading.current_thread():
                        logger.info("⏳ 等待后台任务完成...")
                        self._background_task.join(timeout=5.0)


"""
UI 管理器 - 管理不同 UI 场景的切换和更新
"""
import threading
import pygame
from typing import Optional, Dict, Any
from ui.screens import BaseScreen, IdleScreen, ListeningScreen, ActionScreen, NewsScreen, TalkingScreen
from ui.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_PRIMARY,
    COLOR_SECONDARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    MODE_IDLE, MODE_LISTENING, MODE_ACTION, MODE_CHAT, MODE_NEWS, MODE_TALKING
)
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class UIManager:
    """UI 管理器 - 线程安全"""
    
    def __init__(self):
        """初始化 UI 管理器"""
        # 初始化 pygame 显示
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("语音 AI 助手")
        
        # 线程安全锁
        self._lock = threading.Lock()
        
        # 当前模式和屏幕
        self.current_mode = MODE_IDLE
        self.current_screen: Optional[BaseScreen] = None
        
        # 初始化所有屏幕（chat 和 talking 使用同一个 TalkingScreen）
        self.screens = {
            MODE_IDLE: IdleScreen(self.screen),
            MODE_LISTENING: ListeningScreen(self.screen),
            MODE_ACTION: ActionScreen(self.screen),
            MODE_CHAT: TalkingScreen(self.screen),  # chat 使用 talking UI
            MODE_NEWS: NewsScreen(self.screen),
            MODE_TALKING: TalkingScreen(self.screen)
        }
        
        # 设置当前屏幕
        self.current_screen = self.screens[MODE_IDLE]
        
        logger.info("🖥️ UI 管理器初始化完成")
    
    def set_mode(self, mode: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        切换 UI 模式（线程安全）
        
        Args:
            mode: 模式名称（idle, listening, action, chat）
            data: 传递给屏幕的数据
        """
        if mode not in self.screens:
            logger.warning(f"⚠️ 未知的 UI 模式: {mode}")
            return
        
        # 线程安全地更新UI状态
        with self._lock:
            logger.info(f"🔄 切换 UI 模式: {self.current_mode} -> {mode}")
            self.current_mode = mode
            self.current_screen = self.screens[mode]
            
            # 更新屏幕数据
            if data is not None:
                self.current_screen.update(data)
    
    def update(self) -> None:
        """
        更新 UI（在主线程中调用，线程安全）
        """
        # 线程安全地更新UI
        with self._lock:
            if self.current_screen:
                self.current_screen.render()
                pygame.display.flip()
    
    def get_screen(self) -> pygame.Surface:
        """
        获取 pygame 屏幕表面
        
        Returns:
            pygame.Surface: 屏幕表面
        """
        return self.screen


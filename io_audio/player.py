"""
音频播放模块
"""
from typing import Optional
from utils.logger import setup_logger
import pygame
import time
import os

logger = setup_logger(__name__)


class AudioPlayer:
    """音频播放器"""
    
    def __init__(self):
        """初始化播放器"""
        # 初始化 pygame mixer
        pygame.mixer.init()
        self.is_playing = False
        logger.info("🔊 音频播放器已初始化")
    
    def play(self, audio_path: str, blocking: bool = True) -> None:
        """
        播放音频文件
        
        Args:
            audio_path: 音频文件路径
            blocking: 是否阻塞等待播放完成
        """
        if not os.path.exists(audio_path):
            logger.error(f"❌ 音频文件不存在: {audio_path}")
            return
        
        logger.info(f"▶️ 播放音频: {audio_path}")
        self.is_playing = True
        
        try:
            # 加载音频文件
            pygame.mixer.music.load(audio_path)
            # 播放音频
            pygame.mixer.music.play()
            
            if blocking:
                # 阻塞等待播放完成
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                logger.info("✅ 音频播放完成")
        except Exception as e:
            logger.error(f"❌ 播放音频失败: {e}", exc_info=True)
        finally:
            self.is_playing = False
    
    def stop(self) -> None:
        """停止播放"""
        logger.info("⏹️ 停止播放")
        try:
            pygame.mixer.music.stop()
            logger.info("✅ 已停止播放")
        except Exception as e:
            logger.error(f"❌ 停止播放失败: {e}", exc_info=True)
        finally:
            self.is_playing = False
    
    def is_playing_audio(self) -> bool:
        """
        检查是否正在播放
        
        Returns:
            bool: 是否正在播放
        """
        return self.is_playing or pygame.mixer.music.get_busy()


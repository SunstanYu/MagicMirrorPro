"""
音频播放模块
"""
from typing import Optional
from utils.logger import setup_logger
import soundfile as sf
import sounddevice as sd
import os

logger = setup_logger(__name__)


class AudioPlayer:
    """音频播放器"""
    
    def __init__(self):
        """初始化播放器"""
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
            # 读取音频文件
            data, samplerate = sf.read(audio_path)
            
            # 如果是立体声，转换为单声道
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            # 0.7倍速播放：降低采样率
            playback_rate = samplerate * 0.7
            
            # 播放音频
            sd.play(data, samplerate=playback_rate)
            
            if blocking:
                # 阻塞等待播放完成
                sd.wait()
                logger.info("✅ 音频播放完成")
        except Exception as e:
            logger.error(f"❌ 播放音频失败: {e}", exc_info=True)
        finally:
            self.is_playing = False
    
    def stop(self) -> None:
        """停止播放"""
        logger.info("⏹️ 停止播放")
        try:
            sd.stop()
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
        try:
            # sounddevice 没有直接的方法检查播放状态，使用 is_playing 标志
            return self.is_playing
        except Exception:
            return False


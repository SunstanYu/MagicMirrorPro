"""
TTS 客户端 - 文本转语音
"""
import time
import numpy as np
from pathlib import Path
from typing import Optional
from tts.models import TTSResult
from utils.logger import setup_logger
import config
import soundfile as sf


logger = setup_logger(__name__)


class TTSClient:
    """TTS 客户端"""
    
    def __init__(self, engine: str = "local"):
        """
        初始化 TTS 客户端
        
        Args:
            engine: TTS 引擎类型 ("local", "gtts", "api")
        """
        self.engine = engine
        logger.info(f"🔧 初始化 TTS 客户端: {engine}")
        
        if engine == "local":
            from piper import PiperVoice
            self.piper_voice = PiperVoice.load(config.PIPER_MODEL_PATH)
            
    
    def synthesize(self, text: str, language: str = "zh") -> TTSResult:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            language: 语言代码，默认 "zh"（中文）
            
        Returns:
            TTSResult: TTS 结果
        """
        logger.info(f"🔊 开始 TTS 合成: {text[:50]}...")
        if self.engine == "local":
            audio_stream = self.piper_voice.synthesize(text)
            audio_data = np.concatenate([chunk.audio_int16_array for chunk in audio_stream])
            audio_data = audio_data.astype(np.float32) / 32768.0
            audio_path = config.AUDIO_TEMP_FILE
            sf.write(str(audio_path), audio_data, self.piper_voice.config.sample_rate)
            return TTSResult(
                audio_path=str(audio_path),
                duration=len(audio_data) / self.piper_voice.config.sample_rate,
                format=config.AUDIO_FORMAT,
                sample_rate=self.piper_voice.config.sample_rate
            )
        else:
            raise ValueError(f"不支持的 TTS 引擎: {self.engine}")
    


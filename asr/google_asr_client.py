"""
Google Speech-to-Text API 客户端 - 简化版，仅保留文件转写
"""
from typing import Optional
from asr.models import ASRResult
from utils.logger import setup_logger
import config
from google.cloud import speech

logger = setup_logger(__name__)


class GoogleASRClient:
    """Google ASR API 客户端"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """初始化 Google ASR 客户端"""
        self.credentials_path = str(credentials_path) if credentials_path else str(config.GOOGLE_ASR_CREDENTIALS_PATH)
        logger.info(f"🔧 初始化 Google ASR 客户端: {self.credentials_path}")
        try:
            self.client = speech.SpeechClient.from_service_account_file(self.credentials_path)
        except:
        self.client = speech.SpeechClient.from_service_account_json(self.credentials_path)
    
    def transcribe(self, audio_path: str, language_code: str = "en-US") -> ASRResult:
        """转写音频文件"""
        logger.info(f"🔊 开始 Google ASR 转写: {audio_path}")
        
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
            language_code=language_code,
        )
        response = self.client.recognize(config=recognition_config, audio=audio)
        if response.results:
            result = response.results[0]
            return ASRResult(
                text=result.alternatives[0].transcript,
                confidence=result.alternatives[0].confidence,
                language_code=language_code
            )
        else:
            return ASRResult(
                text="",
            confidence=0.0,
            language_code=language_code
        )

"""
本地 ASR 占位实现（用于开发测试）
"""
from asr.models import ASRResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LocalASRStub:
    """本地 ASR 占位实现"""
    
    def __init__(self):
        """初始化本地 ASR stub"""
        logger.info("🔧 初始化本地 ASR Stub（占位实现）")
        # TODO: 可以在这里初始化 vosk 或其他本地 ASR 模型
        # from vosk import Model, KaldiRecognizer
        # self.model = Model("path/to/model")
    
    def transcribe(self, audio_path: str, language_code: str = "zh-CN") -> ASRResult:
        """
        转写音频文件（占位实现）
        
        Args:
            audio_path: 音频文件路径
            language_code: 语言代码
            
        Returns:
            ASRResult: 模拟的识别结果
        """
        logger.info(f"🔊 [Stub] 模拟转写: {audio_path}")
        
        # 返回模拟结果
        # TODO: 可以在这里实现真实的 vosk 识别
        mock_text = "今天天气怎么样"
        logger.info(f"📝 [Stub] 模拟识别结果: {mock_text}")
        
        return ASRResult(
            text=mock_text,
            confidence=0.95,
            language_code=language_code,
            alternatives=["今天天气如何", "天气情况"]
        )


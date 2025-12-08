"""
TTS 结果数据模型
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TTSResult:
    """TTS 合成结果"""
    audio_path: str                    # 生成的音频文件路径
    duration: Optional[float] = None   # 音频时长（秒）
    format: str = "wav"                # 音频格式
    sample_rate: int = 16000            # 采样率


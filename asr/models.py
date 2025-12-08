"""
ASR 结果数据模型
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ASRResult:
    """ASR 识别结果"""
    text: str                          # 识别的文本
    confidence: float = 0.0           # 置信度 (0.0-1.0)
    language_code: str = "zh-CN"       # 语言代码
    alternatives: List[str] = None     # 备选文本列表
    timestamp_start: Optional[float] = None  # 开始时间戳
    timestamp_end: Optional[float] = None    # 结束时间戳
    
    def __post_init__(self):
        """初始化后处理"""
        if self.alternatives is None:
            self.alternatives = []


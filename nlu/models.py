"""
NLU 相关数据模型
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LLMResponse:
    """LLM API 返回的原始响应"""
    text: str                          # LLM 返回的文本
    raw_data: Dict[str, Any] = None    # 原始响应数据
    tokens_used: Optional[int] = None  # 使用的 token 数量
    model: Optional[str] = None        # 使用的模型名称
    
    def __post_init__(self):
        """初始化后处理"""
        if self.raw_data is None:
            self.raw_data = {}


@dataclass
class Intent:
    """解析后的意图"""
    intent_type: str                   # "predefined_action" 或 "chat"
    action_name: Optional[str] = None  # 动作名称（如 "weather", "news"）
    action_params: Dict[str, Any] = None  # 动作参数
    reply_text: str = ""               # 需要回复给用户的文本
    confidence: float = 0.0            # 意图识别置信度
    
    def __post_init__(self):
        """初始化后处理"""
        if self.action_params is None:
            self.action_params = {}


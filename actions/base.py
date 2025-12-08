"""
动作基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAction(ABC):
    """动作基类"""
    
    def __init__(self, name: str):
        """
        初始化动作
        
        Args:
            name: 动作名称
        """
        self.name = name
        logger.info(f"🔧 初始化动作: {self.name}")
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行动作
        
        Args:
            params: 动作参数
            
        Returns:
            Dict[str, Any]: 执行结果，包含：
                - reply_text: 需要回复的文本
                - data: 动作返回的数据（用于 UI 显示）
                - success: 是否成功
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证参数（可选实现）
        
        Args:
            params: 动作参数
            
        Returns:
            bool: 参数是否有效
        """
        return True


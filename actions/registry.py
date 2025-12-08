"""
动作注册表 - 管理所有预定义动作
"""
from typing import Dict, Optional
from actions.base import BaseAction
from actions.weather import WeatherAction
from actions.news import NewsAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ActionRegistry:
    """动作注册表"""
    
    def __init__(self):
        """初始化动作注册表"""
        self.actions: Dict[str, BaseAction] = {}
        self._register_default_actions()
        logger.info(f"📋 动作注册表初始化完成，已注册 {len(self.actions)} 个动作")
    
    def _register_default_actions(self):
        """注册默认动作"""
        # 注册天气动作
        self.register(WeatherAction())
        
        # 注册新闻动作
        self.register(NewsAction())
        
        # TODO: 注册其他动作
        # self.register(TimerAction())
        # self.register(MusicAction())
    
    def register(self, action: BaseAction) -> None:
        """
        注册动作
        
        Args:
            action: 动作实例
        """
        self.actions[action.name] = action
        logger.info(f"✅ 注册动作: {action.name}")
    
    def get_action(self, action_name: str) -> Optional[BaseAction]:
        """
        获取动作实例
        
        Args:
            action_name: 动作名称
            
        Returns:
            Optional[BaseAction]: 动作实例，如果不存在则返回 None
        """
        action = self.actions.get(action_name)
        if action is None:
            logger.warning(f"⚠️ 未找到动作: {action_name}")
        return action
    
    def list_actions(self) -> list:
        """
        列出所有已注册的动作名称
        
        Returns:
            list: 动作名称列表
        """
        return list(self.actions.keys())


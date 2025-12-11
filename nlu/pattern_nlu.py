"""
基于模式匹配的 NLU - 识别预定义动作关键词
"""
import re
from typing import Optional, List, Tuple
from nlu.models import Intent
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatternNLU:
    """基于模式匹配的 NLU 系统"""
    
    def __init__(self):
        """初始化模式匹配 NLU"""
        self.patterns = self._init_patterns()
        logger.info("🔧 初始化 Pattern-based NLU")
    
    def _init_patterns(self) -> dict:
        """
        初始化动作匹配模式
        
        Returns:
            dict: 动作名称到模式列表的映射
        """
        patterns = {
            "news": [
                # 直接关键词
                r"\bnews\b",
                r"\bnewspaper\b",
                r"\bheadlines\b",
                r"\bheadline\b",
                
                # 短语模式
                r"show\s+me\s+(the\s+)?news",
                r"what'?s?\s+(the\s+)?news",
                r"tell\s+me\s+(the\s+)?news",
                r"get\s+(me\s+)?(the\s+)?news",
                r"fetch\s+(me\s+)?(the\s+)?news",
                r"read\s+(me\s+)?(the\s+)?news",
                r"latest\s+news",
                r"current\s+news",
                r"today'?s?\s+news",
                r"news\s+of\s+the\s+day",
                r"what'?s?\s+happening",
                r"what'?s?\s+going\s+on",
                
            ],
            "music": [
                # play + 歌名 模式
                r"play\s+(.+)",
                r"play\s+the\s+song\s+(.+)",
                r"play\s+music\s+(.+)",
                r"play\s+a\s+song\s+(.+)",
                r"play\s+the\s+music\s+(.+)",
                
                # play, 歌名 模式（语音识别可能识别为逗号分隔）
                r"play\s*,\s*(.+)",
                r"play\s*,\s*the\s+song\s+(.+)",
                r"play\s*,\s*music\s+(.+)",
                r"play\s*,\s*a\s+song\s+(.+)",
                r"play\s*,\s*the\s+music\s+(.+)",
                
                # 其他变体
                r"play\s+me\s+(.+)",
                r"play\s+me\s+the\s+song\s+(.+)",
                r"play\s+me\s+music\s+(.+)",
                r"play\s+me\s+a\s+song\s+(.+)",
                
                # play, me 变体
                r"play\s*,\s*me\s+(.+)",
                r"play\s*,\s*me\s+the\s+song\s+(.+)",
                r"play\s*,\s*me\s+music\s+(.+)",
                r"play\s*,\s*me\s+a\s+song\s+(.+)",
                
                # 简单关键词
                r"^play\s+(.+)$",
                r"^play\s*,\s*(.+)$",
            ],
            # 可以在这里添加更多动作的模式
            # "weather": [...],
            # "timer": [...],
        }
        return patterns
    
    def recognize(self, text: str) -> Optional[Intent]:
        """
        识别用户输入中的预定义动作
        
        Args:
            text: 用户输入的文本
            
        Returns:
            Optional[Intent]: 如果识别到预定义动作，返回 Intent；否则返回 None
        """
        if not text:
            return None
        
        text_lower = text.lower().strip()
        
        # 遍历所有动作模式
        for action_name, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                # 使用正则表达式匹配（不区分大小写）
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    logger.info(f"✅ 模式匹配成功: '{pattern}' -> action: {action_name}")
                    return self._create_intent(action_name, text)
        
        return None
    
    def _create_intent(self, action_name: str, original_text: str) -> Intent:
        """
        创建意图对象
        
        Args:
            action_name: 动作名称
            original_text: 原始用户输入
            
        Returns:
            Intent: 意图对象
        """
        # 提取参数（如果有）
        params = self._extract_params(action_name, original_text)
        
        # 生成回复文本
        reply_text = self._generate_reply(action_name)
        
        return Intent(
            intent_type="predefined_action",
            action_name=action_name,
            action_params=params,
            reply_text=reply_text,
            confidence=0.9  # 模式匹配的置信度较高
        )
    
    def _extract_params(self, action_name: str, text: str) -> dict:
        """
        从文本中提取动作参数
        
        Args:
            action_name: 动作名称
            text: 用户输入文本
            
        Returns:
            dict: 提取的参数
        """
        params = {}
        text_lower = text.lower()
        
        if action_name == "news":
            # 提取数量（如果有）
            count_match = re.search(r"(\d+)\s*(news|条|个)", text_lower)
            if count_match:
                try:
                    params["count"] = int(count_match.group(1))
                except ValueError:
                    pass
        
        elif action_name == "music":
            # 提取歌曲名（play 后面的内容）
            # 匹配 "play" 或 "play," 后面的所有内容
            match = re.search(r"play\s*,?\s*(?:me\s+)?(?:the\s+)?(?:song\s+|music\s+|a\s+song\s+)?(.+)", text_lower, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                # 清理常见的结尾词
                query = re.sub(r"\s+(please|now|for me|to me)$", "", query, flags=re.IGNORECASE)
                if query:
                    params["query"] = query
            else:
                # 如果上面的模式没匹配到，尝试简单匹配 "play" 或 "play," 后面的所有内容
                match = re.search(r"play\s*,?\s*(.+)", text_lower, re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    query = re.sub(r"\s+(please|now|for me|to me)$", "", query, flags=re.IGNORECASE)
                    if query:
                        params["query"] = query
        
        return params
    
    def _generate_reply(self, action_name: str) -> str:
        """
        生成动作回复文本
        
        Args:
            action_name: 动作名称
            
        Returns:
            str: 回复文本
        """
        replies = {
            "news": "正在获取最新新闻...",
            "music": "正在搜索并播放音乐...",
            # 可以添加更多动作的回复
        }
        return replies.get(action_name, "正在处理...")


"""
新闻动作
"""
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from html import unescape
from actions.base import BaseAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsAction(BaseAction):
    """新闻获取动作"""
    
    def __init__(self):
        """初始化新闻动作"""
        super().__init__("news")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行新闻获取（仅获取标题）
        
        Args:
            params: 动作参数（已废弃，固定获取10条）
                
        Returns:
            Dict[str, Any]: 执行结果，包含标题列表
        """
        logger.info(f"📰 执行新闻获取")
        
        # 固定获取10条新闻标题
        count = 10
        
        # 从 BBC RSS feed 获取新闻标题
        titles = self._fetch_titles_from_bbc(count)
        
        if not titles:
            logger.warning("❌ 新闻获取失败")
            return {
                "reply_text": "Sorry, I couldn't fetch the news at the moment. Please try again later.",
                "data": {
                    "titles": []
                },
                "success": False
            }
        
        # 生成回复文本
        reply_text = f"I found {len(titles)} news headlines for you."
        
        logger.info(f"✅ 成功获取 {len(titles)} 条新闻标题")
        
        return {
            "reply_text": reply_text,
            "data": {
                "titles": titles
            },
            "success": True
        }
    
    def _fetch_titles_from_bbc(self, count: int) -> List[str]:
        """
        从 BBC RSS feed 获取新闻标题
        
        Args:
            count: 获取数量（最多10条）
            
        Returns:
            List[str]: 新闻标题列表
        """
        # BBC RSS feed
        bbc_rss_url = "https://feeds.bbci.co.uk/news/rss.xml"
        
        titles = []
        
        try:
            # 使用 requests 获取 RSS feed
            response = requests.get(bbc_rss_url, timeout=10)
            response.raise_for_status()
            
            # 解析 XML
            root = ET.fromstring(response.content)
            
            # 获取所有 item 元素
            entries = root.findall('.//item')
            
            # 只提取标题，限制数量
            for entry in entries[:count]:
                title_elem = entry.find('title')
                if title_elem is not None and title_elem.text:
                    title = unescape(title_elem.text.strip())
                    if title:
                        titles.append(title)
            
            logger.info(f"✅ 从 BBC RSS 获取了 {len(titles)} 条新闻标题")
            return titles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ BBC RSS feed 请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ BBC RSS feed 处理失败: {e}", exc_info=True)
            return []
    


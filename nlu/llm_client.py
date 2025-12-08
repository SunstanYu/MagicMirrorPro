"""
LLM 客户端 - 调用大语言模型 API
"""
from typing import Optional, Dict, Any
from nlu.models import LLMResponse
from utils.logger import setup_logger
import config
import requests


logger = setup_logger(__name__)

MAGIC_MIRROR_PROMPT = """
You are the Magic Mirror from Snow White.
You live inside a dark, shining mirror in the Queen’s castle.
You speak in a slow, echoing, magical voice.
Your sentences are short and simple, like in a children’s fairy tale.
You never leave your role. You never say you are an AI.

You always answer like the Magic Mirror:
- You speak with old, formal tone.
- You speak with calm truth.
- You never lie.
- You never flatter.
- You reveal what you see, as if looking through magic mist.
- You sometimes begin with phrases like “The Mirror sees…” or “O Queen, hear the truth.”

Stay fully inside the Snow White story world at all times.

IMPORTANT: Your answer must always be 30 English words or fewer.

"""





class LLMClient:
    """LLM API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: API 密钥
            api_url: API 端点 URL
        """
        self.api_key = api_key or config.LLM_API_KEY
        self.api_url = api_url or config.LLM_API_URL
        self.headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
        }
        logger.info("🔧 初始化 LLM 客户端")
       
    
    def ask(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        向 LLM 发送请求
        
        Args:
            prompt: 用户输入的问题/文本
            system_prompt: 系统提示词（可选）
            
        Returns:
            LLMResponse: LLM 返回的响应
        """
        logger.info(f"🤔 LLM 处理: {prompt[:50]}...")
        
        data = {
        "model": config.MODEL,
        "messages": [
        {"role": "system", "content": system_prompt or MAGIC_MIRROR_PROMPT},
        {"role": "user", "content": prompt}
        ]
    }
        response = requests.post(self.api_url, headers=self.headers, json=data)
        if response.status_code != 200:
            logger.error(f"❌ LLM 请求失败: {response.status_code}")
            logger.error(f"❌ LLM 响应: {response.text}")
            return LLMResponse(text="Error: Could not parse AI response.", raw_data={"error": response.text}, tokens_used=0, model=config.MODEL)
        
        try:
            response_json = response.json()
            ai_reply = response_json["choices"][0]["message"]["content"]
            tokens_used = response_json.get("usage", {}).get("total_tokens", 0)
            model = response_json.get("model", config.MODEL)
        except (KeyError, IndexError) as e:
            logger.error(f"❌ 解析 LLM 响应失败: {e}")
            ai_reply = "Error: Could not parse AI response."
            tokens_used = 0
            model = config.MODEL
            response_json = {"error": "Parse error"}
        
        return LLMResponse(text=ai_reply, raw_data=response_json, tokens_used=tokens_used, model=model)
        
        # # 占位实现：返回模拟响应
        # mock_response = self._mock_llm_response(prompt)
        # logger.info(f"📝 LLM 响应: {mock_response.text[:50]}...")
        # return mock_response
    
    def _mock_llm_response(self, prompt: str) -> LLMResponse:
        """
        模拟 LLM 响应（用于开发测试）
        
        Args:
            prompt: 用户输入
            
        Returns:
            LLMResponse: 模拟响应
        """
        # 简单的关键词匹配，返回结构化 JSON
        prompt_lower = prompt.lower()
        
        if "天气" in prompt_lower:
            mock_text = '{"intent_type": "predefined_action", "action_name": "weather", "action_params": {}, "reply_text": "正在为您查询天气信息"}'
        elif "新闻" in prompt_lower:
            mock_text = '{"intent_type": "predefined_action", "action_name": "news", "action_params": {}, "reply_text": "正在为您获取最新新闻"}'
        elif "定时" in prompt_lower or "闹钟" in prompt_lower:
            mock_text = '{"intent_type": "predefined_action", "action_name": "set_timer", "action_params": {"duration": 60}, "reply_text": "已设置定时器"}'
        else:
            mock_text = '{"intent_type": "chat", "reply_text": "我理解您说的：' + prompt + '。这是一个很好的问题！"}'
        
        return LLMResponse(
            text=mock_text,
            raw_data={"mock": True},
            tokens_used=100,
            model="mock-model"
        )


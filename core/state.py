"""
应用状态枚举
"""
from enum import Enum, auto


class AppState(Enum):
    """应用状态枚举"""
    IDLE = auto()              # 空闲状态，等待唤醒
    LISTENING = auto()         # 正在录音
    TRANSCRIBING = auto()      # 正在转写（ASR）
    THINKING = auto()          # 正在思考（LLM 处理）
    ACTING = auto()            # 执行预定义动作
    CHATTING = auto()          # 普通聊天模式
    SPEAKING = auto()          # 正在播放 TTS 回复


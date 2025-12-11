"""
生成预生成的语音文件
用于 news 和 action 的固定回复
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tts.tts_client import TTSClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_preset_audio():
    """生成预生成的语音文件"""
    tts_client = TTSClient()
    resources_dir = project_root / "resources"
    resources_dir.mkdir(exist_ok=True)
    
    # 生成新闻回复语音
    news_text = "Here are the news headlines"
    news_path = resources_dir / "news_headlines.wav"
    logger.info(f"🎵 生成新闻回复语音: {news_text}")
    try:
        result = tts_client.synthesize(news_text)
        # 复制到 resources 目录
        import shutil
        shutil.copy(result.audio_path, str(news_path))
        logger.info(f"✅ 新闻回复语音已保存: {news_path}")
    except Exception as e:
        logger.error(f"❌ 生成新闻回复语音失败: {e}", exc_info=True)
        return False
    
    # 生成动作完成回复语音
    action_text = "Mission accomplished"
    action_path = resources_dir / "mission_accomplished.wav"
    logger.info(f"🎵 生成动作完成回复语音: {action_text}")
    try:
        result = tts_client.synthesize(action_text)
        # 复制到 resources 目录
        import shutil
        shutil.copy(result.audio_path, str(action_path))
        logger.info(f"✅ 动作完成回复语音已保存: {action_path}")
    except Exception as e:
        logger.error(f"❌ 生成动作完成回复语音失败: {e}", exc_info=True)
        return False
    
    logger.info("✅ 所有预生成语音文件已生成完成")
    return True

if __name__ == "__main__":
    success = generate_preset_audio()
    sys.exit(0 if success else 1)


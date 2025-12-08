"""
语音 AI 助手 - 主程序入口
"""
import sys
import os
import pygame
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.app import AssistantApp
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("🚀 启动语音 AI 助手...")
    
    # # 设置显示设备为 fb0（必须在 pygame.init() 之前）
    # os.putenv('SDL_VIDEODRIVER', 'fbcon')
    # os.putenv('SDL_FBDEV', '/dev/fb1')
    
    # 初始化 pygame
    pygame.init()
    
    try:
        # 创建应用实例
        app = AssistantApp()
        
        # 运行主循环
        app.run()
        
    except KeyboardInterrupt:
        logger.info("👋 用户中断，退出程序")
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}", exc_info=True)
    finally:
        pygame.quit()
        logger.info("✅ 程序已退出")


if __name__ == "__main__":
    main()


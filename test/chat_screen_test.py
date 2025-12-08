"""
聊天屏幕测试文件
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from ui.screens import ChatScreen
from ui.constants import *
import config


def test_chat_screen():
    """测试聊天屏幕显示"""
    print("=" * 60)
    print("🧪 聊天屏幕测试")
    print("=" * 60)
    
    # 初始化 pygame
    print("🔧 初始化 pygame...")
    pygame.init()
    
    try:
        # 创建屏幕
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("聊天屏幕测试")
        print(f"✅ 屏幕初始化成功: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # 创建聊天屏幕实例
        print("📺 创建聊天屏幕...")
        chat_screen = ChatScreen(screen)
        print("✅ 聊天屏幕创建成功")
        
        # 测试数据
        test_chats = [
            {
                "user_text": "Hello, how are you?",
                "text": "I'm doing well, thank you for asking! How can I help you today?"
            },
            {
                "user_text": "今天天气怎么样？",
                "text": "今天天气晴朗，温度22度，非常适合外出活动。"
            },
            {
                "user_text": "What is artificial intelligence?",
                "text": "Artificial intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans."
            }
        ]
        
        current_chat_index = 0
        
        # 设置初始聊天数据
        print("\n📊 设置初始聊天数据...")
        chat_screen.update(test_chats[current_chat_index])
        print(f"   用户: {test_chats[current_chat_index]['user_text']}")
        print(f"   助手: {test_chats[current_chat_index]['text'][:50]}...")
        
        # 运行测试循环
        print("\n🖥️ 开始显示测试...")
        print("=" * 60)
        print("操作说明:")
        print("  - 按空格键: 切换到下一个聊天示例")
        print("  - 按 R 键: 重置为第一个聊天")
        print("  - 按 ESC 键: 退出测试")
        print("  - 关闭窗口: 退出测试")
        print("=" * 60)
        
        clock = pygame.time.Clock()
        running = True
        start_time = time.time()
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # 切换到下一个聊天
                        current_chat_index = (current_chat_index + 1) % len(test_chats)
                        chat_screen.update(test_chats[current_chat_index])
                        print(f"\n🔄 切换到聊天 {current_chat_index + 1}/{len(test_chats)}")
                        print(f"   用户: {test_chats[current_chat_index]['user_text']}")
                        print(f"   助手: {test_chats[current_chat_index]['text'][:50]}...")
                    elif event.key == pygame.K_r:
                        # 重置为第一个聊天
                        current_chat_index = 0
                        chat_screen.update(test_chats[current_chat_index])
                        print(f"\n🔄 重置为第一个聊天")
                        print(f"   用户: {test_chats[current_chat_index]['user_text']}")
                        print(f"   助手: {test_chats[current_chat_index]['text'][:50]}...")
            
            # 渲染屏幕
            chat_screen.render()
            pygame.display.flip()
            
            # 控制帧率
            clock.tick(30)
            
            # 显示运行时间（每5秒一次）
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and int(elapsed * 10) % 50 == 0:
                print(f"⏱️  运行中... 当前聊天: {current_chat_index + 1}/{len(test_chats)}, "
                      f"运行时间: {elapsed:.1f}秒")
        
        print("\n" + "=" * 60)
        print("📊 测试统计")
        print("=" * 60)
        print(f"总运行时间: {elapsed:.2f} 秒")
        print(f"测试聊天数量: {len(test_chats)}")
        print("=" * 60)
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        pygame.quit()
    
    return True


if __name__ == "__main__":
    success = test_chat_screen()
    sys.exit(0 if success else 1)


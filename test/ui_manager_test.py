"""
UI 管理器测试 - 测试屏幕切换功能
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from ui.ui_manager import UIManager
from ui.constants import *
import config


def test_ui_manager_switch():
    """测试 UI 管理器屏幕切换"""
    print("=" * 60)
    print("🧪 UI 管理器测试 - 屏幕切换")
    print("=" * 60)
    
    # 初始化 pygame
    print("🔧 初始化 pygame...")
    pygame.init()
    
    try:
        # 创建 UI 管理器
        print("📺 创建 UI 管理器...")
        ui_manager = UIManager()
        print("✅ UI 管理器创建成功")
        print(f"   当前模式: {ui_manager.current_mode}")
        print(f"   屏幕尺寸: {config.UI_WIDTH}x{config.UI_HEIGHT}")
        
        # 设置初始天气数据（用于空闲屏幕）
        print("\n📊 设置初始天气数据...")
        initial_weather = {
            "temperature": 22,
            "condition": "sunny",
            "location": "Current Location"
        }
        ui_manager.set_mode("idle", data={"weather": initial_weather})
        print("✅ 已切换到空闲屏幕")
        
        # 准备聊天测试数据
        test_chat_data = {
            "user_text": "Hello, how are you?",
            "text": "I'm doing well, thank you for asking! How can I help you today?"
        }
        
        # 运行测试循环
        print("\n🖥️ 开始测试...")
        print("=" * 60)
        print("操作说明:")
        print("  - 按空格键: 按顺序切换屏幕")
        print("    空闲屏幕 → 录音屏幕 → 聊天屏幕 → 空闲屏幕...")
        print("  - 按 ESC 键: 退出测试")
        print("  - 关闭窗口: 退出测试")
        print("=" * 60)
        print("\n当前状态: 空闲屏幕（显示时钟和天气）")
        print("按空格键开始切换流程...")
        
        # 定义屏幕切换顺序
        screen_sequence = ["idle", "listening", "chat"]
        sequence_index = 0
        
        clock = pygame.time.Clock()
        running = True
        start_time = time.time()
        switch_count = 0
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    print("\n👋 用户关闭窗口")
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        print("\n👋 用户按 ESC 退出")
                    elif event.key == pygame.K_SPACE:
                        # 按顺序切换屏幕
                        sequence_index = (sequence_index + 1) % len(screen_sequence)
                        next_mode = screen_sequence[sequence_index]
                        switch_count += 1
                        
                        print(f"\n🔄 切换到: {next_mode}")
                        
                        if next_mode == "idle":
                            ui_manager.set_mode("idle", data={"weather": initial_weather})
                            print("✅ 空闲屏幕（时钟 + 天气）")
                        elif next_mode == "listening":
                            ui_manager.set_mode("listening")
                            print("✅ 录音屏幕（视频循环播放）")
                        elif next_mode == "chat":
                            ui_manager.set_mode("chat", data=test_chat_data)
                            print("✅ 聊天屏幕（用户消息 + 助手回复）")
                        
                        print(f"   按空格键继续切换到下一个屏幕...")
            
            # 更新 UI（渲染当前屏幕）
            ui_manager.update()
            
            # 控制帧率
            clock.tick(30)
            
            # 显示当前状态（每5秒一次，避免刷屏）
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and int(elapsed * 10) % 50 == 0:
                current_mode = ui_manager.current_mode
                mode_display = {
                    "idle": "空闲屏幕（时钟+天气）",
                    "listening": "录音屏幕（视频播放）",
                    "action": "动作屏幕",
                    "chat": "聊天屏幕（对话气泡）"
                }
                print(f"⏱️  运行中... 当前模式: {mode_display.get(current_mode, current_mode)}, "
                      f"切换次数: {switch_count}, 运行时间: {elapsed:.1f}秒")
        
        # 输出最终统计
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("📊 测试统计")
        print("=" * 60)
        print(f"总运行时间: {total_time:.2f} 秒")
        print(f"屏幕切换次数: {switch_count}")
        print(f"最终模式: {ui_manager.current_mode}")
        print("=" * 60)
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理资源
        if 'ui_manager' in locals():
            # 清理录音屏幕的视频资源
            if hasattr(ui_manager, 'screens'):
                listening_screen = ui_manager.screens.get("listening")
                if listening_screen and hasattr(listening_screen, 'cleanup'):
                    listening_screen.cleanup()
        pygame.quit()
    
    return True


if __name__ == "__main__":
    success = test_ui_manager_switch()
    sys.exit(0 if success else 1)


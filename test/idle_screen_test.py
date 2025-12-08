"""
空闲屏幕测试文件
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from ui.screens import IdleScreen
from ui.constants import *
import config


def test_idle_screen():
    """测试空闲屏幕显示"""
    print("=" * 60)
    print("🧪 空闲屏幕测试")
    print("=" * 60)
    
    # 初始化 pygame
    print("🔧 初始化 pygame...")
    pygame.init()
    
    try:
        # 创建屏幕
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("空闲屏幕测试")
        print(f"✅ 屏幕初始化成功: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # 创建空闲屏幕实例
        print("📺 创建空闲屏幕...")
        idle_screen = IdleScreen(screen)
        print("✅ 空闲屏幕创建成功")
        
        # 测试默认天气数据
        print("\n📊 测试默认天气数据...")
        print(f"   温度: {idle_screen.weather_data.get('temperature')}°C")
        print(f"   天气: {idle_screen.weather_data.get('condition')}")
        print(f"   位置: {idle_screen.weather_data.get('location')}")
        
        # 测试更新天气数据
        print("\n🔄 测试更新天气数据...")
        new_weather = {
            "temperature": 25,
            "condition": "cloudy",
            "location": "Beijing"
        }
        idle_screen.update({"weather": new_weather})
        print(f"   新温度: {idle_screen.weather_data.get('temperature')}°C")
        print(f"   新天气: {idle_screen.weather_data.get('condition')}")
        print(f"   新位置: {idle_screen.weather_data.get('location')}")
        
        # 运行测试循环
        print("\n🖥️ 开始显示测试（按 ESC 或关闭窗口退出）...")
        print("   屏幕上方应显示时钟")
        print("   屏幕下方应显示天气信息")
        
        clock = pygame.time.Clock()
        running = True
        start_time = time.time()
        test_duration = 10  # 测试10秒
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # 按空格键切换天气数据
                        test_weather = {
                            "temperature": 18,
                            "condition": "rain",
                            "location": "Shanghai"
                        }
                        idle_screen.update({"weather": test_weather})
                        print("🔄 已更新天气数据")
            
            # 渲染屏幕（时钟会自动更新）
            idle_screen.render()
            pygame.display.flip()
            
            # 控制帧率
            clock.tick(30)
            
            # 自动退出（可选）
            if time.time() - start_time > test_duration:
                print(f"\n⏱️ 测试时间到（{test_duration}秒），自动退出")
                running = False
        
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
    success = test_idle_screen()
    sys.exit(0 if success else 1)


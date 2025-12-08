"""
测试 NewsScreen 的新闻播报UI功能 - 在屏幕上显示
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pygame
from ui.screens import NewsScreen
from ui.constants import WINDOW_WIDTH, WINDOW_HEIGHT

# 初始化pygame（显示窗口）
pygame.init()


def test_news_display():
    """测试新闻显示功能 - 在屏幕上显示"""
    print("=" * 70)
    print("测试 NewsScreen - 显示假新闻")
    print("=" * 70)
    print("按 ESC 键或关闭窗口退出")
    print("-" * 70)
    
    # 创建实际窗口
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("News UI Test")
    
    news_screen = NewsScreen(screen)
    
    # 传入假新闻标题
    fake_titles = [
        "Breaking: Major event happened today",
        "Technology: New innovation announced",
        "Sports: Championship game results",
        "Business: Market update",
        "Weather: Sunny day expected"
    ]
    
    print(f"\n传入假新闻标题 ({len(fake_titles)} 条):")
    for i, title in enumerate(fake_titles, 1):
        print(f"  {i}. {title}")
    
    # 更新新闻数据
    news_screen.update({"titles": fake_titles})
    
    print(f"\n✅ 新闻数据更新成功")
    print(f"   标题数量: {len(news_screen.titles)}")
    print(f"   文本宽度: {news_screen.text_width} 像素")
    print(f"\n窗口已打开，请查看滚动效果...")
    
    # 主循环 - 显示滚动效果
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 渲染新闻屏幕（会自动滚动）
        news_screen.render()
        
        # 更新显示
        pygame.display.flip()
        
        # 控制帧率（60 FPS）
        clock.tick(60)
    
    pygame.quit()
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    test_news_display()


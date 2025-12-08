"""
录音屏幕测试文件 - 测试视频循环播放
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from ui.screens import ListeningScreen
from ui.constants import *
import config


def test_listening_screen():
    """测试录音屏幕视频播放"""
    print("=" * 60)
    print("🧪 录音屏幕测试 - 视频循环播放")
    print("=" * 60)
    
    # 初始化 pygame
    print("🔧 初始化 pygame...")
    pygame.init()
    
    try:
        # 创建屏幕
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("录音屏幕测试 - 视频循环播放")
        print(f"✅ 屏幕初始化成功: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # 创建录音屏幕实例
        print("📺 创建录音屏幕...")
        listening_screen = ListeningScreen(screen)
        print("✅ 录音屏幕创建成功")
        
        # 检查视频状态
        if listening_screen.video_cap and listening_screen.video_cap.isOpened():
            print(f"✅ 视频文件已加载: {listening_screen.video_path}")
            fps = listening_screen.video_fps
            print(f"📹 视频帧率: {fps:.2f} fps")
        else:
            print("⚠️ 视频文件未加载，将显示备用界面")
        
        # 运行测试循环
        print("\n🖥️ 开始视频播放测试...")
        print("   视频将循环播放")
        print("   按 ESC 或关闭窗口退出")
        print("   按空格键重新初始化视频")
        
        clock = pygame.time.Clock()
        running = True
        start_time = time.time()
        frame_count = 0
        test_duration = 30  # 测试30秒
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # 重新初始化视频
                        print("🔄 重新初始化视频...")
                        listening_screen.cleanup()
                        listening_screen._init_video()
                        if listening_screen.video_cap and listening_screen.video_cap.isOpened():
                            print("✅ 视频重新加载成功")
                        else:
                            print("⚠️ 视频重新加载失败")
            
            # 渲染屏幕（视频播放）
            listening_screen.render()
            pygame.display.flip()
            
            # 统计帧数
            frame_count += 1
            
            # 控制帧率
            clock.tick(30)
            
            # 每5秒输出一次统计信息
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and frame_count % 150 == 0:  # 每5秒输出一次
                fps_actual = frame_count / elapsed if elapsed > 0 else 0
                print(f"⏱️  已播放 {elapsed:.1f} 秒, 帧数: {frame_count}, 实际帧率: {fps_actual:.1f} fps")
            
            # 自动退出（可选）
            if elapsed > test_duration:
                print(f"\n⏱️ 测试时间到（{test_duration}秒），自动退出")
                running = False
        
        # 输出最终统计
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        print("\n" + "=" * 60)
        print("📊 测试统计")
        print("=" * 60)
        print(f"总播放时间: {total_time:.2f} 秒")
        print(f"总帧数: {frame_count}")
        print(f"平均帧率: {avg_fps:.2f} fps")
        print("=" * 60)
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理资源
        if 'listening_screen' in locals():
            listening_screen.cleanup()
        pygame.quit()
    
    return True


if __name__ == "__main__":
    success = test_listening_screen()
    sys.exit(0 if success else 1)


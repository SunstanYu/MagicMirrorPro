"""
测试 MusicAction 的音乐搜索和播放功能
"""
import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from actions.music import MusicAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_music_search():
    """测试音乐搜索功能"""
    print("=" * 70)
    print("测试 MusicAction - 音乐搜索功能")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 1: 搜索歌曲】")
    print("-" * 70)
    
    test_query = "jazz"
    
    try:
        tracks = music_action._search_tracks(test_query, limit=3)
        
        if tracks:
            print(f"✅ 成功搜索到 {len(tracks)} 首歌曲")
            print(f"\n   搜索结果（前 {len(tracks)} 首）:")
            for i, track in enumerate(tracks, 1):
                name = track.get("name", "未知")
                artist = track.get("artist_name", "未知艺术家")
                duration = track.get("duration", 0)
                print(f"     {i}. {name} - {artist} ({duration}秒)")
        else:
            print(f"❌ 未找到歌曲")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()


def test_music_execute_full_playback():
    """测试音乐执行功能（完整播放一首歌）"""
    print("\n\n" + "=" * 70)
    print("测试 MusicAction - 完整播放一首歌")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 2: 完整播放一首歌】")
    print("-" * 70)
    
    params = {"query": "jazz"}
    
    try:
        result = music_action.execute(params)
        
        if result["success"]:
            print(f"✅ 成功开始播放")
            print(f"   回复文本: {result['reply_text']}")
            print(f"   歌曲名: {result['data'].get('track_name', '未知')}")
            print(f"   艺术家: {result['data'].get('artist', '未知')}")
            print(f"   专辑: {result['data'].get('album', '未知')}")
            duration = result['data'].get('duration', 0)
            print(f"   时长: {duration}秒")
            
            # 等待播放线程启动
            print(f"\n   ⏳ 等待播放线程启动...")
            time.sleep(2)
            
            if music_action.is_playing():
                print(f"   ✅ 播放已开始")
                print(f"   ⏳ 等待播放完成（预计 {duration} 秒，实际播放时间约为 {duration * 0.8:.1f} 秒）...")
                
                # 轮询等待播放完成
                start_time = time.time()
                check_interval = 1.0  # 每秒检查一次
                last_status_time = start_time
                
                while music_action.is_playing():
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # 每5秒显示一次进度
                    if current_time - last_status_time >= 5.0:
                        print(f"   ⏳ 播放中... 已播放 {elapsed:.0f} 秒")
                        last_status_time = current_time
                    
                    time.sleep(check_interval)
                
                elapsed = time.time() - start_time
                print(f"   ✅ 播放完成！总耗时: {elapsed:.1f} 秒")
            else:
                print(f"   ⚠️ 播放未启动或已结束")
        else:
            print(f"❌ 执行失败: {result['reply_text']}")
            
    except KeyboardInterrupt:
        print(f"\n   ⏹️ 用户中断播放")
        music_action.stop()
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


def test_music_execute_empty_query():
    """测试空查询"""
    print("\n\n" + "=" * 70)
    print("测试 MusicAction - 空查询处理")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 3: 空查询】")
    print("-" * 70)
    
    params = {"query": ""}
    
    try:
        result = music_action.execute(params)
        
        if not result["success"]:
            print(f"✅ 正确处理空查询")
            print(f"   回复文本: {result['reply_text']}")
        else:
            print(f"❌ 应该返回失败，但返回了成功")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_music_execute_no_results():
    """测试无搜索结果"""
    print("\n\n" + "=" * 70)
    print("测试 MusicAction - 无搜索结果处理")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 4: 无搜索结果】")
    print("-" * 70)
    
    # 使用一个不太可能找到的查询
    params = {"query": "xxxxxxxxxxxxxnonexistentxxxxxxxxxxxxx"}
    
    try:
        result = music_action.execute(params)
        
        if not result["success"]:
            print(f"✅ 正确处理无搜索结果")
            print(f"   回复文本: {result['reply_text']}")
        else:
            print(f"❌ 应该返回失败，但返回了成功")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_music_stop_and_status():
    """测试停止播放和状态检查"""
    print("\n\n" + "=" * 70)
    print("测试 MusicAction - 停止播放和状态检查")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 5: 停止和状态检查】")
    print("-" * 70)
    
    # 初始状态
    print(f"   初始播放状态: {music_action.is_playing()}")
    
    # 开始播放（但不等待完成）
    params = {"query": "jazz"}
    try:
        result = music_action.execute(params)
        if result["success"]:
            print(f"   开始播放后状态: {music_action.is_playing()}")
            
            # 等待一小段时间
            time.sleep(1)
            print(f"   1秒后播放状态: {music_action.is_playing()}")
            
            # 停止播放
            music_action.stop()
            print(f"   停止后播放状态: {music_action.is_playing()}")
            
            # 再次停止（应该不会出错）
            music_action.stop()
            print(f"   再次停止后播放状态: {music_action.is_playing()}")
        else:
            print(f"   ⚠️ 无法开始播放，跳过状态测试")
    except Exception as e:
        print(f"   ⚠️ 播放测试失败: {e}")


def test_music_track_info():
    """测试歌曲信息提取"""
    print("\n\n" + "=" * 70)
    print("测试 MusicAction - 歌曲信息提取")
    print("=" * 70)
    
    music_action = MusicAction()
    
    print("\n【测试 6: 歌曲信息提取】")
    print("-" * 70)
    
    try:
        # 搜索歌曲
        tracks = music_action._search_tracks("jazz", limit=1)
        
        if tracks:
            track = tracks[0]
            track_info = music_action._get_track_info(track)
            
            print(f"✅ 成功提取歌曲信息")
            print(f"   歌曲名: {track_info.get('name', '未知')}")
            print(f"   艺术家: {track_info.get('artist', '未知')}")
            print(f"   专辑: {track_info.get('album', '未知')}")
            print(f"   时长: {track_info.get('duration', 0)}秒")
            print(f"   音频URL: {track_info.get('audio_url', '无')[:60]}...")
            print(f"   下载URL: {track_info.get('audio_download', '无')[:60]}...")
        else:
            print(f"❌ 未找到歌曲，无法测试")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("开始测试 MusicAction")
    print("=" * 70)
    
    try:
        test_music_search()
        test_music_execute_full_playback()
        test_music_execute_empty_query()
        test_music_execute_no_results()
        test_music_stop_and_status()
        test_music_track_info()
        
        print("\n\n" + "=" * 70)
        print("所有测试完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()


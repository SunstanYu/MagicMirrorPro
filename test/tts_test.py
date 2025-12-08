"""
TTS Client 简单测试
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tts.tts_client import TTSClient
import config


def test_tts_synthesize():
    """测试 TTS synthesize 方法"""
    print("=" * 60)
    print("🧪 TTS Client 测试")
    print("=" * 60)
    
    # 测试文本
    test_text = "Hello! This is a test of the TTS system."
    print(f"📝 测试文本: {test_text}")
    print()
    
    # 初始化客户端
    try:
        print("🔧 初始化 TTS 客户端...")
        client = TTSClient(engine="local")
        print("✅ TTS 客户端初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 测试合成
    print("🔄 开始合成语音...")
    start_time = time.time()
    
    try:
        result = client.synthesize(test_text)
        elapsed_time = time.time() - start_time
        
        # 显示结果
        print()
        print("=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        print(f"✅ 合成成功")
        print(f"⏱️  合成时间: {elapsed_time:.2f} 秒")
        print(f"📁 音频文件: {result.audio_path}")
        print(f"🎵 音频时长: {result.duration:.2f} 秒")
        print(f"📊 采样率: {result.sample_rate} Hz")
        print(f"📦 格式: {result.format}")
        print("=" * 60)
        
        # 检查文件是否存在
        if Path(result.audio_path).exists():
            file_size = Path(result.audio_path).stat().st_size
            print(f"✅ 音频文件已生成，大小: {file_size / 1024:.2f} KB")
        else:
            print(f"⚠️ 警告: 音频文件不存在")
        
        return True
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ 合成失败: {e}")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_tts_synthesize()
    sys.exit(0 if success else 1)


"""
测试 StreamingRecorder 模块
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from io_audio.streaming_recorder import StreamingRecorder
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


def test_streaming_recorder():
    """测试流式录音和识别"""
    print("=" * 60)
    print("测试 StreamingRecorder 模块")
    print("=" * 60)
    
    try:
        # 初始化流式录音器
        print("\n1. 初始化 StreamingRecorder...")
        recorder = StreamingRecorder(wake_word="hello")
        print("✅ 初始化成功")
        
        # 显示配置信息
        print(f"\n配置信息:")
        print(f"  - 唤醒词: {recorder.wake_word}")
        print(f"  - 采样率: {recorder.sample_rate} Hz")
        print(f"  - 设备ID: {recorder.device_id}")
        print(f"  - 音量增益: {recorder.volume_gain}x")
        print(f"  - 结果保存路径: {config.ASR_RESULT_FILE}")
        
        # 开始测试
        print("\n2. 开始录音和识别测试...")
        print("   请说 'hello' 唤醒，然后说一句话")
        print("   按 Ctrl+C 可以随时停止\n")
        
        # 执行录音和识别
        result = recorder.record_and_transcribe()
        
        # 显示结果
        print("\n" + "=" * 60)
        if result and result.text:
            print("✅ 识别成功！")
            print(f"\n识别结果:")
            print(f"  文本: {result.text}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  语言: {result.language_code}")
            print(f"\n结果已保存到: {config.ASR_RESULT_FILE}")
        else:
            print("⚠️ 未识别到内容")
            print("   可能的原因:")
            print("   - 未检测到唤醒词 'hello'")
            print("   - 识别过程中没有语音输入")
            print("   - 识别超时")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断测试")
        if 'recorder' in locals():
            recorder.stop()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        if 'recorder' in locals():
            recorder.stop()


if __name__ == "__main__":
    test_streaming_recorder()


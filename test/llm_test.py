"""
LLM Client 简单测试
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nlu.llm_client import LLMClient
import config


def test_llm_ask():
    """测试 LLM ask 方法：读取 ASR 结果文件，测试响应时间"""
    print("=" * 60)
    print("🧪 LLM Client 测试")
    print("=" * 60)
    
    # 读取 ASR 结果文件
    asr_file = config.ASR_RESULT_FILE
    if not asr_file.exists():
        print(f"❌ ASR 结果文件不存在: {asr_file}")
        print("   请先运行 ASR 识别，生成结果文件")
        return False
    
    # 读取文件内容
    with open(asr_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()
    
    if not prompt:
        print(f"❌ ASR 结果文件为空: {asr_file}")
        return False
    
    print(f"📝 输入文本: {prompt}")
    print()
    
    # 初始化客户端
    try:
        client = LLMClient()
        print("✅ LLM 客户端初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 测试 ask 方法并测量响应时间
    print("🔄 发送请求到 LLM...")
    start_time = time.time()
    
    try:
        result = client.ask(prompt)
        elapsed_time = time.time() - start_time
        
        # 显示结果
        print()
        print("=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        print(f"✅ 请求成功")
        print(f"⏱️  响应时间: {elapsed_time:.2f} 秒")
        print(f"📝 响应内容: {result.text}")
        if result.tokens_used:
            print(f"🔢 Token 使用: {result.tokens_used}")
        if result.model:
            print(f"🤖 模型: {result.model}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ 请求失败: {e}")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        return False


if __name__ == "__main__":
    success = test_llm_ask()
    sys.exit(0 if success else 1)

"""
测试 PatternNLU 的 news 关键词识别功能
"""
import sys
import os

# 添加项目根目录到路径（test/ 的父目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from nlu.pattern_nlu import PatternNLU
from nlu.models import Intent


def test_news_recognition():
    """测试 news 关键词识别"""
    print("=" * 60)
    print("测试 PatternNLU 的 news 关键词识别")
    print("=" * 60)
    
    # 初始化 PatternNLU
    pattern_nlu = PatternNLU()
    
    # 测试用例：应该识别为 news 的输入
    positive_test_cases = [
        "news",
        "show me news",
        "what's the news",
        "tell me the news",
        "get me news",
        "fetch the news",
        "read me news",
        "latest news",
        "current news",
        "today's news",
        "news of the day",
        "what's happening",
        "what's going on",
        "show me the latest news",
        "I want to see the news",
        "can you get me some news",
        "newspaper",
        "headlines",
        "headline",
    ]
    
    # 测试用例：不应该识别为 news 的输入
    negative_test_cases = [
        "hello",
        "how are you",
        "what time is it",
        "weather",
        "play music",
        "set timer",
        "nothing related to news",
        "I don't want news",
    ]
    
    print("\n【测试 1: 应该识别为 news 的输入】")
    print("-" * 60)
    passed = 0
    failed = 0
    
    for test_input in positive_test_cases:
        result = pattern_nlu.recognize(test_input)
        if result and result.action_name == "news":
            print(f"✅ PASS: '{test_input}' -> news")
            passed += 1
        else:
            print(f"❌ FAIL: '{test_input}' -> {result.action_name if result else 'None'}")
            failed += 1
    
    print(f"\n通过: {passed}/{len(positive_test_cases)}, 失败: {failed}/{len(positive_test_cases)}")
    
    print("\n【测试 2: 不应该识别为 news 的输入】")
    print("-" * 60)
    passed_neg = 0
    failed_neg = 0
    
    for test_input in negative_test_cases:
        result = pattern_nlu.recognize(test_input)
        if result is None or result.action_name != "news":
            print(f"✅ PASS: '{test_input}' -> {result.action_name if result else 'None'}")
            passed_neg += 1
        else:
            print(f"❌ FAIL: '{test_input}' -> news (不应该识别为 news)")
            failed_neg += 1
    
    print(f"\n通过: {passed_neg}/{len(negative_test_cases)}, 失败: {failed_neg}/{len(negative_test_cases)}")
    
    print("\n【测试 3: 参数提取测试】")
    print("-" * 60)
    
    param_test_cases = [
        ("show me tech news", {"category": "technology"}),
        ("get sports news", {"category": "sports"}),
        ("latest business news", {"category": "business"}),
        ("5 news", {"count": 5}),
        ("get 10 news", {"count": 10}),
        ("technology news", {"category": "technology"}),
    ]
    
    for test_input, expected_params in param_test_cases:
        result = pattern_nlu.recognize(test_input)
        if result and result.action_name == "news":
            # 检查参数
            params_match = True
            for key, value in expected_params.items():
                if result.action_params.get(key) != value:
                    params_match = False
                    break
            
            if params_match:
                print(f"✅ PASS: '{test_input}' -> params: {result.action_params}")
            else:
                print(f"⚠️  WARN: '{test_input}' -> params: {result.action_params}, expected: {expected_params}")
        else:
            print(f"❌ FAIL: '{test_input}' -> {result.action_name if result else 'None'}")
    
    print("\n【测试 4: 详细输出测试】")
    print("-" * 60)
    
    detailed_test = "show me the latest news"
    result = pattern_nlu.recognize(detailed_test)
    
    if result:
        print(f"输入: '{detailed_test}'")
        print(f"识别结果:")
        print(f"  - 意图类型: {result.intent_type}")
        print(f"  - 动作名称: {result.action_name}")
        print(f"  - 动作参数: {result.action_params}")
        print(f"  - 回复文本: {result.reply_text}")
        print(f"  - 置信度: {result.confidence}")
    else:
        print(f"❌ 未识别到意图: '{detailed_test}'")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_news_recognition()


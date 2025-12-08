"""
测试 NewsAction 的新闻标题获取功能（BBC RSS feed，仅标题）
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from actions.news import NewsAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_basic_news_fetch():
    """测试基本新闻标题获取功能"""
    print("=" * 70)
    print("测试 NewsAction - 基本新闻标题获取")
    print("=" * 70)
    
    news_action = NewsAction()
    
    print("\n【测试 1: 基本新闻标题获取（固定10条）】")
    print("-" * 70)
    
    params = {}  # params 已废弃，但保留以兼容接口
    
    try:
        result = news_action.execute(params)
        
        if result["success"]:
            titles = result['data']['titles']
            print(f"✅ 成功获取新闻标题")
            print(f"   回复文本: {result['reply_text']}")
            print(f"   获取数量: {len(titles)}")
            
            # 显示前5条标题
            print(f"\n   前5条标题:")
            for i, title in enumerate(titles[:5], 1):
                print(f"     {i}. {title[:70]}...")
        else:
            print(f"❌ 获取失败: {result['reply_text']}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_news_count():
    """测试固定数量（10条）的新闻标题获取"""
    print("\n\n" + "=" * 70)
    print("测试 NewsAction - 固定数量（10条）的新闻标题获取")
    print("=" * 70)
    
    news_action = NewsAction()
    
    print("\n【测试 2: 固定数量验证】")
    print("-" * 70)
    
    params = {}  # params 已废弃
    
    try:
        result = news_action.execute(params)
        
        if result["success"]:
            titles = result['data']['titles']
            actual_count = len(titles)
            
            if actual_count == 10:
                print(f"✅ 成功获取 {actual_count} 条新闻标题（符合预期）")
                print(f"   回复文本: {result['reply_text']}")
            elif actual_count > 0:
                print(f"⚠️  获取了 {actual_count} 条新闻标题（预期10条）")
                print(f"   回复文本: {result['reply_text']}")
            else:
                print(f"❌ 获取数量为0")
        else:
            print(f"❌ 获取失败: {result['reply_text']}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_news_titles_quality():
    """测试新闻标题质量"""
    print("\n\n" + "=" * 70)
    print("测试 NewsAction - 新闻标题质量验证")
    print("=" * 70)
    
    news_action = NewsAction()
    
    print("\n【测试 3: 标题质量验证】")
    print("-" * 70)
    
    params = {}
    
    try:
        result = news_action.execute(params)
        
        if result["success"]:
            titles = result['data']['titles']
            
            # 验证标题质量
            valid_titles = [t for t in titles if t and len(t.strip()) > 0]
            empty_titles = [t for t in titles if not t or len(t.strip()) == 0]
            
            print(f"✅ 成功获取 {len(titles)} 条新闻标题")
            print(f"   有效标题: {len(valid_titles)} 条")
            print(f"   空标题: {len(empty_titles)} 条")
            print(f"   标题有效性: {len(valid_titles)/len(titles)*100:.1f}%")
            
            # 显示标题示例
            if valid_titles:
                print(f"\n   标题示例（前 5 条）:")
                for i, title in enumerate(valid_titles[:5], 1):
                    print(f"     {i}. {title}")
        else:
            print(f"❌ 获取失败: {result['reply_text']}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_news_detailed_output():
    """测试新闻标题详细输出"""
    print("\n\n" + "=" * 70)
    print("测试 NewsAction - 新闻标题详细输出")
    print("=" * 70)
    
    news_action = NewsAction()
    
    print("\n【测试 4: 标题详细输出示例】")
    print("-" * 70)
    
    params = {}
    
    try:
        result = news_action.execute(params)
        
        if result["success"]:
            titles = result['data']['titles']
            print(f"\n成功: {result['success']}")
            print(f"回复: {result['reply_text']}")
            print(f"\n新闻标题列表 ({len(titles)} 条):")
            print("=" * 70)
            
            for i, title in enumerate(titles, 1):
                print(f"{i:2d}. {title}")
        else:
            print(f"❌ 获取失败: {result['reply_text']}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_news_data_structure():
    """测试返回数据结构"""
    print("\n\n" + "=" * 70)
    print("测试 NewsAction - 返回数据结构验证")
    print("=" * 70)
    
    news_action = NewsAction()
    
    print("\n【测试 5: 数据结构验证】")
    print("-" * 70)
    
    params = {}
    
    try:
        result = news_action.execute(params)
        
        # 验证顶层结构
        required_keys = ["reply_text", "data", "success"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"❌ 缺少必需的顶层键: {missing_keys}")
        else:
            print("✅ 顶层结构完整")
        
        # 验证 data 结构
        if "data" in result:
            data = result["data"]
            data_required_keys = ["titles"]
            data_missing_keys = [key for key in data_required_keys if key not in data]
            
            if data_missing_keys:
                print(f"❌ 缺少必需的 data 键: {data_missing_keys}")
            else:
                print("✅ data 结构完整")
                titles = data.get('titles', [])
                print(f"   标题数量: {len(titles)}")
                
                # 验证 titles 是列表
                if isinstance(titles, list):
                    print("✅ titles 是列表类型")
                else:
                    print(f"❌ titles 不是列表类型，而是 {type(titles).__name__}")
        
        # 验证标题结构
        if result.get("success") and result["data"].get("titles"):
            titles = result["data"]["titles"]
            if titles:
                first_title = titles[0]
                
                # 验证标题是字符串
                if isinstance(first_title, str):
                    print("✅ 标题是字符串类型")
                    print(f"   示例标题: {first_title[:60]}...")
                    print(f"   标题长度: {len(first_title)} 字符")
                else:
                    print(f"❌ 标题不是字符串类型，而是 {type(first_title).__name__}")
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("开始测试 NewsAction")
    print("=" * 70)
    
    try:
        test_basic_news_fetch()
        test_news_count()
        test_news_titles_quality()
        test_news_detailed_output()
        test_news_data_structure()
        
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


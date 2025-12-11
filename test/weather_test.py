"""
天气 API 测试文件
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.weather_client import WeatherClient
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


def test_weather_client():
    """测试天气客户端"""
    print("=" * 50)
    print("天气 API 测试")
    print("=" * 50)
    
    # 创建天气客户端
    print(f"\n📍 测试位置: {config.WEATHER_LOCATION}")
    print(f"🔑 API Key: {'已配置' if config.WEATHER_API_KEY else '未配置'}")
    print()
    
    weather_client = WeatherClient()
    
    # 测试获取天气
    print("🌤️ 正在获取天气数据...")
    print("-" * 50)
    
    try:
        weather_data = weather_client.get_weather()
        
        print(f"✅ 获取成功!")
        print(f"   位置: {weather_data.get('location', 'N/A')}")
        print(f"   温度: {weather_data.get('temperature', 'N/A')}°C")
        print(f"   天气: {weather_data.get('condition', 'N/A')}")
        print(f"   湿度: {weather_data.get('humidity', 'N/A')}%")
        print(f"   风速: {weather_data.get('wind_speed', 'N/A')} m/s")
        print(f"   成功: {weather_data.get('success', False)}")
        
        if weather_data.get('success'):
            print("\n✅ 测试通过：天气数据获取成功！")
            return True
        else:
            print("\n⚠️ 测试警告：使用了模拟数据")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_locations():
    """测试多个城市"""
    print("\n" + "=" * 50)
    print("多城市测试")
    print("=" * 50)
    
    test_cities = [
        "Ithaca,US",
        "New York,US",
        "Los Angeles,US",
        "Chicago,US"
    ]
    
    weather_client = WeatherClient()
    
    for city in test_cities:
        print(f"\n📍 测试城市: {city}")
        print("-" * 50)
        
        try:
            weather_data = weather_client.get_weather(city)
            
            if weather_data.get('success'):
                print(f"✅ {city}: {weather_data.get('temperature')}°C - {weather_data.get('condition')}")
            else:
                print(f"⚠️ {city}: 获取失败，使用模拟数据")
                
        except Exception as e:
            print(f"❌ {city}: 错误 - {e}")


if __name__ == "__main__":
    print("\n")
    
    # 基本测试
    success = test_weather_client()
    
    # 多城市测试（可选）
    if success:
        print("\n是否测试多个城市？(y/N): ", end="")
        try:
            choice = input().strip().lower()
            if choice == 'y':
                test_multiple_locations()
        except:
            pass
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50 + "\n")


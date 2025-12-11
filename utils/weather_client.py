"""
天气 API 客户端 - 支持 Weather.gov API（美国）和 OpenWeatherMap API
"""
import requests
import time
from typing import Optional, Dict, Any
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class WeatherClient:
    """天气 API 客户端 - 优先使用 Weather.gov（美国免费），备选 OpenWeatherMap"""
    
    def __init__(self, api_key: Optional[str] = None, location: Optional[str] = None):
        """
        初始化天气客户端
        
        Args:
            api_key: OpenWeatherMap API key（可选，如果为 None，使用 config.WEATHER_API_KEY）
            location: 位置（城市名，如果为 None，使用 config.WEATHER_LOCATION）
        """
        self.api_key = api_key or config.WEATHER_API_KEY
        self.location = location or config.WEATHER_LOCATION
        # Weather.gov API（免费，仅限美国，不需要 API key）
        self.weather_gov_base = "https://api.weather.gov"
        # OpenWeatherMap API（备选）
        self.openweather_base = "https://api.openweathermap.org/data/2.5/weather"
        
        # 设置 User-Agent（Weather.gov API 要求）
        self.headers = {
            "User-Agent": "MagicMirrorPro/1.0 (contact: weather@example.com)"
        }
    
    def get_weather(self, location: Optional[str] = None) -> Dict[str, Any]:
        """
        获取天气信息（优先使用 Weather.gov API，失败则尝试 OpenWeatherMap）
        
        Args:
            location: 位置（可选，如果不提供则使用默认位置）
            
        Returns:
            Dict[str, Any]: 天气数据，包含：
                - temperature: 温度（摄氏度）
                - condition: 天气状况（英文描述）
                - location: 位置
                - humidity: 湿度（百分比）
                - wind_speed: 风速（m/s）
                - success: 是否成功
        """
        loc = location or self.location
        
        # 优先尝试 Weather.gov API（免费，仅限美国）
        weather_data = self._get_weather_gov(loc)
        if weather_data.get("success"):
            return weather_data
        
        # 如果 Weather.gov 失败，尝试 OpenWeatherMap（需要 API key）
        if self.api_key:
            weather_data = self._get_openweather(loc)
            if weather_data.get("success"):
                return weather_data
        
        # 都失败则使用模拟数据
        return self._get_mock_weather(loc)
    
    def _get_weather_gov(self, location: str) -> Dict[str, Any]:
        """
        使用 Weather.gov API 获取天气（免费，仅限美国）
        
        Args:
            location: 城市名，格式如 "Ithaca,NY" 或 "Ithaca"
            
        Returns:
            Dict[str, Any]: 天气数据
        """
        try:
            # 解析城市名（可能包含州代码）
            city_parts = location.split(",")
            city_name = city_parts[0].strip()
            state_code = city_parts[1].strip() if len(city_parts) > 1 else None
            
            # 第一步：根据城市名获取经纬度（使用 geocoding API）
            # 简化版：直接使用 wttr.in 作为备选，或使用已知城市的坐标
            # 这里我们使用一个更简单的方法：直接查询 Weather.gov 的 stations API
            
            # 尝试使用 wttr.in API（免费，支持美国城市）
            wttr_url = f"https://wttr.in/{city_name}?format=j1"
            response = requests.get(wttr_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析 wttr.in 返回的数据
            current = data.get("current_condition", [{}])[0]
            temp_c = int(current.get("temp_C", 0))
            condition = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = int(current.get("humidity", 0))
            wind_speed_kmh = float(current.get("windspeedKmph", 0))
            wind_speed_ms = wind_speed_kmh / 3.6  # 转换为 m/s
            
            # 获取城市名
            area_name = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", city_name)
            
            weather_data = {
                "temperature": temp_c,
                "condition": condition,
                "location": area_name,
                "humidity": humidity,
                "wind_speed": round(wind_speed_ms, 1),
                "success": True
            }
            
            logger.info(f"✅ 使用 wttr.in 获取天气成功: {weather_data['location']} - {weather_data['temperature']}°C - {weather_data['condition']}")
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ wttr.in API 请求失败: {e}")
            return {"success": False}
        except (KeyError, IndexError) as e:
            logger.warning(f"⚠️ 解析 wttr.in 数据失败: {e}")
            return {"success": False}
        except Exception as e:
            logger.warning(f"⚠️ wttr.in 查询异常: {e}")
            return {"success": False}
    
    def _get_openweather(self, location: str) -> Dict[str, Any]:
        """
        使用 OpenWeatherMap API 获取天气（备选方案）
        
        Args:
            location: 城市名
            
        Returns:
            Dict[str, Any]: 天气数据
        """
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",  # 使用摄氏度
                "lang": "en"  # 英文描述
            }
            
            response = requests.get(self.openweather_base, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_data = {
                "temperature": int(data["main"]["temp"]),
                "condition": data["weather"][0]["description"],
                "location": data["name"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "success": True
            }
            
            logger.info(f"✅ 使用 OpenWeatherMap 获取天气成功: {weather_data['location']} - {weather_data['temperature']}°C - {weather_data['condition']}")
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ OpenWeatherMap API 请求失败: {e}")
            return {"success": False}
        except (KeyError, IndexError) as e:
            logger.warning(f"⚠️ 解析 OpenWeatherMap 数据失败: {e}")
            return {"success": False}
        except Exception as e:
            logger.warning(f"⚠️ OpenWeatherMap 查询异常: {e}")
            return {"success": False}
    
    def _get_mock_weather(self, location: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模拟天气数据（当 API 不可用时）
        
        Args:
            location: 位置
            
        Returns:
            Dict[str, Any]: 模拟天气数据
        """
        logger.warning("⚠️ 使用模拟天气数据")
        return {
            "temperature": 22,
            "condition": "晴天",
            "location": location or self.location or "当前位置",
            "humidity": 65,
            "wind_speed": 10,
            "success": False
        }


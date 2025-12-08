"""
Pygame 屏幕/场景类
"""
import pygame
import datetime
import os
from typing import Optional, Dict, Any, List
from ui.constants import *
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseScreen:
    """屏幕基类"""
    
    def __init__(self, surface: pygame.Surface):
        """
        初始化屏幕
        
        Args:
            surface: Pygame 绘制表面
        """
        self.surface = surface
        self.font_large = pygame.font.Font(None, FONT_SIZE_LARGE)
        self.font_medium = pygame.font.Font(None, FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.Font(None, FONT_SIZE_SMALL)
    
    def render(self) -> None:
        """渲染屏幕（子类实现）"""
        pass
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        更新屏幕数据
        
        Args:
            data: 更新数据
        """
        pass


class IdleScreen(BaseScreen):
    """空闲屏幕"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化空闲屏幕"""
        super().__init__(surface)
        self.weather_data: Optional[Dict[str, Any]] = {
        "temperature": 22,
        "condition": "晴天",
        "location": "当前位置"
    }
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新天气数据"""
        if data:
            self.weather_data = data.get("weather")
    
    def render(self) -> None:
        """渲染空闲屏幕"""
        self.surface.fill(COLOR_BG)
        
        # 上方显示时钟
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        # 中文星期映射
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekdays[now.weekday()]
        date_str = now.strftime(f"%Y-%m-%d {weekday}")
        
        # 显示时间（大字体）
        time_text = self.font_large.render(time_str, True, COLOR_TEXT)
        time_rect = time_text.get_rect(center=(WINDOW_WIDTH // 2, 80))
        self.surface.blit(time_text, time_rect)
        
        # 显示日期（中等字体）
        date_text = self.font_medium.render(date_str, True, COLOR_TEXT)
        date_rect = date_text.get_rect(center=(WINDOW_WIDTH // 2, 110))
        self.surface.blit(date_text, date_rect)
        
        # 下方显示天气
        if self.weather_data:
            self._render_weather()
        else:
            # 如果没有天气数据，显示提示
            weather_text = self.font_medium.render("天气信息加载中...", True, COLOR_TEXT)
            weather_rect = weather_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100))
            self.surface.blit(weather_text, weather_rect)
    
    def _render_weather(self) -> None:
        """渲染天气信息"""
        if not self.weather_data:
            return
        
        y_pos = WINDOW_HEIGHT - 80
        x_pos = WINDOW_WIDTH // 2
        
        # 显示温度
        if "temperature" in self.weather_data:
            temp = self.weather_data["temperature"]
            temp_text = self.font_large.render(f"{temp}°C", True, COLOR_SUCCESS)
            temp_rect = temp_text.get_rect(center=(WINDOW_WIDTH // 2, y_pos))
            self.surface.blit(temp_text, temp_rect)
            y_pos += 50 
        
        # 显示天气状况
        if "condition" in self.weather_data:
            condition = self.weather_data["condition"]
            condition_text = self.font_medium.render(condition, True, COLOR_TEXT)
            condition_rect = condition_text.get_rect(center=(x_pos-50, y_pos))
            self.surface.blit(condition_text, condition_rect)
        
        # 显示位置（如果有）
        if "location" in self.weather_data:
            location = self.weather_data["location"]
            location_text = self.font_small.render(location, True, COLOR_TEXT)
            location_rect = location_text.get_rect(center=(x_pos+50, y_pos))
            self.surface.blit(location_text, location_rect)


class ListeningScreen(BaseScreen):
    """录音屏幕 - 循环播放图片"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化录音屏幕"""
        super().__init__(surface)
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self._init_images()
    
    def _init_images(self):
        """初始化图片列表"""
        try:
            image_dir = "/home/pi/MagicMirrorPro/resources/listening"
            if os.path.exists(image_dir):
                # 获取所有图片文件，按文件名排序
                files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
                self.image_paths = [os.path.join(image_dir, f) for f in files]
                
                # 加载所有图片
                for img_path in self.image_paths:
                    try:
                        img = pygame.image.load(img_path)
                        # 缩放图片以适应屏幕
                        img = self._scale_image(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载图片失败 {img_path}: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 listening 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何图片")
            else:
                logger.warning(f"⚠️ 图片目录不存在: {image_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应屏幕"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 计算缩放比例（保持比例）
        scale = min(screen_w / img_w, screen_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        pass
    
    def render(self) -> None:
        """渲染录音屏幕 - 循环播放图片"""
        if not self.images:
            self._render_fallback()
            return
        
        # 更新帧计数器
        self.frame_counter += 1
        if self.frame_counter >= self.frame_interval:
            self.frame_counter = 0
            # 切换到下一张图片
            self.current_frame_index = (self.current_frame_index + 1) % len(self.images)
        
        # 获取当前图片
        current_img = self.images[self.current_frame_index]
        
        # 清空屏幕（填黑）
        self.surface.fill((0, 0, 0))
        
        # 计算居中位置并绘制
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = (screen_h - img_h) // 2
        self.surface.blit(current_img, (x, y))
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        self.surface.fill(COLOR_BG)
        text = self.font_large.render("Recording...", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)
    
    def cleanup(self):
        """清理资源（不清空图片，因为屏幕实例会被复用）"""
        # 不清空图片，因为 UI 管理器会复用同一个屏幕实例
        # 如果清空图片，第二次切换时会显示 "Recording..."
        # 如果需要重新加载图片，可以在切换模式时调用 _init_images()
        pass


class ActionScreen(BaseScreen):
    """动作执行屏幕"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化动作屏幕"""
        super().__init__(surface)
        self.data: Optional[Dict[str, Any]] = None
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新动作数据"""
        self.data = data
    
    def render(self) -> None:
        """渲染动作屏幕"""
        self.surface.fill(COLOR_BG)
        
        if self.data is None:
            text = self.font_medium.render("执行动作中...", True, COLOR_TEXT)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.surface.blit(text, text_rect)
            return
        
        # 显示动作标题
        action_name = self.data.get("action_name", "动作")
        title = self.font_large.render(f"动作: {action_name}", True, COLOR_PRIMARY)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.surface.blit(title, title_rect)
        
        # 显示动作数据
        data = self.data.get("data", {})
        y_offset = 120
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                continue
            text = self.font_medium.render(f"{key}: {value}", True, COLOR_TEXT)
            self.surface.blit(text, (50, y_offset))
            y_offset += 40
        
        # 如果是天气数据，显示特殊格式
        if "temperature" in data:
            temp_text = self.font_large.render(f"{data['temperature']}°C", True, COLOR_SUCCESS)
            temp_rect = temp_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.surface.blit(temp_text, temp_rect)
            
            if "condition" in data:
                condition_text = self.font_medium.render(data["condition"], True, COLOR_TEXT)
                condition_rect = condition_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
                self.surface.blit(condition_text, condition_rect)


class TalkingScreen(BaseScreen):
    """说话屏幕 - 循环播放图片"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化说话屏幕"""
        super().__init__(surface)
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self._init_images()
    
    def _init_images(self):
        """初始化图片列表"""
        try:
            image_dir = "/home/pi/MagicMirrorPro/resources/talking"
            if os.path.exists(image_dir):
                # 获取所有图片文件，按文件名排序
                files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
                self.image_paths = [os.path.join(image_dir, f) for f in files]
                
                # 加载所有图片
                for img_path in self.image_paths:
                    try:
                        img = pygame.image.load(img_path)
                        # 缩放图片以适应屏幕
                        img = self._scale_image(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载图片失败 {img_path}: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 talking 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何图片")
            else:
                logger.warning(f"⚠️ 图片目录不存在: {image_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应屏幕"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 计算缩放比例（保持比例）
        scale = min(screen_w / img_w, screen_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        # 如果图片列表为空，重新初始化（可能被 cleanup 清空了）
        if not self.images:
            self._init_images()
    
    def render(self) -> None:
        """渲染说话屏幕 - 循环播放图片"""
        if not self.images:
            self._render_fallback()
            return
        
        # 更新帧计数器
        self.frame_counter += 1
        if self.frame_counter >= self.frame_interval:
            self.frame_counter = 0
            # 切换到下一张图片
            self.current_frame_index = (self.current_frame_index + 1) % len(self.images)
        
        # 获取当前图片
        current_img = self.images[self.current_frame_index]
        
        # 清空屏幕（填黑）
        self.surface.fill((0, 0, 0))
        
        # 计算居中位置并绘制
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = (screen_h - img_h) // 2
        self.surface.blit(current_img, (x, y))
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        self.surface.fill(COLOR_BG)
        text = self.font_large.render("Speaking...", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)
    
    def cleanup(self):
        """清理资源（不清空图片，因为屏幕实例会被复用）"""
        # 不清空图片，因为 UI 管理器会复用同一个屏幕实例
        # 如果清空图片，第二次切换时会显示 fallback 界面
        # 如果需要重新加载图片，可以在切换模式时调用 _init_images()
        pass


class NewsScreen(BaseScreen):
    """新闻播报屏幕 - 标题从右向左滚动"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化新闻屏幕"""
        super().__init__(surface)
        self.titles: List[str] = []
        self.scroll_x = 0  # 滚动位置
        self.scroll_speed = 1  # 滚动速度（像素/帧）- 调慢
        self.separator = "  |  "  # 标题间隔标志
        self.combined_text = ""  # 合并后的文本
        self.text_surface: Optional[pygame.Surface] = None
        self.text_width = 0
        self.screen_title = "Latest News"  # 屏幕标题
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新新闻数据"""
        if data:
            titles = data.get("titles", [])
            if titles:
                self.titles = titles
                # 合并所有标题，用分隔符连接
                self.combined_text = self.separator.join(self.titles)
                # 如果标题数量大于1，在末尾也添加分隔符，形成循环效果
                if len(self.titles) > 1:
                    self.combined_text += self.separator
                # 渲染文本表面（使用大字体）
                self.text_surface = self.font_large.render(self.combined_text, True, COLOR_TEXT)
                self.text_width = self.text_surface.get_width()
                # 重置滚动位置
                self.scroll_x = WINDOW_WIDTH
    
    def render(self) -> None:
        """渲染新闻屏幕 - 滚动显示标题"""
        self.surface.fill(COLOR_BG)
        
        # 绘制屏幕标题（顶部居中）
        title_text = self.font_large.render(self.screen_title, True, COLOR_PRIMARY)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 30))
        self.surface.blit(title_text, title_rect)
        
        if not self.titles:
            # 如果没有标题，显示提示
            text = self.font_medium.render("Loading news...", True, COLOR_TEXT)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.surface.blit(text, text_rect)
            return
        
        if not self.text_surface:
            return
        
        # 计算垂直居中位置（在标题下方）
        y_pos = (WINDOW_HEIGHT - FONT_SIZE_LARGE) // 2 + 20
        
        # 从右向左滚动
        self.scroll_x -= self.scroll_speed
        
        # 如果文本完全滚出屏幕左侧，从右侧重新开始（形成循环）
        if self.scroll_x + self.text_width < 0:
            self.scroll_x = WINDOW_WIDTH
        
        # 绘制主文本
        self.surface.blit(self.text_surface, (self.scroll_x, y_pos))
        
        # 绘制重复的文本，形成无缝循环
        # 计算右侧重复文本的位置
        repeat_x = self.scroll_x + self.text_width
        # 如果重复文本在屏幕内，绘制它
        if repeat_x < WINDOW_WIDTH:
            self.surface.blit(self.text_surface, (repeat_x, y_pos))


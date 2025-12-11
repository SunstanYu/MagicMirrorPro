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
        "temperature": -5,
        "condition": "Snowy",
        "location": "Ithaca, NY"
        }
        # 定义颜色（与 testui.py 一致）
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_GRAY = (170, 170, 170)
        self.COLOR_GOLD = (255, 215, 0)
        # 定义字体（与 testui.py 一致）
        self.font_time = pygame.font.SysFont('monospace', 80, bold=True)  # 特大时间
        self.font_date = pygame.font.SysFont('monospace', 20)             # 日期
        self.font_weather = pygame.font.SysFont('monospace', 30)          # 天气
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        if data:
            self.weather_data = data.get("weather")
    
    def render(self) -> None:
        """渲染空闲屏幕（与 testui.py 完全一致）"""
        self.surface.fill(self.COLOR_BLACK)
        
        # 1. 获取当前时间
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")  # 例如：23:13
        date_str = now.strftime("%Y/%m/%d")  # 例如：2025/12/10
        
        # 2. 渲染时间
        time_surface = self.font_time.render(time_str, True, self.COLOR_GOLD)
        # 将时间放在屏幕中央偏上
        time_rect = time_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT * 0.35))
        self.surface.blit(time_surface, time_rect)
        
        # 3. 渲染日期
        date_surface = self.font_date.render(date_str, True, self.COLOR_GRAY)
        # 放在时间下方，略微留空
        date_rect = date_surface.get_rect(center=(WINDOW_WIDTH // 2, time_rect.bottom + 10))
        self.surface.blit(date_surface, date_rect)
        
        # 4. 渲染天气
        self._render_weather()
    
    def _render_weather(self) -> None:
        """渲染天气信息（与 testui.py 完全一致）"""
        if not self.weather_data:
            return
        
        # 1. 获取天气数据
        temp = self.weather_data.get("temperature", -5)
        desc = self.weather_data.get("condition", "Snowy")
        temp_str = f"{round(temp)}°C"
        desc_str = desc
        
        # 2. 渲染温度 (较大，突出显示)
        temp_surface = self.font_weather.render(temp_str, True, self.COLOR_WHITE)
        temp_rect = temp_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT * 0.80))
        self.surface.blit(temp_surface, temp_rect)
        
        # 3. 渲染描述 (较小，居中在底部)
        desc_surface = self.font_date.render(desc_str, True, self.COLOR_GRAY)
        desc_rect = desc_surface.get_rect(center=(WINDOW_WIDTH // 2, temp_rect.bottom + 5))
        self.surface.blit(desc_surface, desc_rect)


class ListeningScreen(BaseScreen):
    """录音屏幕 - 下方2/3显示图片动画，上方1/3不显示文字"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化录音屏幕"""
        super().__init__(surface)
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self.appearing_count = 0  # appearing 图片数量
        self._init_images()
    
    def _init_images(self, show_appearing: bool = False):
        """初始化图片列表"""
        self.images = []
        self.appearing_count = 0
        
        try:
            # 如果需要显示 appearing 动画，先加载 appearing 图片
            if show_appearing:
                appearing_dir = "/home/pi/MagicMirrorPro/resources/appearing"
                if os.path.exists(appearing_dir):
                    appearing_files = sorted([f for f in os.listdir(appearing_dir) if f.endswith('.png')])
                    for f in appearing_files:
                        try:
                            img = pygame.image.load(os.path.join(appearing_dir, f))
                            img = self._scale_image_for_bottom_area(img)
                            self.images.append(img)
                            self.appearing_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ 加载 appearing 图片失败: {e}")
            
            # 加载 listening 图片
            listening_dir = "/home/pi/MagicMirrorPro/resources/listening"
            if os.path.exists(listening_dir):
                listening_files = sorted([f for f in os.listdir(listening_dir) if f.endswith('.png')])
                for f in listening_files:
                    try:
                        img = pygame.image.load(os.path.join(listening_dir, f))
                        img = self._scale_image_for_bottom_area(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载 listening 图片失败: {e}")
            
            if self.images:
                logger.info(f"✅ 加载了 {len(self.images)} 张图片 (appearing: {self.appearing_count}, listening: {len(self.images) - self.appearing_count})")
            else:
                logger.warning("⚠️ 没有加载到任何图片")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方2/3区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方2/3区域的高度
        bottom_area_h = int(screen_h * 2 / 3)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        if data and data.get("show_appearing", False):
            self.current_frame_index = 0
            self.frame_counter = 0
            self._init_images(show_appearing=True)
    
    def render(self) -> None:
        """渲染录音屏幕 - 下方2/3显示图片，上方1/3不显示文字"""
        # 清空屏幕
        self.surface.fill((0, 0, 0))
        
        # 渲染上方1/3区域的文字
        self._render_text_area()
        
        if not self.images:
            self._render_fallback()
            return
        
        # 更新帧计数器
        self.frame_counter += 1
        if self.frame_counter >= self.frame_interval:
            self.frame_counter = 0
            self.current_frame_index += 1
            # 如果播放完所有图片，循环到 listening 图片开始位置
            if self.current_frame_index >= len(self.images):
                self.current_frame_index = self.appearing_count if self.appearing_count > 0 else 0
        
        # 获取当前图片
        current_img = self.images[self.current_frame_index]
        
        # 计算下方2/3区域的起始位置
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)  # 上方1/3区域高度
        bottom_area_y = top_area_h  # 下方2/3区域起始Y坐标
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (int(screen_h * 2 / 3) - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))
    
    def _render_text_area(self):
        """渲染上方1/3区域的文字"""
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)
        
        lines = ["How can I help you?"]
            # 绘制文字（垂直居中在上方1/3区域）
        y_start = (top_area_h - len(lines) * FONT_SIZE_MEDIUM) // 2
        for i, line in enumerate(lines):
            text_surface = self.font_medium.render(line, True, COLOR_TEXT)
            text_rect = text_surface.get_rect(center=(screen_w // 2, y_start + i * FONT_SIZE_MEDIUM))
            self.surface.blit(text_surface, text_rect)
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        self.surface.fill(COLOR_BG)
        text = self.font_large.render("Recording...", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)
    
    def cleanup(self):
        """清理资源（不清空图片，因为屏幕实例会被复用）"""
        pass


class ThinkingScreen(BaseScreen):
    """思考屏幕 - 下方2/3显示图片动画，上方1/3显示识别到的文字"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化思考屏幕"""
        super().__init__(surface)
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self.recognized_text: str = ""  # 识别到的文字
        self._init_images()
    
    def _init_images(self):
        """初始化图片列表"""
        try:
            image_dir = "/home/pi/MagicMirrorPro/resources/noding"
            if os.path.exists(image_dir):
                # 获取所有图片文件，按文件名排序
                files = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
                self.image_paths = [os.path.join(image_dir, f) for f in files]
                
                # 加载所有图片
                for img_path in self.image_paths:
                    try:
                        img = pygame.image.load(img_path)
                        # 缩放图片以适应下方2/3区域
                        img = self._scale_image_for_bottom_area(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载图片失败 {img_path}: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 thinking 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何图片")
            else:
                logger.warning(f"⚠️ 图片目录不存在: {image_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方2/3区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方2/3区域的高度
        bottom_area_h = int(screen_h * 2 / 3)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        if data:
            # 获取识别到的文字
            self.recognized_text = data.get("text", "")
        # 如果图片列表为空，重新初始化
        if not self.images:
            self._init_images()
    
    def render(self) -> None:
        """渲染思考屏幕 - 下方2/3显示图片，上方1/3显示识别文字"""
        # 清空屏幕
        self.surface.fill((0, 0, 0))
        
        # 渲染上方1/3区域的文字
        self._render_text_area()
        
        # 渲染下方2/3区域的图片
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
        
        # 计算下方2/3区域的起始位置
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)  # 上方1/3区域高度
        bottom_area_y = top_area_h  # 下方2/3区域起始Y坐标
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (int(screen_h * 2 / 3) - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))
    
    def _render_text_area(self):
        """渲染上方1/3区域的文字"""
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)
        
        if self.recognized_text:
            # 显示识别到的文字（自动换行）
            words = self.recognized_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surface = self.font_medium.render(test_line, True, COLOR_TEXT)
                if test_surface.get_width() <= screen_w - 20:  # 留10像素边距
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # 绘制文字（垂直居中在上方1/3区域）
            y_start = (top_area_h - len(lines) * FONT_SIZE_MEDIUM) // 2
            for i, line in enumerate(lines):
                text_surface = self.font_medium.render(line, True, COLOR_TEXT)
                text_rect = text_surface.get_rect(center=(screen_w // 2, y_start + i * FONT_SIZE_MEDIUM))
                self.surface.blit(text_surface, text_rect)
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        text = self.font_large.render("Thinking...", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)
    
    def cleanup(self):
        """清理资源（不清空图片，因为屏幕实例会被复用）"""
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
    """说话屏幕 - 下方2/3显示图片动画，上方1/3显示回复文字"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化说话屏幕"""
        super().__init__(surface)
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self.reply_text: str = ""  # 回复文字
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
                        # 缩放图片以适应下方2/3区域
                        img = self._scale_image_for_bottom_area(img)
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
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方2/3区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方2/3区域的高度
        bottom_area_h = int(screen_h * 2 / 3)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新屏幕数据"""
        if data:
            # 获取回复文字
            self.reply_text = data.get("text", "")
        # 如果图片列表为空，重新初始化
        if not self.images:
            self._init_images()
    
    def render(self) -> None:
        """渲染说话屏幕 - 下方2/3显示图片，上方1/3显示回复文字"""
        # 清空屏幕
        self.surface.fill((0, 0, 0))
        
        # 渲染上方1/3区域的文字
        self._render_text_area()
        
        # 渲染下方2/3区域的图片
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
        
        # 计算下方2/3区域的起始位置
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)  # 上方1/3区域高度
        bottom_area_y = top_area_h  # 下方2/3区域起始Y坐标
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (int(screen_h * 2 / 3) - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))
    
    def _render_text_area(self):
        """渲染上方1/3区域的文字"""
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)
        
        if self.reply_text:
            # 显示回复文字（自动换行）
            words = self.reply_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surface = self.font_medium.render(test_line, True, COLOR_TEXT)
                if test_surface.get_width() <= screen_w - 20:  # 留10像素边距
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # 绘制文字（垂直居中在上方1/3区域）
            y_start = (top_area_h - len(lines) * FONT_SIZE_MEDIUM) // 2 + 15
            for i, line in enumerate(lines):
                text_surface = self.font_medium.render(line, True, COLOR_TEXT)
                text_rect = text_surface.get_rect(center=(screen_w // 2, y_start + i * FONT_SIZE_MEDIUM))
                self.surface.blit(text_surface, text_rect)
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        text = self.font_large.render("Speaking...", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)
    
    def cleanup(self):
        """清理资源（不清空图片，因为屏幕实例会被复用）"""
        pass


class NewsScreen(BaseScreen):
    """新闻播报屏幕 - 上1/3显示当前新闻标题，下2/3显示图片动画"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化新闻屏幕"""
        super().__init__(surface)
        self.current_title = ""  # 当前正在播报的新闻标题
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self._init_images()
    
    def _init_images(self):
        """初始化图片列表"""
        try:
            image_dir = "/home/pi/MagicMirrorPro/resources/newspaper"
            if os.path.exists(image_dir):
                # 获取所有图片文件，按文件名排序
                files = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
                self.image_paths = [os.path.join(image_dir, f) for f in files]
                
                # 加载所有图片
                for img_path in self.image_paths:
                    try:
                        img = pygame.image.load(img_path)
                        # 缩放图片以适应下方2/3区域
                        img = self._scale_image_for_bottom_area(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载图片失败 {img_path}: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 newspaper 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何图片")
            else:
                logger.warning(f"⚠️ 图片目录不存在: {image_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方2/3区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方2/3区域的高度
        bottom_area_h = int(screen_h * 2 / 3)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新新闻数据"""
        if data:
            # 优先使用 current_title，如果没有则从 titles 中获取当前索引的标题
            current_title = data.get("current_title", "")
            if not current_title:
                titles = data.get("titles", [])
                current_index = data.get("current_index", 0)
                if titles and 0 <= current_index < len(titles):
                    current_title = titles[current_index]
            
            if current_title:
                self.current_title = current_title
                logger.info(f"📰 NewsScreen 更新: {current_title[:50]}...")
            else:
                logger.warning("⚠️ NewsScreen 收到空标题")
        else:
            logger.warning("⚠️ NewsScreen update 收到 None 数据")
    
    def render(self) -> None:
        """渲染新闻屏幕 - 上1/3显示当前新闻标题，下2/3显示图片动画"""
        # 清空屏幕
        self.surface.fill(COLOR_BG)
        
        # 渲染上方1/3区域的新闻标题
        self._render_title_area()
        
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
        
        # 计算下方2/3区域的起始位置
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)  # 上方1/3区域高度
        bottom_area_y = top_area_h  # 下方2/3区域起始Y坐标
        bottom_area_h = int(screen_h * 2 / 3)  # 下方2/3区域高度
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (bottom_area_h - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))
    
    def _render_title_area(self):
        """渲染顶部一行的新闻标题 - 从右向左滚动"""
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)
        
        # 计算垂直居中位置（在顶部区域内）
        y_center = top_area_h // 2
        
        if not hasattr(self, 'scroll_x'):
            self.scroll_x = screen_w  # 初始位置在屏幕右侧
            self.text_surface = None
            self.text_width = 0
        
        if self.current_title:
            # 如果标题变化了，重新渲染文本表面
            if not self.text_surface or not hasattr(self, '_last_title') or self._last_title != self.current_title:
                self.text_surface = self.font_large.render(self.current_title, True, COLOR_TEXT)
                self.text_width = self.text_surface.get_width()
                self._last_title = self.current_title
                # 如果文本宽度小于屏幕宽度，从右侧开始；否则从屏幕右侧外开始
                if self.text_width < screen_w:
                    self.scroll_x = screen_w
                else:
                    self.scroll_x = screen_w  # 从屏幕右侧开始
            
            # 从右向左滚动
            self.scroll_x -= 2  # 滚动速度（像素/帧）
            
            # 如果文本完全滚出屏幕左侧，从右侧重新开始（形成循环）
            if self.scroll_x + self.text_width < 0:
                self.scroll_x = screen_w
            
            # 绘制文本
            self.surface.blit(self.text_surface, (self.scroll_x, y_center - FONT_SIZE_LARGE // 2))
            
            # 如果文本宽度大于屏幕宽度，绘制重复的文本形成无缝循环
            if self.text_width > screen_w:
                repeat_x = self.scroll_x + self.text_width
                # 如果重复文本在屏幕内，绘制它
                if repeat_x < screen_w:
                    self.surface.blit(self.text_surface, (repeat_x, y_center - FONT_SIZE_LARGE // 2))
        else:
            # 如果没有标题，显示提示
            text = self.font_medium.render("Loading news...", True, COLOR_TEXT)
            text_rect = text.get_rect(center=(screen_w // 2, y_center))
            self.surface.blit(text, text_rect)
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        screen_w, screen_h = self.surface.get_size()
        text = self.font_large.render("News Playing", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(screen_w // 2, screen_h // 2))
        self.surface.blit(text, text_rect)


class CallingScreen(BaseScreen):
    """通话屏幕 - 上1/3显示"Calling"标题，下2/3循环播放telescope图片"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化通话屏幕"""
        super().__init__(surface)
        self.images: List[pygame.Surface] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self._init_images()
    
    def _init_images(self):
        """初始化telescope图片列表"""
        try:
            telescope_dir = "/home/pi/MagicMirrorPro/resources/telescope"
            if os.path.exists(telescope_dir):
                telescope_files = sorted([f for f in os.listdir(telescope_dir) if f.endswith('.png')])
                for f in telescope_files:
                    try:
                        img = pygame.image.load(os.path.join(telescope_dir, f))
                        img = self._scale_image_for_bottom_area(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载 telescope 图片失败: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 telescope 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何 telescope 图片")
            else:
                logger.warning(f"⚠️ telescope 目录不存在: {telescope_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化 telescope 图片失败: {e}")
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方2/3区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方2/3区域的高度
        bottom_area_h = int(screen_h * 2 / 3)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def render(self) -> None:
        """渲染通话屏幕"""
        self.surface.fill(COLOR_BG)
        
        # 渲染上方1/3区域的"Calling"标题
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 3)  # 上方1/3区域高度
        
        calling_text = self.font_large.render("Calling", True, COLOR_PRIMARY)
        calling_rect = calling_text.get_rect(center=(screen_w // 2, top_area_h // 2))
        self.surface.blit(calling_text, calling_rect)
        
        # 渲染下方2/3区域的telescope图片动画
        if not self.images:
            # 如果没有图片，显示占位文字
            fallback_text = self.font_medium.render("No images available", True, COLOR_TEXT)
            fallback_rect = fallback_text.get_rect(center=(screen_w // 2, screen_h // 2))
            self.surface.blit(fallback_text, fallback_rect)
            return
        
        # 更新帧计数器
        self.frame_counter += 1
        if self.frame_counter >= self.frame_interval:
            self.frame_counter = 0
            self.current_frame_index += 1
            # 循环播放
            if self.current_frame_index >= len(self.images):
                self.current_frame_index = 0
        
        # 获取当前图片
        current_img = self.images[self.current_frame_index]
        
        # 计算下方2/3区域的起始位置
        bottom_area_y = top_area_h  # 下方2/3区域起始Y坐标
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (int(screen_h * 2 / 3) - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))


class MusicScreen(BaseScreen):
    """音乐播放屏幕 - 下方1/2显示图片动画，上方1/2显示歌曲信息"""
    
    def __init__(self, surface: pygame.Surface):
        """初始化音乐屏幕"""
        super().__init__(surface)
        self.track_name = ""
        self.artist = ""
        self.album = ""
        self.duration = 0
        self.image_paths: List[str] = []
        self.current_frame_index = 0
        self.frame_counter = 0
        self.frame_interval = 5  # 每5帧切换一张图片
        self.images: List[pygame.Surface] = []
        self._init_images()
    
    def _init_images(self):
        """初始化图片列表"""
        try:
            image_dir = "/home/pi/MagicMirrorPro/resources/music"
            if os.path.exists(image_dir):
                # 获取所有图片文件，按文件名排序
                files = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
                self.image_paths = [os.path.join(image_dir, f) for f in files]
                
                # 加载所有图片
                for img_path in self.image_paths:
                    try:
                        img = pygame.image.load(img_path)
                        # 缩放图片以适应下方1/2区域
                        img = self._scale_image_for_bottom_area(img)
                        self.images.append(img)
                    except Exception as e:
                        logger.warning(f"⚠️ 加载图片失败 {img_path}: {e}")
                
                if self.images:
                    logger.info(f"✅ 加载了 {len(self.images)} 张 music 图片")
                else:
                    logger.warning("⚠️ 没有加载到任何图片")
            else:
                logger.warning(f"⚠️ 图片目录不存在: {image_dir}")
        except Exception as e:
            logger.error(f"❌ 初始化图片失败: {e}")
    
    def _scale_image_for_bottom_area(self, img: pygame.Surface) -> pygame.Surface:
        """缩放图片以适应下方1/2区域"""
        screen_w, screen_h = self.surface.get_size()
        img_w, img_h = img.get_size()
        
        # 下方1/2区域的高度
        bottom_area_h = int(screen_h / 2)
        bottom_area_w = screen_w
        
        # 计算缩放比例（保持比例，适应下方区域）
        scale = min(bottom_area_w / img_w, bottom_area_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        return pygame.transform.scale(img, (new_w, new_h))
    
    def update(self, data: Optional[Dict[str, Any]] = None) -> None:
        """更新音乐数据"""
        if data:
            self.track_name = data.get("track_name", "")
            self.artist = data.get("artist", "")
            self.album = data.get("album", "")
            self.duration = data.get("duration", 0)
    
    def render(self) -> None:
        """渲染音乐屏幕 - 下方1/2显示图片，上方1/2显示歌曲信息"""
        # 清空屏幕
        self.surface.fill(COLOR_BG)
        
        # 渲染上方1/2区域的歌曲信息
        self._render_text_area()
        
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
        
        # 计算下方1/2区域的起始位置
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 2)  # 上方1/2区域高度
        bottom_area_y = top_area_h  # 下方1/2区域起始Y坐标
        
        # 计算图片在下方区域的居中位置
        img_w, img_h = current_img.get_size()
        x = (screen_w - img_w) // 2
        y = bottom_area_y + (int(screen_h / 2) - img_h) // 2
        
        # 绘制图片
        self.surface.blit(current_img, (x, y))
    
    def _render_text_area(self):
        """渲染上方1/2区域的歌曲信息"""
        screen_w, screen_h = self.surface.get_size()
        top_area_h = int(screen_h / 2)
        
        # 计算垂直居中位置
        y_start = top_area_h // 2
        
        if self.track_name:
            # 歌曲名（大字体）
            track_text = self.font_large.render(self.track_name, True, COLOR_TEXT)
            track_rect = track_text.get_rect(center=(screen_w // 2, y_start - 40))
            self.surface.blit(track_text, track_rect)
        
        if self.artist:
            # 艺术家（中等字体）
            artist_text = self.font_medium.render(f"by {self.artist}", True, COLOR_TEXT)
            artist_rect = artist_text.get_rect(center=(screen_w // 2, y_start))
            self.surface.blit(artist_text, artist_rect)
        
        if self.album:
            # 专辑（小字体）
            album_text = self.font_small.render(f"Album: {self.album}", True, COLOR_TEXT)
            album_rect = album_text.get_rect(center=(screen_w // 2, y_start + 40))
            self.surface.blit(album_text, album_rect)
    
    def _render_fallback(self):
        """渲染备用界面（当图片不可用时）"""
        self.surface.fill(COLOR_BG)
        text = self.font_large.render("Music Playing", True, COLOR_PRIMARY)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(text, text_rect)


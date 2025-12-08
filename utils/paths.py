"""
路径管理工具
"""
from pathlib import Path
import config


def get_audio_temp_path(filename: str) -> Path:
    """
    获取临时音频文件路径
    
    Args:
        filename: 文件名
        
    Returns:
        Path: 完整路径
    """
    return config.AUDIO_TEMP_DIR / filename


def ensure_dir(path: Path) -> None:
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    return config.PROJECT_ROOT


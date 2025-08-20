"""
工具函数模块
"""

import logging
import os
from pathlib import Path

def setup_logging(debug=False):
    """设置日志配置"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mediascribe.log', encoding='utf-8')
        ]
    )

def validate_video_file(video_path):
    """验证视频文件是否存在且格式支持"""
    if not os.path.exists(video_path):
        return False
    
    # 支持的视频格式
    supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    file_ext = Path(video_path).suffix.lower()
    
    return file_ext in supported_formats

def format_time(seconds):
    """将秒数格式化为时:分:秒"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def ensure_directory(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

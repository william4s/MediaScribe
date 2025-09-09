"""
配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 默认配置
DEFAULT_CONFIG = {
    # ASR服务配置
    'asr': {
        'base_url': 'http://localhost:8760',
        'timeout': 300,
        'default_language': None,  # 自动检测
        'word_timestamps': True,
        'vad_filter': False
    },
    
    # LLM服务配置
    'llm': {
        'base_url': 'http://192.168.1.3:8000',
        'api_key': 'sk-kfccrazythursdayvme50',
        'model': 'qwen3',
        'timeout': 120,
        'temperature': 0.7,
        'max_tokens': None
    },
    
    # 视频处理配置
    'video': {
        'supported_formats': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'],
        'audio_format': 'mp3',
        'audio_sample_rate': 16000,
        'audio_channels': 1
    },
    
    # 输出配置
    'output': {
        'default_dir': 'output',
        'create_markdown': True,
        'create_json': True,
        'preserve_raw_transcript': True
    },
    
    # 摘要配置
    'summary': {
        'max_overall_length': 200,
        'max_segment_length': 100,
        'enable_timeline': False,
        'timeline_interval': 60
    },
    
    # 图像处理配置
    'image': {
        'extract_fps': 1.0,  # 提高到1秒1帧
        'similarity_threshold': 0.95,  # 提升到95%
        'max_frames_per_segment': 50,
        'uniform_sampling': True,  # 启用均匀采样
        'record_timestamps': True,  # 记录时间戳
        'image_format': 'jpg',
        'image_quality': 85,
        'crop_confidence_threshold': 0.5,
        'crop_mode': 'center',  # 'center', 'yolo', 'none'
        'center_crop_ratios': ['4:3'],  # 中心裁剪比例
        'enable_smart_cropping': True
    },
    
    # 服务配置
    'services': {
        'embedding_service_url': 'http://localhost:8762',
        'yolo_service_url': 'http://localhost:8761',
        'timeout': 120
    },
    
    # 向量计算配置（为中高难度功能预留）
    'vector': {
        'embedding_model': 'clip-vit-base-patch32',
        'similarity_metric': 'cosine',
        'batch_size': 32
    },
    
    # PDF生成配置（为高难度功能预留）
    'pdf': {
        'font_family': 'SimHei',  # 支持中文
        'title_font_size': 16,
        'content_font_size': 12,
        'margin': 50,
        'enable_toc': True
    }
}

def get_config():
    """获取配置"""
    config = DEFAULT_CONFIG.copy()
    
    # 从环境变量覆盖配置
    if os.getenv('WHISPER_URL'):
        config['asr']['base_url'] = os.getenv('WHISPER_URL')
    
    if os.getenv('LLM_URL'):
        config['llm']['base_url'] = os.getenv('LLM_URL')
    
    if os.getenv('LLM_API_KEY'):
        config['llm']['api_key'] = os.getenv('LLM_API_KEY')
    
    if os.getenv('LLM_MODEL'):
        config['llm']['model'] = os.getenv('LLM_MODEL')
    
    return config

# 全局配置实例
CONFIG = get_config()

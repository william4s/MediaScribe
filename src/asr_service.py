"""
ASR服务模块
调用Whisper ASR服务进行语音转文字
"""

import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ASRService:
    """ASR服务客户端"""
    
    def __init__(self, base_url='http://localhost:8760'):
        self.base_url = base_url.rstrip('/')
        self.logger = logger
        
    def transcribe(self, audio_path, language=None, task='transcribe', 
                   vad_filter=False, word_timestamps=True, output='json'):
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 指定语言代码（如'zh', 'en'等），None为自动检测
            task: 任务类型 ('transcribe' 或 'translate')
            vad_filter: 是否启用语音活动检测过滤
            word_timestamps: 是否返回词级时间戳
            output: 输出格式 ('json', 'text', 'srt', 'vtt')
            
        Returns:
            dict: 转录结果
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 构建请求URL
        params = {
            'encode': 'true',
            'task': task,
            'vad_filter': str(vad_filter).lower(),
            'word_timestamps': str(word_timestamps).lower(),
            'output': output
        }
        
        if language:
            params['language'] = language
        
        url = f"{self.base_url}/asr"
        
        self.logger.info(f"开始转录音频: {audio_path}")
        self.logger.debug(f"请求URL: {url}")
        self.logger.debug(f"请求参数: {params}")
        
        try:
            # 准备文件上传
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'audio_file': (audio_path.name, audio_file, 'audio/mpeg')
                }
                
                # 发送请求
                response = requests.post(
                    url,
                    params=params,
                    files=files,
                    timeout=300  # 5分钟超时
                )
                
                response.raise_for_status()
                
                result = response.json()
                
                self.logger.info(f"转录成功，检测到语言: {result.get('language', 'unknown')}")
                self.logger.info(f"转录文本长度: {len(result.get('text', ''))}")
                self.logger.info(f"分段数量: {len(result.get('segments', []))}")
                
                return result
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ASR请求失败: {e}")
            raise Exception(f"ASR转录失败: {e}")
        except Exception as e:
            self.logger.error(f"转录处理失败: {e}")
            raise Exception(f"转录处理失败: {e}")
    
    def health_check(self):
        """检查ASR服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_supported_languages(self):
        """获取支持的语言列表（如果API提供）"""
        try:
            response = requests.get(f"{self.base_url}/languages", timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # 返回Whisper常见支持的语言
        return [
            'zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'ar',
            'hi', 'pt', 'it', 'nl', 'sv', 'no', 'da', 'fi', 'pl'
        ]

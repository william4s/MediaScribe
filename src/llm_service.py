"""
LLM服务模块
调用大语言模型API进行文本处理
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务客户端"""
    
    def __init__(self, base_url='http://192.168.1.3:8000', 
                 api_key='sk-kfccrazythursdayvme50', model='qwen3'):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.logger = logger
        
    def chat_completion(self, messages, temperature=0.7, max_tokens=None):
        """
        调用LLM聊天完成API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大令牌数
            
        Returns:
            str: LLM响应内容
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature
        }
        
        if max_tokens:
            payload['max_tokens'] = max_tokens
        
        self.logger.debug(f"LLM请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120  # 2分钟超时
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            self.logger.debug(f"LLM响应: {content}")
            
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"LLM请求失败: {e}")
            raise Exception(f"LLM请求失败: {e}")
        except Exception as e:
            self.logger.error(f"LLM处理失败: {e}")
            raise Exception(f"LLM处理失败: {e}")
    
    def health_check(self):
        """检查LLM服务是否可用"""
        try:
            response = self.chat_completion([
                {"role": "user", "content": "测试连接"}
            ])
            return len(response) > 0
        except:
            return False
    
    def generate_summary(self, text, max_length=200):
        """
        生成文本摘要
        
        Args:
            text: 待摘要的文本
            max_length: 摘要最大长度
            
        Returns:
            str: 摘要文本
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的文本摘要助手。请为用户提供的文本生成简洁、准确的摘要，摘要长度不超过{max_length}字。"
            },
            {
                "role": "user",
                "content": f"请为以下文本生成摘要：\n\n{text}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3)
    
    def generate_overall_summary(self, text):
        """
        生成整体摘要（仅发送纯文字）
        
        Args:
            text: 完整转录文本（纯文字）
            
        Returns:
            str: 整体摘要
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频内容摘要助手。请用中文为用户提供的文本生成简洁、准确的摘要，摘要长度控制在150-250字之间。要求突出重点内容，保持逻辑清晰。"
            },
            {
                "role": "user",
                "content": f"请为以下视频转录文本生成中文摘要：\n\n{text}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3)
    
    def generate_segment_summary(self, segment_text, start_time, end_time):
        """
        生成单个分段的摘要
        
        Args:
            segment_text: 分段文本（纯文字）
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            str: 分段摘要
        """
        time_info = f"时间段：{self._format_time(start_time)} - {self._format_time(end_time)}"
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频内容分析助手。请用中文为用户提供的文本段落生成简洁摘要，摘要长度控制在50-100字之间。要求突出该段落的核心内容。"
            },
            {
                "role": "user",
                "content": f"{time_info}\n\n请为以下文本段落生成中文摘要：\n\n{segment_text}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3)
    
    def _format_time(self, seconds):
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

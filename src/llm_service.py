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
    
    def segment_and_summarize(self, text, segments_info):
        """
        根据时间段信息对文本进行分段并生成摘要
        
        Args:
            text: 完整转录文本
            segments_info: 分段信息列表
            
        Returns:
            dict: 分段和摘要结果
        """
        system_prompt = """你是一个专业的视频内容分析助手。用户会提供视频的完整转录文本和分段信息，请你：

1. 为整个内容生成一个总体摘要
2. 为每个时间段生成相应的摘要
3. 确保摘要准确反映该时间段的主要内容
4. 返回严格按照以下JSON格式的结果：

{
  "overall_summary": "整体摘要内容",
  "segments": [
    {
      "start_time": 开始时间（秒）,
      "end_time": 结束时间（秒）,
      "text": "该段的原始文本",
      "summary": "该段的摘要"
    }
  ]
}

要求：
- 摘要要简洁明了，突出重点
- 保持原文的逻辑结构
- 每段摘要长度控制在50-100字
- 总体摘要长度控制在200字以内
- 必须返回有效的JSON格式"""

        user_content = f"""完整转录文本：
{text}

分段信息：
{json.dumps(segments_info, ensure_ascii=False, indent=2)}

请按照要求返回JSON格式的分析结果。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.chat_completion(messages, temperature=0.3)
        
        try:
            # 尝试解析JSON响应
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            self.logger.warning("LLM返回的不是有效JSON，尝试提取...")
            # 如果不是有效JSON，尝试简单处理
            return {
                "overall_summary": response[:200] + "..." if len(response) > 200 else response,
                "segments": []
            }

"""
摘要生成器模块
负责处理转录结果并生成结构化摘要
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SummaryGenerator:
    """摘要生成器"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.logger = logger
    
    def generate_summary_with_segments(self, transcript_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据转录结果生成摘要和分段处理
        
        Args:
            transcript_result: ASR转录结果
            
        Returns:
            dict: 包含整体摘要和分段摘要的结果
        """
        self.logger.info("开始生成摘要和分段处理...")
        
        # 提取完整文本和分段信息
        full_text = transcript_result.get('text', '')
        segments = transcript_result.get('segments', [])
        language = transcript_result.get('language', 'unknown')
        
        if not full_text or not segments:
            raise ValueError("转录结果缺少必要的文本或分段信息")
        
        self.logger.info(f"处理语言: {language}, 文本长度: {len(full_text)}, 分段数: {len(segments)}")
        
        # 预处理分段信息
        segments_info = []
        for segment in segments:
            segment_info = {
                'start_time': segment.get('start', 0),
                'end_time': segment.get('end', 0),
                'text': segment.get('text', '').strip()
            }
            segments_info.append(segment_info)
        
        # 调用LLM生成摘要
        try:
            summary_result = self.llm_service.segment_and_summarize(full_text, segments_info)
            
            # 验证和补充结果
            result = self._validate_and_enhance_result(summary_result, segments_info, full_text)
            
            # 添加元数据
            result['metadata'] = {
                'language': language,
                'total_duration': segments[-1].get('end', 0) if segments else 0,
                'total_segments': len(segments),
                'total_words': len(full_text.split()),
                'source': 'whisper_asr'
            }
            
            self.logger.info("摘要生成完成")
            return result
            
        except Exception as e:
            self.logger.error(f"摘要生成失败: {e}")
            # 返回备用结果
            return self._create_fallback_result(segments_info, full_text, language)
    
    def _validate_and_enhance_result(self, llm_result: Dict[str, Any], 
                                   segments_info: List[Dict], full_text: str) -> Dict[str, Any]:
        """验证并增强LLM结果"""
        
        result = {
            'overall_summary': llm_result.get('overall_summary', ''),
            'segments': []
        }
        
        # 如果LLM没有返回整体摘要，生成一个简单的
        if not result['overall_summary']:
            result['overall_summary'] = self._generate_simple_summary(full_text)
        
        # 处理分段结果
        llm_segments = llm_result.get('segments', [])
        
        for i, original_segment in enumerate(segments_info):
            # 尝试找到对应的LLM分段
            llm_segment = None
            if i < len(llm_segments):
                llm_segment = llm_segments[i]
            
            segment_result = {
                'start_time': original_segment['start_time'],
                'end_time': original_segment['end_time'],
                'text': original_segment['text'],
                'summary': ''
            }
            
            # 设置摘要
            if llm_segment and llm_segment.get('summary'):
                segment_result['summary'] = llm_segment['summary']
            else:
                # 生成简单摘要
                segment_result['summary'] = self._generate_simple_segment_summary(
                    original_segment['text']
                )
            
            result['segments'].append(segment_result)
        
        return result
    
    def _generate_simple_summary(self, text: str, max_length: int = 200) -> str:
        """生成简单的文本摘要（备用方案）"""
        # 简单的摘要逻辑：取前几句话
        sentences = text.split('。')
        summary = ''
        
        for sentence in sentences:
            if len(summary + sentence) < max_length:
                summary += sentence + '。'
            else:
                break
        
        return summary.strip() or text[:max_length] + '...'
    
    def _generate_simple_segment_summary(self, text: str, max_length: int = 100) -> str:
        """生成简单的分段摘要（备用方案）"""
        if len(text) <= max_length:
            return text.strip()
        
        # 取前半部分
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    def _create_fallback_result(self, segments_info: List[Dict], 
                              full_text: str, language: str) -> Dict[str, Any]:
        """创建备用结果（当LLM调用失败时）"""
        self.logger.warning("使用备用摘要生成方案")
        
        result = {
            'overall_summary': self._generate_simple_summary(full_text),
            'segments': [],
            'metadata': {
                'language': language,
                'total_duration': segments_info[-1]['end_time'] if segments_info else 0,
                'total_segments': len(segments_info),
                'total_words': len(full_text.split()),
                'source': 'whisper_asr',
                'fallback_mode': True
            }
        }
        
        for segment_info in segments_info:
            segment_result = {
                'start_time': segment_info['start_time'],
                'end_time': segment_info['end_time'],
                'text': segment_info['text'],
                'summary': self._generate_simple_segment_summary(segment_info['text'])
            }
            result['segments'].append(segment_result)
        
        return result
    
    def generate_timeline_summary(self, summary_result: Dict[str, Any], 
                                time_intervals: int = 60) -> List[Dict]:
        """
        按时间间隔生成时间线摘要（为未来功能预留）
        
        Args:
            summary_result: 摘要结果
            time_intervals: 时间间隔（秒）
            
        Returns:
            list: 时间线摘要列表
        """
        timeline = []
        current_time = 0
        segments = summary_result.get('segments', [])
        
        while current_time < summary_result['metadata']['total_duration']:
            end_time = current_time + time_intervals
            
            # 找到这个时间段内的所有分段
            interval_segments = [
                seg for seg in segments 
                if seg['start_time'] < end_time and seg['end_time'] > current_time
            ]
            
            if interval_segments:
                # 合并这个时间段的内容
                combined_text = ' '.join([seg['text'] for seg in interval_segments])
                combined_summary = ' '.join([seg['summary'] for seg in interval_segments])
                
                timeline.append({
                    'start_time': current_time,
                    'end_time': min(end_time, summary_result['metadata']['total_duration']),
                    'text': combined_text,
                    'summary': combined_summary,
                    'segment_count': len(interval_segments)
                })
            
            current_time = end_time
        
        return timeline

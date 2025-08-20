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
        
        self.logger.info(f"处理语言: {language}, 文本长度: {len(full_text)}, 原始分段数: {len(segments)}")
        
        # 智能合并分段为3-6段
        merged_segments = self._merge_segments_intelligently(segments)
        self.logger.info(f"合并后分段数: {len(merged_segments)}")
        
        # 生成整体摘要（只发送纯文字）
        overall_summary = self._generate_overall_summary_safe(full_text)
        
        # 生成各段摘要
        segment_summaries = []
        for i, segment in enumerate(merged_segments):
            self.logger.info(f"正在处理第 {i+1}/{len(merged_segments)} 段...")
            try:
                summary = self.llm_service.generate_segment_summary(
                    segment['text'], 
                    segment['start_time'], 
                    segment['end_time']
                )
                segment['summary'] = summary
            except Exception as e:
                self.logger.warning(f"第 {i+1} 段摘要生成失败: {e}，使用备用方案")
                segment['summary'] = self._generate_simple_segment_summary(segment['text'])
            
            segment_summaries.append(segment)
        
        # 构建最终结果
        result = {
            'overall_summary': overall_summary,
            'segments': segment_summaries,
            'metadata': {
                'language': language,
                'total_duration': segments[-1].get('end', 0) if segments else 0,
                'original_segments_count': len(segments),
                'merged_segments_count': len(merged_segments),
                'total_words': len(full_text.split()),
                'source': 'whisper_asr'
            }
        }
        
        self.logger.info("摘要生成完成")
        return result
    
    def _merge_segments_intelligently(self, segments: List[Dict]) -> List[Dict]:
        """
        智能合并分段，确保最终分段数在3-6之间
        
        Args:
            segments: 原始分段列表
            
        Returns:
            List[Dict]: 合并后的分段列表
        """
        if not segments:
            return []
        
        total_segments = len(segments)
        
        # 如果原始分段已经在理想范围内，直接返回
        if 3 <= total_segments <= 6:
            return segments
        
        # 计算目标分段数
        if total_segments <= 12:
            target_segments = 4  # 小于等于12段时，合并为4段
        elif total_segments <= 18:
            target_segments = 5  # 12-18段时，合并为5段
        else:
            target_segments = 6  # 超过18段时，合并为6段
        
        # 计算每个合并段应包含的原始段数
        segments_per_group = total_segments // target_segments
        remainder = total_segments % target_segments
        
        merged = []
        current_index = 0
        
        for i in range(target_segments):
            # 当前组的段数（如果有余数，前几组多分配一段）
            group_size = segments_per_group + (1 if i < remainder else 0)
            
            if current_index >= total_segments:
                break
            
            # 合并当前组的所有段
            group_segments = segments[current_index:current_index + group_size]
            
            if group_segments:
                merged_segment = {
                    'start_time': group_segments[0]['start'],
                    'end_time': group_segments[-1]['end'],
                    'text': ' '.join([seg['text'].strip() for seg in group_segments if seg.get('text')]),
                    'original_segment_ids': [seg.get('id', current_index + j) for j, seg in enumerate(group_segments)]
                }
                merged.append(merged_segment)
            
            current_index += group_size
        
        return merged
    
    def _generate_overall_summary_safe(self, full_text: str) -> str:
        """
        安全地生成整体摘要
        
        Args:
            full_text: 完整文本
            
        Returns:
            str: 整体摘要
        """
        try:
            # 只发送纯文字给LLM
            return self.llm_service.generate_overall_summary(full_text)
        except Exception as e:
            self.logger.warning(f"整体摘要生成失败: {e}，使用备用方案")
            return self._generate_simple_summary(full_text)
    
    def _create_fallback_result(self, segments: List[Dict], 
                              full_text: str, language: str) -> Dict[str, Any]:
        """创建备用结果（当LLM调用失败时）"""
        self.logger.warning("使用备用摘要生成方案")
        
        # 转换segments格式以便使用智能合并
        segments_info = []
        for segment in segments:
            segment_info = {
                'start_time': segment.get('start', 0),
                'end_time': segment.get('end', 0),
                'text': segment.get('text', '').strip(),
                'start': segment.get('start', 0),  # 保持原格式兼容
                'end': segment.get('end', 0)
            }
            segments_info.append(segment_info)
        
        # 合并分段
        merged_segments = self._merge_segments_intelligently(segments_info)
        
        # 生成简单摘要
        segment_summaries = []
        for segment in merged_segments:
            segment_result = {
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'text': segment['text'],
                'summary': self._generate_simple_segment_summary(segment['text'])
            }
            segment_summaries.append(segment_result)
        
        result = {
            'overall_summary': self._generate_simple_summary(full_text),
            'segments': segment_summaries,
            'metadata': {
                'language': language,
                'total_duration': segments_info[-1]['end_time'] if segments_info else 0,
                'original_segments_count': len(segments_info),
                'merged_segments_count': len(merged_segments),
                'total_words': len(full_text.split()),
                'source': 'whisper_asr',
                'fallback_mode': True
            }
        }
        
        return result
    
    def _generate_simple_summary(self, text: str, max_length: int = 200) -> str:
        """生成简单的中文文本摘要（备用方案）"""
        if not text:
            return "无法生成摘要：文本为空"
        
        # 去除多余空格和换行
        clean_text = ' '.join(text.split())
        
        if len(clean_text) <= max_length:
            return f"视频内容摘要：{clean_text}"
        
        # 尝试按句子分割（中英文兼容）
        import re
        sentences = re.split(r'[。！？.!?]', clean_text)
        summary = "视频内容摘要："
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(summary + sentence) < max_length - 10:
                summary += sentence + "。"
            else:
                break
        
        if summary == "视频内容摘要：":
            summary = f"视频内容摘要：{clean_text[:max_length-10]}..."
            
        return summary
    
    def _generate_simple_segment_summary(self, text: str, max_length: int = 80) -> str:
        """生成简单的中文分段摘要（备用方案）"""
        if not text:
            return "该段落内容为空"
        
        clean_text = ' '.join(text.split())
        
        if len(clean_text) <= max_length:
            return clean_text
        
        # 取关键部分
        return clean_text[:max_length-3] + "..."
    
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

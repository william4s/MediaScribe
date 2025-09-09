"""
高难度功能：图文混排PDF报告生成器
支持对每段摘要文字并发处理视觉内容，汇总后生成图文混排报告
"""

import asyncio
import concurrent.futures
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import time
import os
from concurrent.futures import ThreadPoolExecutor

# PDF生成相关
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.visual_processor import VisualProcessor
from src.config import CONFIG

logger = logging.getLogger(__name__)

class AdvancedMediaProcessor:
    """高难度图文混排处理器"""
    
    def __init__(self, visual_processor: VisualProcessor):
        self.visual_processor = visual_processor
        self.logger = logger
        
        # 注册中文字体 (如果有的话)
        try:
            # 尝试注册系统中文字体
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/System/Library/Fonts/PingFang.ttc',
                '/Windows/Fonts/simhei.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.chinese_font = 'ChineseFont'
                    break
            else:
                self.chinese_font = 'Helvetica'  # 备用字体
                
        except Exception as e:
            self.logger.warning(f"中文字体注册失败，使用默认字体: {e}")
            self.chinese_font = 'Helvetica'
    
    def process_video_with_concurrent_visual(self, video_path: str, summary_result: Dict[str, Any], 
                                           output_dir: str) -> Dict[str, Any]:
        """
        对每段摘要并发处理视觉内容
        
        Args:
            video_path: 视频文件路径
            summary_result: 文本摘要结果
            output_dir: 输出目录
            
        Returns:
            dict: 完整的图文混排结果
        """
        self.logger.info("开始高难度并发视觉处理...")
        
        output_path = Path(output_dir)
        visual_output_dir = output_path / "visual_segments"
        visual_output_dir.mkdir(exist_ok=True)
        
        segments = summary_result.get('segments', [])
        
        # 使用线程池并发处理每个分段
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:  # 限制并发数避免资源耗尽
            # 为每个分段创建任务
            future_to_segment = {}
            
            for i, segment in enumerate(segments):
                segment_output_dir = visual_output_dir / f"segment_{i+1}"
                
                future = executor.submit(
                    self._process_single_segment_visual,
                    video_path,
                    segment,
                    str(segment_output_dir),
                    i + 1
                )
                future_to_segment[future] = (i, segment)
            
            # 收集结果
            visual_results = [None] * len(segments)
            
            for future in concurrent.futures.as_completed(future_to_segment):
                segment_index, segment = future_to_segment[future]
                try:
                    result = future.result()
                    visual_results[segment_index] = result
                    self.logger.info(f"分段 {segment_index + 1} 视觉处理完成")
                except Exception as e:
                    self.logger.error(f"分段 {segment_index + 1} 视觉处理失败: {e}")
                    visual_results[segment_index] = self._create_fallback_visual_result(segment)
        
        processing_time = time.time() - start_time
        self.logger.info(f"并发视觉处理完成，总耗时: {processing_time:.2f}秒")
        
        # 构建完整结果
        enhanced_result = {
            **summary_result,
            'visual_segments': visual_results,
            'processing_stats': {
                'total_processing_time': processing_time,
                'concurrent_segments': len(segments),
                'visual_output_dir': str(visual_output_dir)
            }
        }
        
        return enhanced_result
    
    def _process_single_segment_visual(self, video_path: str, segment: Dict[str, Any], 
                                     output_dir: str, segment_num: int) -> Dict[str, Any]:
        """
        处理单个分段的视觉内容
        
        Args:
            video_path: 视频文件路径
            segment: 分段信息
            output_dir: 该分段的输出目录
            segment_num: 分段编号
            
        Returns:
            dict: 该分段的视觉处理结果
        """
        self.logger.info(f"开始处理分段 {segment_num} 的视觉内容...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        start_time = segment.get('start_time', 0)
        end_time = segment.get('end_time', 0)
        duration = end_time - start_time
        
        # 配置该分段的处理参数
        segment_config = {
            'max_frames': min(10, max(3, int(duration / 10))),  # 根据时长动态调整帧数
            'start_time': start_time,
            'duration': duration,
            'similarity_threshold': 0.85,  # 较低的阈值以保留更多不同的图片
            'crop_mode': 'center'
        }
        
        try:
            # 处理该分段的视频帧
            result = self.visual_processor.process_video_frames(
                video_path=video_path,
                output_dir=str(output_path),
                **segment_config
            )
            
            # 选择关键图片 (最多3张)
            key_images = self._select_key_images_for_segment(
                result.get('final_images', []), 
                max_images=3
            )
            
            return {
                'segment_number': segment_num,
                'time_range': f"{start_time:.1f}s - {end_time:.1f}s",
                'duration': duration,
                'text': segment.get('text', ''),
                'summary': segment.get('summary', ''),
                'visual_result': result,
                'key_images': key_images,
                'image_count': len(key_images),
                'processing_config': segment_config
            }
            
        except Exception as e:
            self.logger.error(f"分段 {segment_num} 视觉处理失败: {e}")
            return self._create_fallback_visual_result(segment, segment_num)
    
    def _select_key_images_for_segment(self, image_paths: List[str], max_images: int = 3) -> List[str]:
        """
        为分段选择关键图片
        
        Args:
            image_paths: 图片路径列表
            max_images: 最大图片数量
            
        Returns:
            list: 选中的关键图片路径
        """
        if not image_paths:
            return []
        
        if len(image_paths) <= max_images:
            return image_paths
        
        # 均匀选择图片
        step = len(image_paths) // max_images
        selected = []
        
        for i in range(max_images):
            index = i * step
            if index < len(image_paths):
                selected.append(image_paths[index])
        
        return selected
    
    def _create_fallback_visual_result(self, segment: Dict[str, Any], segment_num: int = None) -> Dict[str, Any]:
        """创建视觉处理失败时的备用结果"""
        return {
            'segment_number': segment_num or 0,
            'time_range': f"{segment.get('start_time', 0):.1f}s - {segment.get('end_time', 0):.1f}s",
            'duration': segment.get('end_time', 0) - segment.get('start_time', 0),
            'text': segment.get('text', ''),
            'summary': segment.get('summary', ''),
            'visual_result': None,
            'key_images': [],
            'image_count': 0,
            'processing_config': None,
            'error': True
        }
    
    def generate_mixed_content_pdf(self, enhanced_result: Dict[str, Any], 
                                 output_path: str, include_images: bool = True) -> str:
        """
        生成图文混排PDF报告
        
        Args:
            enhanced_result: 包含视觉处理的完整结果
            output_path: PDF输出路径
            include_images: 是否包含图片
            
        Returns:
            str: 生成的PDF文件路径
        """
        self.logger.info("开始生成图文混排PDF报告...")
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 定义样式
        styles = self._create_pdf_styles()
        story = []
        
        # 添加标题
        story.append(Paragraph("MediaScribe 图文混排视频讲义", styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        
        # 添加元信息
        metadata = enhanced_result.get('metadata', {})
        info_data = [
            ['总时长', f"{metadata.get('total_duration', 0):.1f} 秒"],
            ['语言', metadata.get('language', 'unknown')],
            ['分段数', str(metadata.get('total_segments', 0))],
            ['处理时间', f"{enhanced_result.get('processing_stats', {}).get('total_processing_time', 0):.1f} 秒"]
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 添加整体摘要
        story.append(Paragraph("整体摘要", styles['Heading1']))
        story.append(Paragraph(enhanced_result.get('overall_summary', ''), styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # 添加分段内容
        visual_segments = enhanced_result.get('visual_segments', [])
        
        for i, visual_segment in enumerate(visual_segments, 1):
            if not visual_segment:
                continue
                
            # 分段标题
            time_range = visual_segment.get('time_range', '')
            story.append(Paragraph(f"第 {i} 段 ({time_range})", styles['Heading2']))
            
            # 分段摘要
            summary = visual_segment.get('summary', '')
            if summary:
                story.append(Paragraph(f"摘要：{summary}", styles['Summary']))
                story.append(Spacer(1, 0.2*inch))
            
            # 添加关键图片
            if include_images and visual_segment.get('key_images'):
                key_images = visual_segment['key_images']
                story.append(Paragraph(f"关键画面 ({len(key_images)} 张):", styles['ImageCaption']))
                
                # 创建图片表格布局
                image_data = []
                images_per_row = 2 if len(key_images) > 1 else 1
                
                for j in range(0, len(key_images), images_per_row):
                    row_images = key_images[j:j+images_per_row]
                    row_data = []
                    
                    for img_path in row_images:
                        try:
                            if os.path.exists(img_path):
                                # 调整图片大小
                                img = Image(img_path)
                                img.drawHeight = 6*cm
                                img.drawWidth = 8*cm
                                row_data.append(img)
                            else:
                                row_data.append(Paragraph("图片未找到", styles['Normal']))
                        except Exception as e:
                            self.logger.warning(f"图片加载失败 {img_path}: {e}")
                            row_data.append(Paragraph("图片加载失败", styles['Normal']))
                    
                    # 填充行到固定长度
                    while len(row_data) < images_per_row:
                        row_data.append("")
                    
                    image_data.append(row_data)
                
                if image_data:
                    if images_per_row == 1:
                        col_widths = [16*cm]
                    else:
                        col_widths = [8*cm, 8*cm]
                        
                    image_table = Table(image_data, colWidths=col_widths)
                    image_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    
                    story.append(image_table)
                    story.append(Spacer(1, 0.2*inch))
            
            # 原始文本内容 (可选)
            text = visual_segment.get('text', '')
            if text and len(text) > 50:  # 只有当文本足够长时才显示
                story.append(Paragraph("详细内容:", styles['Subheading']))
                # 限制文本长度避免PDF过长
                display_text = text[:500] + "..." if len(text) > 500 else text
                story.append(Paragraph(display_text, styles['Detail']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # 每3段后分页
            if i % 3 == 0 and i < len(visual_segments):
                story.append(PageBreak())
        
        # 添加统计信息
        story.append(PageBreak())
        story.append(Paragraph("处理统计", styles['Heading1']))
        
        stats = enhanced_result.get('processing_stats', {})
        stats_text = f"""
        • 总处理时间: {stats.get('total_processing_time', 0):.2f} 秒
        • 并发分段数: {stats.get('concurrent_segments', 0)}
        • 总图片数: {sum(vs.get('image_count', 0) for vs in visual_segments if vs)}
        • 视觉处理成功率: {len([vs for vs in visual_segments if vs and not vs.get('error')]) / len(visual_segments) * 100:.1f}%
        """
        
        story.append(Paragraph(stats_text, styles['Normal']))
        
        # 生成PDF
        try:
            doc.build(story)
            self.logger.info(f"PDF报告生成成功: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"PDF生成失败: {e}")
            raise
    
    def _create_pdf_styles(self) -> Dict[str, ParagraphStyle]:
        """创建PDF样式"""
        styles = getSampleStyleSheet()
        
        # 自定义样式
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=self.chinese_font,
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=18,
                spaceAfter=12,
                textColor=colors.darkblue
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=16,
                spaceAfter=10,
                textColor=colors.darkgreen
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                spaceAfter=6,
                alignment=TA_JUSTIFY
            ),
            'Summary': ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                spaceAfter=6,
                leftIndent=20,
                textColor=colors.darkred,
                alignment=TA_JUSTIFY
            ),
            'Detail': ParagraphStyle(
                'CustomDetail',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=10,
                spaceAfter=6,
                leftIndent=20,
                textColor=colors.grey,
                alignment=TA_JUSTIFY
            ),
            'ImageCaption': ParagraphStyle(
                'CustomImageCaption',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                spaceAfter=6,
                textColor=colors.darkblue,
                alignment=TA_LEFT
            ),
            'Subheading': ParagraphStyle(
                'CustomSubheading',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                spaceAfter=6,
                textColor=colors.black,
                alignment=TA_LEFT
            )
        }
        
        return custom_styles

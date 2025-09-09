#!/usr/bin/env python3
"""
MediaScribe - 统一入口程序
整合所有功能：音频模式、视觉模式、高级模式
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path

from src.video_processor import VideoProcessor
from src.asr_service import ASRService
from src.llm_service import LLMService
from src.summary_generator import SummaryGenerator
from src.utils import setup_logging, validate_video_file

def main():
    """统一主函数"""
    parser = argparse.ArgumentParser(
        description='MediaScribe - 智能视频内容分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 处理模式说明:
  audio      仅音频处理 (快速转录) - 2-5分钟  
  visual     视觉处理模式 (图像分析) - 10-20分钟  
  advanced   高级模式 (并发+PDF) - 15-30分钟
  auto       自动选择模式 (默认) - 自适应

📝 使用示例:
  python mediascribe.py video.mp4                    # 自动模式
  python mediascribe.py video.mp4 --mode audio       # 仅音频  
  python mediascribe.py video.mp4 --mode visual      # 视觉处理
  python mediascribe.py video.mp4 --mode advanced    # 高级模式
        """
    )
    
    # 基础参数
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--mode', choices=['auto', 'audio', 'visual', 'advanced'], 
                       default='auto', help='处理模式 (默认: auto)')
    
    # 服务配置
    parser.add_argument('--whisper-url', default='http://localhost:8760', help='Whisper ASR服务地址')
    parser.add_argument('--llm-url', default='http://192.168.1.3:8000', help='LLM服务地址')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    # 视觉处理参数
    visual_group = parser.add_argument_group('🖼️ 视觉处理选项 (visual/advanced模式)')
    visual_group.add_argument('--crop-mode', choices=['center', 'yolo', 'none'], 
                             default='center', help='裁剪模式 (默认: center)')
    visual_group.add_argument('--max-frames', type=int, default=50, 
                             help='最大抽帧数 (默认: 50)')
    visual_group.add_argument('--similarity-threshold', type=float, default=0.95,
                             help='相似度阈值 (默认: 0.95)')
    
    # 高级模式参数
    advanced_group = parser.add_argument_group('🚀 高级模式选项 (advanced模式)')
    advanced_group.add_argument('--disable-concurrent', action='store_true',
                               help='禁用并发处理 (默认: 开启)')
    advanced_group.add_argument('--disable-pdf', action='store_true',
                               help='禁用PDF生成 (默认: 开启)')
    advanced_group.add_argument('--max-workers', type=int, default=3,
                               help='最大并发线程数 (默认: 3)')
    advanced_group.add_argument('--no-images', action='store_true',
                               help='PDF不包含图片 (默认: 包含)')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(debug=args.debug)
    
    # 验证输入文件
    if not validate_video_file(args.video_path):
        print(f"❌ 错误: 视频文件不存在或格式不支持: {args.video_path}")
        sys.exit(1)
    
    # 智能模式选择
    if args.mode == 'auto':
        selected_mode = auto_select_mode(args.video_path)
        print(f"🎯 自动选择模式: {selected_mode}")
    else:
        selected_mode = args.mode
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 显示启动信息
    print("🚀 MediaScribe 统一处理系统")
    print("="*80)
    print(f"📹 输入视频: {args.video_path}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🎯 处理模式: {get_mode_description(selected_mode)}")
    print(f"🔧 调试模式: {'开启' if args.debug else '关闭'}")
    
    if selected_mode in ['visual', 'advanced']:
        print(f"🖼️ 视觉配置: {args.crop_mode}裁剪, 最大{args.max_frames}帧, 阈值{args.similarity_threshold}")
        
    if selected_mode == 'advanced':
        print(f"⚡ 高级配置: 并发{'关闭' if args.disable_concurrent else '开启'}, "
              f"PDF{'关闭' if args.disable_pdf else '开启'}, "
              f"图片{'排除' if args.no_images else '包含'}")
    
    print("="*80)
    
    # 根据模式执行相应处理
    total_start_time = time.time()
    
    try:
        if selected_mode == 'audio':
            result = process_audio_mode(args, output_dir)
        elif selected_mode == 'visual':
            result = process_visual_mode(args, output_dir)
        elif selected_mode == 'advanced':
            result = process_advanced_mode(args, output_dir)
        else:
            raise ValueError(f"未知的处理模式: {selected_mode}")
        
        # 显示完成信息
        total_time = time.time() - total_start_time
        print(f"\n🎉 处理完成! 总耗时: {total_time:.2f}秒")
        
        # 显示生成的文件
        print("\n📁 生成的文件:")
        total_size = 0
        for file_path in sorted(output_dir.rglob('*')):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                rel_path = file_path.relative_to(output_dir)
                print(f"  📄 {rel_path} ({size_mb:.2f}MB)")
        
        print(f"\n📊 总输出大小: {total_size:.2f}MB")
        print("="*80)
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断处理")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def auto_select_mode(video_path: str) -> str:
    """根据文件大小自动选择处理模式"""
    video_file = Path(video_path)
    file_size_mb = video_file.stat().st_size / (1024 * 1024)
    
    if file_size_mb < 50:
        return 'audio'     # 小文件 < 50MB: 快速音频处理
    elif file_size_mb < 200:
        return 'visual'    # 中等文件 50-200MB: 视觉处理
    else:
        return 'advanced'  # 大文件 > 200MB: 高级处理

def get_mode_description(mode: str) -> str:
    """获取模式描述"""
    descriptions = {
        'audio': 'audio (音频模式 - 快速转录)',
        'visual': 'visual (视觉模式 - 图像分析)',
        'advanced': 'advanced (高级模式 - 并发+PDF)'
    }
    return descriptions.get(mode, mode)

def process_audio_mode(args, output_dir: Path) -> dict:
    """🎵 音频模式处理 - 快速转录和摘要"""
    print("🎵 启动音频模式...")
    
    # 初始化服务
    video_processor = VideoProcessor()
    asr_service = ASRService(base_url=args.whisper_url)
    llm_service = LLMService(base_url=args.llm_url)
    summary_generator = SummaryGenerator(llm_service)
    
    # 音频提取
    print("  🎵 提取音频...")
    audio_path = video_processor.extract_audio(args.video_path, str(output_dir / "audio.mp3"))
    
    # 转录
    print("  🔤 语音转录...")
    transcript_result = asr_service.transcribe_audio(audio_path)
    
    # 保存转录结果
    transcript_path = output_dir / "transcript_raw.json"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_result, f, ensure_ascii=False, indent=2)
    
    # 生成摘要
    print("  📝 智能摘要...")
    summary_result = summary_generator.generate_summary_with_segments(transcript_result)
    
    # 保存最终结果
    final_result_path = output_dir / "final_result.json"
    with open(final_result_path, 'w', encoding='utf-8') as f:
        json.dump(summary_result, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    report_path = output_dir / "report.md"
    generate_markdown_report(summary_result, str(report_path))
    
    print("  ✅ 音频模式处理完成")
    return summary_result

def process_visual_mode(args, output_dir: Path) -> dict:
    """🖼️ 视觉模式处理 - 图像分析"""
    print("🖼️ 启动视觉模式...")
    
    # 先执行音频处理
    summary_result = process_audio_mode(args, output_dir)
    
    # 导入视觉处理模块
    try:
        from src.visual_processor import VisualProcessor
        print("  📦 视觉模块加载成功")
    except ImportError as e:
        print(f"  ❌ 视觉处理模块导入失败: {e}")
        print("  ⚠️ 降级到音频模式处理")
        return summary_result
    
    # 检查视觉服务
    print("  📡 检查视觉服务...")
    visual_processor = VisualProcessor()
    
    try:
        # 简单的服务检查 (如果check_services方法存在的话)
        if hasattr(visual_processor, 'check_services'):
            service_status = visual_processor.check_services()
            print(f"    ✅ 视觉服务: {service_status}")
        else:
            print("    ⚠️ 跳过服务检查")
    except Exception as e:
        print(f"    ⚠️ 服务检查失败: {e}, 继续尝试处理")
    
    # 视觉处理
    print("  🔍 执行视觉处理...")
    visual_output_dir = output_dir / "visual"
    
    try:
        visual_result = visual_processor.process_video_frames(
            video_path=args.video_path,
            output_dir=str(visual_output_dir),
            max_frames=args.max_frames,
            crop_mode=args.crop_mode,
            similarity_threshold=args.similarity_threshold
        )
        
        print(f"    📸 处理图片: {visual_result.get('processing_stats', {}).get('final_image_count', 0)} 张")
        
        # 合并结果
        enhanced_result = {
            **summary_result,
            'visual_processing': visual_result
        }
        
        # 保存增强结果
        enhanced_path = output_dir / "visual_result.json"
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_result, f, ensure_ascii=False, indent=2)
        
        print("  ✅ 视觉模式处理完成")
        return enhanced_result
        
    except Exception as e:
        print(f"  ⚠️ 视觉处理失败: {e}")
        print("  📝 继续使用音频处理结果")
        return summary_result

def process_advanced_mode(args, output_dir: Path) -> dict:
    """🚀 高级模式处理 - 并发处理和PDF生成"""
    print("🚀 启动高级模式...")
    
    # 先执行视觉模式处理
    enhanced_result = process_visual_mode(args, output_dir)
    
    # 检查是否启用高级功能
    enable_concurrent = not args.disable_concurrent
    enable_pdf = not args.disable_pdf
    
    if not enable_concurrent and not enable_pdf:
        print("  ⚠️ 并发和PDF都已禁用，返回视觉处理结果")
        return enhanced_result
    
    # 导入高级处理模块
    try:
        from src.advanced_processor import AdvancedMediaProcessor
        from src.visual_processor import VisualProcessor
        
        visual_processor = VisualProcessor()
        advanced_processor = AdvancedMediaProcessor(visual_processor)
        print("  📦 高级模块加载成功")
        
    except ImportError as e:
        print(f"  ❌ 高级处理模块导入失败: {e}")
        print("  ⚠️ 尝试生成简单PDF...")
        
        if enable_pdf:
            try:
                simple_pdf_path = output_dir / "simple_report.pdf"
                generate_simple_pdf(enhanced_result, str(simple_pdf_path))
                print(f"    ✅ 简单PDF报告: {simple_pdf_path}")
            except Exception as pdf_e:
                print(f"    ❌ PDF生成失败: {pdf_e}")
                
        return enhanced_result
    
    try:
        # 并发视觉处理
        if enable_concurrent and 'visual_segments' not in enhanced_result:
            print("  ⚡ 执行并发视觉处理...")
            enhanced_result = advanced_processor.process_video_with_concurrent_visual(
                video_path=args.video_path,
                summary_result=enhanced_result,
                output_dir=str(output_dir / "concurrent")
            )
            
            # 显示并发处理统计
            stats = enhanced_result.get('processing_stats', {})
            print(f"    🔄 并发分段: {stats.get('concurrent_segments', 0)}")
            print(f"    ⏱️ 处理时间: {stats.get('total_processing_time', 0):.1f}秒")
        
        # PDF生成
        if enable_pdf:
            print("  📄 生成图文混排PDF...")
            pdf_path = str(output_dir / "advanced_report.pdf")
            
            advanced_processor.generate_mixed_content_pdf(
                enhanced_result=enhanced_result,
                output_path=pdf_path,
                include_images=not args.no_images
            )
            
            # 显示PDF信息
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                print(f"    ✅ PDF报告: {pdf_path} ({size_mb:.2f}MB)")
        
        # 保存最终结果
        advanced_path = output_dir / "advanced_result.json"
        with open(advanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_result, f, ensure_ascii=False, indent=2)
        
        print("  ✅ 高级模式处理完成")
        return enhanced_result
        
    except Exception as e:
        print(f"  ⚠️ 高级处理失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return enhanced_result

def generate_markdown_report(summary_result: dict, output_path: str):
    """生成Markdown报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# MediaScribe 视频分析报告\n\n")
        f.write(f"## 整体摘要\n\n{summary_result.get('overall_summary', '')}\n\n")
        
        # 基本信息
        metadata = summary_result.get('metadata', {})
        f.write("## 基本信息\n\n")
        f.write(f"- **语言**: {metadata.get('language', 'unknown')}\n")
        f.write(f"- **总时长**: {metadata.get('total_duration', 0):.1f}秒\n")
        f.write(f"- **分段数**: {metadata.get('total_segments', 0)}\n")
        f.write(f"- **总词数**: {metadata.get('total_words', 0)}\n\n")
        
        # 分段内容
        f.write("## 分段内容\n\n")
        for i, segment in enumerate(summary_result.get('segments', []), 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 第 {i} 段 ({start_time:.1f}s - {end_time:.1f}s)\n\n")
            f.write(f"**摘要**: {segment.get('summary', '')}\n\n")
            
            # 限制原文长度避免markdown过长
            text = segment.get('text', '')
            if len(text) > 300:
                text = text[:300] + "..."
            f.write(f"**原文**: {text}\n\n")
            f.write("---\n\n")

def generate_simple_pdf(summary_result: dict, output_path: str):
    """生成简单的PDF报告 (备用方案)"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 标题
        story.append(Paragraph("MediaScribe 视频分析报告", styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        
        # 整体摘要
        story.append(Paragraph("整体摘要", styles['Heading1']))
        story.append(Paragraph(summary_result.get('overall_summary', ''), styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # 分段内容 (限制数量避免PDF过大)
        segments = summary_result.get('segments', [])[:10]  # 最多10段
        story.append(Paragraph(f"分段内容 (前{len(segments)}段)", styles['Heading1']))
        
        for i, segment in enumerate(segments, 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            story.append(Paragraph(f"第 {i} 段 ({start_time:.1f}s - {end_time:.1f}s)", styles['Heading2']))
            story.append(Paragraph(f"摘要: {segment.get('summary', '')}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        
    except Exception as e:
        raise Exception(f"简单PDF生成失败: {e}")

if __name__ == "__main__":
    main()

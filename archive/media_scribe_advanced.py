#!/usr/bin/env python3
"""
MediaScribe - 高难度版本
支持并发视觉处理和图文混排PDF生成
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
from src.visual_processor import VisualProcessor
from src.advanced_processor import AdvancedMediaProcessor
from src.utils import setup_logging, validate_video_file
from src.config import CONFIG

def main():
    """主函数 - 高难度完整处理"""
    parser = argparse.ArgumentParser(description='MediaScribe - 高难度图文混排讲义工具')
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--whisper-url', default='http://localhost:8760', help='Whisper ASR服务地址')
    parser.add_argument('--llm-url', default='http://192.168.1.3:8000', help='LLM服务地址')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    # 高难度特定参数
    parser.add_argument('--enable-concurrent', action='store_true', default=True, 
                       help='启用并发视觉处理 (默认开启)')
    parser.add_argument('--generate-pdf', action='store_true', default=True,
                       help='生成PDF报告 (默认开启)')
    parser.add_argument('--max-workers', type=int, default=3,
                       help='最大并发工作线程数 (默认: 3)')
    parser.add_argument('--include-images', action='store_true', default=True,
                       help='PDF中包含图片 (默认开启)')
    
    # 视觉处理参数
    parser.add_argument('--crop-mode', choices=['center', 'yolo', 'none'], default='center',
                       help='裁剪模式 (默认: center)')
    parser.add_argument('--similarity-threshold', type=float, default=0.85,
                       help='图片相似度阈值 (默认: 0.85)')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(debug=args.debug)
    
    # 验证输入文件
    if not validate_video_file(args.video_path):
        print(f"错误: 视频文件不存在或格式不支持: {args.video_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 MediaScribe 高难度处理模式启动...")
    print("="*80)
    print(f"📹 输入视频: {args.video_path}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🔧 并发处理: {'开启' if args.enable_concurrent else '关闭'}")
    print(f"📄 PDF生成: {'开启' if args.generate_pdf else '关闭'}")
    print(f"🖼️ 图片模式: {args.crop_mode}")
    print("="*80)
    
    total_start_time = time.time()
    
    try:
        # 初始化服务
        print("🔧 初始化服务...")
        video_processor = VideoProcessor()
        asr_service = ASRService(base_url=args.whisper_url)
        llm_service = LLMService(base_url=args.llm_url)
        summary_generator = SummaryGenerator(llm_service)
        visual_processor = VisualProcessor()
        advanced_processor = AdvancedMediaProcessor(visual_processor)
        
        # 检查服务状态
        print("📡 检查服务状态...")
        services_ok = True
        
        try:
            asr_health = asr_service.health_check()
            print(f"  ✅ ASR服务: {asr_health}")
        except Exception as e:
            print(f"  ❌ ASR服务连接失败: {e}")
            services_ok = False
        
        try:
            llm_health = llm_service.health_check()
            print(f"  ✅ LLM服务: {llm_health}")
        except Exception as e:
            print(f"  ❌ LLM服务连接失败: {e}")
            services_ok = False
        
        try:
            visual_health = visual_processor.check_services()
            print(f"  ✅ 视觉服务: {visual_health}")
        except Exception as e:
            print(f"  ❌ 视觉服务连接失败: {e}")
            services_ok = False
        
        if not services_ok:
            print("❌ 部分服务不可用，但将尝试继续处理...")
        
        # 阶段1: 基础音频处理
        print("\n🎵 阶段1: 音频提取与转录...")
        phase1_start = time.time()
        
        audio_path = video_processor.extract_audio(args.video_path, str(output_dir / "audio.mp3"))
        print(f"  ✅ 音频提取完成: {audio_path}")
        
        transcript_result = asr_service.transcribe_audio(audio_path)
        transcript_path = output_dir / "transcript_raw.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_result, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 转录完成: {transcript_path}")
        
        phase1_time = time.time() - phase1_start
        print(f"  ⏱️ 阶段1耗时: {phase1_time:.2f}秒")
        
        # 阶段2: 文本摘要生成
        print("\n📝 阶段2: 智能摘要生成...")
        phase2_start = time.time()
        
        summary_result = summary_generator.generate_summary_with_segments(transcript_result)
        summary_path = output_dir / "summary_result.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 摘要生成完成: {summary_path}")
        
        segments_count = len(summary_result.get('segments', []))
        print(f"  📊 生成分段数: {segments_count}")
        
        phase2_time = time.time() - phase2_start
        print(f"  ⏱️ 阶段2耗时: {phase2_time:.2f}秒")
        
        # 阶段3: 并发视觉处理 (高难度核心)
        print(f"\n🖼️ 阶段3: 并发视觉处理 (高难度模式)...")
        print(f"  🔄 将对 {segments_count} 个分段进行并发视觉处理...")
        phase3_start = time.time()
        
        if args.enable_concurrent:
            enhanced_result = advanced_processor.process_video_with_concurrent_visual(
                video_path=args.video_path,
                summary_result=summary_result,
                output_dir=str(output_dir)
            )
        else:
            print("  ⚠️ 并发处理已禁用，跳过视觉处理")
            enhanced_result = summary_result
            enhanced_result['visual_segments'] = []
            enhanced_result['processing_stats'] = {'total_processing_time': 0}
        
        enhanced_path = output_dir / "enhanced_result.json"
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_result, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 增强结果保存: {enhanced_path}")
        
        phase3_time = time.time() - phase3_start
        print(f"  ⏱️ 阶段3耗时: {phase3_time:.2f}秒")
        
        # 阶段4: PDF报告生成 (高难度核心)
        print(f"\n📄 阶段4: 图文混排PDF生成...")
        phase4_start = time.time()
        
        if args.generate_pdf:
            pdf_path = str(output_dir / "mediascribe_report.pdf")
            try:
                generated_pdf = advanced_processor.generate_mixed_content_pdf(
                    enhanced_result=enhanced_result,
                    output_path=pdf_path,
                    include_images=args.include_images
                )
                print(f"  ✅ PDF报告生成成功: {generated_pdf}")
            except Exception as e:
                print(f"  ❌ PDF生成失败: {e}")
                # 生成备用的markdown报告
                md_path = output_dir / "backup_report.md"
                generate_markdown_report(enhanced_result, str(md_path))
                print(f"  📝 已生成备用Markdown报告: {md_path}")
        else:
            print("  ⚠️ PDF生成已禁用")
        
        phase4_time = time.time() - phase4_start
        print(f"  ⏱️ 阶段4耗时: {phase4_time:.2f}秒")
        
        # 总结
        total_time = time.time() - total_start_time
        print("\n" + "="*80)
        print("🎉 MediaScribe 高难度处理完成!")
        print("="*80)
        print("📊 处理统计:")
        print(f"  🕐 总处理时间: {total_time:.2f}秒")
        print(f"  🎵 音频处理: {phase1_time:.2f}秒")
        print(f"  📝 文本摘要: {phase2_time:.2f}秒")
        print(f"  🖼️ 视觉处理: {phase3_time:.2f}秒")
        print(f"  📄 PDF生成: {phase4_time:.2f}秒")
        
        if enhanced_result.get('visual_segments'):
            visual_stats = enhanced_result.get('processing_stats', {})
            total_images = sum(vs.get('image_count', 0) for vs in enhanced_result['visual_segments'] if vs)
            print(f"  📸 总图片数: {total_images}")
            print(f"  🔄 并发分段: {visual_stats.get('concurrent_segments', 0)}")
        
        print("\n📁 生成的文件:")
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  📄 {file_path.name} ({size_mb:.2f}MB)")
        
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def generate_markdown_report(enhanced_result, output_path):
    """生成增强的Markdown报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# MediaScribe 高难度处理报告\n\n")
        f.write(f"## 整体摘要\n\n{enhanced_result.get('overall_summary', '')}\n\n")
        
        # 元数据
        metadata = enhanced_result.get('metadata', {})
        f.write("## 基本信息\n\n")
        f.write(f"- **语言**: {metadata.get('language', 'unknown')}\n")
        f.write(f"- **总时长**: {metadata.get('total_duration', 0):.1f}秒\n")
        f.write(f"- **分段数**: {metadata.get('total_segments', 0)}\n")
        f.write(f"- **总词数**: {metadata.get('total_words', 0)}\n\n")
        
        # 处理统计
        stats = enhanced_result.get('processing_stats', {})
        f.write("## 处理统计\n\n")
        f.write(f"- **总处理时间**: {stats.get('total_processing_time', 0):.2f}秒\n")
        f.write(f"- **并发分段数**: {stats.get('concurrent_segments', 0)}\n\n")
        
        # 分段内容
        f.write("## 图文混排内容\n\n")
        visual_segments = enhanced_result.get('visual_segments', [])
        
        for i, visual_segment in enumerate(visual_segments, 1):
            if not visual_segment:
                continue
                
            time_range = visual_segment.get('time_range', '')
            f.write(f"### 第 {i} 段 ({time_range})\n\n")
            
            summary = visual_segment.get('summary', '')
            if summary:
                f.write(f"**摘要**: {summary}\n\n")
            
            # 图片信息
            image_count = visual_segment.get('image_count', 0)
            if image_count > 0:
                f.write(f"**关键画面**: {image_count} 张\n")
                key_images = visual_segment.get('key_images', [])
                for j, img_path in enumerate(key_images, 1):
                    f.write(f"  {j}. {img_path}\n")
                f.write("\n")
            
            text = visual_segment.get('text', '')
            if text:
                # 限制显示长度
                display_text = text[:300] + "..." if len(text) > 300 else text
                f.write(f"**详细内容**: {display_text}\n\n")
            
            f.write("---\n\n")

if __name__ == "__main__":
    main()

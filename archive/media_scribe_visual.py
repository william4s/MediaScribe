#!/usr/bin/env python3
"""
MediaScribe - 视频生成图文混排讲义工具 (支持视觉处理)
主入口文件
"""

import os
import sys
import argparse
import json
from pathlib import Path

from src.video_processor import VideoProcessor
from src.asr_service import ASRService
from src.llm_service import LLMService
from src.summary_generator import SummaryGenerator
from src.visual_processor import VisualProcessor
from src.utils import setup_logging, validate_video_file
from src.config import CONFIG

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MediaScribe - 视频生成图文混排讲义工具')
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--whisper-url', default='http://localhost:8760', help='Whisper ASR服务地址')
    parser.add_argument('--llm-url', default='http://192.168.1.3:8000', help='LLM服务地址')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    # 视觉处理相关参数
    parser.add_argument('--enable-visual', action='store_true', help='启用视觉处理功能')
    parser.add_argument('--extract-fps', type=float, default=1.0, help='抽帧率 (每秒几帧, 默认: 1.0)')
    parser.add_argument('--start-time', type=int, default=0, help='开始处理时间 (秒, 默认: 0)')
    parser.add_argument('--duration', type=int, help='处理时长 (秒, 默认: 整个视频)')
    parser.add_argument('--crop-mode', choices=['center', 'yolo', 'none'], default='center', 
                       help='裁剪模式: center(中心裁剪), yolo(YOLO检测), none(不裁剪) (默认: center)')
    parser.add_argument('--crop-ratios', nargs='+', default=['4:3'], 
                       help='中心裁剪比例 (默认: 4:3)')
    parser.add_argument('--crop-confidence', type=float, default=0.5, help='YOLO裁剪置信度阈值 (默认: 0.5)')
    parser.add_argument('--similarity-threshold', type=float, default=0.95, help='图片相似度阈值 (默认: 0.95)')
    
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
    
    try:
        # 初始化服务
        video_processor = VideoProcessor()
        asr_service = ASRService(args.whisper_url)
        llm_service = LLMService(args.llm_url)
        summary_generator = SummaryGenerator(llm_service)
        
        # 如果启用视觉处理，初始化视觉处理器
        visual_processor = None
        if args.enable_visual:
            visual_processor = VisualProcessor()
            # 更新相似度阈值
            visual_processor.similarity_threshold = args.similarity_threshold
        
        print(f"正在处理视频: {args.video_path}")
        print(f"视觉处理: {'启用' if args.enable_visual else '禁用'}")
        
        # 步骤1: 音视频分流
        print("步骤1: 提取音频...")
        audio_path = video_processor.extract_audio(args.video_path, output_dir)
        print(f"音频提取完成: {audio_path}")
        
        # 步骤2: ASR转录
        print("步骤2: 语音转文字...")
        transcript_result = asr_service.transcribe(audio_path)
        print(f"转录完成，检测到语言: {transcript_result.get('language', 'unknown')}")
        
        # 保存原始转录结果
        transcript_path = output_dir / "transcript_raw.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_result, f, ensure_ascii=False, indent=2)
        print(f"原始转录结果已保存: {transcript_path}")
        
        # 步骤3: 视觉处理 (可选)
        visual_results = None
        if args.enable_visual and visual_processor:
            print("步骤3: 视觉处理...")
            print(f"  抽帧参数: fps={args.extract_fps}, start_time={args.start_time}, duration={args.duration}")
            print(f"  裁剪参数: mode={args.crop_mode}, ratios={args.crop_ratios}, confidence={args.crop_confidence}")
            print(f"  去重参数: similarity_threshold={args.similarity_threshold}")
            
            visual_results = visual_processor.process_video_frames(
                video_path=args.video_path,
                output_dir=output_dir / "visual",
                fps=args.extract_fps,
                start_time=args.start_time,
                duration=args.duration,
                crop_mode=args.crop_mode,
                crop_ratios=args.crop_ratios,
                crop_confidence=args.crop_confidence
            )
            
            print("视觉处理完成!")
            stats = visual_results['processing_stats']
            print(f"  处理统计:")
            print(f"    原始帧数: {stats['original_frame_count']}")
            print(f"    处理前图片数: {stats['images_before_dedup']}")
            print(f"    最终图片数: {stats['final_image_count']}")
            print(f"    去重率: {stats['deduplication_rate']:.1%}")
        
        # 步骤4: 生成摘要并分段
        print("步骤4: 生成摘要和分段...")
        summary_result = summary_generator.generate_summary_with_segments(transcript_result)
        
        # 如果有视觉处理结果，将其整合到最终结果中
        if visual_results:
            summary_result['visual_processing'] = visual_results
        
        # 保存最终结果
        final_result_path = output_dir / "final_result.json"
        with open(final_result_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        print(f"最终结果已保存: {final_result_path}")
        
        # 生成可读的报告
        report_path = output_dir / "report.md"
        generate_markdown_report(summary_result, report_path, visual_results)
        print(f"Markdown报告已生成: {report_path}")
        
        print("\n" + "="*50)
        print("处理完成！")
        print("输出文件:")
        print(f"  - 音频文件: {audio_path}")
        print(f"  - 原始转录: {transcript_path}")
        print(f"  - 最终结果: {final_result_path}")
        print(f"  - 报告文件: {report_path}")
        
        if visual_results:
            visual_dir = output_dir / "visual"
            print(f"  - 视觉处理目录: {visual_dir}")
            print(f"  - 最终保留图片数: {len(visual_results['final_images'])}")
        
        print("="*50)
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def generate_markdown_report(summary_result, output_path, visual_results=None):
    """生成Markdown格式的报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 视频讲义报告\n\n")
        
        # 整体摘要
        f.write(f"## 整体摘要\n\n{summary_result.get('overall_summary', '')}\n\n")
        
        # 视觉处理结果 (如果有)
        if visual_results:
            f.write("## 视觉处理结果\n\n")
            stats = visual_results['processing_stats']
            f.write(f"- **原始抽取帧数**: {stats['original_frame_count']}\n")
            f.write(f"- **处理前图片数**: {stats['images_before_dedup']}\n")
            f.write(f"- **最终保留图片数**: {stats['final_image_count']}\n")
            f.write(f"- **删除重复图片数**: {stats['removed_duplicate_count']}\n")
            f.write(f"- **去重率**: {stats['deduplication_rate']:.1%}\n\n")
            
            # 智能裁剪统计
            if visual_results.get('cropped_images'):
                f.write("### 智能裁剪统计\n\n")
                detected_labels = {}
                for crop in visual_results['cropped_images']:
                    label = crop['label']
                    if label not in detected_labels:
                        detected_labels[label] = 0
                    detected_labels[label] += 1
                
                f.write("检测到的物体类型:\n\n")
                for label, count in detected_labels.items():
                    f.write(f"- **{label}**: {count} 个\n")
                f.write("\n")
            
            # 最终保留的图片
            if visual_results['final_images']:
                f.write("### 最终保留的关键图片\n\n")
                for i, img_path in enumerate(visual_results['final_images'][:20], 1):  # 最多显示20张
                    img_name = Path(img_path).name
                    relative_path = Path(img_path).relative_to(Path(output_path).parent)
                    f.write(f"{i}. ![{img_name}]({relative_path})\n")
                
                if len(visual_results['final_images']) > 20:
                    f.write(f"\n*还有 {len(visual_results['final_images']) - 20} 张图片...*\n")
                f.write("\n")
        
        # 分段内容
        f.write("## 分段内容\n\n")
        
        for i, segment in enumerate(summary_result.get('segments', []), 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 段落 {i} ({start_time:.1f}s - {end_time:.1f}s)\n\n")
            f.write(f"**摘要:** {segment.get('summary', '')}\n\n")
            f.write(f"**原文:** {segment.get('text', '')}\n\n")

if __name__ == '__main__':
    main()

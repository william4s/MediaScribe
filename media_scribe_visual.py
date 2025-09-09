#!/usr/bin/env python3
"""
MediaScribe - 视频生成图文混排讲义工具 (支持视觉处理)
增强版本主入口文件
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
    parser.add_argument('--max-frames', type=int, default=50, help='最大抽帧数量 (默认: 50)')
    
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
    
    print("🚀 MediaScribe 增强版本启动...")
    print("="*60)
    print(f"📹 输入视频: {args.video_path}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🖼️ 视觉处理: {'开启' if args.enable_visual else '关闭'}")
    if args.enable_visual:
        print(f"   - 裁剪模式: {args.crop_mode}")
        print(f"   - 最大帧数: {args.max_frames}")
        print(f"   - 相似度阈值: {args.similarity_threshold}")
    print("="*60)
    
    try:
        # 初始化服务
        print("🔧 初始化服务...")
        video_processor = VideoProcessor()
        asr_service = ASRService(args.whisper_url)
        llm_service = LLMService(args.llm_url)
        summary_generator = SummaryGenerator(llm_service)
        
        # 检查服务状态
        print("📡 检查服务状态...")
        try:
            asr_health = asr_service.health_check()
            print(f"  ✅ ASR服务: {asr_health}")
        except Exception as e:
            print(f"  ❌ ASR服务连接失败: {e}")
        
        try:
            llm_health = llm_service.health_check()
            print(f"  ✅ LLM服务: {llm_health}")
        except Exception as e:
            print(f"  ❌ LLM服务连接失败: {e}")
        
        # 视觉处理初始化
        visual_processor = None
        if args.enable_visual:
            try:
                visual_processor = VisualProcessor()
                # 检查视觉服务
                embedding_status = visual_processor._check_embedding_service()
                yolo_status = visual_processor._check_yolo_service()
                print(f"  ✅ Embedding服务 (端口8762): {embedding_status}")
                print(f"  ✅ YOLO服务 (端口8761): {yolo_status}")
            except Exception as e:
                print(f"  ❌ 视觉服务初始化失败: {e}")
                print("  ⚠️ 视觉处理功能将被禁用")
                args.enable_visual = False
        
        # 步骤1: 音视频分流
        print("\n🎵 步骤1: 提取音频...")
        audio_path = video_processor.extract_audio(args.video_path, str(output_dir))
        print(f"  ✅ 音频提取完成: {audio_path}")
        
        # 步骤2: ASR转录
        print("\n🗣️ 步骤2: 语音转文字...")
        transcript_result = asr_service.transcribe(audio_path)
        print(f"  ✅ 转录完成，检测到语言: {transcript_result.get('language', 'unknown')}")
        
        # 保存原始转录结果
        transcript_path = output_dir / "transcript_raw.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_result, f, ensure_ascii=False, indent=2)
        print(f"  📄 原始转录结果已保存: {transcript_path}")
        
        # 步骤3: 生成摘要并分段
        print("\n📝 步骤3: 生成摘要和分段...")
        summary_result = summary_generator.generate_summary_with_segments(transcript_result)
        print(f"  ✅ 摘要生成完成，共 {len(summary_result.get('segments', []))} 个分段")
        
        # 步骤4: 视觉处理 (如果启用)
        if args.enable_visual and visual_processor:
            print("\n🖼️ 步骤4: 视觉处理...")
            
            # 配置视觉处理参数
            visual_config = {
                'fps': args.extract_fps,  # 使用extract_fps参数
                'start_time': args.start_time,
                'duration': args.duration,
                'crop_mode': args.crop_mode
            }
            
            if args.crop_mode == 'center':
                visual_config['crop_ratios'] = args.crop_ratios
            elif args.crop_mode == 'yolo':
                visual_config['crop_confidence'] = args.crop_confidence
            
            try:
                # 创建视觉处理输出目录
                visual_output_dir = output_dir / "visual_processing"
                visual_output_dir.mkdir(exist_ok=True)
                
                # 执行视觉处理
                visual_result = visual_processor.process_video_frames(
                    video_path=args.video_path,
                    output_dir=str(visual_output_dir),
                    **visual_config
                )
                
                print(f"  ✅ 视觉处理完成:")
                print(f"     - 原始帧数: {visual_result.get('original_frame_count', 0)}")
                print(f"     - 最终保留: {visual_result.get('final_image_count', 0)}")
                print(f"     - 去重效率: {visual_result.get('deduplication_rate', 0)*100:.1f}%")
                
                # 保存视觉处理结果
                visual_result_path = output_dir / "visual_processing_results.json"
                with open(visual_result_path, 'w', encoding='utf-8') as f:
                    json.dump(visual_result, f, ensure_ascii=False, indent=2)
                print(f"  📄 视觉处理结果已保存: {visual_result_path}")
                
                # 合并结果
                summary_result['visual_processing'] = visual_result
                
            except Exception as e:
                print(f"  ❌ 视觉处理失败: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
        
        # 保存最终结果
        print("\n💾 保存结果...")
        final_result_path = output_dir / "final_result.json"
        with open(final_result_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        print(f"  📄 最终结果已保存: {final_result_path}")
        
        # 生成可读的报告
        if args.enable_visual and 'visual_processing' in summary_result:
            report_path = output_dir / "report_with_visual.md"
            generate_visual_markdown_report(summary_result, report_path)
            print(f"  📋 增强报告已生成: {report_path}")
        else:
            report_path = output_dir / "report.md"
            generate_markdown_report(summary_result, report_path)
            print(f"  📋 标准报告已生成: {report_path}")
        
        print("\n🎉 处理完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 处理过程中出现错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def generate_markdown_report(summary_result, output_path):
    """生成标准Markdown格式的报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 视频讲义报告\n\n")
        f.write(f"## 整体摘要\n\n{summary_result.get('overall_summary', '')}\n\n")
        
        # 元数据信息
        metadata = summary_result.get('metadata', {})
        f.write("## 基本信息\n\n")
        f.write(f"- **语言**: {metadata.get('language', 'unknown')}\n")
        f.write(f"- **总时长**: {metadata.get('total_duration', 0):.1f}秒\n")
        f.write(f"- **分段数**: {metadata.get('total_segments', 0)}\n")
        f.write(f"- **总词数**: {metadata.get('total_words', 0)}\n\n")
        
        f.write("## 分段内容\n\n")
        
        for i, segment in enumerate(summary_result.get('segments', []), 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 段落 {i} ({start_time:.1f}s - {end_time:.1f}s)\n\n")
            f.write(f"**摘要:** {segment.get('summary', '')}\n\n")
            f.write(f"**原文:** {segment.get('text', '')}\n\n")
            f.write("---\n\n")

def generate_visual_markdown_report(summary_result, output_path):
    """生成包含视觉处理的增强Markdown报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 视频讲义报告 (含视觉分析)\n\n")
        f.write(f"## 整体摘要\n\n{summary_result.get('overall_summary', '')}\n\n")
        
        # 元数据信息
        metadata = summary_result.get('metadata', {})
        f.write("## 基本信息\n\n")
        f.write(f"- **语言**: {metadata.get('language', 'unknown')}\n")
        f.write(f"- **总时长**: {metadata.get('total_duration', 0):.1f}秒\n")
        f.write(f"- **分段数**: {metadata.get('total_segments', 0)}\n")
        f.write(f"- **总词数**: {metadata.get('total_words', 0)}\n\n")
        
        # 视觉处理统计
        visual_processing = summary_result.get('visual_processing', {})
        if visual_processing:
            f.write("## 视觉分析统计\n\n")
            f.write(f"- **原始帧数**: {visual_processing.get('original_frame_count', 0)}\n")
            f.write(f"- **处理后帧数**: {visual_processing.get('images_before_dedup', 0)}\n")
            f.write(f"- **最终保留**: {visual_processing.get('final_image_count', 0)}\n")
            f.write(f"- **去重效率**: {visual_processing.get('deduplication_rate', 0)*100:.1f}%\n\n")
            
            # 关键图片
            final_images = visual_processing.get('final_images', [])
            if final_images:
                f.write("### 关键画面\n\n")
                for i, img_path in enumerate(final_images[:10], 1):  # 最多显示10张
                    f.write(f"{i}. `{img_path}`\n")
                f.write("\n")
        
        f.write("## 分段内容\n\n")
        
        for i, segment in enumerate(summary_result.get('segments', []), 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 段落 {i} ({start_time:.1f}s - {end_time:.1f}s)\n\n")
            f.write(f"**摘要:** {segment.get('summary', '')}\n\n")
            f.write(f"**原文:** {segment.get('text', '')}\n\n")
            f.write("---\n\n")

if __name__ == '__main__':
    main()

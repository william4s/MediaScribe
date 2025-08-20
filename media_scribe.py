#!/usr/bin/env python3
"""
MediaScribe - 视频生成图文混排讲义工具
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
from src.utils import setup_logging, validate_video_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MediaScribe - 视频生成图文混排讲义工具')
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--whisper-url', default='http://localhost:8760', help='Whisper ASR服务地址')
    parser.add_argument('--llm-url', default='http://192.168.1.3:8000', help='LLM服务地址')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
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
        
        print(f"正在处理视频: {args.video_path}")
        
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
        
        # 步骤3: 生成摘要并分段
        print("步骤3: 生成摘要和分段...")
        summary_result = summary_generator.generate_summary_with_segments(transcript_result)
        
        # 保存最终结果
        final_result_path = output_dir / "final_result.json"
        with open(final_result_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        print(f"最终结果已保存: {final_result_path}")
        
        # 生成可读的报告
        report_path = output_dir / "report.md"
        generate_markdown_report(summary_result, report_path)
        print(f"Markdown报告已生成: {report_path}")
        
        print("处理完成！")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def generate_markdown_report(summary_result, output_path):
    """生成Markdown格式的报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 视频讲义报告\n\n")
        f.write(f"## 整体摘要\n\n{summary_result.get('overall_summary', '')}\n\n")
        f.write("## 分段内容\n\n")
        
        for i, segment in enumerate(summary_result.get('segments', []), 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 段落 {i} ({start_time:.1f}s - {end_time:.1f}s)\n\n")
            f.write(f"**摘要:** {segment.get('summary', '')}\n\n")
            f.write(f"**原文:** {segment.get('text', '')}\n\n")

if __name__ == '__main__':
    main()

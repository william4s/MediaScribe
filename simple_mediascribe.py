#!/usr/bin/env python3
"""
MediaScribe 简化测试版本
专门针对当前测试场景优化
"""

import os
import sys
import json
import requests
from pathlib import Path

def extract_audio_with_ffmpeg(video_path, output_dir):
    """使用ffmpeg提取音频"""
    import subprocess
    
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    audio_filename = f"{video_path.stem}.mp3"
    audio_path = output_dir / audio_filename
    
    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-vn',  # 不包含视频流
        '-acodec', 'mp3',
        '-ar', '16000',  # 采样率16kHz
        '-ac', '1',      # 单声道
        '-y',            # 覆盖输出文件
        str(audio_path)
    ]
    
    print(f"提取音频: {video_path} -> {audio_path}")
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"音频提取成功: {audio_path}")
        return str(audio_path)
    except subprocess.CalledProcessError as e:
        print(f"音频提取失败: {e.stderr}")
        raise

def transcribe_with_whisper(audio_path, whisper_url='http://localhost:8760'):
    """调用Whisper ASR服务"""
    params = {
        'encode': 'true',
        'task': 'transcribe',
        'vad_filter': 'false',
        'word_timestamps': 'true',
        'output': 'json'
    }
    
    url = f"{whisper_url}/asr"
    
    print(f"开始转录: {audio_path}")
    
    with open(audio_path, 'rb') as audio_file:
        files = {
            'audio_file': (Path(audio_path).name, audio_file, 'audio/mpeg')
        }
        
        response = requests.post(
            url,
            params=params,
            files=files,
            timeout=300
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"转录完成，语言: {result.get('language')}, 分段数: {len(result.get('segments', []))}")
        return result

def generate_summary_with_llm(transcript_result, llm_url='http://192.168.1.3:8000', api_key='sk-kfccrazythursdayvme50'):
    """调用LLM生成摘要（简化版）"""
    full_text = transcript_result.get('text', '')
    segments = transcript_result.get('segments', [])
    
    # 简化版：只为整个内容生成摘要，不逐段处理
    system_prompt = "你是一个专业的摘要助手。请为用户提供的视频转录文本生成简洁的摘要，长度控制在200字以内。"
    
    # 截取前2000字符避免超时
    text_for_summary = full_text[:2000] + "..." if len(full_text) > 2000 else full_text
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请为以下视频转录内容生成摘要：\\n\\n{text_for_summary}"}
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': 'qwen3',
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 500
    }
    
    try:
        print("正在生成整体摘要...")
        response = requests.post(
            f"{llm_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60  # 降低超时时间
        )
        
        response.raise_for_status()
        result = response.json()
        
        overall_summary = result['choices'][0]['message']['content']
        print("摘要生成成功")
        
    except Exception as e:
        print(f"LLM摘要生成失败，使用备用方案: {e}")
        # 备用摘要：取前200字符
        overall_summary = full_text[:200] + "..." if len(full_text) > 200 else full_text
    
    # 构建简化的结果
    result = {
        "overall_summary": overall_summary,
        "segments": [],
        "metadata": {
            "language": transcript_result.get('language', 'unknown'),
            "total_duration": segments[-1].get('end', 0) if segments else 0,
            "total_segments": len(segments),
            "total_words": len(full_text.split()),
            "source": "whisper_asr"
        }
    }
    
    # 为每个分段添加基本信息（不生成单独摘要以避免超时）
    for segment in segments:
        segment_info = {
            "start_time": segment.get('start', 0),
            "end_time": segment.get('end', 0),
            "text": segment.get('text', '').strip(),
            "summary": segment.get('text', '').strip()[:50] + "..." if len(segment.get('text', '')) > 50 else segment.get('text', '').strip()
        }
        result["segments"].append(segment_info)
    
    return result

def create_markdown_report(summary_result, output_path):
    """生成Markdown报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 视频讲义报告\\n\\n")
        f.write(f"## 整体摘要\\n\\n{summary_result.get('overall_summary', '')}\\n\\n")
        f.write("## 基本信息\\n\\n")
        
        metadata = summary_result.get('metadata', {})
        f.write(f"- **语言**: {metadata.get('language', 'unknown')}\\n")
        f.write(f"- **总时长**: {metadata.get('total_duration', 0):.1f}秒\\n")
        f.write(f"- **分段数**: {metadata.get('total_segments', 0)}\\n")
        f.write(f"- **总词数**: {metadata.get('total_words', 0)}\\n\\n")
        
        f.write("## 分段内容（前10段预览）\\n\\n")
        
        # 只显示前10段，避免文件过大
        segments = summary_result.get('segments', [])[:10]
        for i, segment in enumerate(segments, 1):
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            f.write(f"### 段落 {i} ({start_time:.1f}s - {end_time:.1f}s)\\n\\n")
            f.write(f"**内容:** {segment.get('text', '')}\\n\\n")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_mediascribe.py <video_path> [output_dir]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_simple"
    
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        sys.exit(1)
    
    try:
        print("=" * 60)
        print("MediaScribe 简化版本 - 视频转讲义工具")
        print("=" * 60)
        
        # 步骤1: 提取音频
        print("\\n步骤1: 提取音频...")
        audio_path = extract_audio_with_ffmpeg(video_path, output_dir)
        
        # 步骤2: 转录
        print("\\n步骤2: 语音转文字...")
        transcript_result = transcribe_with_whisper(audio_path)
        
        # 保存原始转录
        output_path = Path(output_dir)
        transcript_path = output_path / "transcript_raw.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_result, f, ensure_ascii=False, indent=2)
        print(f"原始转录保存: {transcript_path}")
        
        # 步骤3: 生成摘要
        print("\\n步骤3: 生成摘要...")
        summary_result = generate_summary_with_llm(transcript_result)
        
        # 保存最终结果
        final_path = output_path / "final_result.json"
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        print(f"最终结果保存: {final_path}")
        
        # 生成报告
        report_path = output_path / "report.md"
        create_markdown_report(summary_result, report_path)
        print(f"报告生成: {report_path}")
        
        print("\\n" + "=" * 60)
        print("处理完成!")
        print("=" * 60)
        print(f"输出目录: {output_path}")
        print(f"整体摘要: {summary_result['overall_summary'][:100]}...")
        print(f"分段数量: {len(summary_result['segments'])}")
        
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

"""
视频处理模块
使用ffmpeg进行音视频分离等操作
"""

import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        self.logger = logger
        
    def extract_audio(self, video_path, output_dir, audio_format='mp3'):
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            audio_format: 音频格式 (mp3, wav等)
            
        Returns:
            str: 音频文件路径
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        # 生成音频文件名
        audio_filename = f"{video_path.stem}.{audio_format}"
        audio_path = output_dir / audio_filename
        
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # 不包含视频流
            '-acodec', 'mp3' if audio_format == 'mp3' else 'pcm_s16le',
            '-ar', '16000',  # 采样率16kHz，适合ASR
            '-ac', '1',      # 单声道
            '-y',            # 覆盖输出文件
            str(audio_path)
        ]
        
        self.logger.info(f"开始提取音频: {video_path} -> {audio_path}")
        self.logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"音频提取成功: {audio_path}")
            return str(audio_path)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg处理失败: {e}")
            self.logger.error(f"错误输出: {e.stderr}")
            raise Exception(f"音频提取失败: {e.stderr}")
    
    def get_video_info(self, video_path):
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            dict: 视频信息
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            info = json.loads(result.stdout)
            
            # 提取有用信息
            video_info = {
                'duration': float(info['format'].get('duration', 0)),
                'size': int(info['format'].get('size', 0)),
                'format_name': info['format'].get('format_name', ''),
                'streams': []
            }
            
            for stream in info['streams']:
                stream_info = {
                    'codec_type': stream.get('codec_type'),
                    'codec_name': stream.get('codec_name'),
                    'duration': float(stream.get('duration', 0))
                }
                
                if stream['codec_type'] == 'video':
                    stream_info.update({
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'fps': eval(stream.get('r_frame_rate', '0/1'))
                    })
                
                video_info['streams'].append(stream_info)
            
            return video_info
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取视频信息失败: {e}")
            raise Exception(f"获取视频信息失败: {e.stderr}")
    
    def extract_frames(self, video_path, output_dir, fps=1, start_time=0, duration=None):
        """
        从视频中提取帧（为中高难度功能预留）
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            fps: 提取帧率
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            
        Returns:
            list: 提取的图片文件路径列表
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        frames_dir = output_dir / 'frames'
        frames_dir.mkdir(exist_ok=True)
        
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f'fps={fps}',
            '-ss', str(start_time)
        ]
        
        if duration:
            cmd.extend(['-t', str(duration)])
        
        cmd.extend([
            '-y',
            str(frames_dir / 'frame_%06d.jpg')
        ])
        
        self.logger.info(f"开始提取帧: {video_path}")
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 获取生成的图片文件列表
            frame_files = sorted(frames_dir.glob('frame_*.jpg'))
            self.logger.info(f"提取了 {len(frame_files)} 个帧")
            
            return [str(f) for f in frame_files]
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"帧提取失败: {e}")
            raise Exception(f"帧提取失败: {e.stderr}")

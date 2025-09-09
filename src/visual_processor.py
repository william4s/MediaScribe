"""
视觉处理模块
实现视频帧抽取、图片向量化、相似度计算和去重功能
"""

import os
import base64
import io
import json
import logging
import requests
import numpy as np
from pathlib import Path
from PIL import Image
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import cv2

from .config import CONFIG

logger = logging.getLogger(__name__)

class VisualProcessor:
    """视觉处理器"""
    
    def __init__(self):
        self.logger = logger
        self.embedding_service_url = "http://localhost:8762"
        self.yolo_service_url = "http://localhost:8761"
        self.similarity_threshold = CONFIG['image']['similarity_threshold']
        self.max_frames_per_segment = CONFIG['image']['max_frames_per_segment']
    
    def _check_embedding_service(self) -> str:
        """检查Embedding服务状态"""
        try:
            response = requests.get(f"{self.embedding_service_url}/", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"服务响应异常: {response.status_code}"
        except Exception as e:
            raise Exception(f"Embedding服务连接失败: {e}")
    
    def _check_yolo_service(self) -> str:
        """检查YOLO服务状态"""
        try:
            response = requests.get(f"{self.yolo_service_url}/", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"服务响应异常: {response.status_code}"
        except Exception as e:
            raise Exception(f"YOLO服务连接失败: {e}")
    
    def check_services(self) -> Dict[str, str]:
        """检查所有视觉处理服务的状态"""
        services_status = {}
        
        try:
            embedding_status = self._check_embedding_service()
            services_status['embedding'] = embedding_status
        except Exception as e:
            services_status['embedding'] = f"失败: {e}"
        
        try:
            yolo_status = self._check_yolo_service()
            services_status['yolo'] = yolo_status
        except Exception as e:
            services_status['yolo'] = f"失败: {e}"
        
        return services_status
        
    def extract_frames_from_video(self, video_path: str, output_dir: str, 
                                 fps: float = 1.0, start_time: int = 0, 
                                 duration: Optional[int] = None, 
                                 uniform_sampling: bool = True) -> List[Dict]:
        """
        从视频中抽取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            fps: 抽取帧率 (仅在uniform_sampling=False时使用)
            start_time: 开始时间（秒）
            duration: 持续时间（秒），None表示到视频结束
            uniform_sampling: 是否使用均匀采样（优先）
            
        Returns:
            List[Dict]: 抽取的图片信息列表，包含路径和时间戳
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        frames_dir = output_dir / 'frames'
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"开始从视频抽取帧: {video_path}")
        self.logger.info(f"参数: fps={fps}, start_time={start_time}, duration={duration}, uniform_sampling={uniform_sampling}")
        
        # 使用OpenCV读取视频
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise Exception(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / video_fps
        
        self.logger.info(f"视频信息: fps={video_fps}, 总帧数={total_frames}, 时长={video_duration:.2f}秒")
        
        # 计算实际处理时长
        if duration:
            actual_duration = min(duration, video_duration - start_time)
        else:
            actual_duration = video_duration - start_time
        
        extracted_frames = []
        
        if uniform_sampling:
            # 均匀采样模式：根据最大帧数均匀分布
            max_frames = min(self.max_frames_per_segment, int(actual_duration))
            
            if max_frames <= 0:
                self.logger.warning("有效持续时间太短，无法抽取帧")
                cap.release()
                return []
            
            # 计算时间间隔
            time_interval = actual_duration / max_frames
            self.logger.info(f"均匀采样: 目标帧数={max_frames}, 时间间隔={time_interval:.2f}秒")
            
            for i in range(max_frames):
                # 计算当前帧的时间点
                current_time = start_time + (i * time_interval)
                frame_number = int(current_time * video_fps)
                
                # 跳转到指定帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning(f"无法读取第 {frame_number} 帧")
                    continue
                
                # 保存帧
                frame_filename = f"frame_{i:06d}_t{current_time:.1f}s.jpg"
                frame_path = frames_dir / frame_filename
                
                # 转换颜色空间 (BGR -> RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                pil_image.save(frame_path, 'JPEG', quality=CONFIG['image']['image_quality'])
                
                frame_info = {
                    'path': str(frame_path),
                    'timestamp': current_time,
                    'frame_number': frame_number,
                    'index': i
                }
                extracted_frames.append(frame_info)
                
        else:
            # 原始按帧率采样模式
            frame_interval = int(video_fps / fps)
            start_frame = int(start_time * video_fps)
            
            if duration:
                end_frame = min(start_frame + int(actual_duration * video_fps), total_frames)
            else:
                end_frame = total_frames
            
            # 跳转到开始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = 0
            current_frame = start_frame
            
            while current_frame < end_frame and frame_count < self.max_frames_per_segment:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if (current_frame - start_frame) % frame_interval == 0:
                    # 计算当前时间点
                    current_time = current_frame / video_fps
                    
                    # 保存帧
                    frame_filename = f"frame_{frame_count:06d}_t{current_time:.1f}s.jpg"
                    frame_path = frames_dir / frame_filename
                    
                    # 转换颜色空间 (BGR -> RGB)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    pil_image.save(frame_path, 'JPEG', quality=CONFIG['image']['image_quality'])
                    
                    frame_info = {
                        'path': str(frame_path),
                        'timestamp': current_time,
                        'frame_number': current_frame,
                        'index': frame_count
                    }
                    extracted_frames.append(frame_info)
                    frame_count += 1
                
                current_frame += 1
        
        cap.release()
        
        self.logger.info(f"抽取完成，共提取 {len(extracted_frames)} 帧")
        if extracted_frames:
            self.logger.info(f"时间范围: {extracted_frames[0]['timestamp']:.1f}s - {extracted_frames[-1]['timestamp']:.1f}s")
        
        return extracted_frames
    
    def crop_image_with_yolo(self, image_path: str, output_dir: str, 
                           confidence_threshold: float = 0.5) -> List[Dict]:
        """
        使用YOLO检测图片中的物体并裁剪
        
        Args:
            image_path: 图片路径
            output_dir: 输出目录
            confidence_threshold: 置信度阈值
            
        Returns:
            List[Dict]: 裁剪结果列表，包含裁剪后的图片路径和检测信息
        """
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        crops_dir = output_dir / 'crops'
        crops_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取图片并转换为base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 调用YOLO服务
        try:
            response = requests.post(
                f"{self.yolo_service_url}/detect/",
                json={"image_base64": image_base64},
                timeout=30
            )
            response.raise_for_status()
            detections = response.json()['detections']
        except Exception as e:
            self.logger.error(f"YOLO检测失败: {e}")
            return []
        
        # 过滤低置信度检测结果
        valid_detections = [d for d in detections if d['confidence'] >= confidence_threshold]
        
        if not valid_detections:
            self.logger.info(f"图片 {image_path.name} 未检测到有效物体")
            return []
        
        # 打开原图进行裁剪
        original_image = Image.open(image_path)
        crop_results = []
        
        for i, detection in enumerate(valid_detections):
            # 获取边界框坐标
            x1 = int(detection['x1'])
            y1 = int(detection['y1'])
            x2 = int(detection['x2'])
            y2 = int(detection['y2'])
            
            # 确保坐标在图像范围内
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(original_image.width, x2)
            y2 = min(original_image.height, y2)
            
            # 裁剪图片
            cropped_image = original_image.crop((x1, y1, x2, y2))
            
            # 保存裁剪后的图片
            crop_filename = f"{image_path.stem}_crop_{i:03d}_{detection['label']}.jpg"
            crop_path = crops_dir / crop_filename
            cropped_image.save(crop_path, 'JPEG', quality=CONFIG['image']['image_quality'])
            
            crop_result = {
                'crop_path': str(crop_path),
                'original_path': str(image_path),
                'bbox': [x1, y1, x2, y2],
                'label': detection['label'],
                'confidence': detection['confidence'],
                'area': (x2 - x1) * (y2 - y1)
            }
            crop_results.append(crop_result)
        
        self.logger.info(f"从图片 {image_path.name} 裁剪出 {len(crop_results)} 个物体")
        return crop_results
    
    def crop_image_center(self, image_path: str, output_dir: str, 
                         aspect_ratios: List[str] = ['4:3', '3:2']) -> List[Dict]:
        """
        使用中心裁剪方式按指定比例裁剪图片
        
        Args:
            image_path: 图片路径
            output_dir: 输出目录
            aspect_ratios: 裁剪比例列表，支持 '4:3', '3:2', '16:9', '1:1'
            
        Returns:
            List[Dict]: 裁剪结果列表，包含裁剪后的图片路径和裁剪信息
        """
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        crops_dir = output_dir / 'crops'
        crops_dir.mkdir(parents=True, exist_ok=True)
        
        # 打开原图
        original_image = Image.open(image_path)
        original_width, original_height = original_image.size
        
        crop_results = []
        
        # 支持的裁剪比例
        ratio_map = {
            '4:3': 4/3,
            '3:2': 3/2,
            '16:9': 16/9,
            '1:1': 1/1,
            '2:3': 2/3,
            '3:4': 3/4
        }
        
        for ratio_name in aspect_ratios:
            if ratio_name not in ratio_map:
                self.logger.warning(f"不支持的比例: {ratio_name}")
                continue
                
            target_ratio = ratio_map[ratio_name]
            current_ratio = original_width / original_height
            
            # 计算裁剪尺寸
            if current_ratio > target_ratio:
                # 原图更宽，需要裁剪左右
                new_width = int(original_height * target_ratio)
                new_height = original_height
                x_offset = (original_width - new_width) // 2
                y_offset = 0
            else:
                # 原图更高，需要裁剪上下
                new_width = original_width
                new_height = int(original_width / target_ratio)
                x_offset = 0
                y_offset = (original_height - new_height) // 2
            
            # 确保裁剪区域在图像范围内
            x1 = max(0, x_offset)
            y1 = max(0, y_offset)
            x2 = min(original_width, x_offset + new_width)
            y2 = min(original_height, y_offset + new_height)
            
            # 执行裁剪
            cropped_image = original_image.crop((x1, y1, x2, y2))
            
            # 保存裁剪后的图片
            crop_filename = f"{image_path.stem}_center_{ratio_name.replace(':', '_')}.jpg"
            crop_path = crops_dir / crop_filename
            cropped_image.save(crop_path, 'JPEG', quality=CONFIG['image']['image_quality'])
            
            crop_result = {
                'crop_path': str(crop_path),
                'original_path': str(image_path),
                'bbox': [x1, y1, x2, y2],
                'crop_type': 'center',
                'aspect_ratio': ratio_name,
                'original_size': [original_width, original_height],
                'cropped_size': [x2 - x1, y2 - y1],
                'area': (x2 - x1) * (y2 - y1)
            }
            crop_results.append(crop_result)
        
        self.logger.info(f"从图片 {image_path.name} 中心裁剪出 {len(crop_results)} 个比例图片")
        return crop_results
    
    def image_to_embedding(self, image_paths: List[str]) -> List[Tuple[str, np.ndarray]]:
        """
        将图片转换为向量表示
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            List[Tuple[str, np.ndarray]]: (图片路径, 向量) 的列表
        """
        if not image_paths:
            return []
        
        self.logger.info(f"开始向量化 {len(image_paths)} 张图片")
        
        # 将图片转换为base64
        base64_images = []
        valid_paths = []
        
        for image_path in image_paths:
            try:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    base64_images.append(image_base64)
                    valid_paths.append(image_path)
            except Exception as e:
                self.logger.error(f"读取图片失败 {image_path}: {e}")
                continue
        
        if not base64_images:
            return []
        
        # 调用embedding服务
        try:
            response = requests.post(
                f"{self.embedding_service_url}/encode-image/",
                json={
                    "images": base64_images,
                    "task": "retrieval",
                    "return_multivector": False
                },
                timeout=120
            )
            response.raise_for_status()
            embeddings = response.json()['embeddings']
        except Exception as e:
            self.logger.error(f"向量化失败: {e}")
            return []
        
        # 组合结果
        results = []
        for path, embedding in zip(valid_paths, embeddings):
            results.append((path, np.array(embedding)))
        
        self.logger.info(f"成功向量化 {len(results)} 张图片")
        return results
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            embedding1: 向量1
            embedding2: 向量2
            
        Returns:
            float: 相似度值 (0-1)
        """
        # 确保向量是二维的
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)
        
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)
    
    def remove_duplicate_images(self, embeddings: List[Tuple[str, np.ndarray]], 
                              threshold: Optional[float] = None) -> List[str]:
        """
        基于向量相似度去除重复图片
        
        Args:
            embeddings: (图片路径, 向量) 的列表
            threshold: 相似度阈值，超过此值认为是重复图片
            
        Returns:
            List[str]: 去重后的图片路径列表
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        if len(embeddings) <= 1:
            return [emb[0] for emb in embeddings]
        
        self.logger.info(f"开始去重，相似度阈值: {threshold}")
        
        # 记录要保留的图片
        keep_indices = []
        removed_count = 0
        
        for i in range(len(embeddings)):
            is_duplicate = False
            
            # 与已选择的图片比较
            for j in keep_indices:
                similarity = self.calculate_similarity(
                    embeddings[i][1], embeddings[j][1]
                )
                
                if similarity > threshold:
                    self.logger.debug(f"发现重复图片: {embeddings[i][0]} 与 {embeddings[j][0]} "
                                    f"相似度: {similarity:.3f}")
                    is_duplicate = True
                    removed_count += 1
                    break
            
            if not is_duplicate:
                keep_indices.append(i)
        
        # 返回保留的图片路径
        kept_paths = [embeddings[i][0] for i in keep_indices]
        
        self.logger.info(f"去重完成: 原始 {len(embeddings)} 张，保留 {len(kept_paths)} 张，"
                        f"删除 {removed_count} 张重复图片")
        
        return kept_paths
    
    def process_video_frames(self, video_path: str, output_dir: str,
                           fps: float = 1.0, start_time: int = 0,
                           duration: Optional[int] = None,
                           crop_mode: str = 'center',
                           crop_ratios: List[str] = ['4:3', '3:2'],
                           crop_confidence: float = 0.5) -> Dict:
        """
        完整的视频帧处理流程：抽帧 -> 裁剪 -> 向量化 -> 去重
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            fps: 抽取帧率
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            crop_mode: 裁剪模式 ('center' 中心裁剪, 'yolo' YOLO检测裁剪, 'none' 不裁剪)
            crop_ratios: 中心裁剪时的比例列表 (仅当crop_mode='center'时有效)
            crop_confidence: YOLO裁剪时的置信度阈值 (仅当crop_mode='yolo'时有效)
            
        Returns:
            Dict: 处理结果
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            'video_path': video_path,
            'output_dir': str(output_dir),
            'original_frames': [],
            'cropped_images': [],
            'final_images': [],
            'removed_duplicates': [],
            'processing_stats': {}
        }
        
        # 1. 抽帧
        self.logger.info("步骤1: 开始抽帧")
        frame_infos = self.extract_frames_from_video(
            video_path, output_dir, fps, start_time, duration, 
            uniform_sampling=CONFIG['image']['uniform_sampling']
        )
        results['original_frames'] = frame_infos
        results['processing_stats']['original_frame_count'] = len(frame_infos)
        
        if not frame_infos:
            self.logger.warning("未抽取到任何帧")
            return results
        
        # 提取图片路径列表用于后续处理
        original_frame_paths = [frame['path'] for frame in frame_infos]
        
        # 2. 裁剪 (根据模式选择)
        images_to_process = original_frame_paths
        
        if crop_mode == 'yolo':
            self.logger.info("步骤2: 开始YOLO智能裁剪")
            all_crops = []
            for frame_path in original_frame_paths:
                crops = self.crop_image_with_yolo(frame_path, output_dir, crop_confidence)
                all_crops.extend(crops)
            
            if all_crops:
                images_to_process = [crop['crop_path'] for crop in all_crops]
                results['cropped_images'] = all_crops
                self.logger.info(f"YOLO裁剪完成，得到 {len(images_to_process)} 个裁剪区域")
            else:
                self.logger.info("未检测到可裁剪的物体，使用原始帧")
        
        elif crop_mode == 'center':
            self.logger.info(f"步骤2: 开始中心裁剪 (比例: {', '.join(crop_ratios)})")
            all_crops = []
            for frame_path in original_frame_paths:
                crops = self.crop_image_center(frame_path, output_dir, crop_ratios)
                all_crops.extend(crops)
            
            if all_crops:
                images_to_process = [crop['crop_path'] for crop in all_crops]
                results['cropped_images'] = all_crops
                self.logger.info(f"中心裁剪完成，得到 {len(images_to_process)} 个裁剪图片")
            else:
                self.logger.warning("中心裁剪失败，使用原始帧")
        
        else:  # crop_mode == 'none'
            self.logger.info("步骤2: 跳过裁剪，直接使用原始帧")
            results['cropped_images'] = []
        
        results['processing_stats']['images_before_dedup'] = len(images_to_process)
        
        # 3. 向量化
        self.logger.info("步骤3: 开始向量化")
        embeddings = self.image_to_embedding(images_to_process)
        
        if not embeddings:
            self.logger.warning("向量化失败")
            return results
        
        # 4. 去重
        self.logger.info("步骤4: 开始去重")
        final_images = self.remove_duplicate_images(embeddings)
        results['final_images'] = final_images
        
        # 计算被删除的图片
        all_images = set(images_to_process)
        kept_images = set(final_images)
        removed_images = list(all_images - kept_images)
        results['removed_duplicates'] = removed_images
        
        # 统计信息
        results['processing_stats'].update({
            'final_image_count': len(final_images),
            'removed_duplicate_count': len(removed_images),
            'deduplication_rate': len(removed_images) / len(images_to_process) if images_to_process else 0
        })
        
        # 保存处理结果到JSON
        result_file = output_dir / 'visual_processing_results.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            # 将numpy数组转换为列表以便JSON序列化
            json_results = results.copy()
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"视觉处理完成，结果保存到: {result_file}")
        self.logger.info(f"处理统计: 原始帧 {results['processing_stats']['original_frame_count']} -> "
                        f"处理前 {results['processing_stats']['images_before_dedup']} -> "
                        f"最终 {results['processing_stats']['final_image_count']} "
                        f"(去重率: {results['processing_stats']['deduplication_rate']:.2%})")
        
        return results

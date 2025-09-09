#!/usr/bin/env python3
"""
视觉处理功能演示脚本
专门用于演示抽帧、裁剪、向量化、去重功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.visual_processor import VisualProcessor

def main():
    """主演示函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🎬 MediaScribe 视觉处理功能演示")
    print("=" * 50)
    
    # 检查服务状态
    processor = VisualProcessor()
    
    print("📡 检查服务状态...")
    try:
        import requests
        
        # 检查embedding服务
        emb_response = requests.get("http://localhost:8762/", timeout=5)
        print(f"✅ Embedding服务 (端口8762): {emb_response.json()['message']}")
        
        # 检查YOLO服务
        yolo_response = requests.get("http://localhost:8761/", timeout=5)
        print(f"✅ YOLO服务 (端口8761): {yolo_response.json()['message']}")
        
    except Exception as e:
        print(f"❌ 服务检查失败: {e}")
        print("请确保两个服务都已启动:")
        print("  docker run -p 8762:8000 jina-v4-service:latest")
        print("  docker run -p 8761:8000 yolo-service:latest")
        return
    
    print()
    
    # 演示参数
    video_path = "test/500001644709044-1-192.mp4"
    output_dir = "output/visual_demo"
    
    if not os.path.exists(video_path):
        print(f"❌ 测试视频不存在: {video_path}")
        return
    
    print(f"📹 输入视频: {video_path}")
    print(f"📁 输出目录: {output_dir}")
    print()
    
    # 执行视觉处理
    print("🚀 开始视觉处理...")
    print("流程: 抽帧 → 中心裁剪 → 向量化 → 去重")
    print()
    
    try:
        results = processor.process_video_frames(
            video_path=video_path,
            output_dir=output_dir,
            fps=1.0,  # 每秒1帧
            start_time=0,
            duration=60,  # 处理前60秒
            crop_mode='center',  # 使用中心裁剪
            crop_ratios=['4:3']  # 4:3比例
        )
        
        # 更新相似度阈值为95%
        processor.similarity_threshold = 0.95
        
        # 显示结果
        print("=" * 50)
        print("🎉 处理完成！结果统计:")
        print("=" * 50)
        
        stats = results['processing_stats']
        print(f"📊 原始抽帧数量: {stats['original_frame_count']}")
        print(f"📊 智能裁剪后: {stats['images_before_dedup']}")
        print(f"📊 去重后保留: {stats['final_image_count']}")
        print(f"📊 删除重复数: {stats['removed_duplicate_count']}")
        print(f"📊 去重效率: {stats['deduplication_rate']:.1%}")
        print()
        
        # 显示检测到的物体类型
        if results['cropped_images']:
            detected_objects = {}
            for crop in results['cropped_images']:
                # 根据裁剪类型获取标签
                if 'label' in crop:  # YOLO裁剪
                    label = crop['label']
                elif 'aspect_ratio' in crop:  # 中心裁剪
                    label = f"center_{crop['aspect_ratio']}"
                else:
                    label = "unknown"
                    
                detected_objects[label] = detected_objects.get(label, 0) + 1
            
            print("🔍 裁剪结果分析:")
            for label, count in detected_objects.items():
                print(f"   • {label}: {count} 个")
        print()
        
        # 显示文件结构
        print("📁 生成的文件结构:")
        output_path = Path(output_dir)
        
        def show_tree(path, prefix=""):
            items = sorted(path.iterdir())
            for i, item in enumerate(items[:10]):  # 只显示前10个
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and len(list(item.iterdir())) > 0:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    sub_items = sorted(item.iterdir())
                    for j, sub_item in enumerate(sub_items[:3]):  # 只显示前3个文件
                        is_sub_last = j == len(sub_items) - 1 or j == 2
                        sub_current_prefix = "└── " if is_sub_last else "├── "
                        print(f"{next_prefix}{sub_current_prefix}{sub_item.name}")
                    
                    if len(sub_items) > 3:
                        print(f"{next_prefix}└── ... ({len(sub_items)-3} more files)")
        
        show_tree(output_path)
        print()
        
        # 显示API调用统计
        print("🌐 API调用统计:")
        print(f"   • YOLO检测调用: {len(results['original_frames'])} 次")
        print(f"   • Embedding向量化: 1 批次 ({len(results['cropped_images'])} 张图片)")
        print()
        
        print("✨ 演示完成！你可以查看生成的图片和结果文件。")
        print(f"详细结果: {output_dir}/visual_processing_results.json")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

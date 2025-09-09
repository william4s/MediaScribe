#!/usr/bin/env python3
"""
测试不同时长和参数的视觉处理效果
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.visual_processor import VisualProcessor

def test_different_durations():
    """测试不同时长的处理效果"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🎬 MediaScribe 不同时长处理效果测试")
    print("=" * 60)
    
    processor = VisualProcessor()
    processor.similarity_threshold = 0.95  # 使用95%相似度阈值
    video_path = "test/500001644709044-1-192.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 测试视频不存在: {video_path}")
        return
    
    # 测试不同时长
    test_configs = [
        {'duration': 30, 'name': '30秒'},
        {'duration': 60, 'name': '60秒'},
        {'duration': 120, 'name': '2分钟'},
        {'duration': 300, 'name': '5分钟'},
    ]
    
    results_summary = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🔄 测试 {i}/{len(test_configs)}: {config['name']}")
        print("-" * 40)
        
        try:
            output_dir = f"output/duration_test_{config['duration']}s"
            
            results = processor.process_video_frames(
                video_path=video_path,
                output_dir=output_dir,
                fps=1.0,  # 1秒1帧
                start_time=0,
                duration=config['duration'],
                crop_mode='center',
                crop_ratios=['4:3']
            )
            
            stats = results['processing_stats']
            
            result_summary = {
                'duration': config['name'],
                'original_frames': stats['original_frame_count'],
                'final_images': stats['final_image_count'],
                'dedup_rate': stats['deduplication_rate'],
                'efficiency': stats['final_image_count'] / stats['original_frame_count']
            }
            
            results_summary.append(result_summary)
            
            # 显示结果
            print(f"✅ 处理完成")
            print(f"   原始帧数: {stats['original_frame_count']}")
            print(f"   最终保留: {stats['final_image_count']}")
            print(f"   去重率: {stats['deduplication_rate']:.1%}")
            print(f"   保留率: {result_summary['efficiency']:.1%}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            result_summary = {
                'duration': config['name'],
                'error': str(e)
            }
            results_summary.append(result_summary)
    
    # 显示对比总结
    print("\n" + "=" * 60)
    print("📊 不同时长处理效果对比")
    print("=" * 60)
    
    print(f"{'时长':<10} {'原始帧':<8} {'保留':<8} {'去重率':<10} {'保留率':<10}")
    print("-" * 60)
    
    for result in results_summary:
        if 'error' not in result:
            print(f"{result['duration']:<10} {result['original_frames']:<8} "
                  f"{result['final_images']:<8} {result['dedup_rate']:.1%}     "
                  f"{result['efficiency']:.1%}")
        else:
            print(f"{result['duration']:<10} {'ERROR':<30}")
    
    print("\n🎯 建议:")
    print("• 30-60秒: 适合快速预览和测试")
    print("• 2-5分钟: 适合讲座片段分析")
    print("• 更长时间: 建议分段处理")
    
    print(f"\n视频总时长: 864.63秒 (约14.4分钟)")
    print(f"当前最大帧数限制: 50帧")

def test_similarity_thresholds():
    """测试不同相似度阈值的效果"""
    print("\n🎯 相似度阈值对比测试")
    print("=" * 50)
    
    processor = VisualProcessor()
    video_path = "test/500001644709044-1-192.mp4"
    
    # 测试不同相似度阈值
    thresholds = [0.85, 0.90, 0.95, 0.98]
    
    print(f"测试参数: 60秒, 1fps, 4:3裁剪")
    print(f"{'阈值':<8} {'保留数':<8} {'去重率':<10}")
    print("-" * 30)
    
    for threshold in thresholds:
        try:
            processor.similarity_threshold = threshold
            output_dir = f"output/threshold_test_{int(threshold*100)}"
            
            results = processor.process_video_frames(
                video_path=video_path,
                output_dir=output_dir,
                fps=1.0,
                start_time=0,
                duration=60,
                crop_mode='center',
                crop_ratios=['4:3']
            )
            
            stats = results['processing_stats']
            print(f"{threshold:<8} {stats['final_image_count']:<8} {stats['deduplication_rate']:.1%}")
            
        except Exception as e:
            print(f"{threshold:<8} ERROR: {str(e)[:20]}...")

if __name__ == "__main__":
    print("请选择测试模式:")
    print("1. 不同时长测试")
    print("2. 相似度阈值测试")
    print("3. 完整测试")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    # 检查服务
    try:
        import requests
        emb_response = requests.get("http://localhost:8762/", timeout=5)
        print("✅ 服务检查通过\n")
        
        if choice == "1":
            test_different_durations()
        elif choice == "2":
            test_similarity_thresholds()
        elif choice == "3":
            test_different_durations()
            test_similarity_thresholds()
        else:
            print("无效选择")
            
    except Exception as e:
        print(f"❌ 服务检查失败: {e}")
        print("请确保embedding服务已启动")

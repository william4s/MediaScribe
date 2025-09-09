#!/usr/bin/env python3
"""
裁剪模式对比演示脚本
展示中心裁剪、YOLO裁剪和无裁剪的效果对比
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.visual_processor import VisualProcessor

def test_crop_modes():
    """测试不同的裁剪模式"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🎬 MediaScribe 裁剪模式对比演示")
    print("=" * 60)
    
    processor = VisualProcessor()
    video_path = "test/500001644709044-1-192.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 测试视频不存在: {video_path}")
        return
    
    # 测试参数
    test_fps = 1.0
    test_duration = 20
    
    # 测试模式配置
    test_modes = [
        {
            'name': '中心裁剪 (4:3)',
            'crop_mode': 'center',
            'crop_ratios': ['4:3'],
            'output_dir': 'output/crop_test_center'
        },
        {
            'name': '中心裁剪 (16:9, 1:1)', 
            'crop_mode': 'center',
            'crop_ratios': ['16:9', '1:1'],
            'output_dir': 'output/crop_test_center_wide'
        },
        {
            'name': 'YOLO智能裁剪',
            'crop_mode': 'yolo',
            'crop_confidence': 0.3,
            'output_dir': 'output/crop_test_yolo'
        },
        {
            'name': '无裁剪',
            'crop_mode': 'none',
            'output_dir': 'output/crop_test_none'
        }
    ]
    
    results_summary = []
    
    for i, mode_config in enumerate(test_modes, 1):
        print(f"\n🔄 测试 {i}/{len(test_modes)}: {mode_config['name']}")
        print("-" * 40)
        
        try:
            # 准备参数
            kwargs = {
                'video_path': video_path,
                'output_dir': mode_config['output_dir'],
                'fps': test_fps,
                'start_time': 0,
                'duration': test_duration,
                'crop_mode': mode_config['crop_mode']
            }
            
            # 添加模式特定参数
            if mode_config['crop_mode'] == 'center':
                kwargs['crop_ratios'] = mode_config['crop_ratios']
            elif mode_config['crop_mode'] == 'yolo':
                kwargs['crop_confidence'] = mode_config['crop_confidence']
            
            # 执行处理
            results = processor.process_video_frames(**kwargs)
            
            # 收集统计信息
            stats = results['processing_stats']
            crop_info = ""
            
            if results['cropped_images']:
                if mode_config['crop_mode'] == 'center':
                    # 统计比例类型
                    ratio_counts = {}
                    for crop in results['cropped_images']:
                        ratio = crop.get('aspect_ratio', 'unknown')
                        ratio_counts[ratio] = ratio_counts.get(ratio, 0) + 1
                    crop_info = f"比例分布: {dict(ratio_counts)}"
                    
                elif mode_config['crop_mode'] == 'yolo':
                    # 统计检测物体类型
                    label_counts = {}
                    for crop in results['cropped_images']:
                        label = crop.get('label', 'unknown')
                        label_counts[label] = label_counts.get(label, 0) + 1
                    crop_info = f"物体分布: {dict(label_counts)}"
            
            result_summary = {
                'mode': mode_config['name'],
                'original_frames': stats['original_frame_count'],
                'processed_images': stats['images_before_dedup'],
                'final_images': stats['final_image_count'],
                'dedup_rate': stats['deduplication_rate'],
                'crop_info': crop_info
            }
            
            results_summary.append(result_summary)
            
            # 显示结果
            print(f"✅ 处理完成")
            print(f"   原始帧数: {stats['original_frame_count']}")
            print(f"   处理后: {stats['images_before_dedup']}")
            print(f"   最终保留: {stats['final_image_count']}")
            print(f"   去重率: {stats['deduplication_rate']:.1%}")
            if crop_info:
                print(f"   {crop_info}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            result_summary = {
                'mode': mode_config['name'],
                'error': str(e)
            }
            results_summary.append(result_summary)
    
    # 显示对比总结
    print("\n" + "=" * 60)
    print("📊 裁剪模式对比总结")
    print("=" * 60)
    
    # 表格头
    print(f"{'模式':<20} {'原始帧':<8} {'处理后':<8} {'最终':<8} {'去重率':<8}")
    print("-" * 60)
    
    for result in results_summary:
        if 'error' not in result:
            print(f"{result['mode']:<20} {result['original_frames']:<8} "
                  f"{result['processed_images']:<8} {result['final_images']:<8} "
                  f"{result['dedup_rate']:.1%}")
        else:
            print(f"{result['mode']:<20} {'ERROR':<32}")
    
    print("\n🎯 建议:")
    print("• 中心裁剪 (4:3, 3:2): 适合讲座、会议视频，保持人物完整")
    print("• 中心裁剪 (16:9, 1:1): 适合风景、展示类视频")
    print("• YOLO裁剪: 适合需要突出物体细节的场景")
    print("• 无裁剪: 适合需要保持原始视角的场景")
    
    print(f"\n📁 详细结果保存在各自的输出目录中")

def demo_center_crop_only():
    """仅演示中心裁剪功能"""
    print("\n🎯 中心裁剪专项演示")
    print("=" * 40)
    
    processor = VisualProcessor()
    
    # 测试单张图片的中心裁剪
    test_image = "test/IMG_20220312_210419.jpg" 
    if not os.path.exists(test_image):
        print("❌ 测试图片不存在，跳过单图测试")
        return
    
    print(f"📷 测试图片: {test_image}")
    
    # 测试多种比例
    test_ratios = ['4:3', '3:2', '16:9', '1:1', '2:3', '3:4']
    output_dir = "output/center_crop_demo"
    
    try:
        crops = processor.crop_image_center(test_image, output_dir, test_ratios)
        
        print(f"✅ 成功生成 {len(crops)} 个裁剪图片:")
        for crop in crops:
            ratio = crop['aspect_ratio']
            size = crop['cropped_size']
            print(f"   • {ratio}: {size[0]}x{size[1]} - {crop['crop_path']}")
            
    except Exception as e:
        print(f"❌ 中心裁剪失败: {e}")

if __name__ == "__main__":
    print("请选择演示模式:")
    print("1. 完整对比演示 (需要服务支持)")
    print("2. 仅中心裁剪演示 (无需服务)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        # 检查服务
        try:
            import requests
            emb_response = requests.get("http://localhost:8762/", timeout=5)
            yolo_response = requests.get("http://localhost:8761/", timeout=5)
            print("✅ 服务检查通过，开始完整演示\n")
            test_crop_modes()
        except Exception as e:
            print(f"❌ 服务检查失败: {e}")
            print("请确保embedding和YOLO服务已启动")
    elif choice == "2":
        demo_center_crop_only()
    else:
        print("无效选择")

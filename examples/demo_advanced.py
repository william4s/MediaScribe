#!/usr/bin/env python3
"""
高难度功能演示脚本
展示并发视觉处理和PDF生成功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append('/home/shiwc/code/MediaScribe')

from src.visual_processor import VisualProcessor
from src.advanced_processor import AdvancedMediaProcessor

def demo_advanced_features():
    """演示高难度功能"""
    print("🚀 MediaScribe 高难度功能演示")
    print("="*60)
    
    # 检查必要的服务
    print("📡 检查服务状态...")
    
    try:
        visual_processor = VisualProcessor()
        service_status = visual_processor.check_services()
        print(f"✅ 视觉服务状态: {service_status}")
    except Exception as e:
        print(f"❌ 视觉服务检查失败: {e}")
        print("⚠️ 请确保以下服务正在运行:")
        print("   - Jina Embedding服务 (端口8762)")
        print("   - YOLO检测服务 (端口8761)")
        return False
    
    # 创建高级处理器
    advanced_processor = AdvancedMediaProcessor(visual_processor)
    
    # 模拟摘要数据
    mock_summary_result = {
        'overall_summary': '这是一个关于Python编程的视频教程，涵盖了基础语法、数据结构和面向对象编程等内容。',
        'segments': [
            {
                'start_time': 0.0,
                'end_time': 20.0,
                'text': '欢迎来到Python编程入门课程。今天我们将学习Python的基础知识，包括变量、数据类型和基本操作符。',
                'summary': 'Python编程入门介绍，讲解基础概念'
            },
            {
                'start_time': 20.0,
                'end_time': 40.0,
                'text': '现在让我们来看看Python中的数据结构。列表、元组、字典和集合是Python中最重要的数据类型。',
                'summary': 'Python数据结构详解：列表、元组、字典、集合'
            },
            {
                'start_time': 40.0,
                'end_time': 60.0,
                'text': '面向对象编程是Python的一个重要特性。我们将学习如何定义类、创建对象和使用继承。',
                'summary': 'Python面向对象编程：类、对象、继承'
            }
        ],
        'metadata': {
            'language': 'zh',
            'total_duration': 60.0,
            'total_segments': 3,
            'total_words': 150,
            'source': 'demo_data'
        }
    }
    
    video_path = "test/500001644709044-1-192.mp4"
    output_dir = "output/advanced_demo"
    
    # 检查测试视频是否存在
    if not Path(video_path).exists():
        print(f"❌ 测试视频不存在: {video_path}")
        print("📝 将生成仅包含文本的PDF演示...")
        
        # 创建一个没有视觉内容的演示
        mock_enhanced_result = {
            **mock_summary_result,
            'visual_segments': [
                {
                    'segment_number': i+1,
                    'time_range': f"{seg['start_time']:.1f}s - {seg['end_time']:.1f}s",
                    'duration': seg['end_time'] - seg['start_time'],
                    'text': seg['text'],
                    'summary': seg['summary'],
                    'visual_result': None,
                    'key_images': [],
                    'image_count': 0,
                    'processing_config': None,
                    'error': False
                }
                for i, seg in enumerate(mock_summary_result['segments'])
            ],
            'processing_stats': {
                'total_processing_time': 0.5,
                'concurrent_segments': 3,
                'visual_output_dir': output_dir
            }
        }
        
        # 生成PDF
        pdf_path = f"{output_dir}/demo_report.pdf"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            print("📄 生成PDF报告...")
            generated_pdf = advanced_processor.generate_mixed_content_pdf(
                enhanced_result=mock_enhanced_result,
                output_path=pdf_path,
                include_images=False
            )
            print(f"✅ PDF演示报告生成成功: {generated_pdf}")
            
            # 显示文件信息
            pdf_file = Path(generated_pdf)
            if pdf_file.exists():
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                print(f"📊 PDF文件大小: {size_mb:.2f}MB")
            
            return True
            
        except Exception as e:
            print(f"❌ PDF生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    else:
        print(f"📹 使用测试视频: {video_path}")
        print("🚀 开始高难度并发视觉处理演示...")
        
        try:
            # 执行并发视觉处理
            start_time = time.time()
            enhanced_result = advanced_processor.process_video_with_concurrent_visual(
                video_path=video_path,
                summary_result=mock_summary_result,
                output_dir=output_dir
            )
            processing_time = time.time() - start_time
            
            print(f"✅ 并发视觉处理完成，耗时: {processing_time:.2f}秒")
            
            # 生成PDF
            pdf_path = f"{output_dir}/advanced_demo_report.pdf"
            print("📄 生成图文混排PDF...")
            
            generated_pdf = advanced_processor.generate_mixed_content_pdf(
                enhanced_result=enhanced_result,
                output_path=pdf_path,
                include_images=True
            )
            
            print(f"✅ 完整PDF报告生成成功: {generated_pdf}")
            
            # 显示统计信息
            visual_segments = enhanced_result.get('visual_segments', [])
            total_images = sum(vs.get('image_count', 0) for vs in visual_segments if vs)
            print(f"📊 总处理图片: {total_images} 张")
            print(f"📊 成功分段: {len([vs for vs in visual_segments if vs and not vs.get('error')])}")
            
            return True
            
        except Exception as e:
            print(f"❌ 高级处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("🎯 MediaScribe 高难度功能演示启动...")
    
    success = demo_advanced_features()
    
    if success:
        print("\n🎉 演示完成！")
        print("📁 请查看生成的文件:")
        print("   - output/advanced_demo/ (视觉处理结果)")
        print("   - *.pdf (图文混排PDF报告)")
    else:
        print("\n❌ 演示失败，请检查服务状态和依赖")
    
    print("="*60)

if __name__ == "__main__":
    main()

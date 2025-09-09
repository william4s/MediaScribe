"""
测试视觉处理器功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.visual_processor import VisualProcessor
from src.config import CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('visual_test.log'),
        logging.StreamHandler()
    ]
)

def test_visual_processor():
    """测试视觉处理器"""
    logger = logging.getLogger(__name__)
    
    # 初始化处理器
    processor = VisualProcessor()
    
    # 测试视频路径 - 使用test目录中的视频
    video_path = "test/500001644709044-1-192.mp4"
    output_dir = "output/visual_test"
    
    if not os.path.exists(video_path):
        logger.error(f"测试视频文件不存在: {video_path}")
        return
    
    logger.info("开始测试视觉处理功能")
    logger.info(f"输入视频: {video_path}")
    logger.info(f"输出目录: {output_dir}")
    
    try:
        # 测试完整的处理流程
        results = processor.process_video_frames(
            video_path=video_path,
            output_dir=output_dir,
            fps=0.5,  # 每2秒抽取1帧
            start_time=0,
            duration=30,  # 只处理前30秒
            enable_cropping=True,
            crop_confidence=0.3  # 降低置信度阈值以获取更多检测结果
        )
        
        # 打印结果
        logger.info("处理完成！")
        logger.info("=" * 50)
        logger.info("处理结果统计:")
        stats = results['processing_stats']
        logger.info(f"  原始抽取帧数: {stats['original_frame_count']}")
        logger.info(f"  去重前图片数: {stats['images_before_dedup']}")
        logger.info(f"  最终保留图片数: {stats['final_image_count']}")
        logger.info(f"  删除重复图片数: {stats['removed_duplicate_count']}")
        logger.info(f"  去重率: {stats['deduplication_rate']:.2%}")
        
        if results['cropped_images']:
            logger.info(f"  智能裁剪区域数: {len(results['cropped_images'])}")
            
            # 显示检测到的物体类型
            detected_labels = {}
            for crop in results['cropped_images']:
                label = crop['label']
                if label not in detected_labels:
                    detected_labels[label] = 0
                detected_labels[label] += 1
            
            logger.info("  检测到的物体类型:")
            for label, count in detected_labels.items():
                logger.info(f"    {label}: {count} 个")
        
        logger.info("=" * 50)
        logger.info(f"详细结果已保存到: {output_dir}/visual_processing_results.json")
        
        # 显示最终保留的图片路径
        logger.info("最终保留的图片:")
        for i, img_path in enumerate(results['final_images'][:10]):  # 只显示前10张
            logger.info(f"  {i+1}. {Path(img_path).name}")
        
        if len(results['final_images']) > 10:
            logger.info(f"  ... 还有 {len(results['final_images']) - 10} 张图片")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_functions():
    """测试各个独立功能"""
    logger = logging.getLogger(__name__)
    processor = VisualProcessor()
    
    logger.info("测试独立功能...")
    
    # 1. 测试抽帧功能
    logger.info("测试1: 抽帧功能")
    video_path = "test/500001644709044-1-192.mp4"
    output_dir = "output/frame_test"
    
    if os.path.exists(video_path):
        try:
            frames = processor.extract_frames_from_video(
                video_path, output_dir, fps=1.0, start_time=0, duration=10
            )
            logger.info(f"抽帧测试成功，抽取了 {len(frames)} 帧")
        except Exception as e:
            logger.error(f"抽帧测试失败: {e}")
    else:
        logger.warning("测试视频不存在，跳过抽帧测试")
    
    # 2. 测试图片向量化（如果有图片的话）
    test_image = "test/IMG_20220312_210419.jpg"
    if os.path.exists(test_image):
        logger.info("测试2: 图片向量化")
        try:
            embeddings = processor.image_to_embedding([test_image])
            if embeddings:
                path, embedding = embeddings[0]
                logger.info(f"向量化测试成功，向量维度: {embedding.shape}")
            else:
                logger.error("向量化测试失败")
        except Exception as e:
            logger.error(f"向量化测试失败: {e}")
    else:
        logger.warning("测试图片不存在，跳过向量化测试")

if __name__ == "__main__":
    # 检查服务是否启动
    print("请确保以下服务已启动:")
    print("1. Embedding服务: http://localhost:8762")
    print("2. YOLO服务: http://localhost:8761")
    print()
    
    # 等待用户确认
    user_input = input("服务已启动？(y/n): ").strip().lower()
    if user_input != 'y':
        print("请先启动相关服务后再运行测试")
        sys.exit(1)
    
    print("开始测试...")
    print()
    
    # 运行测试
    success = test_visual_processor()
    
    if success:
        print("\n✅ 测试完成！")
    else:
        print("\n❌ 测试失败！")
        
    # 运行独立功能测试
    print("\n运行独立功能测试...")
    test_individual_functions()

# MediaScribe 视觉处理功能使用指南

## 功能概述

MediaScribe 现已支持中难度的视觉处理功能，实现了完整的视频帧处理工作流：

1. **视频抽帧** - 从视频中按指定帧率抽取图片
2. **智能裁剪** - 使用YOLO模型检测物体并自动裁剪
3. **图片向量化** - 使用Jina v4模型将图片转换为向量
4. **相似度去重** - 基于余弦相似度算法去除重复图片

## 核心工作流

**正确的处理顺序**：抽帧 → 裁剪 → 向量化 → 去重

## 前置条件

### 1. 启动所需服务

**Embedding服务** (端口 8762):
```bash
cd service/embedding_service
docker build -t jina-v4-service:latest .
docker run -p 8762:8000 jina-v4-service:latest
```

**YOLO服务** (端口 8761):
```bash
cd service/yolo_service
docker build -t yolo-service:latest .
docker run -p 8761:8000 yolo-service:latest
```

### 2. 安装Python依赖

```bash
conda activate mediascribe
pip install opencv-python scikit-learn Pillow numpy
```

## 使用方法

### 1. 完整视觉处理流程

```bash
python media_scribe_enhanced.py video.mp4 \
    --enable-visual \
    --extract-fps 0.5 \
    --duration 60 \
    --crop-confidence 0.3 \
    --similarity-threshold 0.8 \
    --output-dir output/demo
```

**参数说明**：
- `--enable-visual`: 启用视觉处理功能
- `--extract-fps 0.5`: 每2秒抽取1帧
- `--duration 60`: 只处理前60秒
- `--crop-confidence 0.3`: YOLO检测置信度阈值
- `--similarity-threshold 0.8`: 图片相似度去重阈值

### 2. 独立测试视觉功能

```bash
python test_visual_processor.py
```

## 输出结果

处理完成后会生成以下文件：

```
output/
├── video_file.mp3                    # 提取的音频
├── transcript_raw.json               # 原始转录结果
├── final_result.json                 # 最终结果(包含视觉处理)
├── report.md                         # 图文混排报告
└── visual/                           # 视觉处理目录
    ├── frames/                       # 原始抽帧
    │   ├── frame_000000.jpg
    │   └── ...
    ├── crops/                        # 智能裁剪后的图片
    │   ├── frame_000000_crop_000_person.jpg
    │   ├── frame_000000_crop_001_clock.jpg
    │   └── ...
    └── visual_processing_results.json # 视觉处理详细结果
```

## 处理统计示例

```
处理统计:
  原始帧数: 18
  处理前图片数: 88  
  最终图片数: 14
  去重率: 84.1%

检测到的物体类型:
  person: 74 个
  clock: 3 个  
  chair: 3 个
  motorcycle: 2 个
  tie: 5 个
  bench: 1 个
```

## API调用示例

### Embedding API

```bash
curl -X 'POST' \
  'http://localhost:8762/encode-image/' \
  -H 'Content-Type: application/json' \
  -d '{
    "images": ["BASE64_IMAGE_DATA"],
    "task": "retrieval",
    "return_multivector": false
  }'
```

### YOLO API

```bash
curl -X 'POST' \
  'http://localhost:8761/detect/' \
  -H 'Content-Type: application/json' \
  -d '{"image_base64": "BASE64_IMAGE_DATA"}'
```

## 配置参数

可在 `src/config.py` 中调整以下参数：

```python
'image': {
    'extract_fps': 1,                    # 默认抽帧率
    'similarity_threshold': 0.85,        # 相似度阈值
    'max_frames_per_segment': 50,        # 最大帧数限制
    'image_quality': 85,                 # 图片质量
    'crop_confidence_threshold': 0.5,    # 裁剪置信度
    'enable_smart_cropping': True        # 启用智能裁剪
}
```

## 核心类和方法

### VisualProcessor 类

主要方法：
- `extract_frames_from_video()` - 视频抽帧
- `crop_image_with_yolo()` - YOLO智能裁剪
- `image_to_embedding()` - 图片向量化
- `remove_duplicate_images()` - 相似度去重
- `process_video_frames()` - 完整处理流程

## 性能优化建议

1. **抽帧率设置**: 
   - 讲座视频建议 0.3-0.5 fps
   - 动态视频建议 1-2 fps

2. **相似度阈值**:
   - 严格去重: 0.8-0.9
   - 保守去重: 0.9-0.95

3. **YOLO置信度**:
   - 精确检测: 0.5-0.7
   - 宽松检测: 0.3-0.5

## 故障排除

### 常见问题

1. **服务连接失败**: 确保 embedding 和 YOLO 服务正常运行
2. **内存不足**: 减少 `max_frames_per_segment` 参数
3. **处理速度慢**: 降低抽帧率或增加相似度阈值

### 检查服务状态

```bash
# 检查embedding服务
curl http://localhost:8762/

# 检查YOLO服务  
curl http://localhost:8761/
```

## 下一步功能

计划支持的增强功能：
- 自定义物体检测类别
- 图片质量评估
- 时间段相关的帧抽取
- 多模态内容关联分析

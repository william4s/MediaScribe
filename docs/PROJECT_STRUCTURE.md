# MediaScribe 项目结构说明

## 目录结构

```
MediaScribe/
├── README.md                    # 项目主要说明文档
├── LICENSE                      # 开源许可证
├── requirements.txt             # Python依赖列表
├── environment.yml              # Conda环境配置
├──
├── media_scribe.py             # 🔵 主程序 - 基础音频处理版本
├── media_scribe_visual.py      # 🟢 主程序 - 增强版本(含视觉处理)
├──
├── src/                        # 📁 核心源代码模块
│   ├── __init__.py
│   ├── config.py               # 配置管理
│   ├── utils.py                # 通用工具函数
│   ├── video_processor.py      # 视频/音频处理
│   ├── asr_service.py          # 语音识别服务
│   ├── llm_service.py          # 大语言模型服务
│   ├── summary_generator.py    # 智能摘要生成
│   └── visual_processor.py     # 🆕 视觉处理模块
├──
├── service/                    # 📁 微服务组件
│   ├── embedding_service/      # 图像向量化服务
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── yolo_service/          # YOLO目标检测服务
│       ├── Dockerfile
│       ├── yolo_server.py
│       └── requirements.txt
├──
├── tests/                      # 📁 测试文件
│   ├── test_components.py      # 组件功能测试
│   ├── test_embedding.py       # 向量化测试
│   ├── test_parameters.py      # 参数配置测试
│   ├── test_visual_processor.py # 视觉处理测试
│   └── test_whisper.py         # ASR服务测试
├──
├── examples/                   # 📁 示例和演示
│   ├── demo_visual.py          # 视觉处理演示
│   └── demo_crop_modes.py      # 图像裁剪模式演示
├──
├── scripts/                    # 📁 辅助脚本
│   └── simple_mediascribe.py   # 简化版本脚本
├──
├── docs/                       # 📁 文档目录
│   ├── PROJECT_STRUCTURE.md    # 本文档
│   ├── IMPLEMENTATION_SUMMARY.md # 实现总结
│   └── VISUAL_GUIDE.md         # 视觉处理指南
├──
├── test/                       # 📁 测试数据
│   ├── 500001644709044-1-192.mp4
│   ├── 500001644709044-1-192.mp3
│   ├── hotwords.mp3
│   └── IMG_20220312_210419.jpg
├──
└── output/                     # 📁 输出目录
    └── visual_demo/            # 视觉处理演示输出
```

## 程序入口说明

### 🔵 media_scribe.py (基础版本)
- **功能**: 音频转录 + 文本摘要
- **适用场景**: 纯音频处理，快速转录
- **输出**: 转录文本 + Markdown报告

### 🟢 media_scribe_visual.py (增强版本)  
- **功能**: 完整视觉处理管道
- **适用场景**: 需要图像分析的视频处理
- **输出**: 转录文本 + 图像分析 + 完整报告

## 核心模块说明

### 📦 src/visual_processor.py (新增)
- **视频帧提取**: 支持均匀采样和时间戳记录
- **智能裁剪**: YOLO检测裁剪 + 中心裁剪(4:3)
- **图像向量化**: 基于Jina v4的向量化
- **相似度去重**: 基于余弦相似度的重复图像过滤

### 📦 service/ (微服务架构)
- **embedding_service**: 图像向量化微服务
- **yolo_service**: 目标检测微服务

### 📦 tests/ (测试体系)
- **单元测试**: 各模块功能测试
- **集成测试**: 服务间协作测试
- **性能测试**: 处理效率测试

## 开发历程

### Phase 1: 基础功能 ✅
- [x] 音频提取与转录
- [x] LLM智能摘要
- [x] 基础配置管理

### Phase 2: 视觉处理 ✅ 
- [x] 视频帧提取算法
- [x] YOLO目标检测集成
- [x] 图像向量化服务
- [x] 相似度去重算法
- [x] 中心裁剪功能

### Phase 3: 优化改进 ✅
- [x] 均匀采样算法
- [x] 时间戳记录
- [x] 配置参数优化
- [x] 项目结构重构

### Phase 4: 规划中 🔄
- [ ] 性能优化
- [ ] 图文混排PDF
- [ ] 在线服务部署

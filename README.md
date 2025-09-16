# MediaScribe - 图文混合课程笔记生成器

基于Python的视频内容分析工具，集成LLM和Whisper技术，能够从视频生成包含图像和文本的智能摘要。
腾讯犀牛鸟开源项目

## 🎯 功能特性

### ✅ 已实现功能

#### 📱 基础音频处理
- ✅ 使用ffmpeg进行音视频分流  
- ✅ 调用Whisper ASR服务进行语音转文字
- ✅ 基于大语言模型的智能摘要生成
- ✅ 分段处理和时间标记
- ✅ JSON格式输出和Markdown报告生成

#### 🖼️ 视觉处理管道 (新增)
- ✅ 视频帧均匀采样提取 (支持时间戳记录)
- ✅ YOLO目标检测智能裁剪
- ✅ 中心裁剪模式 (4:3比例优化)  
- ✅ 基于Jina v4的图像向量化
- ✅ 余弦相似度去重算法 (去重率60-90%)
- ✅ 微服务架构 (embedding + YOLO检测)

### 🔄 进行中功能
- 🔄 性能优化和并发处理
- 🔄 图文混排PDF报告生成  
- 🔄 在线服务API部署

### 📋 规划功能
- 📋 多语言支持优化
- 📋 云端存储集成
- 📋 实时处理能力

## 系统要求

- Python 3.10+
- FFmpeg 
- Whisper ASR服务 
- LLM API服务 (支持OpenAI格式)

## 安装

1. 克隆项目
```bash
git clone <项目地址>
cd MediaScribe
```

2. 创建conda环境
```bash
conda env create -f environment.yml
conda activate mediascribe
```

3. 或使用pip安装依赖
```bash
pip install -r requirements.txt
```

## 配置

### 环境变量
可通过环境变量配置服务地址：

```bash
export WHISPER_URL="http://localhost:8760"
export LLM_URL="http://localhost:8000"
export LLM_API_KEY="sk-kfccrazythursdayvme50"
export LLM_MODEL="qwen3"
```

### 配置文件
详细配置请参考 `src/config.py`

## 📦 使用方法

### 🎯 推荐: 智能入口 (新增)
```bash
# 自动选择最佳处理模式
python mediascribe.py test/500001644709044-1-192.mp4

# 强制使用音频模式 (快速)
python mediascribe.py test/500001644709044-1-192.mp4 --audio-only

# 强制使用视觉模式 (完整) 
python mediascribe.py test/500001644709044-1-192.mp4 --visual
```

### 🔵 基础版本 (仅音频处理)
```bash
# 基础音频转录和摘要
python media_scribe.py test/500001644709044-1-192.mp4
```

### 🟢 增强版本 (含视觉处理)  
```bash
# 完整视觉处理管道 - 中心裁剪模式
python media_scribe_visual.py test/500001644709044-1-192.mp4 --crop-mode center

# YOLO检测裁剪模式
python media_scribe_visual.py test/500001644709044-1-192.mp4 --crop-mode yolo

# 自定义参数
python media_scribe_visual.py test/500001644709044-1-192.mp4 \
  --crop-mode center \
  --max-frames 30 \
  --similarity-threshold 0.90 \
  --output-dir my_output
```

### 🎯 演示示例
```bash
# 视觉处理功能演示
python examples/demo_visual.py

# 裁剪模式对比演示  
python examples/demo_crop_modes.py
```

### ⚙️ 服务依赖

启动必需的微服务：
```bash
# 启动图像向量化服务 (端口8762)
cd service/embedding_service && python main.py

# 启动YOLO检测服务 (端口8761)  
cd service/yolo_service && python yolo_server.py
```

## 🎯 输出文件

### 📄 基础版本输出
- `audio.mp3` - 提取的音频文件
- `transcript_raw.json` - 原始转录结果  
- `final_result.json` - 最终处理结果
- `report.md` - Markdown格式报告
- `mediascribe.log` - 处理日志

### 🖼️ 增强版本输出 (新增)
- `visual_processing_results.json` - 视觉处理结果
- `frames/` - 提取的视频帧 (包含时间戳)
- `crops/` - 智能裁剪的图片
- `report_visual.md` - 包含图像的增强报告

### 📊 处理统计示例
```json
{
  "processing_stats": {
    "original_frame_count": 50,
    "images_before_dedup": 50, 
    "final_image_count": 16,
    "removed_duplicate_count": 34,
    "deduplication_rate": 0.68
  },
  "visual_analysis": {
    "time_range": "0.0s - 58.8s",
    "sampling_interval": "1.2s",
    "crop_mode": "center_4:3"
  }
}

### 输出格式示例

```json
{
  "overall_summary": "视频整体摘要内容...",
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 4.0,
      "text": "原始转录文本...",
      "summary": "该段摘要..."
    }
  ],
  "metadata": {
    "language": "zh",
    "total_duration": 120.5,
    "total_segments": 30,
    "total_words": 500,
    "source": "whisper_asr"
  }
}
```

## 📁 项目结构

```
MediaScribe/
├── README.md                    # 项目说明文档
├── LICENSE                      # 开源许可证  
├── requirements.txt             # Python依赖
├── environment.yml              # Conda环境配置
├──
├── mediascribe.py              # 🎯 智能入口 - 自动选择模式
├── media_scribe.py             # 🔵 基础版本 - 仅音频处理
├── media_scribe_visual.py      # 🟢 增强版本 - 含视觉处理
├──
├── src/                        # 📁 核心源代码
│   ├── config.py               # 配置管理
│   ├── utils.py                # 工具函数
│   ├── video_processor.py      # 视频/音频处理
│   ├── asr_service.py          # ASR服务
│   ├── llm_service.py          # LLM服务
│   ├── summary_generator.py    # 摘要生成
│   └── visual_processor.py     # 🆕 视觉处理模块
├──
├── service/                    # 📁 微服务组件
│   ├── embedding_service/      # 图像向量化服务
│   └── yolo_service/          # YOLO检测服务
├──
├── tests/                      # 📁 测试文件
│   ├── test_components.py      # 组件测试
│   ├── test_visual_processor.py # 视觉处理测试
│   └── test_*.py              # 其他测试
├──
├── examples/                   # 📁 示例演示
│   ├── demo_visual.py          # 视觉处理演示
│   └── demo_crop_modes.py      # 裁剪模式演示
├──
├── scripts/                    # 📁 辅助脚本
├── docs/                       # 📁 项目文档
├── test/                       # 📁 测试数据
└── output/                     # 📁 输出目录
```

> 📖 详细结构说明请参考: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## API接口

### Whisper ASR服务
需要部署支持以下接口的Whisper服务：
- `POST /asr` - 语音转文字
- `GET /detect-language` - 检测语言

### LLM服务
需要支持OpenAI格式的聊天完成API：
- `POST /v1/chat/completions` - 聊天完成

## 🔧 开发说明

### 🎨 视觉处理架构 (新增)
项目采用模块化设计，支持多种图像处理模式：

1. **帧提取算法** - `visual_processor.extract_frames_from_video()`
   - 均匀采样: 在视频时长内均匀分布取帧
   - 时间戳记录: 每帧精确记录时间位置
   - 可配置最大帧数 (默认50帧)

2. **智能裁剪** - `visual_processor.crop_images()`
   - YOLO模式: 基于目标检测的智能裁剪
   - 中心模式: 4:3比例中心裁剪 (适合课程视频)

3. **向量化去重** - `visual_processor.vectorize_and_deduplicate()`  
   - Jina v4 图像向量化
   - 余弦相似度计算
   - 智能去重 (相似度阈值可调)

### 🧪 测试体系
```bash
# 运行所有测试
python -m pytest tests/

# 测试视觉处理模块
python tests/test_visual_processor.py

# 性能测试  
python tests/test_parameters.py
```

### 📈 性能指标
- **抽帧速度**: ~50帧/4秒 (864秒视频)
- **向量化速度**: ~50张图片/35秒  
- **去重效率**: 60-90% (取决于内容相似度)
- **内存占用**: 峰值 < 2GB (50帧处理)

## 故障排除

### 常见问题

1. **FFmpeg未找到**
   - 确保FFmpeg已安装并在PATH中
   - Ubuntu: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

2. **ASR服务连接失败**
   - 检查Whisper服务是否正常运行
   - 验证服务地址和端口

3. **LLM服务调用失败**
   - 检查API密钥是否正确
   - 验证模型名称和服务地址

4. **内存不足**
   - 对于大视频文件，考虑分段处理
   - 调整批处理大小

## 许可证

[MIT License](https://github.com/william4s/MediaScribe/blob/main/LICENSE)
## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

Weichun Shi
Email:shiweihcun24@mails.ucas.ac.cn

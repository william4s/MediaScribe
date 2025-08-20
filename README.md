# MediaScribe - 视频生成图文混排讲义工具

这是一个基于Python的视频内容分析工具，可以将视频转换为结构化的图文混排讲义。

## 功能特性

### 当前实现（低难度）
- ✅ 使用ffmpeg进行音视频分流
- ✅ 调用Whisper ASR服务进行语音转文字
- ✅ 基于大语言模型的智能摘要生成
- ✅ 分段处理和时间标记
- ✅ JSON格式输出和Markdown报告生成

### 规划功能（中难度）
- 🔄 视频帧提取和去重
- 🔄 图像向量化和相似度分析
- 🔄 图片裁剪和优化

### 规划功能（高难度）
- 🔄 并发处理和性能优化
- 🔄 图文混排PDF报告生成
- 🔄 腾讯文档在线集成

## 系统要求

- Python 3.10+
- FFmpeg (命令行工具)
- Whisper ASR服务 (http://localhost:8760)
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
export LLM_URL="http://192.168.1.3:8000"
export LLM_API_KEY="sk-kfccrazythursdayvme50"
export LLM_MODEL="qwen3"
```

### 配置文件
详细配置请参考 `src/config.py`

## 使用方法

### 基本用法
```bash
python media_scribe.py test/500001644709044-1-192.mp4
```

### 指定输出目录
```bash
python media_scribe.py test/500001644709044-1-192.mp4 -o my_output
```

### 自定义服务地址
```bash
python media_scribe.py test/500001644709044-1-192.mp4 \
  --whisper-url http://localhost:8760 \
  --llm-url http://192.168.1.3:8000
```

### 调试模式
```bash
python media_scribe.py test/500001644709044-1-192.mp4 --debug
```

## 输出文件

处理完成后，在输出目录中会生成：

- `audio.mp3` - 提取的音频文件
- `transcript_raw.json` - 原始转录结果
- `final_result.json` - 最终处理结果
- `report.md` - Markdown格式报告
- `mediascribe.log` - 处理日志

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

## 项目结构

```
MediaScribe/
├── media_scribe.py          # 主入口文件
├── src/                     # 源代码目录
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── utils.py            # 工具函数
│   ├── video_processor.py  # 视频处理
│   ├── asr_service.py      # ASR服务
│   ├── llm_service.py      # LLM服务
│   └── summary_generator.py # 摘要生成
├── test/                   # 测试文件
├── output/                 # 默认输出目录
├── environment.yml         # Conda环境配置
├── requirements.txt        # Pip依赖
└── README.md
```

## API接口

### Whisper ASR服务
需要部署支持以下接口的Whisper服务：
- `POST /asr` - 语音转文字
- `GET /health` - 健康检查

### LLM服务
需要支持OpenAI格式的聊天完成API：
- `POST /v1/chat/completions` - 聊天完成

## 开发说明

### 扩展功能
项目已为中高难度功能预留接口：

1. **图像处理** - `VideoProcessor.extract_frames()`
2. **向量计算** - 配置中的vector部分
3. **PDF生成** - 配置中的pdf部分

### 测试
```bash
# 运行测试
pytest

# 测试覆盖率
pytest --cov=src
```

### 日志
项目使用Python标准logging模块，日志文件保存为 `mediascribe.log`

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

[指定许可证]

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

[联系信息]

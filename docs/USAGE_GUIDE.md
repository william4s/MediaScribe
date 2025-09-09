# MediaScribe 使用指南

## 🚀 三种使用方式

### 1. 🎯 智能模式 (推荐)
```bash
# 自动根据文件大小选择处理模式
python mediascribe.py video.mp4
```

### 2. 🔵 基础模式 (快速转录)
```bash
# 仅音频转录，速度快
python media_scribe.py video.mp4
python mediascribe.py video.mp4 --audio-only
```

### 3. 🟢 增强模式 (完整分析)
```bash
# 包含视觉处理，功能全面
python media_scribe_visual.py video.mp4 --enable-visual
python mediascribe.py video.mp4 --visual
```

## ⚡ 性能对比

| 模式 | 处理时间 | 资源消耗 | 输出内容 | 适用场景 |
|------|----------|----------|----------|----------|
| 基础模式 | 2-5分钟 | 低 | 文本摘要 | 会议录音、播客转录 |
| 增强模式 | 10-20分钟 | 高 | 图文报告 | 课程视频、教学内容 |
| 智能模式 | 自适应 | 自适应 | 自适应 | 通用场景 |

## 🛠️ 服务依赖

### 基础模式需要:
- Whisper ASR 服务 (端口8760)
- LLM 服务 (端口8000)

### 增强模式额外需要:
- Jina Embedding 服务 (端口8762)
- YOLO 检测服务 (端口8761)

## 📝 使用建议

1. **首次使用**: 推荐智能模式 `python mediascribe.py video.mp4`
2. **快速转录**: 使用基础模式 `python media_scribe.py video.mp4`  
3. **完整分析**: 使用增强模式 `python media_scribe_visual.py video.mp4 --enable-visual`
4. **批量处理**: 根据文件大小选择合适模式

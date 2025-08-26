# 1. 使用支持 PyTorch 2.3+ 和 CUDA 12.1 的新版 devel 镜像
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

# 2. 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV HF_ENDPOINT="https://hf-mirror.com"

# 3. 安装系统依赖 (git)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 4. 设置工作目录
WORKDIR /app

# 5. 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r requirements.txt

# 6. 复制本地模型到镜像中
# 确保你的项目文件夹下有 model/jina-embeddings-v4 这个子目录
# COPY /home/shiwc/model/jinaai/jina-embeddings-v4 /models/jina-embeddings-v4

# 7. 复制你的应用代码
COPY main.py .

# 8. 暴露你指定的端口 7892
EXPOSE 7892

# 9. 设置启动命令，注意修改端口号
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7892"]
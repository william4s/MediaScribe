# 1. 使用 Ultralytics 官方镜像作为基础
# 这个镜像已经包含了 CUDA, PyTorch, 和 ultralytics 包
FROM ultralytics/ultralytics:latest

# 2. 设置工作目录
WORKDIR /app

# 3. 复制并安装我们自己的API服务依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制我们的API服务代码
COPY yolo_server.py .

# 5. 暴露端口
EXPOSE 8000

# 6. 设置启动命令，运行 FastAPI 服务
CMD ["uvicorn", "yolo_server:app", "--host", "0.0.0.0", "--port", "8000"]
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from transformers import AutoModel
import torch
from PIL import Image
import base64
import io
import requests

# --- 1. 初始化 FastAPI 应用和模型 ---
app = FastAPI(title="Jina Embeddings v4 Service")

# ## 关键步骤 1: 加载 v4 模型 ##
# 注意 torch_dtype=torch.float16 用于半精度推理，可提速并节省显存
MODEL_PATH = '/models/jina-embeddings-v4'
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"检测到并正在使用设备: {device}")
print(f"正在从 {MODEL_PATH} 加载模型...")

model = AutoModel.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    torch_dtype=torch.float16 # 使用半精度
)
model.to(device)
print(f"模型已成功加载并移动到 {device}")

# --- 2. 定义 API 的请求和响应数据结构 ---
class TextEncodeRequest(BaseModel):
    texts: List[str]
    task: Optional[str] = Field(default="retrieval", description="任务类型: 'retrieval', 'text-matching', 'code'")
    prompt_name: Optional[str] = Field(default=None, description="Prompt名称: 'query', 'passage'")
    return_multivector: bool = Field(default=False, description="是否返回多个向量")

class ImageEncodeRequest(BaseModel):
    images: List[str] = Field(description="图像URL或Base64编码的数据URI列表")
    task: Optional[str] = Field(default="retrieval", description="任务类型: 'retrieval'")
    return_multivector: bool = Field(default=False, description="是否返回多个向量")

class EmbeddingResponse(BaseModel):
    # 使用 Any 类型以灵活支持单向量和多向量输出
    embeddings: Any

# --- 3. 创建 API 端点 (Endpoints) ---
@app.get("/")
def read_root():
    return {"message": "欢迎使用 Jina Embeddings v4 服务"}
@app.post("/encode-text/", response_model=EmbeddingResponse)
async def encode_text_endpoint(request: TextEncodeRequest):
    try:
        embeddings_tensor = model.encode_text(
            texts=request.texts,
            task=request.task,
            prompt_name=request.prompt_name,
            return_multivector=request.return_multivector
        )
        
        # ## 关键修改：检查返回的是否为Tensor ##
        if torch.is_tensor(embeddings_tensor):
            final_embeddings = embeddings_tensor.cpu().tolist()
        else:
            # 如果是列表，则对其中每个Tensor进行处理
            final_embeddings = [t.cpu().tolist() for t in embeddings_tensor]

        return EmbeddingResponse(embeddings=final_embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/encode-image/", response_model=EmbeddingResponse)
async def encode_image_endpoint(request: ImageEncodeRequest):
    try:
        pil_images = []
        for image_str in request.images:
            if image_str.startswith('http://') or image_str.startswith('https://'):
                # 如果是URL，下载图片
                response = requests.get(image_str, stream=True)
                response.raise_for_status()
                image = Image.open(response.raw).convert("RGB")
                pil_images.append(image)
            else:
                # 否则，认为是Base64编码的字符串
                # 可能的格式 "data:image/jpeg;base64,xxxxxx" or just "xxxxxx"
                if ',' in image_str:
                    base64_data = image_str.split(',', 1)[1]
                else:
                    base64_data = image_str
                
                image_data = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                pil_images.append(image)

        # model.encode_image 可以直接处理 PIL Image 对象列表
        embeddings_tensor = model.encode_image(
            images=pil_images, 
            task=request.task,
            return_multivector=request.return_multivector
        )
        
        if torch.is_tensor(embeddings_tensor):
            final_embeddings = embeddings_tensor.cpu().tolist()
        else:
            final_embeddings = [t.cpu().tolist() for t in embeddings_tensor]

        return EmbeddingResponse(embeddings=final_embeddings)
    except Exception as e:
        # 增加更详细的错误日志
        print(f"处理图片时发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
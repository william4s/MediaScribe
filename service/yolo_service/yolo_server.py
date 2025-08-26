from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO
from PIL import Image
import base64
import io
from typing import List

# --- 1. 初始化 FastAPI 应用 ---
app = FastAPI(title="YOLOv8 Object Detection Service")

# --- 2. 定义请求和响应的数据模型 ---
class ImageRequest(BaseModel):
    image_base64: str

class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    confidence: float

class DetectionResponse(BaseModel):
    detections: List[Box]

# --- 3. 加载 YOLOv8 模型 ---
# 模型在服务启动时加载一次，常驻内存
print("正在加载 YOLOv8n 模型...")
model = YOLO('yolov8n.pt')
print("YOLOv8n 模型加载成功。")

# --- 4. 创建 API 端点 ---
@app.post("/detect/", response_model=DetectionResponse)
async def detect_objects(request: ImageRequest):
    """
    接收 Base64 编码的图片，返回检测到的所有物体边框、标签和置信度。
    """
    try:
        # 解码 Base64 字符串
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # 使用 YOLO 模型进行预测
        results = model(image)

        # 解析并格式化结果
        detections = []
        if results:
            result = results[0] # 获取第一张图的结果
            boxes = result.boxes.xyxy.cpu().numpy() # 边框坐标 (x1, y1, x2, y2)
            confs = result.boxes.conf.cpu().numpy()   # 置信度
            cls_ids = result.boxes.cls.cpu().numpy()  # 类别ID
            class_names = result.names                # 类别ID到名称的映射

            for i in range(len(boxes)):
                detections.append(Box(
                    x1=boxes[i][0],
                    y1=boxes[i][1],
                    x2=boxes[i][2],
                    y2=boxes[i][3],
                    label=class_names[int(cls_ids[i])],
                    confidence=confs[i]
                ))
        
        return DetectionResponse(detections=detections)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "欢迎使用 YOLOv8 目标检测服务"}
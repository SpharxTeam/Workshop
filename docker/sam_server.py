from fastapi import FastAPI, UploadFile, File
import numpy as np
import cv2
from segment_anything import SamPredictor, sam_model_registry
import torch

app = FastAPI()

# 加载模型
sam_checkpoint = "sam_vit_h_4b8939.pth"
model_type = "vit_h"
device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device=device)
predictor = SamPredictor(sam)

@app.post("/segment")
async def segment_image(file: UploadFile = File(...)):
    """接收图像，返回自动分割结果"""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    predictor.set_image(image)
    masks, scores, _ = predictor.predict()
    
    # 返回掩码和分数
    return {
        "masks": masks.tolist(),
        "scores": scores.tolist(),
        "image_shape": image.shape
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "SAM"}
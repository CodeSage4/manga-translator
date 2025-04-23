from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.easyocr import OCRProcessor
import cv2
import numpy as np
from app.config import settings

router = APIRouter()
ocr = OCRProcessor()

@router.post("/upload/")
async def upload_manga(
    file: UploadFile = File(...),
    source_language: str = "Japanese"
):
    try:
        # Read and validate image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Process image with OCR
        text_regions = await ocr.process_image(image, source_language)
        
        return {
            "status": "success",
            "filename": file.filename,
            "text_regions": text_regions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
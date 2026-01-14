from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
import cv2
import uuid
import os
import shutil

from pipeline import process_page
from translators import render_translations,mymemory_translator_factory

# Translator (swap later if needed)
translator = mymemory_translator_factory()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/results", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.post("/translate-page")
async def translate_page(
    file: UploadFile = File(...),
    debug: bool = Form(False),
):
    # Save upload
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    upload_path = f"static/uploads/{file_id}{ext}"

    if ext.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
        return {"error": "Unsupported file type"}


    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Load image
    img = cv2.imread(upload_path)
    if img is None:
        return {"error": "Invalid image"}

    

    # Run pipeline
    bubbles = process_page(img, translator, debug=debug)
    rendered = render_translations(img, bubbles)

    # Save result
    out_path = f"static/results/{file_id}_translated.png"
    cv2.imwrite(out_path, rendered)

    return {
        "image_url": f"/static/results/{file_id}_translated.png",
        "bubble_count": len(bubbles),
        "bubbles": [
            {
                "bbox": b["bbox"],
                "jp": b["jp"],
                "en": b["en"]
            }
            for b in bubbles
        ]
    }


@app.get("/")
def root():
    return {"status": "Manga Translation API running"}

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import easyocr
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import os
import uuid
import requests

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "processed_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

reader = easyocr.Reader(['ja', 'en'], gpu=False)

# Translation function using MyMemory API
def translate_text(text, source_lang='ja', target_lang='en'):
    url = f"https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}"
    response = requests.get(url)
    data = response.json()
    return data['responseData']['translatedText']

# Load a font dynamically based on bounding box height
def get_font(box_height):
    font_size = max(10, int(box_height * 0.8))  # Minimum size 10
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except:
        return ImageFont.load_default()

@app.post("/process/")
async def process_image(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    img_np = np.array(image)

    results = reader.readtext(img_np)
    draw = ImageDraw.Draw(image)

    translated_texts = []
    for (bbox, text, conf) in results:
        translated = translate_text(text, source_lang, target_lang)
        points = [tuple(map(int, point)) for point in bbox]
        draw.line(points + [points[0]], width=2, fill="red")

        # Bounding box dimensions
        min_x = min([p[0] for p in points])
        min_y = min([p[1] for p in points])
        max_x = max([p[0] for p in points])
        max_y = max([p[1] for p in points])
        box_width = max_x - min_x
        box_height = max_y - min_y

        # Get dynamic font
        font = get_font(box_height)

        # Draw white rectangle over existing text
        draw.rectangle([min_x, min_y, max_x, max_y], fill="white")

        # Write translated text
        draw.text((min_x + 2, min_y + 2), translated, fill="black", font=font)

        translated_texts.append({
            "text": translated,
            "position": {"x": min_x + 2, "y": min_y + 2}
        })

    # Save processed image
    output_filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(UPLOAD_DIR, output_filename)
    image.save(output_path)

    return {
        "processed_image": f"/processed_images/{output_filename}",
        "translated_texts": translated_texts
    }

@app.get("/processed_images/{filename}")
async def get_image(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))

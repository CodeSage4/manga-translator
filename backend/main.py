from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import os
import time
from paddleocr import PaddleOCR
import requests
import shutil
import uuid
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# Initialize the app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/processed", exist_ok=True)
os.makedirs("static/boxes", exist_ok=True)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize OCR engines for different text orientations
horizontal_ocr = PaddleOCR(use_angle_cls=False, lang='japan', use_gpu=False)
vertical_ocr = PaddleOCR(
    use_angle_cls=True, 
    lang='japan', 
    use_gpu=False,
    det_db_thresh=0.3
)

# Set up Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Basic translation function using MyMemory API
def translate_text(text, source_lang="ja", target_lang="en"):
    """
    Translate text using MyMemory API (free tier)
    """
    url = "https://api.mymemory.translated.net/get"
    params = {
        'q': text,
        'langpair': f'{source_lang}|{target_lang}'
    }
    
    try:
        response = requests.get(url, params=params)
        result = response.json()
        return result['responseData']['translatedText']
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

async def enhance_translation_with_gemini(japanese_text, base_translation, manga_context=""):
    """
    Use Gemini API to improve translation quality with context awareness
    """
    if not GEMINI_API_KEY:
        return base_translation  # Fallback to base translation if no API key
    
    try:
        # Create a well-crafted prompt for manga translation
        prompt = f"""
        You are an expert manga translator who maintains the cultural nuances and context.
        
        Original Japanese text: {japanese_text}
        
        Initial machine translation: {base_translation}
        
        {f"Additional context about this manga: {manga_context}" if manga_context else ""}
        
        Please provide an improved translation that:
        1. Maintains the tone and style appropriate for manga
        2. Preserves cultural references and honorifics when appropriate
        3. Sounds natural in English while preserving the original meaning
        4. Considers any provided context
        
        Improved translation:
        """
        
        # Configure the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Get the enhanced translation
        response = model.generate_content(prompt)
        
        # Extract and return the enhanced translation
        enhanced_translation = response.text.strip()
        return enhanced_translation
    
    except Exception as e:
        print(f"Gemini API error: {e}")
        return base_translation  # Fallback to base translation

def process_horizontal_text(image_path):
    """Process image optimized for horizontal text"""
    ocr_result = horizontal_ocr.ocr(image_path, cls=False)
    processed_results = []
    
    if ocr_result is None:
        return processed_results
    
    for idx, line in enumerate(ocr_result):
        if len(line) > 0:
            box = line[0][0]
            text = line[0][1][0]
            confidence = line[0][1][1]
            
            min_x = min(point[0] for point in box)
            min_y = min(point[1] for point in box)
            
            processed_results.append({
                "box": box,
                "text": text,
                "confidence": confidence,
                "is_vertical": False,
                "position": {"x": min_x + 2, "y": min_y + 2}
            })
    
    return processed_results

def process_vertical_text(image_path):
    """Process image optimized for vertical text"""
    ocr_result = vertical_ocr.ocr(image_path, cls=True)
    
    if ocr_result is None:
        return []
        
    image = cv2.imread(image_path)
    processed_results = []
    
    for idx, line in enumerate(ocr_result):
        if len(line) > 0:
            box = line[0][0]
            text = line[0][1][0]
            confidence = line[0][1][1]
            
            # Check if vertical based on box dimensions
            x_min = min(point[0] for point in box)
            x_max = max(point[0] for point in box)
            y_min = min(point[1] for point in box)
            y_max = max(point[1] for point in box)
            
            width = x_max - x_min
            height = y_max - y_min
            is_vertical = height > width * 1.5  # Simple heuristic for vertical text
            
            # For vertical text with poor recognition, try rotation
            if is_vertical and len(text) <= 3:  # Short text might need special handling
                try:
                    # Crop the region
                    x_min = max(0, int(x_min))
                    y_min = max(0, int(y_min))
                    x_max = min(image.shape[1], int(x_max))
                    y_max = min(image.shape[0], int(y_max))
                    
                    region = image[y_min:y_max, x_min:x_max]
                    if region.size > 0:
                        # Rotate for better OCR
                        rotated_region = cv2.rotate(region, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        
                        # Save temporarily for OCR
                        temp_path = f"temp_rotated_{idx}.png"
                        cv2.imwrite(temp_path, rotated_region)
                        
                        # Run OCR again on rotated region
                        rotated_result = vertical_ocr.ocr(temp_path, cls=False)
                        if rotated_result and len(rotated_result[0]) > 0:
                            rotated_text = rotated_result[0][0][1][0]
                            rotated_conf = rotated_result[0][0][1][1]
                            
                            # If rotated result seems better, use it
                            if rotated_conf > confidence and len(rotated_text) > len(text):
                                text = rotated_text
                                confidence = rotated_conf
                                
                        # Clean up temporary file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                except Exception as e:
                    print(f"Error during rotation processing: {e}")
            
            min_x = min(point[0] for point in box)
            min_y = min(point[1] for point in box)
            
            processed_results.append({
                "box": box,
                "text": text,
                "confidence": confidence,
                "is_vertical": is_vertical,
                "position": {"x": min_x + 2, "y": min_y + 2}
            })
    
    return processed_results

def visualize_ocr_boxes(image_path, processed_results):
    """
    Create a visualization of OCR bounding boxes with orientation info
    """
    image = cv2.imread(image_path)
    
    for idx, item in enumerate(processed_results):
        # Get box and text info
        box = np.array(item["box"]).reshape((-1, 1, 2)).astype(np.int32)
        text = item["text"]
        is_vertical = item.get("is_vertical", False)
        
        # Green for horizontal, blue for vertical
        color = (0, 0, 255) if is_vertical else (0, 255, 0)
        
        # Draw box
        cv2.polylines(image, [box], True, color, 2)
        
        # Add text identifier
        cv2.putText(
            image, 
            f"{idx+1}{'V' if is_vertical else 'H'}", 
            (int(box[0][0][0]), int(box[0][0][1]) - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (255, 0, 0), 
            2
        )
    
    return image

def overlay_translations(image_path, translated_texts):
    """
    Overlay translated text onto the image with support for vertical text
    """
    # Open image with PIL for better text support
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font that supports both Latin and Japanese
    try:
        font = ImageFont.truetype("Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Overlay each translated text
    for item in translated_texts:
        x = item["position"]["x"]
        y = item["position"]["y"]
        translated_text = item["text"]
        is_vertical = item.get("is_vertical", False)
        
        # For vertical text
        if is_vertical:
            # Create background
            char_width = 30
            text_height = len(translated_text) * 20
            
            # Draw white rectangle for background (rotated for vertical)
            draw.rectangle(
                [(x-5, y-5), (x + char_width, y + text_height)], 
                fill=(255, 255, 255, 200)
            )
            
            # Draw text characters vertically
            for i, char in enumerate(translated_text):
                draw.text((x, y + i*20), char, fill=(0, 0, 0), font=font)
        else:
            # Horizontal text - regular handling
            text_width = len(translated_text) * 12
            text_height = 30
            
            # Draw white rectangle for background
            draw.rectangle(
                [(x-5, y-5), (x + text_width, y + text_height)], 
                fill=(255, 255, 255, 200)
            )
            
            # Draw translated text
            draw.text((x, y), translated_text, fill=(0, 0, 0), font=font)
    
    return img

@app.post("/process/")
async def process_image(
    file: UploadFile = File(...),
    source_lang: str = Form("ja"),
    target_lang: str = Form("en"),
    show_boxes: bool = Form(False),
    manga_context: str = Form(""),
    is_vertical_text: bool = Form(False)  # Parameter for vertical text detection
):
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join("static/uploads", f"{file_id}{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    status_log = []
    status_log.append("File received and saved")
    
    # Choose the appropriate OCR function based on checkbox
    if is_vertical_text:
        status_log.append("Using vertical text optimization")
        processed_results = process_vertical_text(file_path)
    else:
        status_log.append("Using horizontal text optimization")
        processed_results = process_horizontal_text(file_path)
    
    status_log.append(f"OCR completed, detected {len(processed_results)} text regions")
    
    # Process the detected text
    translated_texts = []
    for idx, item in enumerate(processed_results):
        japanese_text = item["text"]
        
        # Basic translation first
        base_translation = translate_text(japanese_text, source_lang, target_lang)
        
        # Enhance with Gemini if available
        enhanced_translation = base_translation
        if GEMINI_API_KEY:
            try:
                enhanced_translation = await enhance_translation_with_gemini(
                    japanese_text, 
                    base_translation,
                    manga_context
                )
            except Exception as e:
                status_log.append(f"Gemini enhancement failed: {str(e)}")
        
        # Copy all properties from processed results to maintain vertical/horizontal info
        translated_item = {
            "original_text": japanese_text,
            "base_translation": base_translation,
            "text": enhanced_translation,
            "is_vertical": item["is_vertical"],
            "position": item["position"]
        }
        translated_texts.append(translated_item)
    
    # Create visualization with bounding boxes
    boxes_filename = f"{file_id}_boxes{file_extension}"
    boxes_path = os.path.join("static/boxes", boxes_filename)
    
    if show_boxes:
        boxes_image = visualize_ocr_boxes(file_path, processed_results)
        cv2.imwrite(boxes_path, boxes_image)
        status_log.append("OCR visualization created")
    
    # Create the translated image
    output_filename = f"{file_id}_translated{file_extension}"
    output_path = os.path.join("static/processed", output_filename)
    
    try:
        translated_image = overlay_translations(file_path, translated_texts)
        translated_image.save(output_path)
        status_log.append("Translated image created")
    except Exception as e:
        status_log.append(f"Error creating translated image: {str(e)}")
        # Copy original as fallback
        shutil.copy(file_path, output_path)
    
    return {
        "processed_image": f"/static/processed/{output_filename}",
        "visualized_boxes_image": f"/static/boxes/{boxes_filename}" if show_boxes else None,
        "translated_texts": translated_texts,
        "status_log": status_log
    }

@app.get("/")
def read_root():
    return {"message": "Manga Translation API"}
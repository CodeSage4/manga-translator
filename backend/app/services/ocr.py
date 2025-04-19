import os
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from typing import List, Dict, Tuple

from app.core.config import settings

class OCRService:
    def __init__(self):
        # Configure tesseract path if provided
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    async def process_image(self, image_path: str, language: str) -> List[Dict]:
        """Process a single image and return the extracted text with bounding boxes"""
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Preprocess the image
        preprocessed_img = self._preprocess_image(img)
        
        # Map language codes to tesseract language codes
        lang_code = self._map_language_to_tesseract(language)
        
        # Extract text with bounding boxes
        custom_config = f'--oem 3 --psm 11 -l {lang_code}'
        data = pytesseract.image_to_data(preprocessed_img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # Build the result
        results = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            # Skip empty text
            if int(data['conf'][i]) < 20 or not data['text'][i].strip():
                continue
                
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            # Get text color
            color = self._get_dominant_color(img, x, y, w, h)
            
            results.append({
                'text': data['text'][i],
                'box': {
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                },
                'confidence': int(data['conf'][i]),
                'color': color,
                'font_size': self._estimate_font_size(h)
            })
        
        return results
    
    async def process_pdf(self, pdf_path: str, language: str, temp_dir: str) -> List[List[Dict]]:
        """Process a PDF file and return extracted text with bounding boxes for each page"""
        # Create temp directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, output_folder=temp_dir)
        
        # Process each page
        results = []
        for i, img in enumerate(images):
            # Save the image temporarily
            img_path = os.path.join(temp_dir, f"page_{i}.jpg")
            img.save(img_path, "JPEG")
            
            # Process the image
            page_results = await self.process_image(img_path, language)
            results.append(page_results)
            
            # Delete the temporary image
            os.remove(img_path)
        
        return results
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess the image to improve OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Apply noise removal
        processed = cv2.GaussianBlur(thresh, (3, 3), 0)
        
        return processed
    
    def _get_dominant_color(self, img: np.ndarray, x: int, y: int, w: int, h: int) -> Tuple[int, int, int]:
        """Get the dominant color in the text region"""
        # Ensure the coordinates are within the image bounds
        height, width = img.shape[:2]
        x = max(0, x)
        y = max(0, y)
        x_end = min(width, x + w)
        y_end = min(height, y + h)
        
        if x_end <= x or y_end <= y:
            return (0, 0, 0)  # Return black if region is invalid
        
        # Extract the region
        region = img[y:y_end, x:x_end]
        
        # Reshape the region to a list of pixels
        pixels = region.reshape((-1, 3))
        
        # Convert to float32
        pixels = np.float32(pixels)
        
        # Define criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        
        # Apply k-means clustering to find the most dominant color
        _, labels, centers = cv2.kmeans(pixels, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert back to uint8
        center = np.uint8(centers)[0]
        
        return tuple(map(int, center))
    
    def _estimate_font_size(self, height: int) -> int:
        """Estimate font size based on the height of the bounding box"""
        # This is a simplistic approach - it assumes the bounding box height
        # is directly proportional to the font size. In reality, you may need
        # a more sophisticated algorithm.
        return max(int(height * 0.7), 10)  # Minimum font size of 10
    
    def _map_language_to_tesseract(self, language: str) -> str:
        """Map a language name to the corresponding tesseract language code"""
        language_map = {
            "Japanese": "jpn",
            "English": "eng",
            "Chinese": "chi_sim",
            "Korean": "kor",
            "Spanish": "spa",
            "French": "fra",
            "German": "deu",
            "Russian": "rus",
            "Italian": "ita",
            "Portuguese": "por",
            "Arabic": "ara"
        }
        
        return language_map.get(language, "eng")  # Default to English if language is not found

ocr_service = OCRService() 
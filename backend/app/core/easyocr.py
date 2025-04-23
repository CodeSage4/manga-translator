import easyocr
import numpy as np
from typing import List, Dict
from app.config import settings

class OCRProcessor:
    def __init__(self):
        """Initialize EasyOCR with supported languages"""
        self.reader = easyocr.Reader(['ja', 'en'])  # Support Japanese and English by default
        self.lang_map = {
            "Japanese": "ja",
            "English": "en",
            "Chinese": "ch_sim",
            "Korean": "ko"
        }

    async def process_image(self, image: np.ndarray, source_language: str = "Japanese") -> List[Dict]:
        """Process image and return text regions with bounding boxes"""
        try:
            lang_code = self.lang_map.get(source_language, "en")
            results = self.reader.readtext(image)
            
            text_regions = []
            for (bbox, text, prob) in results:
                if prob < settings.MIN_CONFIDENCE:
                    continue
                    
                # Convert bbox to x,y,w,h format
                x = min(point[0] for point in bbox)
                y = min(point[1] for point in bbox)
                w = max(point[0] for point in bbox) - x
                h = max(point[1] for point in bbox) - y
                
                text_regions.append({
                    'text': text,
                    'bbox': (int(x), int(y), int(w), int(h)),
                    'confidence': prob
                })
            
            return text_regions
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ocr import OCRService

class TestOCR(unittest.TestCase):
    def setUp(self):
        self.ocr_service = OCRService()
        self.test_image_path = os.path.join(
            os.path.dirname(__file__), 
            "test_data", 
            "sample_manga.jpg"
        )
        
        # Create test data directory if it doesn't exist
        os.makedirs(os.path.join(os.path.dirname(__file__), "test_data"), exist_ok=True)
        
    def test_preprocess_image(self):
        """Test that image preprocessing works"""
        if not os.path.exists(self.test_image_path):
            self.skipTest(f"Test image not found at {self.test_image_path}")
            
        import cv2
        img = cv2.imread(self.test_image_path)
        if img is None:
            self.skipTest(f"Could not read test image at {self.test_image_path}")
            
        processed = self.ocr_service._preprocess_image(img)
        self.assertIsNotNone(processed)
        self.assertEqual(processed.shape[:2], img.shape[:2])
        
    def test_estimate_font_size(self):
        """Test font size estimation"""
        # Test with various heights
        self.assertEqual(self.ocr_service._estimate_font_size(100), 70)
        self.assertEqual(self.ocr_service._estimate_font_size(10), 10)  # Minimum size
        
    def test_map_language(self):
        """Test language code mapping"""
        self.assertEqual(self.ocr_service._map_language_to_tesseract("Japanese"), "jpn")
        self.assertEqual(self.ocr_service._map_language_to_tesseract("English"), "eng")
        self.assertEqual(self.ocr_service._map_language_to_tesseract("Unknown"), "eng")  # Default
            
if __name__ == "__main__":
    unittest.main() 
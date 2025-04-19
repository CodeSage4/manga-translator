import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
from googletrans import Translator

class MangaProcessor:
    def __init__(self, tesseract_path=None):
        """Initialize the manga processor with optional tesseract path"""
        # Configure tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Try to load from environment variable
            import os
            env_path = os.environ.get('TESSERACT_PATH')
            if env_path:
                pytesseract.pytesseract.tesseract_cmd = env_path
        
        # Initialize translator
        self.translator = Translator()
        
        # Set language mapping for Tesseract
        self.lang_map = {
            "Japanese": "jpn",
            "Chinese": "chi_sim",
            "Korean": "kor",
            "English": "eng"
        }
        
        # Default parameters for text detection
        self.min_confidence = 40  # Minimum confidence for OCR
        self.padding = 5  # Padding around detected text regions
    
    def detect_text_regions(self, image_path, source_language="Japanese"):
        """
        Step 1 & 2: Detect dialogue boxes in the image and remember their coordinates
        Returns a list of dictionaries with text regions and their coordinates
        """
        print(f"Detecting text regions in {image_path}...")
        
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to get text regions (white text on black background)
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations to find text blocks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=4)
        eroded = cv2.erode(dilated, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find potential text regions
        text_regions = []
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter out very small regions
            if w < 20 or h < 20:
                continue
            
            # Filter out very large regions
            if w > img.shape[1] * 0.9 or h > img.shape[0] * 0.9:
                continue
            
            # Add padding to the region
            x = max(0, x - self.padding)
            y = max(0, y - self.padding)
            w = min(img.shape[1] - x, w + 2 * self.padding)
            h = min(img.shape[0] - y, h + 2 * self.padding)
            
            text_regions.append({
                "box": (x, y, w, h),
                "image": img[y:y+h, x:x+w].copy()
            })
        
        print(f"Found {len(text_regions)} potential text regions")
        
        # Save a debug image showing the detected regions
        debug_img = img.copy()
        for region in text_regions:
            x, y, w, h = region["box"]
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Save the debug image
        debug_path = os.path.splitext(image_path)[0] + "_detected.jpg"
        cv2.imwrite(debug_path, debug_img)
        print(f"Saved debug image with detected regions to {debug_path}")
        
        return text_regions, img
    
    def perform_ocr(self, text_regions, source_language="Japanese"):
        """
        Step 3: Perform OCR on the text regions
        Returns the text regions with extracted text
        """
        print(f"Performing OCR on {len(text_regions)} regions...")
        
        # Get the appropriate language code for Tesseract
        lang_code = self.lang_map.get(source_language, "eng")
        
        # Configure OCR
        custom_config = f'--oem 1 --psm 11 -l {lang_code}'
        
        # Process each region
        for i, region in enumerate(text_regions):
            # Convert the region to PIL Image
            pil_img = Image.fromarray(cv2.cvtColor(region["image"], cv2.COLOR_BGR2RGB))
            
            # Perform OCR
            text = pytesseract.image_to_string(pil_img, config=custom_config, lang=lang_code)
            
            # Clean up text (remove extra whitespace and newlines)
            text = ' '.join(text.strip().split())
            
            # Store the extracted text
            region["text"] = text
            
            print(f"Region {i+1}: {text if text else '[No text detected]'}")
        
        # Filter out regions with no text
        text_regions = [r for r in text_regions if r.get("text", "").strip()]
        print(f"Found {len(text_regions)} regions with text")
        
        return text_regions
    
    def translate_text(self, text_regions, source_language="Japanese", target_language="English"):
        """
        Translate the extracted text from each region
        """
        print(f"Translating text from {source_language} to {target_language}...")
        
        # Set up source and target language codes
        source_code = source_language.lower()
        target_code = target_language.lower()
        
        # Translate each text region
        for region in text_regions:
            original_text = region.get("text", "")
            if not original_text:
                region["translated_text"] = ""
                continue
            
            try:
                # Translate using Google Translate
                translation = self.translator.translate(
                    original_text, 
                    src=source_code, 
                    dest=target_code
                )
                
                # Store the translation
                region["translated_text"] = translation.text
                print(f"Original: {original_text}")
                print(f"Translated: {translation.text}")
                print("-" * 40)
            except Exception as e:
                print(f"Translation error: {e}")
                region["translated_text"] = original_text  # Keep original text as fallback
        
        return text_regions
    
    def render_translated_image(self, original_image, text_regions, output_path):
        """
        Step 4: Mask the original image with translated text
        """
        print(f"Rendering translated image to {output_path}...")
        
        # Convert to PIL Image for text rendering
        pil_img = Image.fromarray(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        # Process each text region
        for region in text_regions:
            x, y, w, h = region["box"]
            translated_text = region.get("translated_text", "")
            
            if not translated_text:
                continue  # Skip regions without translation
            
            # Draw a white background for text
            draw.rectangle([x, y, x+w, y+h], fill=(255, 255, 255))
            
            # Determine font size based on region size
            font_size = self._estimate_font_size(w, h, translated_text)
            
            try:
                # Try to use a nice font
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                # Fallback to default
                font = ImageFont.load_default()
            
            # Draw the translated text
            self._draw_text_with_wrapping(
                draw, translated_text, (x, y), w, h, font, (0, 0, 0)
            )
        
        # Save the result
        pil_img.save(output_path)
        print(f"Saved translated image to {output_path}")
        
        return output_path
    
    def _estimate_font_size(self, width, height, text):
        """Estimate the appropriate font size for the region"""
        # Base size on region dimensions and text length
        area = width * height
        text_length = len(text)
        
        # More complex calculation could be implemented here
        base_size = int(min(width, height) / 8)  # Start with 1/8 of the smallest dimension
        
        # Adjust for text length
        if text_length > 0:
            size_factor = 1.0 / (0.5 + 0.5 * (text_length / 20))  # Reduce size for longer text
            base_size = int(base_size * size_factor)
        
        # Ensure size is reasonable
        return max(10, min(base_size, 36))  # Between 10 and 36pt
    
    def _draw_text_with_wrapping(self, draw, text, position, max_width, max_height, font, color):
        """Draw text with wrapping to fit within region"""
        x, y = position
        y_offset = 0
        
        # Split text into words
        words = text.split()
        
        if not words:
            return
        
        # Process line by line
        current_line = words[0]
        for word in words[1:]:
            # Check if adding this word exceeds width
            test_line = current_line + " " + word
            text_width = draw.textlength(test_line, font=font)
            
            if text_width <= max_width:
                # Word fits, add it to the current line
                current_line = test_line
            else:
                # Draw the current line and start a new one
                draw.text((x, y + y_offset), current_line, font=font, fill=color)
                y_offset += font.getbbox("A")[3] + 2  # Line height + spacing
                current_line = word
                
                # Check if we've exceeded the box height
                if y_offset > max_height:
                    break
        
        # Draw the last line
        if current_line and y_offset <= max_height:
            draw.text((x, y + y_offset), current_line, font=font, fill=color)
    
    def process_manga_image(self, input_path, output_path, source_language="Japanese", target_language="English"):
        """Process a manga image with the full pipeline"""
        try:
            # Step 1 & 2: Detect text regions and get their coordinates
            text_regions, original_image = self.detect_text_regions(input_path, source_language)
            
            # Step 3: Perform OCR on each text region
            text_regions = self.perform_ocr(text_regions, source_language)
            
            # Translate the extracted text
            text_regions = self.translate_text(text_regions, source_language, target_language)
            
            # Step 4: Render the translated text onto the image
            self.render_translated_image(original_image, text_regions, output_path)
            
            return True
        except Exception as e:
            print(f"Error processing manga image: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Process manga images with translation")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument("--source", default="Japanese", help="Source language")
    parser.add_argument("--target", default="English", help="Target language")
    parser.add_argument("--tesseract", help="Path to Tesseract executable")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create processor
    processor = MangaProcessor(tesseract_path=args.tesseract)
    
    # Process the image
    success = processor.process_manga_image(
        args.input, args.output, args.source, args.target
    )
    
    if success:
        print("Processing completed successfully!")
    else:
        print("Processing failed.") 
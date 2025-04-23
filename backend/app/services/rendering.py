import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from typing import List, Dict, Tuple

from app.config import settings

class RenderingService:
    def __init__(self):
        # Common font for fallback
        self.default_font = "arial.ttf"
        self.font_dir = os.path.join(os.path.dirname(__file__), "../../fonts")
        
        # Ensure the font directory exists
        os.makedirs(self.font_dir, exist_ok=True)
    
    async def render_text_on_image(self, image_path: str, translated_results: List[Dict], output_path: str) -> str:
        """Render translated text on the image and save to output path"""
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to PIL Image
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Create a draw object
        draw = ImageDraw.Draw(pil_img)
        
        # Render each text box
        for result in translated_results:
            x = result['box']['x']
            y = result['box']['y']
            width = result['box']['width']
            height = result['box']['height']
            text = result['text']
            color = result.get('color', (0, 0, 0))
            font_size = result.get('font_size', 12)
            
            # Convert color if it's in BGR (OpenCV) format
            if isinstance(color, tuple) and len(color) == 3:
                color = (color[2], color[1], color[0])  # BGR to RGB
            
            # Get a suitable font
            font = self._get_font(font_size)
            
            # Draw a background rectangle
            draw.rectangle([x, y, x + width, y + height], fill=(255, 255, 255))
            
            # Draw the text
            self._draw_text_with_wrapping(draw, text, (x, y), width, height, font, color)
        
        # Save the result
        pil_img.save(output_path)
        
        return output_path
    
    async def render_text_on_pdf(self, pdf_images: List[str], translated_results_per_page: List[List[Dict]], output_dir: str, job_id: str) -> str:
        """Render translated text on each page of a PDF and save to output directory"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each page
        output_images = []
        for i, (image_path, results) in enumerate(zip(pdf_images, translated_results_per_page)):
            output_path = os.path.join(output_dir, f"{job_id}_page_{i}.jpg")
            await self.render_text_on_image(image_path, results, output_path)
            output_images.append(output_path)
        
        # Combine the images into a PDF
        output_pdf_path = os.path.join(output_dir, f"{job_id}.pdf")
        self._combine_images_to_pdf(output_images, output_pdf_path)
        
        # Delete the temporary images
        for image_path in output_images:
            os.remove(image_path)
        
        return output_pdf_path
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font with the specified size"""
        try:
            # Use a common font that's available on most systems
            return ImageFont.truetype(self.default_font, size)
        except IOError:
            # Fallback to default PIL font
            return ImageFont.load_default()
    
    def _draw_text_with_wrapping(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int], 
                                 width: int, height: int, font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        """Draw text with wrapping to fit within the given width and height"""
        x, y = position
        
        # Split text into words
        words = text.split()
        if not words:
            return
        
        # Start with all words in the first line
        lines = [words]
        line_idx = 0
        word_idx = 0
        
        # Wrap words into lines
        while line_idx < len(lines):
            # Check if the current line is too wide
            line_text = ' '.join(lines[line_idx])
            text_width = draw.textlength(line_text, font=font)
            
            if text_width <= width:
                # Line fits, move to next line
                line_idx += 1
                word_idx = 0
                continue
            
            # Line doesn't fit, try to move the last word to a new line
            if len(lines[line_idx]) == 1:
                # Can't wrap a single word
                line_idx += 1
                word_idx = 0
                continue
            
            # Move the last word to a new line
            last_word = lines[line_idx].pop()
            if line_idx + 1 >= len(lines):
                lines.append([])
            lines[line_idx + 1].insert(0, last_word)
        
        # Draw each line
        line_height = font.getbbox("Ay")[3]  # Get line height
        y_pos = y
        
        for line in lines:
            line_text = ' '.join(line)
            draw.text((x, y_pos), line_text, font=font, fill=color)
            y_pos += line_height
            
            if y_pos > y + height:
                # Out of space, stop drawing
                break
    
    def _combine_images_to_pdf(self, image_paths: List[str], output_path: str):
        """Combine multiple images into a PDF"""
        images = [Image.open(path) for path in image_paths]
        if not images:
            raise ValueError("No images to combine")
        
        # Save as PDF
        images[0].save(
            output_path, 
            save_all=True, 
            append_images=images[1:],
            resolution=100.0
        )

rendering_service = RenderingService() 
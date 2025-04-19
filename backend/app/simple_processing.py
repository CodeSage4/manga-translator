import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

def detect_text_regions(image_path, num_regions=3):
    """
    Simulate text detection by generating random regions
    Returns a list of (x, y, width, height) tuples
    """
    try:
        img = cv2.imread(image_path)
        height, width = img.shape[:2]
        
        # Generate random regions
        regions = []
        for _ in range(num_regions):
            # Create random-sized region
            region_width = random.randint(width // 6, width // 3)
            region_height = random.randint(height // 10, height // 5)
            
            # Random position (ensuring it's within image bounds)
            x = random.randint(10, width - region_width - 10)
            y = random.randint(10, height - region_height - 10)
            
            regions.append((x, y, region_width, region_height))
        
        return regions
    except Exception as e:
        print(f"Error in text detection: {e}")
        return []

def overlay_translated_text(image_path, output_path, source_lang, target_lang):
    """
    Create a simulated translation by adding overlay text
    """
    try:
        # Open the image with PIL
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Try to get a system font that exists
        font_size = 24
        try:
            # Try different common fonts
            font_options = [
                "arial.ttf", "Arial.ttf",
                "cour.ttf", "Courier.ttf",
                "times.ttf", "Times.ttf",
                "verdana.ttf", "Verdana.ttf"
            ]
            font = None
            for font_name in font_options:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except IOError:
                    continue
            
            # Fallback to default if no font found
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        # Detect regions (simulated)
        regions = detect_text_regions(image_path)
        
        # Sample translated texts based on source and target language
        translations = {
            "Japanese": {
                "English": ["Hello", "Thank you", "What?", "Where?", "Amazing!"],
                "Spanish": ["Hola", "Gracias", "¿Qué?", "¿Dónde?", "¡Increíble!"],
                "French": ["Bonjour", "Merci", "Quoi?", "Où?", "Incroyable!"],
            },
            "Chinese": {
                "English": ["Welcome", "Good", "Bad", "Why?", "How?"],
                "Spanish": ["Bienvenido", "Bueno", "Malo", "¿Por qué?", "¿Cómo?"],
            }
        }
        
        # Default translations if language pair not found
        default_translations = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        
        # Get translations for the language pair
        source_translations = translations.get(source_lang, {})
        translated_texts = source_translations.get(target_lang, default_translations)
        
        # Draw white background and translated text on each region
        for i, (x, y, width, height) in enumerate(regions):
            # Select a translation (cycling through the available ones)
            text = translated_texts[i % len(translated_texts)]
            
            # Draw white background
            draw.rectangle([x, y, x + width, y + height], fill="white")
            
            # Draw text
            draw.text((x + 5, y + 5), text, fill="black", font=font)
        
        # Save the result
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error in text overlay: {e}")
        return False

def process_manga_image(input_path, output_path, source_lang, target_lang):
    """
    Process a manga image by simulating OCR and translation
    """
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return False
    
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    return overlay_translated_text(input_path, output_path, source_lang, target_lang) 
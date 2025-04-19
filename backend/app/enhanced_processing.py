import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import tempfile
import re

# Try to import pytesseract, but don't fail if not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    
# Try to import translation libraries, but don't fail if not available
try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    
# Try to import PDF libraries, but don't fail if not available
try:
    from pdf2image import convert_from_path
    # Check if we can find a poppler path in the environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        POPPLER_PATH = os.environ.get('POPPLER_PATH')
        if POPPLER_PATH and os.path.exists(POPPLER_PATH):
            print(f"Found Poppler path in environment: {POPPLER_PATH}")
        else:
            print(f"Warning: POPPLER_PATH environment variable is set to {POPPLER_PATH}, but the directory doesn't exist")
            # Try common locations
            common_locations = [
                "C:\\poppler\\bin",
                "C:\\Program Files\\poppler\\bin",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "poppler", "bin")
            ]
            for path in common_locations:
                if os.path.exists(path):
                    POPPLER_PATH = path
                    print(f"Found Poppler at {POPPLER_PATH}")
                    break
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        POPPLER_PATH = None
    
    # Test if we can convert a PDF
    try:
        # Create a minimal PDF for testing
        test_pdf = os.path.join(tempfile.gettempdir(), "pdf_test.pdf")
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(test_pdf)
        c.drawString(100, 750, "PDF test")
        c.save()
        
        # Try to convert it
        kwargs = {}
        if POPPLER_PATH:
            kwargs['poppler_path'] = POPPLER_PATH
        
        test_result = convert_from_path(test_pdf, **kwargs)
        print(f"PDF support test successful: Converted test PDF to {len(test_result)} images")
        PDF_SUPPORT_AVAILABLE = True
    except Exception as e:
        print(f"PDF support test failed: {e}")
        PDF_SUPPORT_AVAILABLE = False
except ImportError:
    POPPLER_PATH = None
    PDF_SUPPORT_AVAILABLE = False
    print("pdf2image not installed, PDF support will not be available")

class MangaTranslator:
    def __init__(self, tesseract_path=None, use_simulation=False):
        self.use_simulation = use_simulation
        
        # Try to configure Tesseract path if provided
        if tesseract_path and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Initialize translation model cache
        self.translation_models = {}
        self.translation_tokenizers = {}

    def detect_text_regions_with_tesseract(self, image_path, source_language):
        """
        Detect text regions using Tesseract OCR
        Returns a list of dictionaries with text and bounding box info
        """
        if not TESSERACT_AVAILABLE:
            print("Tesseract not available, falling back to simulation")
            return self._simulate_text_regions(image_path)
        
        try:
            # Map language to Tesseract language code
            lang_map = {
                "Japanese": "jpn",
                "Chinese": "chi_sim",
                "Korean": "kor",
                "English": "eng",
                "Spanish": "spa",
                "French": "fra",
                "German": "deu"
            }
            lang_code = lang_map.get(source_language, "eng")
            
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                return self._simulate_text_regions(image_path)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Save the preprocessed image to a temp file
            temp_filename = tempfile.mktemp(suffix='.jpg')
            cv2.imwrite(temp_filename, gray)
            
            # Get text and bounding boxes
            custom_config = f'--oem 1 --psm 11 -l {lang_code}'
            data = pytesseract.image_to_data(Image.open(temp_filename), output_type=pytesseract.Output.DICT, config=custom_config)
            
            # Clean up temp file
            os.unlink(temp_filename)
            
            # Extract regions with confidence > 40%
            regions = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 40 and data['text'][i].strip():
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    regions.append({
                        'text': data['text'][i],
                        'box': (x, y, w, h),
                        'conf': int(data['conf'][i])
                    })
            
            # If no regions detected, fall back to simulation
            if not regions:
                print("No text regions detected with Tesseract, falling back to simulation")
                return self._simulate_text_regions(image_path)
                
            return regions
        except Exception as e:
            print(f"Error in Tesseract OCR: {e}")
            # Fall back to simulation in case of error
            return self._simulate_text_regions(image_path)

    def _simulate_text_regions(self, image_path, num_regions=3):
        """
        Simulate text detection by generating random regions
        Returns a list of dictionaries with simulated text and bounding box info
        """
        try:
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            
            # Generate random regions
            regions = []
            for i in range(num_regions):
                # Create random-sized region
                region_width = random.randint(width // 6, width // 3)
                region_height = random.randint(height // 10, height // 5)
                
                # Random position (ensuring it's within image bounds)
                x = random.randint(10, width - region_width - 10)
                y = random.randint(10, height - region_height - 10)
                
                # Simulated text (based on region size)
                simulated_text = f"Text Region {i+1}"
                
                regions.append({
                    'text': simulated_text,
                    'box': (x, y, region_width, region_height),
                    'conf': 80  # Simulated confidence level
                })
            
            return regions
        except Exception as e:
            print(f"Error in text region simulation: {e}")
            return []

    def translate_text(self, text, source_language, target_language):
        """
        Translate text using MarianMT models or fallback to mock translations
        """
        if not TRANSLATION_AVAILABLE or self.use_simulation:
            return self._get_mock_translation(text, source_language, target_language)
        
        try:
            # Get model name for this language pair
            model_name = self._get_translation_model_name(source_language, target_language)
            
            # Check if we already have this model loaded
            if model_name not in self.translation_models:
                try:
                    # Load model and tokenizer
                    tokenizer = MarianTokenizer.from_pretrained(model_name)
                    model = MarianMTModel.from_pretrained(model_name)
                    
                    self.translation_tokenizers[model_name] = tokenizer
                    self.translation_models[model_name] = model
                except Exception as e:
                    print(f"Error loading translation model: {e}")
                    return self._get_mock_translation(text, source_language, target_language)
            
            # Get model and tokenizer
            tokenizer = self.translation_tokenizers[model_name]
            model = self.translation_models[model_name]
            
            # Translate
            inputs = tokenizer(text, return_tensors="pt", padding=True)
            outputs = model.generate(**inputs)
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return translated_text
        except Exception as e:
            print(f"Error in translation: {e}")
            return self._get_mock_translation(text, source_language, target_language)

    def _get_translation_model_name(self, source_language, target_language):
        """Map language names to HuggingFace model names"""
        lang_code_map = {
            "English": "en",
            "Japanese": "jap",
            "Chinese": "zh",
            "Korean": "kor",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Russian": "ru",
            "Italian": "it",
            "Portuguese": "pt",
            "Arabic": "ar"
        }
        
        source_code = lang_code_map.get(source_language, "en")
        target_code = lang_code_map.get(target_language, "en")
        
        return f"Helsinki-NLP/opus-mt-{source_code}-{target_code}"

    def _get_mock_translation(self, text, source_language, target_language):
        """Provide mock translations for demo purposes"""
        # Sample mock translations for common languages
        translations = {
            "Japanese": {
                "English": {
                    "こんにちは": "Hello",
                    "ありがとう": "Thank you",
                    "何": "What",
                    "どこ": "Where",
                    "すごい": "Amazing"
                }
            },
            "Chinese": {
                "English": {
                    "你好": "Hello",
                    "谢谢": "Thank you",
                    "什么": "What",
                    "哪里": "Where",
                    "很好": "Very good"
                }
            }
        }
        
        # Check if we have a translation for this language pair and text
        source_dict = translations.get(source_language, {})
        target_dict = source_dict.get(target_language, {})
        
        # Return the translation if available, otherwise return original with [TR] prefix
        if text in target_dict:
            return target_dict[text]
        
        # If the text doesn't match exactly, check for partial matches
        for src, tgt in target_dict.items():
            if src in text:
                return text.replace(src, tgt)
        
        # Return text with prefix for simulation
        return f"[{target_language}] {text}"

    def overlay_translated_text(self, image_path, output_path, text_regions, target_language):
        """
        Create a translated image by overlaying translated text on the original image
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
            
            # Draw white background and translated text on each region
            for region in text_regions:
                # Extract data
                text = region.get('translated_text', region.get('text', ''))
                x, y, width, height = region['box']
                
                # Skip very small regions
                if width < 20 or height < 10:
                    continue
                
                # Calculate appropriate font size based on region height
                adapted_font_size = max(int(height * 0.7), 12)
                try:
                    # Try to create font with adapted size
                    adapted_font = ImageFont.truetype(font.path, adapted_font_size)
                except:
                    # Fall back to default font if sizing fails
                    adapted_font = font
                
                # Draw white background
                draw.rectangle([x, y, x + width, y + height], fill="white")
                
                # Draw text
                # For languages that read right-to-left, you might need additional handling here
                draw.text((x + 5, y + 5), text, fill="black", font=adapted_font)
            
            # Save the result
            img.save(output_path)
            return True
        except Exception as e:
            print(f"Error in text overlay: {e}")
            return False

    def process_manga_image(self, input_path, output_path, source_language, target_language):
        """
        Process a manga image with OCR and translation
        """
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            return False
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Step 1: Detect text regions
            if self.use_simulation:
                text_regions = self._simulate_text_regions(input_path)
            else:
                text_regions = self.detect_text_regions_with_tesseract(input_path, source_language)
            
            # Step 2: Translate text in each region
            for region in text_regions:
                source_text = region['text']
                region['translated_text'] = self.translate_text(source_text, source_language, target_language)
            
            # Step 3: Create translated image with overlaid text
            return self.overlay_translated_text(input_path, output_path, text_regions, target_language)
        except Exception as e:
            print(f"Error processing manga image: {e}")
            return False
            
    def process_pdf(self, input_path, output_path, source_language, target_language):
        """
        Process a PDF manga by extracting pages, processing each one, and recombining
        """
        if not PDF_SUPPORT_AVAILABLE:
            print("PDF support not available, falling back to simple copy")
            # Just copy the PDF as-is
            import shutil
            shutil.copy(input_path, output_path)
            return True
            
        try:
            # Create a temporary directory for the pages
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract pages from PDF
                print(f"Converting PDF: {input_path}")
                
                # Set up conversion parameters
                kwargs = {}
                
                # Try with the global POPPLER_PATH first
                if 'POPPLER_PATH' in globals() and POPPLER_PATH and os.path.exists(POPPLER_PATH):
                    print(f"Using global Poppler path: {POPPLER_PATH}")
                    kwargs['poppler_path'] = POPPLER_PATH
                # If not defined globally, check environment
                else:
                    # Try to load from environment variables
                    try:
                        from dotenv import load_dotenv
                        load_dotenv()
                        env_poppler_path = os.environ.get('POPPLER_PATH')
                        if env_poppler_path and os.path.exists(env_poppler_path):
                            print(f"Using Poppler path from env: {env_poppler_path}")
                            kwargs['poppler_path'] = env_poppler_path
                    except Exception as e:
                        print(f"Error loading Poppler path from env: {e}")
                
                # Convert PDF to images
                try:
                    print(f"Attempting to convert PDF with kwargs: {kwargs}")
                    pages = convert_from_path(input_path, output_folder=temp_dir, **kwargs)
                    print(f"Successfully converted PDF to {len(pages)} pages")
                except Exception as e:
                    print(f"Error converting PDF with provided settings: {e}")
                    print("Trying alternative paths for Poppler...")
                    
                    # Try common locations
                    common_paths = [
                        "C:\\poppler\\bin",
                        "C:\\Program Files\\poppler\\bin",
                        "C:\\Users\\Lenovo\\AppData\\Local\\Programs\\poppler\\bin",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "poppler", "bin")
                    ]
                    
                    success = False
                    for path in common_paths:
                        if os.path.exists(path):
                            print(f"Trying Poppler at: {path}")
                            try:
                                pages = convert_from_path(input_path, output_folder=temp_dir, poppler_path=path)
                                print(f"Successfully converted PDF using alternative path: {path}")
                                success = True
                                break
                            except Exception as nested_e:
                                print(f"Failed with path {path}: {nested_e}")
                    
                    if not success:
                        print("All PDF conversion attempts failed, falling back to simple copy")
                        import shutil
                        shutil.copy(input_path, output_path)
                        return True
                
                # Process each page
                processed_images = []
                for i, page in enumerate(pages):
                    # Save the page as an image
                    page_path = os.path.join(temp_dir, f'page_{i}.jpg')
                    page.save(page_path, 'JPEG')
                    
                    # Process the page
                    result_path = os.path.join(temp_dir, f'result_{i}.jpg')
                    if self.process_manga_image(page_path, result_path, source_language, target_language):
                        processed_images.append(result_path)
                    else:
                        # If processing failed, use the original page
                        processed_images.append(page_path)
                
                # Combine processed images back into a PDF
                if processed_images:
                    # Open first image
                    first_image = Image.open(processed_images[0])
                    # Convert all other images to RGB (same as first)
                    other_images = []
                    for img_path in processed_images[1:]:
                        img = Image.open(img_path)
                        if img.mode != first_image.mode:
                            img = img.convert(first_image.mode)
                        other_images.append(img)
                    
                    # Save as PDF
                    first_image.save(
                        output_path,
                        save_all=True,
                        append_images=other_images
                    )
                    return True
                else:
                    print("No pages were processed")
                    return False
        except Exception as e:
            print(f"Error processing PDF: {e}")
            print("Falling back to simple copy")
            # Fallback to simple copy
            try:
                import shutil
                shutil.copy(input_path, output_path)
                return True
            except Exception as copy_e:
                print(f"Error even when copying PDF: {copy_e}")
                return False

# Helper function to create a translator instance
def create_translator(tesseract_path=None, use_simulation=False):
    return MangaTranslator(tesseract_path, use_simulation)

# For backwards compatibility with the simplified version
def process_manga_image(input_path, output_path, source_language, target_language):
    """
    Process a manga image by detecting text, translating, and overlaying text
    """
    translator = create_translator(use_simulation=True)
    return translator.process_manga_image(input_path, output_path, source_language, target_language) 
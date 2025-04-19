import os
import sys
import uvicorn

print("=== Manga Translator Backend Server ===")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check if Tesseract is available
try:
    import pytesseract
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR found: Version {tesseract_version}")
        print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
    except Exception as e:
        print(f"Tesseract OCR not found: {e}")
        # Try to set from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            tesseract_path = os.environ.get('TESSERACT_PATH')
            if tesseract_path:
                print(f"Setting Tesseract path from .env: {tesseract_path}")
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
            else:
                print("No TESSERACT_PATH found in .env file")
        except Exception as e:
            print(f"Error loading .env file: {e}")
except ImportError:
    print("pytesseract not installed")

# Check if PDF support is available
try:
    from pdf2image import convert_from_path
    print("PDF2Image found, PDF support should be available")
    
    # Check if Poppler is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        poppler_path = os.environ.get('POPPLER_PATH')
        if poppler_path:
            print(f"Poppler path from .env: {poppler_path}")
            # Verify if the directory exists
            if os.path.exists(poppler_path):
                print("Poppler directory exists")
            else:
                print(f"WARNING: Poppler directory not found at {poppler_path}")
        else:
            print("No POPPLER_PATH found in .env file")
    except Exception as e:
        print(f"Error checking Poppler: {e}")
except ImportError:
    print("pdf2image not installed, PDF support will not be available")

# Check if enhanced processing is available
try:
    from app.enhanced_processing import PDF_SUPPORT_AVAILABLE, create_translator
    translator = create_translator()
    print(f"Enhanced processing available: {True}")
    print(f"PDF support available in enhanced processing: {PDF_SUPPORT_AVAILABLE}")
except ImportError as e:
    print(f"Enhanced processing not available: {e}")
except Exception as e:
    print(f"Error importing enhanced processing: {e}")

# Check storage directories
upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "uploads")
result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "results")
temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")

if not os.path.exists(upload_dir):
    print(f"Creating upload directory: {upload_dir}")
    os.makedirs(upload_dir, exist_ok=True)

if not os.path.exists(result_dir):
    print(f"Creating result directory: {result_dir}")
    os.makedirs(result_dir, exist_ok=True)
    
if not os.path.exists(temp_dir):
    print(f"Creating temp directory: {temp_dir}")
    os.makedirs(temp_dir, exist_ok=True)

print("All required directories have been verified")

print("\nStarting the backend server...")
print("API will be available at http://localhost:8000\n")

# Run the uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.simplified_main:app", host="0.0.0.0", port=8000, reload=True) 
import os
import sys
import shutil
import tempfile
import requests
from PIL import Image, ImageDraw, ImageFont

# Configuration
API_URL = "http://localhost:8000"  # Base URL for the API
TEST_IMAGE_PATH = "test_image.jpg"  # Path to a test image
TEST_PDF_PATH = "test_pdf.pdf"     # Path to a test PDF
VERBOSE = True  # Set to True for detailed logs

def log(message):
    """Print log message if verbose is enabled"""
    if VERBOSE:
        print(message)

def check_api_connection():
    """Check if the API is running and accessible"""
    log("Checking API connection...")
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            log(f"✅ API is running and accessible at {API_URL}")
            return True
        else:
            log(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Failed to connect to API: {e}")
        return False

def check_storage_directories():
    """Check if storage directories exist and are writable"""
    log("Checking storage directories...")
    
    # Get the backend directory
    backend_dir = os.path.join(os.getcwd(), "backend")
    if not os.path.exists(backend_dir):
        log("⚠️ Working from non-root directory, trying to find backend directory...")
        backend_dir = os.getcwd()
        if "backend" not in backend_dir:
            log("❌ Cannot locate backend directory")
            return False
    
    # Check storage directories
    storage_dir = os.path.join(backend_dir, "storage")
    upload_dir = os.path.join(storage_dir, "uploads")
    result_dir = os.path.join(storage_dir, "results")
    temp_dir = os.path.join(backend_dir, "temp")
    
    # Check if directories exist
    directories = {
        "storage": storage_dir,
        "uploads": upload_dir,
        "results": result_dir,
        "temp": temp_dir
    }
    
    all_exist = True
    for name, path in directories.items():
        if os.path.exists(path):
            # Check if directory is writable
            if os.access(path, os.W_OK):
                log(f"✅ Directory '{name}' exists and is writable: {path}")
                
                # Count files in directory
                files = os.listdir(path)
                log(f"   - Contains {len(files)} files")
            else:
                log(f"❌ Directory '{name}' exists but is NOT writable: {path}")
                all_exist = False
        else:
            log(f"❌ Directory '{name}' does NOT exist: {path}")
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """Check for required environment variables"""
    log("Checking environment variables...")
    
    # Key environment variables
    variables = {
        "TESSERACT_PATH": os.environ.get("TESSERACT_PATH"),
        "POPPLER_PATH": os.environ.get("POPPLER_PATH")
    }
    
    all_valid = True
    for name, value in variables.items():
        if value:
            if name.endswith("PATH") and not os.path.exists(value):
                log(f"❌ Environment variable {name} points to non-existent path: {value}")
                all_valid = False
            else:
                log(f"✅ Environment variable {name} is set: {value}")
        else:
            log(f"⚠️ Environment variable {name} is not set")
    
    return all_valid

def check_dependencies():
    """Check if required packages are installed"""
    log("Checking Python dependencies...")
    
    dependencies = {
        "fastapi": "For API server",
        "uvicorn": "For running the server",
        "pytesseract": "For OCR processing",
        "pdf2image": "For PDF processing",
        "Pillow": "For image processing",
        "numpy": "For numerical operations",
        "reportlab": "For PDF generation",
        "httpx": "For HTTP requests",
        "aiofiles": "For async file operations",
        "python-multipart": "For file uploads"
    }
    
    all_installed = True
    for package, purpose in dependencies.items():
        try:
            __import__(package)
            log(f"✅ {package} is installed ({purpose})")
        except ImportError:
            log(f"❌ {package} is NOT installed ({purpose})")
            all_installed = False
    
    return all_installed

def create_test_files():
    """Create test files for uploading"""
    log("Creating test files...")
    
    # Create a simple test image
    if not os.path.exists(TEST_IMAGE_PATH):
        try:
            log(f"Creating test image: {TEST_IMAGE_PATH}")
            img = Image.new('RGB', (500, 500), color='white')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            draw.text((100, 100), "Test Image", fill="black", font=font)
            img.save(TEST_IMAGE_PATH)
            log(f"✅ Test image created: {TEST_IMAGE_PATH}")
        except Exception as e:
            log(f"❌ Failed to create test image: {e}")
            return False
    else:
        log(f"✅ Test image already exists: {TEST_IMAGE_PATH}")
    
    # Create a test PDF
    if not os.path.exists(TEST_PDF_PATH):
        try:
            log(f"Creating test PDF: {TEST_PDF_PATH}")
            try:
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(TEST_PDF_PATH)
                c.drawString(100, 750, "Test PDF")
                c.save()
                log(f"✅ Test PDF created: {TEST_PDF_PATH}")
            except Exception as e:
                log(f"❌ Failed to create PDF: {e}")
                return False
        except Exception as e:
            log(f"❌ Failed to create test PDF: {e}")
            return False
    else:
        log(f"✅ Test PDF already exists: {TEST_PDF_PATH}")
    
    return True

def test_file_upload(file_path, content_type):
    """Test uploading a file and monitor the process"""
    log(f"\nTesting upload of {file_path} ({content_type})...")
    
    if not os.path.exists(file_path):
        log(f"❌ Test file not found: {file_path}")
        return False
    
    try:
        file_stats = os.stat(file_path)
        log(f"File size: {file_stats.st_size} bytes")
        
        # Check if file is readable
        with open(file_path, 'rb') as f:
            sample = f.read(100)  # Read first 100 bytes
            log(f"✅ File is readable, first bytes: {sample[:10]}")
        
        # Prepare the multipart form data
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb'), content_type)
        }
        
        data = {
            'source_language': 'Japanese',
            'target_language': 'English'
        }
        
        # Log the request details
        log(f"Making POST request to {API_URL}/upload")
        log(f"Files: {files['file'][0]}")
        log(f"Data: {data}")
        
        # Make the request with debug info
        log("Sending request...")
        
        # Run a detailed test to find where it fails
        try:
            # Step 1: Open file for reading
            log("Step 1: Open file for reading")
            with open(file_path, 'rb') as file_obj:
                file_content = file_obj.read()
                log(f"   ✅ File read successfully: {len(file_content)} bytes")
                
                # Step 2: Prepare request data
                log("Step 2: Prepare request data")
                import io
                file_obj = io.BytesIO(file_content)
                files = {
                    'file': (os.path.basename(file_path), file_obj, content_type)
                }
                log(f"   ✅ Request data prepared")
                
                # Step 3: Send the request with a longer timeout
                log("Step 3: Send the request")
                response = requests.post(
                    f"{API_URL}/upload", 
                    files=files, 
                    data=data,
                    timeout=30  # Increase timeout to 30 seconds
                )
                log(f"   ✅ Request sent, status code: {response.status_code}")
                
                # Step 4: Check response
                log("Step 4: Check response")
                if response.status_code == 200:
                    log(f"   ✅ Response received: {response.text}")
                    
                    # Parse response
                    job_data = response.json()
                    job_id = job_data.get('job_id')
                    log(f"✅ Upload successful! Job ID: {job_id}")
                    
                    # Monitor job status
                    log("\nMonitoring job status...")
                    for i in range(10):  # Check status 10 times
                        try:
                            status_response = requests.get(f"{API_URL}/job/{job_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                log(f"Status: {status_data.get('status')}, Progress: {status_data.get('progress')}%")
                                
                                # If job completed or failed, stop checking
                                if status_data.get('status') in ('completed', 'failed'):
                                    if status_data.get('status') == 'completed':
                                        log(f"✅ Job completed successfully")
                                    else:
                                        log(f"❌ Job failed: {status_data.get('error')}")
                                    break
                            else:
                                log(f"❌ Failed to get job status: {status_response.status_code}")
                                break
                        except Exception as e:
                            log(f"❌ Error checking job status: {e}")
                            break
                        
                        # Wait before checking again
                        import time
                        time.sleep(2)
                    
                    return True
                else:
                    log(f"   ❌ Error response: {response.status_code}, {response.text}")
                    return False
                
        except Exception as e:
            log(f"❌ Request failed at some stage: {e}")
            import traceback
            log(traceback.format_exc())
            return False
            
    except Exception as e:
        log(f"❌ Error during upload test: {e}")
        import traceback
        log(traceback.format_exc())
        return False

def check_backend_logs():
    """Check backend server logs if available"""
    log("\nLooking for backend logs...")
    
    # Common log file locations
    log_paths = [
        "backend/app.log",
        "backend/logs/app.log",
        "logs/backend.log",
        "app.log"
    ]
    
    found = False
    for path in log_paths:
        if os.path.exists(path):
            log(f"Found log file: {path}")
            try:
                # Get last 20 lines
                with open(path, 'r') as f:
                    lines = f.readlines()
                    log(f"Last {min(20, len(lines))} lines of log:")
                    for line in lines[-20:]:
                        log(f"  {line.strip()}")
                found = True
            except Exception as e:
                log(f"Error reading log file: {e}")
    
    if not found:
        log("No log files found in common locations")

def main():
    """Run all checks"""
    log("=== Manga Translator Upload Diagnostics ===")
    
    # Check API connection
    api_ok = check_api_connection()
    if not api_ok:
        log("\n❌ CRITICAL: Cannot connect to API. Make sure the backend server is running.")
        return
    
    # Check storage directories
    storage_ok = check_storage_directories()
    if not storage_ok:
        log("\n⚠️ WARNING: Storage directory issues detected. This may cause upload failures.")
    
    # Check environment variables
    env_ok = check_environment_variables()
    if not env_ok:
        log("\n⚠️ WARNING: Environment variable issues detected. OCR or PDF processing may fail.")
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        log("\n⚠️ WARNING: Missing dependencies detected. Some features may not work.")
    
    # Create test files
    files_ok = create_test_files()
    if not files_ok:
        log("\n❌ CRITICAL: Failed to create test files. Cannot proceed with upload tests.")
        return
    
    # Test image upload
    log("\n=== IMAGE UPLOAD TEST ===")
    image_ok = test_file_upload(TEST_IMAGE_PATH, "image/jpeg")
    
    # Test PDF upload
    log("\n=== PDF UPLOAD TEST ===")
    pdf_ok = test_file_upload(TEST_PDF_PATH, "application/pdf")
    
    # Check backend logs if tests failed
    if not (image_ok and pdf_ok):
        check_backend_logs()
    
    # Summary
    log("\n=== DIAGNOSTICS SUMMARY ===")
    log(f"API Connection:      {'✅ OK' if api_ok else '❌ FAILED'}")
    log(f"Storage Directories: {'✅ OK' if storage_ok else '⚠️ WARNING'}")
    log(f"Environment Vars:    {'✅ OK' if env_ok else '⚠️ WARNING'}")
    log(f"Dependencies:        {'✅ OK' if deps_ok else '⚠️ WARNING'}")
    log(f"Image Upload:        {'✅ OK' if image_ok else '❌ FAILED'}")
    log(f"PDF Upload:          {'✅ OK' if pdf_ok else '❌ FAILED'}")
    
    if not (image_ok and pdf_ok):
        log("\n🔎 TROUBLESHOOTING SUGGESTIONS:")
        log("1. Make sure the backend server is running")
        log("2. Check backend server logs for errors")
        log("3. Verify storage directories exist and are writable")
        log("4. Confirm Tesseract and Poppler are correctly installed")
        log("5. Check that TESSERACT_PATH and POPPLER_PATH environment variables are correctly set")
        log("6. Try creating a new test file with smaller file size")
        log("7. Check if any antivirus or firewall is blocking the connection")
        log("8. Make sure frontend is calling the correct API URL")

if __name__ == "__main__":
    main() 
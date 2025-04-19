import os
import requests
from PIL import Image
import tempfile
import time

# Test configuration
API_URL = "http://localhost:8000"  # Base URL for the API
TEST_IMAGE_PATH = "test_image.jpg"  # Path to a test image
TEST_PDF_PATH = "test_pdf.pdf"     # Path to a test PDF

def create_test_files():
    """Create test files for upload if they don't exist"""
    # Create a simple test image
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Creating test image: {TEST_IMAGE_PATH}")
        img = Image.new('RGB', (500, 500), color='white')
        # Add some text
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        draw.text((100, 100), "Test Image", fill="black", font=font)
        img.save(TEST_IMAGE_PATH)
    
    # Create a test PDF
    if not os.path.exists(TEST_PDF_PATH):
        print(f"Creating test PDF: {TEST_PDF_PATH}")
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(TEST_PDF_PATH)
            c.drawString(100, 750, "Test PDF")
            c.save()
        except Exception as e:
            print(f"Error creating PDF: {e}")
            print("Please create a test PDF manually for testing")

def test_image_upload():
    """Test uploading an image file"""
    print("\n=== Testing Image Upload ===")
    
    # Check if test file exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    try:
        # Prepare the files and data for the request
        files = {
            'file': (os.path.basename(TEST_IMAGE_PATH), open(TEST_IMAGE_PATH, 'rb'), 'image/jpeg')
        }
        data = {
            'source_language': 'Japanese',
            'target_language': 'English'
        }
        
        # Make the request
        print(f"Uploading {TEST_IMAGE_PATH} to {API_URL}/upload")
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
        
        # Check the response
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get('job_id')
            print(f"Upload successful! Job ID: {job_id}")
            
            # Monitor the job status
            monitor_job(job_id)
            return True
        else:
            print(f"Upload failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error during image upload test: {e}")
        return False

def test_pdf_upload():
    """Test uploading a PDF file"""
    print("\n=== Testing PDF Upload ===")
    
    # Check if test file exists
    if not os.path.exists(TEST_PDF_PATH):
        print(f"Test PDF not found: {TEST_PDF_PATH}")
        return False
    
    try:
        # Prepare the files and data for the request
        files = {
            'file': (os.path.basename(TEST_PDF_PATH), open(TEST_PDF_PATH, 'rb'), 'application/pdf')
        }
        data = {
            'source_language': 'Japanese',
            'target_language': 'English'
        }
        
        # Make the request
        print(f"Uploading {TEST_PDF_PATH} to {API_URL}/upload")
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
        
        # Check the response
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get('job_id')
            print(f"Upload successful! Job ID: {job_id}")
            
            # Monitor the job status
            monitor_job(job_id)
            return True
        else:
            print(f"Upload failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error during PDF upload test: {e}")
        return False

def monitor_job(job_id, max_attempts=30, delay=2):
    """Monitor the status of a job"""
    print(f"Monitoring job: {job_id}")
    
    for i in range(max_attempts):
        try:
            # Get job status
            response = requests.get(f"{API_URL}/job/{job_id}")
            
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get('status')
                progress = job_data.get('progress')
                
                print(f"Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    print("Job completed successfully!")
                    result_file = job_data.get('result_file')
                    if result_file:
                        print(f"Result file: {result_file}")
                    return True
                elif status == 'failed':
                    error = job_data.get('error')
                    print(f"Job failed: {error}")
                    return False
                
                # Wait before checking again
                time.sleep(delay)
            else:
                print(f"Failed to get job status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error monitoring job: {e}")
            return False
    
    print(f"Timeout waiting for job completion after {max_attempts * delay} seconds")
    return False

def main():
    """Main test function"""
    print("=== Manga Translator Upload Test ===")
    
    # Create test files if needed
    create_test_files()
    
    # Test API connection
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            print(f"API is running at {API_URL}")
        else:
            print(f"API returned status code: {response.status_code}")
            print("Please make sure the backend server is running")
            return
    except Exception as e:
        print(f"Failed to connect to API: {e}")
        print("Please make sure the backend server is running")
        return
    
    # Test image upload
    image_success = test_image_upload()
    
    # Test PDF upload
    pdf_success = test_pdf_upload()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Image upload test: {'SUCCESS' if image_success else 'FAILED'}")
    print(f"PDF upload test: {'SUCCESS' if pdf_success else 'FAILED'}")

if __name__ == "__main__":
    main() 
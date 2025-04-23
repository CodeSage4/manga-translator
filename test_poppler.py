import os
import sys
from pdf2image import convert_from_path
import tempfile

def test_poppler():
    """Test if Poppler is available for PDF processing"""
    print("PDF2Image Test Script")
    print("====================")
    
    # Check if poppler is in PATH or needs to be specified
    poppler_path = None
    
    # Common poppler installation locations on Windows
    possible_paths = [
        r"C:\Program Files\poppler\bin",
        r"C:\poppler\bin",
        r"C:\Users\Lenovo\AppData\Local\Programs\poppler\bin"
    ]
    
    # Check if any of these paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found potential Poppler path: {path}")
            poppler_path = path
            break
    
    if not poppler_path:
        print("Poppler path not found in common locations!")
        print("You may need to download and install Poppler for Windows.")
        print("Get it from: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("\nAfter installing, add the following to your backend/.env file:")
        print("POPPLER_PATH=C:\\path\\to\\poppler\\bin")
        return False
    
    # Try to use pdf2image with the detected poppler path
    try:
        # Create a temporary PDF file for testing
        temp_pdf = os.path.join(tempfile.gettempdir(), "test.pdf")
        
        # Check if we need to create a test PDF
        if not os.path.exists(temp_pdf):
            print("Creating a test PDF file...")
            try:
                from reportlab.pdfgen import canvas
                
                c = canvas.Canvas(temp_pdf)
                c.drawString(100, 750, "Test PDF for Poppler")
                c.save()
                print(f"Test PDF created at: {temp_pdf}")
            except Exception as e:
                print(f"Could not create test PDF: {e}")
                print("Will try to use pdf2image anyway...")
        
        print(f"\nTesting PDF2Image with Poppler path: {poppler_path}")
        # Try to convert the PDF to images
        if os.path.exists(temp_pdf):
            images = convert_from_path(temp_pdf, poppler_path=poppler_path)
            print(f"Success! Converted PDF to {len(images)} image(s).")
            
            # Update the .env file
            env_path = os.path.join("backend", ".env")
            if os.path.exists(env_path):
                # Escape backslashes for the .env file
                escaped_path = poppler_path.replace("\\", "\\\\")
                
                # Read the current content
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading .env file: {e}")
                    return False
                
                # Update or add the Poppler path
                if "POPPLER_PATH=" in content:
                    # Replace existing line
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        if line.strip().startswith("POPPLER_PATH="):
                            new_lines.append(f"POPPLER_PATH={escaped_path}")
                        else:
                            new_lines.append(line)
                    
                    # Write back the updated content
                    try:
                        with open(env_path, 'w') as f:
                            f.write('\n'.join(new_lines))
                    except Exception as e:
                        print(f"Error writing to .env file: {e}")
                        return False
                else:
                    # Add new line
                    try:
                        with open(env_path, 'a') as f:
                            f.write(f"\nPOPPLER_PATH={escaped_path}\n")
                    except Exception as e:
                        print(f"Error appending to .env file: {e}")
                        return False
                
                print(f"Updated .env file with Poppler path: {escaped_path}")
            
            return True
        else:
            print(f"Test PDF file not found at {temp_pdf}")
            return False
    except Exception as e:
        print(f"Error testing pdf2image: {e}")
        print("\nYou need to install Poppler for Windows:")
        print("1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract to a directory (e.g. C:\\poppler)")
        print("3. Add the bin directory to your PATH or set POPPLER_PATH in the .env file")
        return False

if __name__ == "__main__":
    success = test_poppler()
    
    if success:
        print("\nPoppler is correctly configured!")
        print("PDF processing in your Manga Translator should now work properly.")
    else:
        print("\nPoppler configuration issue detected.")
        print("Please install Poppler and configure the path.")
    
    input("\nPress Enter to exit...")
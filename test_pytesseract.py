import os
import sys
import pytesseract
from PIL import Image

# Try different possible Tesseract installation paths
possible_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
    r"C:\Users\Lenovo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    # Add your custom path here if you installed it elsewhere
]

def find_tesseract():
    """Try to find the Tesseract executable"""
    print("Looking for Tesseract executable...")
    
    # Check if user has specified the path in environment variable
    env_path = os.environ.get('TESSERACT_PATH')
    if env_path and os.path.exists(env_path):
        print(f"Found Tesseract via environment variable: {env_path}")
        return env_path
    
    # Try all possible paths
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found Tesseract at: {path}")
            return path
    
    # Prompt user for custom path
    print("Tesseract not found in standard locations.")
    custom_path = input("Please enter the full path to tesseract.exe (or press Enter to skip): ")
    
    if custom_path and os.path.exists(custom_path):
        print(f"Found Tesseract at custom path: {custom_path}")
        return custom_path
    
    return None

def test_tesseract(path):
    """Test if Tesseract is working"""
    if not path:
        print("No Tesseract path provided. Cannot test.")
        return False
    
    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = path
    
    try:
        # Get version
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract is working! Version: {version}")
        
        # Update the .env file
        env_path = os.path.join("backend", ".env")
        if os.path.exists(env_path):
            # Escape backslashes for the .env file
            escaped_path = path.replace("\\", "\\\\")
            
            # Read the current content
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Update or add the Tesseract path
            if "TESSERACT_PATH=" in content:
                # Replace existing line
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if line.strip().startswith("TESSERACT_PATH="):
                        new_lines.append(f"TESSERACT_PATH={escaped_path}")
                    elif line.strip().startswith("#TESSERACT_PATH="):
                        continue  # Skip commented paths
                    else:
                        new_lines.append(line)
                
                # Write back the updated content
                with open(env_path, 'w') as f:
                    f.write('\n'.join(new_lines))
            else:
                # Add new line
                with open(env_path, 'a') as f:
                    f.write(f"\nTESSERACT_PATH={escaped_path}\n")
            
            print(f"Updated .env file with Tesseract path: {escaped_path}")
        
        return True
    except Exception as e:
        print(f"Error testing Tesseract: {e}")
        return False

if __name__ == "__main__":
    print("Tesseract OCR Test Script")
    print("=========================")
    
    # Find Tesseract
    tesseract_path = find_tesseract()
    
    if tesseract_path:
        # Test Tesseract
        if test_tesseract(tesseract_path):
            print("\nTesseract is correctly configured!")
            print("OCR functionality in your Manga Translator should now work properly.")
        else:
            print("\nFailed to verify Tesseract functionality.")
            print("Make sure Tesseract is correctly installed.")
    else:
        print("\nCould not find Tesseract executable.")
        print("Please download and install Tesseract from:")
        print("https://github.com/UB-Mannheim/tesseract/releases/")
    
    input("\nPress Enter to exit...") 
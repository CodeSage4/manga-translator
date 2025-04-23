import subprocess
import sys
from pathlib import Path
import os

def start_backend():
    """Start the backend server with proper environment setup"""
    backend_dir = Path(__file__).parent / "backend"
    
    # Ensure we're in the backend directory
    os.chdir(backend_dir)
    
    # Start the server on port 8080
    subprocess.run([
        sys.executable, 
        "-m", "uvicorn", 
        "app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8080"
    ])

if __name__ == "__main__":
    start_backend()
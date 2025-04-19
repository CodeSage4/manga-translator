from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import time
from typing import Dict, Any

app = FastAPI()

# Print debugging info
print("Configuring CORS to allow all origins")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# In-memory job storage
jobs = {}

# Job progress simulator
def simulate_progress(job_id: str):
    """Simulate job progress in the background"""
    import threading
    
    def update_progress():
        for progress in range(0, 101, 10):
            jobs[job_id]["progress"] = progress
            jobs[job_id]["status"] = "processing" if progress < 100 else "completed"
            time.sleep(1)  # Simulate processing time
    
    # Start progress simulation in a background thread
    thread = threading.Thread(target=update_progress)
    thread.daemon = True
    thread.start()

@app.get("/")
async def root():
    return {"message": "API is working!"}

@app.get("/languages")
async def get_languages():
    """Return supported languages"""
    print("Languages endpoint called")
    return {
        "Japanese": ["English", "Spanish", "French", "German"],
        "Chinese": ["English", "Spanish", "French", "German"],
        "Korean": ["English", "Spanish", "French", "German"],
        "English": ["Japanese", "Chinese", "Spanish", "French", "German"]
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_language: str = Form("Japanese"),
    target_language: str = Form("English")
):
    """Handle file upload and start processing"""
    content = await file.read()
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Store job information
    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "status": "queued",
        "progress": 0,
        "file_size": len(content),
        "source_language": source_language,
        "target_language": target_language
    }
    
    # Start progress simulation
    simulate_progress(job_id)
    
    return {
        "job_id": job_id,
        "status": "queued"
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    if job_id not in jobs:
        return {
            "job_id": job_id,
            "status": "not_found",
            "progress": 0,
            "error": "Job not found"
        }
    
    job = jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"]
    }
    
    # Add result URL if job is completed
    if job["status"] == "completed":
        response["result"] = f"/download/{job_id}"
    
    return response

@app.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download processed file"""
    if job_id not in jobs:
        return {"error": "Job not found"}
    
    return {
        "message": "This is a placeholder for the actual file download",
        "job_id": job_id,
        "filename": jobs[job_id]["filename"]
    }

if __name__ == "__main__":
    # Use a fixed port for consistency
    PORT = 8001
    HOST = "0.0.0.0"
    
    print("Starting minimal test API server...")
    print(f"API will be available at http://localhost:{PORT}")
    print("Also try accessing via:")
    print(f"1. http://127.0.0.1:{PORT}")
    print(f"2. http://{HOST}:{PORT}")
    print("\nFrontend should use this URL (check frontend/src/services/api.ts):")
    print(f"const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:{PORT}';")
    print("\nProgress bar should now work correctly!")
    uvicorn.run(app, host=HOST, port=PORT) 
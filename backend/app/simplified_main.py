import os
import tempfile
import uuid
import shutil
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import asyncio

# Try to import the enhanced processing module
try:
    from app.enhanced_processing import create_translator
    ENHANCED_PROCESSING = True
except ImportError:
    try:
        # For local development
        from enhanced_processing import create_translator
        ENHANCED_PROCESSING = True
    except ImportError:
        ENHANCED_PROCESSING = False
        # Fallback to simple processing
        try:
            from app.simple_processing import process_manga_image
        except ImportError:
            # For local development
            from simple_processing import process_manga_image

# Set up the FastAPI app
app = FastAPI(title="Manga Translator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up directories
TEMP_DIR = os.path.join(tempfile.gettempdir(), "manga_translator")
os.makedirs(TEMP_DIR, exist_ok=True)

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
RESULT_DIR = os.path.join(STORAGE_DIR, "results")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Constants
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
SUPPORTED_LANGUAGES = {
    "Japanese": ["English", "Spanish", "French", "German"],
    "Chinese": ["English", "Spanish", "French", "German"],
    "Korean": ["English", "Spanish", "French", "German"],
    "English": ["Japanese", "Chinese", "Spanish", "French", "German"]
}

# In-memory job storage
jobs: Dict[str, Dict[str, Any]] = {}

# Models
class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    result_file: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Manga Translator API is running"}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_language: str = "Japanese",
    target_language: str = "English",
    background_tasks: BackgroundTasks = None
):
    try:
        print(f"Upload requested: Filename={file.filename}, Source={source_language}, Target={target_language}")
        
        # Validate file extension
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            error_msg = f"File format not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            print(f"Upload error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate languages
        if source_language not in SUPPORTED_LANGUAGES:
            error_msg = f"Source language not supported. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            print(f"Upload error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if target_language not in SUPPORTED_LANGUAGES.get(source_language, []):
            error_msg = f"Target language not supported for {source_language}. Supported target languages: {', '.join(SUPPORTED_LANGUAGES.get(source_language, []))}"
            print(f"Upload error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generate job ID and paths
        job_id = str(uuid.uuid4())
        upload_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        
        # Determine result filename and path based on file type
        if file_extension == "pdf":
            result_filename = f"{job_id}_translated.pdf"
        else:
            result_filename = f"{job_id}_translated.png"
        
        result_path = os.path.join(RESULT_DIR, result_filename)
        
        print(f"File will be saved to: {upload_path}")
        print(f"Result will be saved to: {result_path}")
        
        # Verify directories exist
        if not os.path.exists(UPLOAD_DIR):
            print(f"Creating upload directory: {UPLOAD_DIR}")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        if not os.path.exists(RESULT_DIR):
            print(f"Creating result directory: {RESULT_DIR}")
            os.makedirs(RESULT_DIR, exist_ok=True)
        
        # Save the uploaded file
        try:
            content = await file.read()
            with open(upload_path, "wb") as f:
                f.write(content)
            print(f"File saved successfully, size: {len(content)} bytes")
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            print(f"Upload error: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        finally:
            # Reset file cursor for potential further reads
            await file.seek(0)
        
        # Create job entry
        jobs[job_id] = {
            "id": job_id,
            "filename": file.filename,
            "status": "queued",
            "progress": 0,
            "upload_path": upload_path,
            "result_path": result_path,
            "result_filename": result_filename,
            "source_language": source_language,
            "target_language": target_language,
            "error": None
        }
        
        print(f"Job created: {job_id}")
        
        # Start processing in background
        if background_tasks is None:
            print("ERROR: No background_tasks object provided")
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        background_tasks.add_task(
            process_file, job_id, upload_path, result_path, source_language, target_language, file_extension
        )
        
        print(f"Background task added for job: {job_id}")
        
        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            status="queued"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_details = f"Unexpected error during upload: {str(e)}"
        print(error_details)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_details)

async def process_file(job_id, upload_path, result_path, source_language, target_language, file_extension):
    """Process an uploaded file with OCR and translation"""
    print(f"Starting processing for job: {job_id}")
    print(f"Input: {upload_path}, Output: {result_path}")
    print(f"Languages: {source_language} -> {target_language}")
    print(f"File extension: {file_extension}")
    
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        print(f"Job status updated to: processing")
        
        # Create translator
        if ENHANCED_PROCESSING:
            print(f"Using enhanced processing (simulation={not ENHANCED_PROCESSING})")
            translator = create_translator(use_simulation=not ENHANCED_PROCESSING)
        else:
            print("Enhanced processing not available, falling back to simple processing")
        
        # Update progress - 25%
        jobs[job_id]["progress"] = 25
        print(f"Progress updated to: 25%")
        await asyncio.sleep(0.5)  # Small delay to simulate work
            
        # Process file based on type
        success = False
        
        if file_extension == "pdf":
            print(f"Processing PDF file")
            if ENHANCED_PROCESSING:
                # Use enhanced processing for PDF
                print(f"Using enhanced processing for PDF")
                try:
                    success = translator.process_pdf(upload_path, result_path, source_language, target_language)
                    print(f"PDF processing result: {success}")
                except Exception as e:
                    print(f"Error in PDF processing: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    raise
            else:
                # Fallback if enhanced processing not available
                print(f"Enhanced processing not available, copying PDF as-is")
                # Just copy the file as we can't process PDFs without pdf2image
                shutil.copy(upload_path, result_path)
                success = True
        else:
            # Process image
            print(f"Processing image file")
            try:
                if ENHANCED_PROCESSING:
                    print(f"Using enhanced processing for image")
                    success = translator.process_manga_image(upload_path, result_path, source_language, target_language)
                else:
                    print(f"Using simple processing for image")
                    success = process_manga_image(upload_path, result_path, source_language, target_language)
                print(f"Image processing result: {success}")
            except Exception as e:
                print(f"Error in image processing: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise
        
        # Update progress - 90%
        jobs[job_id]["progress"] = 90
        print(f"Progress updated to: 90%")
        await asyncio.sleep(0.5)  # Small delay to simulate work
        
        # Update job status based on process result
        if success:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            print(f"Job completed successfully: {job_id}")
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Processing failed"
            print(f"Job failed (processing error): {job_id}")
    
    except Exception as e:
        # Handle any exceptions
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"Job failed (exception): {job_id}")
        print(f"Error details: {str(e)}")
        import traceback
        print(traceback.format_exc())

@app.get("/job/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Get the status of a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return JobStatus(
        job_id=job["id"],
        status=job["status"],
        progress=job["progress"],
        result_file=job["result_filename"] if job["status"] == "completed" else None,
        error=job["error"]
    )

@app.get("/download/{job_id}")
def download_result(job_id: str):
    """Download the result of a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    result_path = job["result_path"]
    
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        path=result_path,
        filename=job["result_filename"],
        media_type="application/octet-stream"
    )

@app.get("/languages", response_model=Dict[str, List[str]])
def get_languages():
    """Get the list of supported languages"""
    return SUPPORTED_LANGUAGES

# For development testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simplified_main:app", host="0.0.0.0", port=8000, reload=True) 
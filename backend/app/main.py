import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.core.config import settings
from app.core.database import get_db, Base, engine
from app.models.job import Job, JobStatus
from app.services.storage import storage_service
from app.tasks import process_manga

# Create tables
Base.metadata.create_all(bind=engine)

# Create temp directory
os.makedirs(settings.TEMP_DIR, exist_ok=True)

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; adjust as needed for security
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

@app.post(f"{settings.API_V1_STR}/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_language: str = settings.DEFAULT_SOURCE_LANGUAGE,
    target_language: str = settings.DEFAULT_TARGET_LANGUAGE,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload a manga file (image or PDF) for translation
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension {file_ext} not allowed")
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Save the file to storage
    file_path = await storage_service.save_upload(file, job_id)
    
    # Create a new job in the database
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        progress=0,
        source_language=source_language,
        target_language=target_language,
        original_filename=file.filename,
        original_file_path=file_path
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start processing in the background
    process_manga.delay(job_id)
    
    return {
        "jobId": job_id,
        "status": "pending"
    }

@app.get(f"{settings.API_V1_STR}/status/{{job_id}}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a processing job
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "jobId": job.id,
        "status": job.status.value,
        "progress": job.progress
    }
    
    # If the job is completed, add the result URL
    if job.status == JobStatus.COMPLETED and job.result_file_path:
        response["result"] = await storage_service.get_download_url(job.result_file_path)
    
    # If the job failed, add the error message
    if job.status == JobStatus.FAILED:
        response["error"] = job.error_message
    
    return response

@app.get(f"{settings.API_V1_STR}/download/{{job_id}}")
async def download_result(job_id: str, db: Session = Depends(get_db)):
    """
    Download a processed file
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job is not completed")
    
    if not job.result_file_path:
        raise HTTPException(status_code=404, detail="Result file not found")
    
    # For local storage, serve the file directly
    if settings.STORAGE_TYPE == "local":
        file_path = job.result_file_path
        return FileResponse(
            path=file_path,
            filename=f"translated_{job.original_filename}",
            media_type="application/octet-stream"
        )
    else:
        # For cloud storage, redirect to the download URL
        download_url = await storage_service.get_download_url(job.result_file_path)
        return {"download_url": download_url}

@app.get(f"{settings.API_V1_STR}/languages")
async def get_languages():
    """
    Get a list of supported languages
    """
    return settings.SUPPORTED_LANGUAGES

@app.on_event("startup")
async def startup_event():
    """
    Perform startup tasks
    """
    # Ensure storage directories exist
    if settings.STORAGE_TYPE == "local":
        os.makedirs(os.path.join(settings.LOCAL_STORAGE_PATH, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(settings.LOCAL_STORAGE_PATH, "results"), exist_ok=True)
    
    # Create temp directory
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform shutdown tasks
    """
    pass 
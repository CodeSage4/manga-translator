import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from app.config import settings
from app.core.database import get_db, Base, engine
from app.models.job import Job, JobStatus
from app.services.storage import storage_service
#from app.tasks import process_manga
from app.api.endpoints import manga, translation
from app.core.easyocr import OCRProcessor  # Update import path

# Create required directories
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.TEMP_DIR.mkdir(exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
#app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(manga.router, prefix=settings.API_V1_STR)
app.include_router(translation.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Manga Translator API"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)}
    )

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
    settings.TEMP_DIR.mkdir(exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform shutdown tasks
    """
    pass

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
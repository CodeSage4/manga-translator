import os
import uuid
from typing import List, Dict
from celery import chain
from sqlalchemy.orm import Session
from pdf2image import convert_from_path

from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.services.ocr import ocr_service
from app.services.translation import translation_service
from app.services.rendering import rendering_service
from app.services.storage import storage_service

@celery_app.task(name="app.tasks.ocr_task")
def ocr_task(job_id: str) -> dict:
    """Process OCR on the uploaded file"""
    # Get database session
    db = SessionLocal()
    try:
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update job status
        job.status = JobStatus.PROCESSING
        job.progress = 10
        db.commit()
        
        # Create temp directory
        temp_dir = os.path.join(settings.TEMP_DIR, job_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download file from storage to temp directory
        local_file_path = storage_service.get_file(job.original_file_path, 
                                                  os.path.join(temp_dir, os.path.basename(job.original_file_path)))
        
        # Check file extension
        file_ext = os.path.splitext(job.original_filename)[1].lower()
        
        # Process the file
        if file_ext == '.pdf':
            ocr_results = ocr_service.process_pdf(local_file_path, job.source_language, temp_dir)
            # Save the PDF pages as images for later use
            pdf_images = []
            pages = convert_from_path(local_file_path, output_folder=temp_dir)
            for i, page in enumerate(pages):
                img_path = os.path.join(temp_dir, f"page_{i}.jpg")
                page.save(img_path, "JPEG")
                pdf_images.append(img_path)
            
            # Store PDF data in result
            result = {
                "job_id": job_id,
                "ocr_results": ocr_results,
                "is_pdf": True,
                "pdf_images": pdf_images
            }
        else:
            # Process as a single image
            ocr_results = ocr_service.process_image(local_file_path, job.source_language)
            result = {
                "job_id": job_id,
                "ocr_results": ocr_results,
                "is_pdf": False,
                "image_path": local_file_path
            }
        
        # Update job progress
        job.progress = 40
        db.commit()
        
        return result
    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@celery_app.task(name="app.tasks.translation_task")
def translation_task(ocr_result: dict) -> dict:
    """Translate extracted text"""
    job_id = ocr_result["job_id"]
    db = SessionLocal()
    try:
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update job progress
        job.progress = 50
        db.commit()
        
        # Translate the OCR results
        if ocr_result["is_pdf"]:
            # Process each page of the PDF
            translated_results = []
            for page_results in ocr_result["ocr_results"]:
                translated_page = translation_service.translate_ocr_results(
                    page_results, job.source_language, job.target_language
                )
                translated_results.append(translated_page)
        else:
            # Process a single image
            translated_results = translation_service.translate_ocr_results(
                ocr_result["ocr_results"], job.source_language, job.target_language
            )
        
        # Update results with translations
        result = ocr_result.copy()
        result["translated_results"] = translated_results
        
        # Update job progress
        job.progress = 70
        db.commit()
        
        return result
    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@celery_app.task(name="app.tasks.rendering_task")
def rendering_task(translation_result: dict) -> dict:
    """Render translated text onto the original image or PDF"""
    job_id = translation_result["job_id"]
    db = SessionLocal()
    try:
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update job progress
        job.progress = 80
        db.commit()
        
        # Create output directory if it doesn't exist
        temp_dir = os.path.join(settings.TEMP_DIR, job_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Render the translated text
        if translation_result["is_pdf"]:
            # Process each page of the PDF
            output_path = rendering_service.render_text_on_pdf(
                translation_result["pdf_images"],
                translation_result["translated_results"],
                temp_dir,
                job_id
            )
            file_ext = "pdf"
        else:
            # Process a single image
            output_path = os.path.join(temp_dir, f"{job_id}_translated.jpg")
            rendering_service.render_text_on_image(
                translation_result["image_path"],
                translation_result["translated_results"],
                output_path
            )
            file_ext = "jpg"
        
        # Save the result to storage
        result_path = storage_service.save_result(output_path, job_id, file_ext)
        
        # Update job status
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result_file_path = result_path
        db.commit()
        
        # Get download URL
        download_url = storage_service.get_download_url(result_path)
        
        return {
            "job_id": job_id,
            "result_path": result_path,
            "download_url": download_url
        }
    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@celery_app.task(name="app.tasks.process_manga")
def process_manga(job_id: str) -> dict:
    """Chain OCR, translation, and rendering tasks"""
    return chain(
        ocr_task.s(job_id),
        translation_task.s(),
        rendering_task.s()
    )() 
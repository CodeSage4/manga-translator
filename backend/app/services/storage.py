import os
import shutil
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import settings

class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        
        if self.storage_type == "local":
            os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
            os.makedirs(os.path.join(settings.LOCAL_STORAGE_PATH, "uploads"), exist_ok=True)
            os.makedirs(os.path.join(settings.LOCAL_STORAGE_PATH, "results"), exist_ok=True)
        
        elif self.storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
    
    async def save_upload(self, file: UploadFile, job_id: str) -> str:
        """Save an uploaded file and return the path where it was saved"""
        file_extension = file.filename.split(".")[-1].lower()
        filename = f"{job_id}.{file_extension}"
        
        if self.storage_type == "local":
            file_path = os.path.join(settings.LOCAL_STORAGE_PATH, "uploads", filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return file_path
            
        elif self.storage_type == "s3":
            s3_key = f"uploads/{filename}"
            try:
                self.s3_client.upload_fileobj(file.file, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
                return s3_key
            except ClientError as e:
                print(f"Error uploading to S3: {e}")
                raise
    
    async def save_result(self, local_file_path: str, job_id: str, file_extension: str) -> str:
        """Save a processed result file and return the path or URL where it was saved"""
        filename = f"{job_id}.{file_extension}"
        
        if self.storage_type == "local":
            result_path = os.path.join(settings.LOCAL_STORAGE_PATH, "results", filename)
            shutil.copy(local_file_path, result_path)
            return result_path
            
        elif self.storage_type == "s3":
            s3_key = f"results/{filename}"
            try:
                self.s3_client.upload_file(local_file_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
                return s3_key
            except ClientError as e:
                print(f"Error uploading result to S3: {e}")
                raise
    
    async def get_file(self, file_path: str, destination: str = None):
        """Get a file from storage and optionally save it to a destination"""
        if self.storage_type == "local":
            if destination:
                shutil.copy(file_path, destination)
                return destination
            return file_path
            
        elif self.storage_type == "s3":
            if not destination:
                destination = os.path.join(settings.TEMP_DIR, os.path.basename(file_path))
            
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            try:
                self.s3_client.download_file(
                    settings.AWS_STORAGE_BUCKET_NAME, 
                    file_path, 
                    destination
                )
                return destination
            except ClientError as e:
                print(f"Error downloading from S3: {e}")
                raise
    
    async def get_download_url(self, file_path: str) -> str:
        """Get a URL for downloading a file"""
        if self.storage_type == "local":
            # For local storage, we'll serve the file through the API
            return f"/api/download/{os.path.basename(file_path).split('.')[0]}"
            
        elif self.storage_type == "s3":
            # Generate a presigned URL
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': file_path
                    },
                    ExpiresIn=3600  # URL expires in 1 hour
                )
                return url
            except ClientError as e:
                print(f"Error generating presigned URL: {e}")
                raise
    
    async def cleanup_old_files(self):
        """Clean up files older than the expiry time"""
        expiry_time = datetime.utcnow() - timedelta(hours=settings.RESULT_EXPIRY_HOURS)
        
        if self.storage_type == "local":
            # Cleanup local files
            for directory in ["uploads", "results"]:
                dir_path = os.path.join(settings.LOCAL_STORAGE_PATH, directory)
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_modified < expiry_time:
                        os.remove(file_path)
                        
        elif self.storage_type == "s3":
            # Cleanup S3 files
            for prefix in ["uploads/", "results/"]:
                response = self.s3_client.list_objects_v2(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < expiry_time:
                            self.s3_client.delete_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=obj['Key']
                            )

storage_service = StorageService() 
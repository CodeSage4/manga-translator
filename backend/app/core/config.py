import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Manga Translator API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend (for Swagger UI)
    ]
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Storage settings
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local", "s3", or "gcp"
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./storage")
    
    # AWS S3 settings (if using S3)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME: str = os.getenv("AWS_STORAGE_BUCKET_NAME", "manga-translator")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./manga_translator.db")
    
    # Translation model settings
    DEFAULT_SOURCE_LANGUAGE: str = "Japanese"
    DEFAULT_TARGET_LANGUAGE: str = "English"
    SUPPORTED_LANGUAGES: list = [
        "Japanese", "English", "Chinese", "Korean", 
        "Spanish", "French", "German", "Russian",
        "Italian", "Portuguese", "Arabic"
    ]
    
    # OCR settings
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", "")  # Path to tesseract executable if not in PATH
    
    # File settings
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "pdf"]
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    RESULT_EXPIRY_HOURS: int = 24  # Hours until processed results are deleted

settings = Settings() 
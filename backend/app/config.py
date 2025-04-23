from pydantic_settings import BaseSettings
from pathlib import Path
import os
from typing import Dict, List, ClassVar

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Manga Translator"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: Path = Path(__file__).parent / "storage"
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    TEMP_DIR: Path = BASE_DIR / "temp"
    OCR_LANGUAGES: List[str] = ["ja", "en"]
    MIN_CONFIDENCE: float = 0.4
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    SUPPORTED_LANGUAGES: ClassVar[Dict[str, str]] = {
        "Japanese": "ja",
        "English": "en",
        "Chinese": "ch_sim",
        "Korean": "ko"
    }
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOAD_DIR, settings.TEMP_DIR, settings.LOCAL_STORAGE_PATH]:
    directory.mkdir(parents=True, exist_ok=True)
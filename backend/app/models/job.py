from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLAlchemyEnum
from app.core.database import Base

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(SQLAlchemyEnum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Float, default=0.0)
    source_language = Column(String)
    target_language = Column(String)
    
    original_filename = Column(String)
    original_file_path = Column(String)
    result_file_path = Column(String, nullable=True)
    
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "jobId": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "sourceLanguage": self.source_language,
            "targetLanguage": self.target_language,
            "originalFilename": self.original_filename,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "errorMessage": self.error_message
        } 
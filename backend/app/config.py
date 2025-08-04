import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Job Matcher AI"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    
    # Scraping Settings
    REQUEST_DELAY: float = 1.0  # Delay between requests
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    # Skills Database
    SKILLS_MODEL_PATH: str = "models/skills_model"
    
    # Job Matching Settings
    MIN_MATCH_SCORE: float = 0.3
    MAX_JOBS_PER_PLATFORM: int = 10
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    skills: List[str]
    match_score: float = Field(..., ge=0, le=100, description="Match percentage with user skills")
    posted_date: str
    source: str
    url: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class SkillsResponse(BaseModel):
    skills: List[str]
    total_count: int = Field(default_factory=lambda: 0)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_count = len(self.skills)

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    extracted_text: str
    skills: List[str]
    processing_time: Optional[float] = None

class ScrapingRequest(BaseModel):
    skills: List[str] = Field(..., min_items=1, max_items=10)
    location: str = "Remote"
    max_jobs: int = Field(default=20, ge=1, le=100)
    platforms: Optional[List[str]] = None  # If None, scrape all platforms

class ScrapingResponse(BaseModel):
    jobs: List[JobResponse]
    total_jobs: int
    platforms_scraped: List[str]
    scraping_time: float
    search_query: str

class JobMatchRequest(BaseModel):
    user_skills: List[str]
    jobs: List[Dict[str, Any]]
    max_results: int = 20

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class PlatformStatus(BaseModel):
    platform: str
    status: str  # "success", "failed", "partial"
    jobs_found: int
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
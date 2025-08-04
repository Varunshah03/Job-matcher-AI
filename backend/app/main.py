from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import List, Dict, Any
import logging

from .core.resume_processor import ResumeProcessor
from .core.skills_extractor import SkillsExtractor
from .core.job_matcher import JobMatcher
from .scrapers.scraper_manager import ScraperManager
from .models.schemas import JobResponse, SkillsResponse, UploadResponse
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Matcher AI API",
    description="AI-powered job matching platform backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
resume_processor = ResumeProcessor()
skills_extractor = SkillsExtractor()
job_matcher = JobMatcher()
scraper_manager = ScraperManager()

@app.get("/")
async def root():
    return {"message": "Job Matcher AI API is running!"}

@app.post("/api/upload-resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process resume to extract text and skills"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF and DOCX files are supported"
            )
        
        # Validate file size (10MB max)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="File size must be less than 10MB"
            )
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Extract text from resume
        resume_text = await resume_processor.extract_text(content, file.filename)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract sufficient text from resume. Please ensure the file is not corrupted."
            )
        
        # Extract skills from resume text
        extracted_skills = await skills_extractor.extract_skills(resume_text)
        
        logger.info(f"Extracted {len(extracted_skills)} skills from resume")
        
        return UploadResponse(
            success=True,
            message="Resume processed successfully",
            filename=file.filename,
            extracted_text=resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            skills=extracted_skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/api/search-jobs", response_model=List[JobResponse])
async def search_jobs(
    background_tasks: BackgroundTasks,
    skills: List[str],
    location: str = "Remote",
    max_jobs: int = 20
):
    """Search for jobs based on extracted skills"""
    try:
        if not skills:
            raise HTTPException(status_code=400, detail="Skills list cannot be empty")
        
        logger.info(f"Searching jobs for skills: {skills[:5]}...")  # Log first 5 skills
        
        # Use top 5 skills for searching to avoid too broad results
        search_skills = skills[:5]
        
        # Start job scraping in background
        scraped_jobs = await scraper_manager.scrape_all_platforms(
            skills=search_skills,
            location=location,
            max_jobs_per_platform=max_jobs // 3  # Distribute across platforms
        )
        
        if not scraped_jobs:
            logger.warning("No jobs found from scraping")
            return []
        
        # Match and rank jobs based on user skills
        matched_jobs = await job_matcher.match_and_rank_jobs(
            jobs=scraped_jobs,
            user_skills=skills,
            max_results=max_jobs
        )
        
        logger.info(f"Found {len(matched_jobs)} matched jobs")
        
        return matched_jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@app.get("/api/skills/extract-from-text")
async def extract_skills_from_text(text: str):
    """Extract skills from provided text"""
    try:
        skills = await skills_extractor.extract_skills(text)
        return SkillsResponse(skills=skills)
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting skills: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Job Matcher AI API is running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
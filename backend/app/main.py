from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import List
from .core.resume_processor import ResumeProcessor
from .core.skills_extractor import SkillsExtractor
from .core.job_matcher import JobMatcher
from .scrapers.scraper_manager import ScraperManager
from .models.schemas import JobResponse, SkillsResponse, UploadResponse

# Clear all existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure custom logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.debug("Logging initialized for Job Matcher AI API")

# Disable Uvicorn's default access logger
logging.getLogger("uvicorn.access").disabled = True

app = FastAPI(
    title="Job Matcher AI API",
    description="AI-powered job matching platform backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
resume_processor = ResumeProcessor()
skills_extractor = SkillsExtractor()
job_matcher = JobMatcher()
scraper_manager = ScraperManager()

class SkillsInput(BaseModel):
    skills: List[str]

@app.post("/api/upload-resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process resume to extract text and skills"""
    logger.info(f"Received upload request for file: {file.filename}, size: {file.size} bytes")
    
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx')):
            logger.error(f"Invalid file type for {file.filename}. Supported types: .pdf, .docx")
            raise HTTPException(
                status_code=400, 
                detail="Only PDF and DOCX files are supported"
            )
        
        # Validate file size (10MB max)
        if file.size > 10 * 1024 * 1024:
            logger.error(f"File {file.filename} exceeds 10MB limit (size: {file.size} bytes)")
            raise HTTPException(
                status_code=400, 
                detail="File size must be less than 10MB"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text from resume
        logger.info(f"Starting text extraction for {file.filename}")
        try:
            resume_text = await resume_processor.extract_text(content, file.filename)
        except Exception as e:
            logger.error(f"Text extraction failed for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Text extraction failed: {str(e)}"
            )
        logger.info(f"Extracted text ({len(resume_text)} characters): {resume_text}")
        
        if not resume_text or len(resume_text.strip()) < 50:
            logger.error(f"Insufficient text extracted from {file.filename}: {len(resume_text)} characters")
            raise HTTPException(
                status_code=400, 
                detail="Could not extract sufficient text from resume. Please ensure the file is not corrupted."
            )
        
        # Extract skills from resume text
        logger.info(f"Starting skills extraction for {file.filename}")
        extracted_skills = await skills_extractor.extract_skills(resume_text)
        logger.info(f"Extracted {len(extracted_skills)} skills from {file.filename}: {extracted_skills}")
        
        # Log all extracted resume data
        logger.info(f"Extracted resume data: filename={file.filename}, size={file.size} bytes, extracted_text_length={len(resume_text)} characters, skills={extracted_skills}")
        
        response = UploadResponse(
            success=True,
            message="Resume processed successfully",
            filename=file.filename,
            extracted_text=resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            skills=extracted_skills
        )
        logger.info(f"Returning response: success={response.success}, skills_count={len(response.skills)}")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP error during resume processing: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing resume {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/api/add-user-skills")
async def add_user_skills(skills_input: SkillsInput):
    """Add user-validated skills to dynamic database"""
    try:
        for skill in skills_input.skills:
            cleaned_skill = skills_extractor._clean_skill_name(skill)
            if skills_extractor._is_valid_skill(cleaned_skill, ""):
                await skills_extractor._save_dynamic_skill(cleaned_skill)
        return {"message": "Skills added successfully"}
    except Exception as e:
        logger.error(f"Error adding user skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add skills")

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
        
        # Use top 5 skills for searching
        search_skills = skills[:5]
        
        # Start job scraping in background
        scraped_jobs = await scraper_manager.scrape_all_platforms(
            skills=search_skills,
            location=location,
            max_jobs_per_platform=max_jobs // 3
        )
        
        if not scraped_jobs:
            return []
        
        # Match and rank jobs
        matched_jobs = await job_matcher.match_and_rank_jobs(
            jobs=scraped_jobs,
            user_skills=skills,
            max_results=max_jobs
        )
        
        return matched_jobs
        
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@app.get("/api/skills/extract-from-text", response_model=SkillsResponse)
async def extract_skills_from_text(text: str):
    """Extract skills from provided text"""
    try:
        skills = await skills_extractor.extract_skills(text)
        return SkillsResponse(skills=skills)
    except Exception as e:
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
    logger.info("Starting Job Matcher AI API server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        log_config=None
    )
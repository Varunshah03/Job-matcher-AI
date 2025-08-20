# debug_scrapers.py - Run this to understand your scraper data structure

import asyncio
import sys
import os

# Add your app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scrapers.scraper_manager import ScraperManager
from app.core.skills_extractor import SkillsExtractor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_your_scrapers():
    """Debug script to understand your scraper data structure"""
    
    try:
        logger.info("🔍 Starting scraper debug session...")
        
        # Initialize your scrapers
        scraper_manager = ScraperManager()
        skills_extractor = SkillsExtractor()
        
        # Test with common job search
        test_skills = ["Python", "React", "Software Engineer"]
        test_location = "Remote"
        
        logger.info(f"🧪 Testing scrapers with skills: {test_skills}")
        
        # Get results from your scrapers
        all_jobs = await scraper_manager.scrape_all_platforms(
            skills=test_skills,
            location=test_location,
            max_jobs_per_platform=5
        )
        
        logger.info(f"📊 SCRAPER ANALYSIS RESULTS:")
        logger.info(f"  Total jobs found: {len(all_jobs)}")
        
        if not all_jobs:
            logger.warning("❌ No jobs returned from scrapers!")
            return
        
        # Analyze first job structure
        sample_job = all_jobs[0]
        logger.info(f"  Sample job keys: {list(sample_job.keys())}")
        
        # Check platform identification fields
        platform_fields = {}
        for job in all_jobs[:10]:  # Check first 10 jobs
            platforms = {
                "source_platform": job.get("source_platform"),
                "portal": job.get("portal"), 
                "source": job.get("source"),
                "platform": job.get("platform"),
                "site": job.get("site"),
                "url_domain": extract_domain_from_url(job.get("application_url") or job.get("job_url") or job.get("url", ""))
            }
            
            for field, value in platforms.items():
                if value:
                    if field not in platform_fields:
                        platform_fields[field] = set()
                    platform_fields[field].add(str(value).lower())
        
        logger.info(f"  Platform identification fields found:")
        for field, values in platform_fields.items():
            logger.info(f"    {field}: {list(values)}")
        
        # Show sample jobs with key fields
        logger.info(f"  Sample jobs:")
        for i, job in enumerate(all_jobs[:3]):
            logger.info(f"    Job {i+1}:")
            logger.info(f"      Title: {job.get('title', 'N/A')}")
            logger.info(f"      Company: {job.get('company', 'N/A')}")
            logger.info(f"      Location: {job.get('location', 'N/A')}")
            logger.info(f"      Source Platform: {job.get('source_platform', 'N/A')}")
            logger.info(f"      Portal: {job.get('portal', 'N/A')}")
            logger.info(f"      Source: {job.get('source', 'N/A')}")
            logger.info(f"      URL: {(job.get('application_url') or job.get('job_url') or job.get('url', 'N/A'))[:100]}...")
            logger.info(f"      Match Score: {job.get('match_score', 'N/A')}")
            logger.info("      ---")
        
        # Test platform filtering
        logger.info(f"🔍 Testing platform filtering:")
        
        platforms_to_test = ['indeed', 'linkedin', 'glassdoor', 'naukri']
        
        for platform in platforms_to_test:
            platform_jobs = []
            for job in all_jobs:
                job_source = (
                    job.get("source_platform", "") or 
                    job.get("portal", "") or 
                    job.get("source", "")
                ).lower()
                
                job_url = (job.get("application_url") or job.get("job_url") or job.get("url", "")).lower()
                
                if platform in job_source or platform in job_url:
                    platform_jobs.append(job)
            
            logger.info(f"  {platform}: {len(platform_jobs)} jobs")
        
        # Check individual scraper methods
        logger.info(f"🔧 Checking ScraperManager methods:")
        scraper_methods = [method for method in dir(scraper_manager) if method.startswith('scrape_')]
        logger.info(f"  Available scraper methods: {scraper_methods}")
        
        # Test if individual platform scrapers exist
        for platform in ['indeed', 'linkedin', 'glassdoor', 'naukri']:
            method_name = f'scrape_{platform}'
            if hasattr(scraper_manager, method_name):
                logger.info(f"  ✅ {method_name} method exists")
                
                try:
                    # Test individual platform scraper
                    method = getattr(scraper_manager, method_name)
                    platform_results = await method(
                        query="Python Developer",
                        location="Remote", 
                        max_jobs=3
                    )
                    logger.info(f"    {platform} individual scraper returned {len(platform_results)} jobs")
                except Exception as e:
                    logger.info(f"    {platform} individual scraper error: {str(e)}")
            else:
                logger.info(f"  ❌ {method_name} method not found")
        
        logger.info("🎉 Debug session completed!")
        
    except Exception as e:
        logger.error(f"❌ Debug session failed: {str(e)}")
        import traceback
        traceback.print_exc()

def extract_domain_from_url(url):
    """Extract domain from URL for platform identification"""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        return domain.replace('www.', '')
    except:
        return None

if __name__ == "__main__":
    asyncio.run(debug_your_scrapers())

# =============================================================================
# QUICK TEST SCRIPT - Add this to your main.py temporarily for testing
# =============================================================================

# Add this endpoint to your main.py for quick testing:
@app.get("/api/test-scrapers")
async def test_scrapers_endpoint():
    """Quick test endpoint to see scraper data structure"""
    try:
        logger.info("🧪 Testing scrapers via API endpoint...")
        
        # Test your scrapers
        all_jobs = await scraper_manager.scrape_all_platforms(
            skills=["Python", "Developer"],
            location="Remote",
            max_jobs_per_platform=3
        )
        
        # Return debug info
        debug_info = {
            "total_jobs": len(all_jobs),
            "sample_job_structure": list(all_jobs[0].keys()) if all_jobs else [],
            "platform_sources": list(set([
                job.get("source_platform") or job.get("portal") or job.get("source") or "unknown"
                for job in all_jobs
            ])),
            "available_scraper_methods": [
                method for method in dir(scraper_manager) 
                if method.startswith('scrape_')
            ],
            "sample_jobs": [
                {
                    "title": job.get("title"),
                    "company": job.get("company"), 
                    "platform_indicators": {
                        "source_platform": job.get("source_platform"),
                        "portal": job.get("portal"),
                        "source": job.get("source"),
                        "url": job.get("application_url") or job.get("job_url") or job.get("url")
                    }
                }
                for job in all_jobs[:5]
            ]
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Test endpoint error: {str(e)}")
        return {"error": str(e), "traceback": str(e.__traceback__)}
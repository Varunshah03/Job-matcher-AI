import asyncio
import logging
from typing import List, Dict, Any
import time

from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper
from .glassdoor_scraper import GlassdoorScraper
from ..models.schemas import PlatformStatus

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages multiple job platform scrapers and coordinates scraping operations"""
    
    def __init__(self):
        self.scrapers = {
            'indeed': IndeedScraper(),
            'linkedin': LinkedInScraper(),
            'glassdoor': GlassdoorScraper()
        }
        self.max_concurrent_scrapers = 3
    
    async def scrape_all_platforms(
        self, 
        skills: List[str], 
        location: str = "Remote", 
        max_jobs_per_platform: int = 10
    ) -> List[Dict[str, Any]]:
        """Scrape jobs from all platforms concurrently"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting scraping for skills: {skills[:3]}... at location: {location}")
            
            # Create scraping tasks for all platforms
            tasks = []
            platform_names = []
            
            for platform_name, scraper in self.scrapers.items():
                task = self._scrape_platform_safe(
                    scraper, platform_name, skills, location, max_jobs_per_platform
                )
                tasks.append(task)
                platform_names.append(platform_name)
            
            # Run all scrapers concurrently with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=120  # 2 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Scraping timeout reached, returning partial results")
                results = [[] for _ in tasks]
            
            # Combine all results
            all_jobs = []
            platform_statuses = []
            
            for i, result in enumerate(results):
                platform_name = platform_names[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Error scraping {platform_name}: {str(result)}")
                    platform_statuses.append(PlatformStatus(
                        platform=platform_name,
                        status="failed",
                        jobs_found=0,
                        error=str(result)
                    ))
                elif isinstance(result, list):
                    all_jobs.extend(result)
                    platform_statuses.append(PlatformStatus(
                        platform=platform_name,
                        status="success",
                        jobs_found=len(result)
                    ))
                    logger.info(f"Successfully scraped {len(result)} jobs from {platform_name}")
                else:
                    logger.warning(f"Unexpected result type from {platform_name}: {type(result)}")
                    platform_statuses.append(PlatformStatus(
                        platform=platform_name,
                        status="failed",
                        jobs_found=0,
                        error="Unexpected result type"
                    ))
            
            # Remove duplicates based on URL
            unique_jobs = self._remove_duplicates(all_jobs)
            
            end_time = time.time()
            scraping_time = end_time - start_time
            
            logger.info(f"Scraping completed in {scraping_time:.2f}s. Found {len(unique_jobs)} unique jobs")
            
            # Log platform status summary
            for status in platform_statuses:
                if status.status == "success":
                    logger.info(f"{status.platform}: {status.jobs_found} jobs")
                else:
                    logger.warning(f"{status.platform}: Failed - {status.error}")
            
            return unique_jobs
            
        except Exception as e:
            logger.error(f"Error in scrape_all_platforms: {str(e)}")
            return []
    
    async def _scrape_platform_safe(
        self, 
        scraper, 
        platform_name: str, 
        skills: List[str], 
        location: str, 
        max_jobs: int
    ) -> List[Dict[str, Any]]:
        """Safely scrape a platform with error handling"""
        try:
            logger.info(f"Starting {platform_name} scraper")
            jobs = await scraper.scrape_jobs(skills, location, max_jobs)
            logger.info(f"{platform_name} scraper completed: {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"Error in {platform_name} scraper: {str(e)}")
            return []
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on URL and title+company combination"""
        seen_urls = set()
        seen_combinations = set()
        unique_jobs = []
        
        for job in jobs:
            job_url = job.get('url', '')
            job_combination = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            
            # Skip if we've seen this URL or title+company combination
            if job_url in seen_urls or job_combination in seen_combinations:
                continue
            
            seen_urls.add(job_url)
            seen_combinations.add(job_combination)
            unique_jobs.append(job)
        
        return unique_jobs
    
    async def scrape_specific_platforms(
        self, 
        platforms: List[str], 
        skills: List[str], 
        location: str = "Remote", 
        max_jobs_per_platform: int = 10
    ) -> List[Dict[str, Any]]:
        """Scrape jobs from specific platforms only"""
        try:
            valid_platforms = [p for p in platforms if p in self.scrapers]
            
            if not valid_platforms:
                logger.warning(f"No valid platforms found in: {platforms}")
                return []
            
            logger.info(f"Scraping specific platforms: {valid_platforms}")
            
            tasks = []
            for platform_name in valid_platforms:
                scraper = self.scrapers[platform_name]
                task = self._scrape_platform_safe(
                    scraper, platform_name, skills, location, max_jobs_per_platform
                )
                tasks.append(task)
            
            # Run selected scrapers concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            all_jobs = []
            for result in results:
                if isinstance(result, list):
                    all_jobs.extend(result)
            
            return self._remove_duplicates(all_jobs)
            
        except Exception as e:
            logger.error(f"Error in scrape_specific_platforms: {str(e)}")
            return []
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available scraping platforms"""
        return list(self.scrapers.keys())
    
    async def test_platform_connectivity(self, platform: str) -> Dict[str, Any]:
        """Test if a specific platform is accessible"""
        try:
            if platform not in self.scrapers:
                return {"platform": platform, "status": "error", "message": "Platform not supported"}
            
            scraper = self.scrapers[platform]
            test_result = await scraper.test_connection()
            
            return {
                "platform": platform,
                "status": "success" if test_result else "failed",
                "message": "Connection successful" if test_result else "Connection failed"
            }
            
        except Exception as e:
            return {
                "platform": platform,
                "status": "error",
                "message": str(e)
            }
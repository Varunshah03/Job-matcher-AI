from typing import List
import asyncio
import logging
from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper
from .glassdoor_scraper import GlassdoorScraper

logger = logging.getLogger(__name__)

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            IndeedScraper(),
            LinkedInScraper(),
            GlassdoorScraper(),
        ]

    async def scrape_all_platforms(self, skills: List[str], location: str = "Remote", max_jobs_per_platform: int = 10) -> List[dict]:
        logger.info(f"Starting scraping for skills: {skills}... at location: {location}")
        start_time = asyncio.get_event_loop().time()
        all_jobs = []

        tasks = []
        for scraper in self.scrapers:
            logger.info(f"Starting {scraper.platform.lower()} scraper")
            tasks.append(self._scrape_with_error_handling(scraper, skills, location, max_jobs_per_platform))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for scraper, result in zip(self.scrapers, results):
            if isinstance(result, Exception):
                logger.error(f"Error in {scraper.platform.lower()} scraper: {str(result)}")
                continue
            logger.info(f"{scraper.platform.lower()} scraper completed: {len(result)} jobs")
            all_jobs.extend(result)

        unique_jobs = []
        seen = set()
        for job in all_jobs:
            job_key = (job["title"], job["company"], job["location"])
            if job_key not in seen:
                seen.add(job_key)
                unique_jobs.append(job)

        end_time = asyncio.get_event_loop().time()
        logger.info(f"Scraping completed in {end_time - start_time:.2f}s. Found {len(unique_jobs)} unique jobs")
        for scraper in self.scrapers:
            logger.info(f"{scraper.platform.lower()}: {len([job for job in unique_jobs if job['source'] == scraper.platform])} jobs")
        
        return unique_jobs

    async def _scrape_with_error_handling(self, scraper, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        try:
            jobs = await scraper.scrape(skills, location, max_jobs)
            logger.info(f"Successfully scraped {len(jobs)} jobs from {scraper.platform.lower()}")
            return jobs
        except Exception as e:
            logger.error(f"Error in {scraper.platform.lower()} scraper: {str(e)}")
            return []
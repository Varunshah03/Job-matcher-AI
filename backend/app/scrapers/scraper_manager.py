# scraper_manager.py - FIXED VERSION (with URL validation + fallback)

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import utils if available
try:
    from env_loader import get_credentials
    from chrome_driver_utils import create_stealth_driver, login_to_site
except ImportError:
    def get_credentials(platform): return None, None
    def create_stealth_driver(): return None
    def login_to_site(*args, **kwargs): return False


# ✅ Simple in-memory job storage
class SimpleJobStorage:
    def __init__(self):
        self.jobs = []

    def store_job(self, job_data: Dict[str, Any]) -> bool:
        try:
            self.jobs.append(job_data)
            return True
        except:
            return False

    def store_jobs_batch(self, job_list: List[Dict[str, Any]]) -> int:
        return sum(1 for job in job_list if self.store_job(job))

    def get_jobs(self, limit: Optional[int] = None, source_platform: Optional[str] = None) -> List[Dict[str, Any]]:
        jobs = self.jobs
        if source_platform:
            jobs = [job for job in jobs if job.get("source") == source_platform]
        return jobs[:limit] if limit else jobs

    def clear_jobs(self):
        self.jobs.clear()

    def get_job_count(self) -> int:
        return len(self.jobs)


logger = logging.getLogger(__name__)


class ScraperManager:
    def __init__(self, storage_type="memory", enable_all_scrapers=True):
        self.storage = SimpleJobStorage()
        self.core_scrapers = []
        self.additional_scrapers = []
        logger.info("🚀 Initializing ScraperManager...")

        self._load_scrapers_safely(enable_all_scrapers)
        self.all_scrapers = self.core_scrapers + self.additional_scrapers

        logger.info(f"ScraperManager initialized with {len(self.all_scrapers)} scrapers: {[s.platform for s in self.all_scrapers]}")

    def _load_scrapers_safely(self, enable_all_scrapers=True):
        """Safely load scrapers"""

        core_scraper_configs = [
            ("app.scrapers.indeed_scraper", "IndeedScraper", "Indeed"),
            ("app.scrapers.himalayas_scraper", "HimalayasScraper", "Himalayas"),
            ("app.scrapers.naukri_scraper", "NaukriScraper", "Naukri"),
        ]

        additional_scraper_configs = [
            ("app.scrapers.linkedin_scraper", "LinkedInScraper", "LinkedIn"),
            ("app.scrapers.glassdoor_scraper", "GlassdoorScraper", "Glassdoor"),
            ("app.scrapers.monster_scraper", "MonsterScraper", "Monster"),
            ("app.scrapers.dice_scraper", "DiceScraper", "Dice"),
            ("app.scrapers.careerbuilder_scraper", "CareerBuilderScraper", "CareerBuilder"),
            ("app.scrapers.ziprecruiter_scraper", "ZipRecruiterScraper", "ZipRecruiter"),
        ]

        self.core_scrapers = self._try_load_scrapers(core_scraper_configs, "core")
        if enable_all_scrapers:
            self.additional_scrapers = self._try_load_scrapers(additional_scraper_configs, "additional")

    def _try_load_scrapers(self, scraper_configs, scraper_type):
        """Try to load scrapers with detailed error reporting"""
        loaded_scrapers = []
        for module_name, class_name, display_name in scraper_configs:
            try:
                module = __import__(module_name, fromlist=[class_name])
                scraper_class = getattr(module, class_name)
                scraper_instance = scraper_class()
                loaded_scrapers.append(scraper_instance)
                logger.info(f"✅ Loaded {display_name} scraper ({scraper_type})")
            except Exception as e:
                logger.warning(f"❌ Could not import {display_name}: {e}")
        return loaded_scrapers

    async def scrape_all_platforms(self, skills: List[str], location: str = "Remote", max_jobs_per_platform: int = 10,
                                   store_results: bool = True, specific_platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info(f"Starting scraping for skills: {skills} at location: {location}")
        start_time = datetime.now()

        scrapers_to_use = self.all_scrapers
        if specific_platforms:
            scrapers_to_use = [s for s in self.all_scrapers if s.platform in specific_platforms]
            logger.info(f"Using specific platforms: {[s.platform for s in scrapers_to_use]}")

        if not scrapers_to_use:
            logger.warning("No scrapers available to use")
            return {"jobs": [], "metadata": {"total_jobs_found": 0, "error": "No scrapers available"}}

        all_jobs, scraping_stats, failed_platforms = [], {}, []

        tasks = [self._scrape_with_error_handling(scraper, skills, location, max_jobs_per_platform) for scraper in scrapers_to_use]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for scraper, result in zip(scrapers_to_use, results):
            if isinstance(result, Exception):
                failed_platforms.append(scraper.platform)
                scraping_stats[scraper.platform] = {"jobs_found": 0, "status": "failed", "error": str(result)}
                continue
            jobs_count = len(result)
            all_jobs.extend(result)
            scraping_stats[scraper.platform] = {"jobs_found": jobs_count, "status": "success"}

        unique_jobs = self._remove_duplicates(all_jobs)

        stored_count = self.storage.store_jobs_batch(unique_jobs) if store_results else 0
        duration = (datetime.now() - start_time).total_seconds()

        platform_distribution = {}
        for job in unique_jobs:
            platform = job.get("source", "Unknown")
            platform_distribution[platform] = platform_distribution.get(platform, 0) + 1

        return {
            "jobs": unique_jobs,
            "metadata": {
                "total_jobs_found": len(unique_jobs),
                "total_raw_jobs": len(all_jobs),
                "duplicates_removed": len(all_jobs) - len(unique_jobs),
                "jobs_stored": stored_count,
                "scraping_duration_seconds": duration,
                "platforms_used": len(scrapers_to_use),
                "failed_platforms": failed_platforms,
                "platform_distribution": platform_distribution,
                "scraping_stats": scraping_stats,
            }
        }

    async def _scrape_with_error_handling(self, scraper, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        try:
            jobs = await scraper.scrape(skills, location, max_jobs)
            validated_jobs = [self._ensure_valid_url(job, scraper.platform) for job in jobs if self._validate_job_data(job)]
            return validated_jobs
        except Exception as e:
            logger.error(f"Error in {scraper.platform} scraper: {e}")
            return []

    def _validate_job_data(self, job: Dict[str, Any]) -> bool:
        required_fields = ["title", "company", "source"]
        return all(job.get(field) for field in required_fields)

    def _ensure_valid_url(self, job: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Ensure job has a valid URL, fallback to Google search"""
        url = job.get("url")
        if not url or not url.startswith("http"):
            query = f"{job.get('title','')} {job.get('company','')} {platform}"
            job["url"] = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return job

    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique_jobs, seen = [], set()
        for job in jobs:
            key = (job.get("title", "").lower(), job.get("company", "").lower(), job.get("location", "").lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        return unique_jobs

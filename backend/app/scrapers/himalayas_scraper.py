# himalayas_scraper.py
import sys
import os
import time
import logging
import random
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

try:
    from app.scrapers.base_scraper import BaseScraper
except ImportError:
    class BaseScraper:
        def __init__(self, platform: str, base_url: str):
            self.platform = platform
            self.base_url = base_url

import aiohttp

logger = logging.getLogger(__name__)

class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app remote jobs using Selenium with API fallback"""

    def __init__(self):
        super().__init__("Himalayas", "https://himalayas.app")
        self.api_url = "https://himalayas.app/jobs/api"
        self.page_load_timeout = 20
        self.element_timeout = 10
        self.max_retries = 2
        self.rate_limit_delay = 1

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        logger.info(f"🚀 Scraping Himalayas for {skills[:2]} (max={max_jobs})")
        jobs = await self._try_selenium_scraping(skills, location, max_jobs)
        if not jobs:
            logger.warning("⚠️ Selenium scrape failed, falling back to API...")
            jobs = await self._fetch_jobs_from_api(max_jobs)
        return jobs

    async def _try_selenium_scraping(self, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        driver = None
        jobs: List[dict] = []
        try:
            driver = self._create_driver()
            search_url = self._build_search_url(skills, location)
            driver.get(search_url)
            await asyncio.sleep(3)

            self._scroll_page(driver)

            cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']:not([href$='/jobs'])")
            logger.info(f"Found {len(cards)} job links")

            for idx, card in enumerate(cards[:max_jobs]):
                try:
                    job = self._extract_card_data(card, skills, idx)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Failed to parse job card {idx}: {e}")
                    continue
            return jobs
        except Exception as e:
            logger.error(f"Himalayas Selenium scrape error: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ])
        options.add_argument(f"user-agent={ua}")
        if UC_AVAILABLE:
            driver = uc.Chrome(options=options, headless=True)
        else:
            driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver

    def _build_search_url(self, skills: List[str], location: str) -> str:
        query = "+".join(skills) if skills else "developer"
        return f"https://himalayas.app/jobs?search={query}"

    def _scroll_page(self, driver: webdriver.Chrome):
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _extract_card_data(self, el, skills: List[str], idx: int) -> Optional[dict]:
        title = el.text.split("\n")[0].strip()
        job_url = el.get_attribute("href")
        company = "Unknown"
        try:
            company = el.find_element(By.XPATH, ".//following-sibling::div").text.strip()
        except Exception:
            pass
        return {
            "id": f"himalayas_selenium_{idx}",
            "title": title,
            "company": company,
            "location": "Remote",
            "description": f"Remote opportunity for {title} on Himalayas.",
            "requirements": [],
            "skills": skills,
            "match_score": self._calculate_match_score(title, "", skills),
            "posted_date": "Recently posted",
            "source": self.platform,
            "url": job_url,
            "salary": "Not disclosed",
            "job_type": "Full-time",
            "experience_level": "Not specified",
            "platform_specific": {
                "remote_friendly": True
            }
        }

    async def _fetch_jobs_from_api(self, limit: int) -> List[dict]:
        jobs = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}?limit={limit}") as resp:
                    if resp.status != 200:
                        logger.error(f"API failed: {resp.status}")
                        return []
                    data = await resp.json()
                    job_list = data if isinstance(data, list) else data.get("jobs", [])
                    for idx, job in enumerate(job_list[:limit]):
                        jobs.append({
                            "id": f"himalayas_api_{idx}",
                            "title": job.get("title", ""),
                            "company": job.get("companyName", ""),
                            "location": "Remote",
                            "description": job.get("description", ""),
                            "requirements": [],
                            "skills": [],
                            "match_score": 0,
                            "posted_date": "Recently posted",
                            "source": self.platform,
                            "url": job.get("applicationLink", ""),
                            "salary": "Not disclosed",
                            "job_type": job.get("employmentType", ""),
                            "experience_level": "Not specified",
                            "platform_specific": {
                                "remote_friendly": True
                            }
                        })
            except Exception as e:
                logger.error(f"API fetch error: {e}")
        return jobs

    def _calculate_match_score(self, title: str, description: str, skills: List[str]) -> float:
        text = f"{title} {description}".lower()
        matches = sum(1 for s in skills if s.lower() in text)
        return round(matches / len(skills) * 100, 1) if skills else 0

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://himalayas.app/jobs") as resp:
                    return resp.status == 200
        except Exception:
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = HimalayasScraper()
    skills = ["Python", "React", "Machine Learning"]
    jobs = asyncio.run(scraper.scrape(skills, max_jobs=5))
    for j in jobs:
        print(f"{j['title']} @ {j['company']} -> {j['url']}")

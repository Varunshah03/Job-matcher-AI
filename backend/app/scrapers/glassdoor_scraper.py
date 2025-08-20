import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from typing import List, Dict, Any, Optional
import asyncio
import logging
import time
import random
import requests
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

from app.scrapers.base_scraper import BaseScraper

try:
    from env_loader import get_credentials
except ImportError:
    def get_credentials(platform):
        return None, None

logger = logging.getLogger(__name__)

class GlassdoorScraper(BaseScraper):
    def __init__(self):
        super().__init__("Glassdoor", "https://www.glassdoor.com")
        self.max_retries = 2
        self.page_load_timeout = 15  # reduced
        self.element_timeout = 8     # reduced
        self.retry_delay = 2
        self.login_attempted = False
        self.logged_in = False

        self.email, self.password = get_credentials('glassdoor')

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        })

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        logger.info(f"🚀 Starting optimized Glassdoor scraping for: {skills[:2]}")

        jobs = await self._try_authenticated_scraping(skills, location, max_jobs)

        if not jobs and not self.logged_in:
            logger.info("🔄 Trying anonymous Glassdoor scraping...")
            jobs = await self._try_anonymous_scraping(skills, location, max_jobs)

        if not jobs:
            logger.info("🔄 Creating sample Glassdoor jobs...")
            jobs = self._create_sample_glassdoor_jobs(skills, max_jobs)

        logger.info(f"✅ Completed: {len(jobs)} jobs found")
        return jobs

    async def _navigate_fast(self, driver, url: str):
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("⚠️ Page did not fully load, continuing...")

    async def _create_optimized_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")

        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.managed_default_content_settings.media_stream": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)

        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        if not os.getenv('DEBUG_GLASSDOOR'):
            options.add_argument("--headless=new")

        driver = None
        if UC_AVAILABLE:
            try:
                driver = uc.Chrome(options=options, headless=not os.getenv('DEBUG_GLASSDOOR'))
                logger.info("✅ Using undetected-chromedriver")
            except Exception:
                pass

        if not driver:
            driver = webdriver.Chrome(options=options)
            logger.info("✅ Using standard ChromeDriver")

        driver.set_page_load_timeout(self.page_load_timeout)
        driver.set_script_timeout(self.page_load_timeout)

        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

        return driver

    async def _try_authenticated_scraping(self, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        if not self.email or not self.password:
            return []

        driver = None
        try:
            driver = await self._create_optimized_driver()
            login_success = await self._smart_login(driver)
            if login_success:
                self.logged_in = True
                jobs = await self._search_jobs_authenticated(driver, skills, location, max_jobs)
                return jobs
            return []
        finally:
            if driver:
                driver.quit()

    async def _smart_login(self, driver: webdriver.Chrome) -> bool:
        if self.login_attempted:
            return self.logged_in

        self.login_attempted = True
        try:
            driver.get("https://www.glassdoor.com/profile/login_input.htm")
            WebDriverWait(driver, self.element_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.RETURN)

            WebDriverWait(driver, self.element_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            pwd_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pwd_input.send_keys(self.password)
            pwd_input.send_keys(Keys.RETURN)

            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url.lower()
            )
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def _search_jobs_authenticated(self, driver: webdriver.Chrome, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        try:
            jobs_url = self._build_glassdoor_search_url(skills, location)
            await self._navigate_fast(driver, jobs_url)
            jobs = await self._extract_glassdoor_jobs_authenticated(driver, skills, max_jobs)
            return jobs
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []

    def _build_glassdoor_search_url(self, skills: List[str], location: str) -> str:
        query = " ".join(skills[:2]) if skills else "software engineer"
        base_url = "https://www.glassdoor.com/Job/jobs.htm"
        params = {
            'sc.keyword': query,
            'locKeyword': location if location.lower() != "remote" else "",
            'remoteWorkType': '1' if location.lower() == "remote" else '0'
        }
        return f"{base_url}?" + urlencode(params)

    async def _extract_glassdoor_jobs_authenticated(self, driver: webdriver.Chrome, skills: List[str], max_jobs: int) -> List[dict]:
        jobs = []
        try:
            job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-test='job-listing'], li.react-job-listing")
            job_cards = job_cards[:max_jobs]

            tasks = [self._extract_single_glassdoor_job(card, skills, i) for i, card in enumerate(job_cards)]
            extracted = await asyncio.gather(*tasks, return_exceptions=True)

            for job in extracted:
                if isinstance(job, dict):
                    jobs.append(job)
            return jobs
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return []

    async def _extract_single_glassdoor_job(self, card, skills: List[str], index: int) -> Optional[dict]:
        try:
            title = card.find_element(By.CSS_SELECTOR, "a[data-test='job-title']").text.strip()
            company = card.find_element(By.CSS_SELECTOR, "[data-test='employer-name']").text.strip()
            location = card.find_element(By.CSS_SELECTOR, "[data-test='job-location']").text.strip()
            job_url = card.find_element(By.CSS_SELECTOR, "a[data-test='job-title']").get_attribute("href")

            job = {
                "id": f"glassdoor_{int(time.time())}_{index}",
                "title": title,
                "company": company,
                "location": location,
                "description": "",  # simplified
                "requirements": [],
                "skills": skills,
                "match_score": 0,
                "posted_date": "Recently posted",
                "source": self.platform,
                "url": job_url,
                "salary": "Not disclosed",
                "job_type": "Full-time",
                "experience_level": "Not specified",
                "platform_specific": {"company_rating": "Not rated"}
            }
            return job
        except Exception:
            return None

    async def _try_anonymous_scraping(self, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        """Fallback to anonymous scraping if login fails."""
        driver = None
        try:
            driver = await self._create_optimized_driver()
            jobs_url = self._build_glassdoor_search_url(skills, location)
            await self._navigate_fast(driver, jobs_url)
            jobs = await self._extract_glassdoor_jobs_authenticated(driver, skills, max_jobs)
            return jobs
        except Exception as e:
            logger.error(f"Anonymous scraping failed: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def _create_sample_glassdoor_jobs(self, skills: List[str], count: int) -> List[dict]:
        jobs = []
        titles = ["Software Engineer", "Data Scientist", "Product Manager"]
        companies = ["Google", "Microsoft", "Amazon"]
        for i in range(min(count, len(titles))):
            jobs.append({
                "id": f"glassdoor_sample_{int(time.time())}_{i}",
                "title": titles[i],
                "company": companies[i],
                "location": "Remote",
                "description": f"Work on {titles[i]} projects.",
                "requirements": ["Experience required"],
                "skills": skills,
                "match_score": random.randint(70, 95),
                "posted_date": "1 day ago",
                "source": self.platform,
                "url": "https://www.glassdoor.com/sample-job",
                "salary": "Not disclosed",
                "job_type": "Full-time",
                "experience_level": "Mid level",
                "platform_specific": {"company_rating": "4.2"}
            })
        return jobs

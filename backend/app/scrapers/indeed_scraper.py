from typing import List
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from .base_scraper import BaseScraper
import logging
import time

logger = logging.getLogger(__name__)

class IndeedScraper(BaseScraper):
    def __init__(self):
        super().__init__("Indeed", "https://www.indeed.com/jobs")

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        logger.info(f"Starting Indeed scraping for skills: {skills}...")
        jobs = []

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.184 Safari/537.36")

        driver = None
        try:
            driver = uc.Chrome(options=chrome_options, version_main=138)
            skills_query = "+".join(skill.replace(" ", "+") for skill in skills)
            location_query = location.replace(" ", "+")
            url = f"{self.base_url}?q={skills_query}&l={location_query}&sc=0kf%3Aattr%28WF8Z8%29%3B"
            driver.get(url)

            # Wait for job cards with retries
            for _ in range(3):
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
                    )
                    break
                except Exception as e:
                    logger.warning(f"Retrying Indeed page load: {str(e)}")
                    time.sleep(3)
                    driver.refresh()
            else:
                logger.error("Failed to load Indeed job cards after retries")
                return jobs

            # Handle CAPTCHA
            try:
                captcha = driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha")
                if captcha:
                    logger.warning("CAPTCHA detected on Indeed. Consider 2Captcha or manual intervention.")
                    return jobs
            except Exception:
                pass

            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
            logger.info(f"Found {len(job_cards)} Indeed job cards")

            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text.strip()
                    company = card.find_element(By.CSS_SELECTOR, "span.companyName").text.strip()
                    location = card.find_element(By.CSS_SELECTOR, "div.companyLocation").text.strip()
                    url = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle").get_attribute("href")
                    posted_date = card.find_element(By.CSS_SELECTOR, "span.date").text.strip() if card.find_elements(By.CSS_SELECTOR, "span.date") else "Unknown"
                    description = ""

                    # Click job for full description
                    driver.execute_script("arguments[0].click();", card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle"))
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobDescriptionSection"))
                    )
                    description = driver.find_element(By.CSS_SELECTOR, "div.jobsearch-JobDescriptionSection").text.strip()
                    driver.back()
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
                    )

                    job = {
                        "id": f"indeed_{i}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "requirements": [],  # Parse in job_matcher.py
                        "skills": skills,
                        "match_score": 0.0,
                        "posted_date": posted_date,
                        "source": self.platform,
                        "url": url,
                        "salary": None,
                        "job_type": None,
                        "experience_level": None,
                    }
                    if title and company and location:
                        jobs.append(job)
                        logger.debug(f"Scraped Indeed job: {title} at {company}")
                    else:
                        logger.warning(f"Skipping incomplete Indeed job {i}: title={title}, company={company}, location={location}")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error scraping Indeed job {i}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Indeed scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()

        logger.info(f"Indeed scraping completed: {len(jobs)} unique jobs found")
        return jobs
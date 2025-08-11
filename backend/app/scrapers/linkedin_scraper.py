from typing import List
import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import os
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com/jobs/search/")
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        logger.info(f"Scraping LinkedIn jobs for skills: {skills}, location: {location}")
        jobs = []

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = None
        try:
            driver = uc.Chrome(options=chrome_options, version_main=138)  # Match Chrome version
            skills_query = "+".join(skill.replace(" ", "+") for skill in skills)
            url = f"{self.base_url}?keywords={skills_query}&location={location}&f_WT=2"  # Remote filter
            driver.get(url)

            # Optional: Login if credentials provided
            if self.email and self.password:
                try:
                    sign_in_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Sign in"))
                    )
                    sign_in_link.click()
                    email_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "session_key"))
                    )
                    email_input.send_keys(self.email)
                    password_input = driver.find_element(By.ID, "session_password")
                    password_input.send_keys(self.password)
                    driver.find_element(By.CSS_SELECTOR, "button.sign-in-form__submit-button").click()
                    WebDriverWait(driver, 10).until(
                        EC.url_contains("/feed") or EC.url_contains("/jobs")
                    )
                    driver.get(url)  # Reload search page
                    logger.info("LinkedIn login successful")
                except Exception as e:
                    logger.warning(f"LinkedIn login failed: {str(e)}")

            # Wait for job cards
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-card"))
            )
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.base-card")
            logger.info(f"Found {len(job_cards)} LinkedIn job cards")

            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    title = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
                    company = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle").text.strip()
                    location = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location").text.strip()
                    url = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                    posted_date = card.find_element(By.CSS_SELECTOR, "time.job-search-card__listdate").text.strip()
                    description = card.find_element(By.CSS_SELECTOR, "div.job-search-card__snippet").text.strip() if card.find_elements(By.CSS_SELECTOR, "div.job-search-card__snippet") else ""

                    job = {
                        "id": f"linkedin_{i}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "requirements": [],  # Parse from description if needed
                        "skills": skills,
                        "match_score": 0.0,
                        "posted_date": posted_date,
                        "source": self.platform,
                        "url": url,
                        "salary": None,
                        "job_type": None,
                        "experience_level": None,
                    }
                    jobs.append(job)
                    logger.debug(f"Scraped LinkedIn job: {title} at {company}")
                except Exception as e:
                    logger.error(f"Error scraping LinkedIn job {i}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"LinkedIn scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()

        logger.info(f"Scraped {len(jobs)} LinkedIn jobs")
        return jobs
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
import time
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class GlassdoorScraper(BaseScraper):
    def __init__(self):
        super().__init__("Glassdoor", "https://www.glassdoor.com/Job/index.htm")
        self.email = os.getenv("GLASSDOOR_EMAIL")
        self.password = os.getenv("GLASSDOOR_PASSWORD")

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        logger.info(f"Scraping Glassdoor jobs for skills: {skills}, location: {location}")
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
            skills_query = "-".join(skill.replace(" ", "-") for skill in skills)
            url = f"https://www.glassdoor.com/Job/{skills_query}-jobs-SRCH_KO0,{len(skills_query)}_IL.0,6_KM0.htm?remoteWorkType=1"
            driver.get(url)

            # Handle CAPTCHA
            try:
                captcha = driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha")
                if captcha:
                    logger.warning("CAPTCHA detected on Glassdoor. Consider 2Captcha or manual intervention.")
                    return jobs
            except Exception:
                pass

            # Optional: Login if credentials provided
            if self.email and self.password:
                try:
                    # Close any modal overlay
                    try:
                        modal = driver.find_element(By.CSS_SELECTOR, "div.Modal")
                        driver.execute_script("arguments[0].remove();", modal)
                        logger.debug("Removed modal overlay")
                    except Exception:
                        pass

                    sign_in_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-hook='sign-in']"))
                    )
                    driver.execute_script("arguments[0].click();", sign_in_button)
                    email_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "inlineUserEmail"))
                    )
                    email_input.send_keys(self.email)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[data-test='emailSubmit']"))
                    password_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "inlineUserPassword"))
                    )
                    password_input.send_keys(self.password)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[data-test='passwordSubmit']"))
                    WebDriverWait(driver, 15).until(
                        EC.url_contains("/Job/")
                    )
                    driver.get(url)  # Reload search page
                    logger.info("Glassdoor login successful")
                except Exception as e:
                    logger.warning(f"Glassdoor login failed: {str(e)}")

            # Wait for job cards with retries
            for _ in range(3):
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.jobListing"))
                    )
                    break
                except Exception as e:
                    logger.warning(f"Retrying Glassdoor page load: {str(e)}")
                    time.sleep(3)
                    driver.refresh()
            else:
                logger.error("Failed to load Glassdoor job cards after retries")
                return jobs

            job_cards = driver.find_elements(By.CSS_SELECTOR, "li.jobListing")
            logger.info(f"Found {len(job_cards)} Glassdoor job cards")

            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    title = card.find_element(By.CSS_SELECTOR, "a.jobLink").text.strip()
                    company = card.find_element(By.CSS_SELECTOR, "div[data-test='employer-name']").text.strip()
                    location = card.find_element(By.CSS_SELECTOR, "div[data-test='job-location']").text.strip()
                    url = card.find_element(By.CSS_SELECTOR, "a.jobLink").get_attribute("href")
                    posted_date = card.find_element(By.CSS_SELECTOR, "div[data-test='job-age']").text.strip() if card.find_elements(By.CSS_SELECTOR, "div[data-test='job-age']") else "Unknown"
                    description = ""

                    # Click job for full description
                    driver.execute_script("arguments[0].click();", card.find_element(By.CSS_SELECTOR, "a.jobLink"))
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.desc"))
                    )
                    description = driver.find_element(By.CSS_SELECTOR, "div.desc").text.strip()
                    driver.back()
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.jobListing"))
                    )

                    job = {
                        "id": f"glassdoor_{i}",
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
                        logger.debug(f"Scraped Glassdoor job: {title} at {company}")
                    else:
                        logger.warning(f"Skipping incomplete Glassdoor job {i}: title={title}, company={company}, location={location}")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error scraping Glassdoor job {i}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Glassdoor scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()

        logger.info(f"Scraped {len(jobs)} Glassdoor jobs")
        return jobs
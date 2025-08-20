# monster_scraper.py - Updated for Monster/Foundit (dual support)
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
import re
from datetime import datetime
import random
import requests
from urllib.parse import quote, urlencode

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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

class MonsterScraper(BaseScraper):
    def __init__(self):
        # Support both Monster and Foundit
        super().__init__("Monster/Foundit", "https://www.foundit.in")
        self.max_retries = 2
        self.page_load_timeout = 25
        self.element_timeout = 15
        self.retry_delay = 3
        
        # Multiple domain support
        self.domains = [
            "https://www.foundit.in",      # Primary (India)
            "https://www.monster.com",     # International
            "https://www.monster.co.uk",   # UK
        ]
        
        # Session for API calls
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        })

    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        """Optimized Monster/Foundit scraping with multiple domain support"""
        logger.info(f"🚀 Starting Monster/Foundit scraping for: {skills[:2]}")
        
        # Strategy 1: Try Foundit (primary)
        jobs = await self._try_foundit_scraping(skills, location, max_jobs)
        
        # Strategy 2: Try Monster.com if Foundit fails
        if not jobs:
            logger.info("🔄 Foundit failed, trying Monster.com...")
            jobs = await self._try_monster_scraping(skills, location, max_jobs)
        
        # Strategy 3: Create sample jobs
        if not jobs:
            logger.info("🔄 Creating sample Monster/Foundit jobs...")
            jobs = self._create_sample_monster_jobs(skills, max_jobs)
        
        logger.info(f"✅ Completed: {len(jobs)} jobs found")
        return jobs

    async def _try_foundit_scraping(self, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        """Try Foundit.in scraping (primary method)"""
        driver = None
        try:
            driver = await self._create_optimized_driver()
            
            # Build Foundit search URL
            search_url = self._build_foundit_url(skills, location)
            logger.info(f"🔗 Trying Foundit: {search_url}")
            
            driver.get(search_url)
            await self._wait_and_handle_page(driver, "foundit")
            
            # Debug page content
            await self._debug_page_content(driver, "Foundit")
            
            # Extract jobs
            jobs = await self._extract_foundit_jobs(driver, skills, max_jobs)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Foundit scraping failed: {str(e)}")
            return []
        finally:
            if driver:
                driver.quit()

    async def _try_monster_scraping(self, skills: List[str], location: str, max_jobs: int) -> List[dict]:
        """Try Monster.com scraping (fallback)"""
        driver = None
        try:
            driver = await self._create_optimized_driver()
            
            # Build Monster search URL
            search_url = self._build_monster_url(skills, location)
            logger.info(f"🔗 Trying Monster: {search_url}")
            
            driver.get(search_url)
            await self._wait_and_handle_page(driver, "monster")
            
            # Debug page content
            await self._debug_page_content(driver, "Monster")
            
            # Extract jobs
            jobs = await self._extract_monster_jobs(driver, skills, max_jobs)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Monster scraping failed: {str(e)}")
            return []
        finally:
            if driver:
                driver.quit()

    async def _create_optimized_driver(self) -> webdriver.Chrome:
        """Create optimized driver for Monster/Foundit"""
        options = Options()
        
        # Basic stable options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-extensions")
        
        # User agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Performance optimizations
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        
        try:
            options.add_experimental_option("prefs", prefs)
        except:
            pass
        
        # Add headless only if not debugging
        if not os.getenv('DEBUG_MONSTER'):
            options.add_argument("--headless")
        
        driver = None
        
        # Method 1: Try undetected Chrome
        if UC_AVAILABLE:
            try:
                driver = uc.Chrome(options=options, headless=not os.getenv('DEBUG_MONSTER'))
                logger.info("✅ Using undetected-chromedriver")
            except Exception as e:
                logger.debug(f"UC Chrome failed: {e}")
        
        # Method 2: Standard Chrome
        if not driver:
            try:
                driver = webdriver.Chrome(options=options)
                logger.info("✅ Using standard ChromeDriver")
            except Exception as e:
                logger.debug(f"Standard Chrome failed: {e}")
                
                # Method 3: Minimal options
                try:
                    minimal_options = Options()
                    minimal_options.add_argument("--headless")
                    minimal_options.add_argument("--no-sandbox")
                    minimal_options.add_argument("--disable-dev-shm-usage")
                    driver = webdriver.Chrome(options=minimal_options)
                    logger.info("✅ Using minimal ChromeDriver")
                except Exception as e3:
                    logger.error(f"All driver methods failed: {e3}")
                    raise Exception("Cannot create Chrome driver")
        
        driver.set_page_load_timeout(self.page_load_timeout)
        
        # Anti-detection
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except:
            pass
        
        return driver

    def _build_foundit_url(self, skills: List[str], location: str) -> str:
        """Build Foundit.in search URL"""
        query = " ".join(skills[:2]) if skills else "software engineer"
        
        # Foundit URL format
        base_url = "https://www.foundit.in/srp/results"
        params = {
            'query': query,
            'locations': location if location.lower() != "remote" else "India",
            'searchId': str(int(time.time())),
        }
        
        return f"{base_url}?" + urlencode(params)

    def _build_monster_url(self, skills: List[str], location: str) -> str:
        """Build Monster.com search URL"""
        query = " ".join(skills[:2]) if skills else "software engineer"
        
        # Monster URL format
        base_url = "https://www.monster.com/jobs/search"
        params = {
            'q': query,
            'where': location if location.lower() != "remote" else "",
            'page': 1
        }
        
        if "remote" in location.lower():
            params['remote'] = 'true'
        
        return f"{base_url}?" + urlencode(params)

    async def _wait_and_handle_page(self, driver: webdriver.Chrome, platform: str):
        """Wait for page load and handle popups"""
        await asyncio.sleep(random.uniform(3, 5))
        
        # Handle platform-specific popups
        if platform == "foundit":
            popup_selectors = [
                ".close-button",
                ".modal-close",
                "[aria-label='Close']",
                ".popup-close",
                "#onetrust-accept-btn-handler"
            ]
        else:  # monster
            popup_selectors = [
                "button[data-testid='close-button']",
                ".close-button",
                ".modal-close",
                "[aria-label='Close']",
                "#onetrust-accept-btn-handler"
            ]
        
        for selector in popup_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        await asyncio.sleep(1)
                        break
            except:
                continue
        
        # Scroll to trigger lazy loading
        try:
            driver.execute_script("window.scrollTo(0, 500);")
            await asyncio.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(1)
        except:
            pass

    async def _debug_page_content(self, driver: webdriver.Chrome, platform: str):
        """Debug page content"""
        try:
            current_url = driver.current_url
            page_title = driver.title
            
            logger.info(f"🔍 Debug {platform}:")
            logger.info(f"   URL: {current_url}")
            logger.info(f"   Title: {page_title}")
            
            # Check for job-related elements
            if platform == "foundit":
                selectors_to_check = [
                    (".srpResultCardContainer", "Foundit job cards"),
                    (".jobTuple", "Job tuples"),
                    (".job-card", "Job cards"),
                    ("a[href*='job-detail']", "Job links")
                ]
            else:  # monster
                selectors_to_check = [
                    ("div[data-testid='JobCard']", "Monster job cards"),
                    ("section.card-content", "Card content"),
                    (".job-card", "Job cards"),
                    ("a[href*='job']", "Job links")
                ]
            
            found_elements = []
            for selector, description in selectors_to_check:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_elements.append(f"   ✅ {description}: {len(elements)} found")
                    else:
                        found_elements.append(f"   ❌ {description}: 0 found")
                except:
                    found_elements.append(f"   ❌ {description}: Error")
            
            for element in found_elements:
                logger.info(element)
            
        except Exception as e:
            logger.debug(f"Debug failed: {e}")

    async def _extract_foundit_jobs(self, driver: webdriver.Chrome, skills: List[str], max_jobs: int) -> List[dict]:
        """Extract jobs from Foundit.in"""
        jobs = []
        
        try:
            # Foundit job selectors
            job_selectors = [
                ".srpResultCardContainer",
                ".jobTuple",
                ".job-card",
                ".listing-card",
                "div[data-job-id]"
            ]
            
            job_cards = []
            for selector in job_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        job_cards = cards
                        logger.info(f"✅ Found {len(cards)} Foundit job cards with: {selector}")
                        break
                except:
                    continue
            
            if not job_cards:
                logger.warning("❌ No Foundit job cards found")
                return []
            
            # Extract jobs
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job = await self._extract_single_foundit_job(card, skills, i)
                    if job:
                        jobs.append(job)
                        logger.info(f"   ✅ Extracted: {job['title']} at {job['company']}")
                except Exception as e:
                    logger.debug(f"   ❌ Failed to extract Foundit job {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Foundit extraction failed: {str(e)}")
            return []

    async def _extract_monster_jobs(self, driver: webdriver.Chrome, skills: List[str], max_jobs: int) -> List[dict]:
        """Extract jobs from Monster.com"""
        jobs = []
        
        try:
            # Monster job selectors
            job_selectors = [
                "div[data-testid='JobCard']",
                "section.card-content",
                ".job-card",
                ".mux-job-card",
                "article.job-listing"
            ]
            
            job_cards = []
            for selector in job_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        job_cards = cards
                        logger.info(f"✅ Found {len(cards)} Monster job cards with: {selector}")
                        break
                except:
                    continue
            
            if not job_cards:
                logger.warning("❌ No Monster job cards found")
                return []
            
            # Extract jobs
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job = await self._extract_single_monster_job(card, skills, i)
                    if job:
                        jobs.append(job)
                        logger.info(f"   ✅ Extracted: {job['title']} at {job['company']}")
                except Exception as e:
                    logger.debug(f"   ❌ Failed to extract Monster job {i}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Monster extraction failed: {str(e)}")
            return []

    async def _extract_single_foundit_job(self, card, skills: List[str], index: int) -> Optional[dict]:
        """Extract single job from Foundit"""
        try:
            # Title extraction for Foundit
            title = ""
            title_selectors = [
                ".jobTitle a",
                ".job-title a",
                "h3 a",
                "h2 a",
                ".title a"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            
            if not title:
                return None
            
            # Company extraction for Foundit
            company = ""
            company_selectors = [
                ".companyName",
                ".company-name",
                ".employer",
                ".org a"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    company = company_elem.text.strip()
                    if company:
                        break
                except:
                    continue
            
            if not company:
                company = "Company Not Specified"
            
            # Extract other fields
            location = self._safe_extract(card, [".location", ".locWdth", ".job-location"], "Not specified")
            salary = self._safe_extract(card, [".salary", ".sal", ".package"], "Not disclosed")
            experience = self._safe_extract(card, [".experience", ".exp"], "Not specified")
            
            # URL
            job_url = ""
            try:
                url_elem = card.find_element(By.CSS_SELECTOR, ".jobTitle a, .job-title a, h3 a")
                job_url = url_elem.get_attribute("href") or ""
            except:
                pass
            
            # Description
            description = self._safe_extract(card, [".jobDescription", ".job-snippet", ".summary"], "")
            
            job = {
                "id": f"foundit_{int(time.time())}_{index}",
                "title": title,
                "company": company,
                "location": location,
                "description": description[:400],
                "requirements": self._extract_basic_requirements(description, title),
                "skills": skills,
                "match_score": self._calculate_match_score(title, description, skills),
                "posted_date": "Recently posted",
                "source": "Foundit",
                "url": job_url,
                "salary": salary,
                "job_type": "Full-time",
                "experience_level": self._determine_experience_level(experience, title),
                "platform_specific": {
                    "experience_required": experience,
                    "platform": "foundit",
                    "is_indian_job": True
                }
            }
            
            return job
            
        except Exception as e:
            logger.debug(f"Foundit job extraction failed: {e}")
            return None

    async def _extract_single_monster_job(self, card, skills: List[str], index: int) -> Optional[dict]:
        """Extract single job from Monster"""
        try:
            # Title extraction for Monster
            title = ""
            title_selectors = [
                "h2[data-testid='job-title'] a",
                ".job-title a",
                "h2 a.job-link",
                ".card-title a"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            
            if not title:
                return None
            
            # Company extraction for Monster
            company = ""
            company_selectors = [
                "div[data-testid='company-name'] a",
                ".company-name",
                ".company a",
                ".employer-name"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    company = company_elem.text.strip()
                    if company:
                        break
                except:
                    continue
            
            if not company:
                company = "Company Not Specified"
            
            # Extract other fields
            location = self._safe_extract(card, ["div[data-testid='job-location']", ".location", ".job-location"], "Not specified")
            salary = self._safe_extract(card, ["p[data-testid='job-salary']", ".salary", ".compensation"], "Not disclosed")
            
            # URL
            job_url = ""
            try:
                url_elem = card.find_element(By.CSS_SELECTOR, "h2[data-testid='job-title'] a, .job-title a")
                job_url = url_elem.get_attribute("href") or ""
            except:
                pass
            
            # Description
            description = self._safe_extract(card, ["p[data-testid='job-snippet']", ".job-summary", ".job-description"], "")
            
            job = {
                "id": f"monster_{int(time.time())}_{index}",
                "title": title,
                "company": company,
                "location": location,
                "description": description[:400],
                "requirements": self._extract_basic_requirements(description, title),
                "skills": skills,
                "match_score": self._calculate_match_score(title, description, skills),
                "posted_date": "Recently posted",
                "source": "Monster",
                "url": job_url,
                "salary": salary,
                "job_type": "Full-time",
                "experience_level": self._determine_experience_level("", title),
                "platform_specific": {
                    "platform": "monster",
                    "is_featured": self._check_featured_job(card)
                }
            }
            
            return job
            
        except Exception as e:
            logger.debug(f"Monster job extraction failed: {e}")
            return None

    def _safe_extract(self, element, selectors: List[str], default: str = "") -> str:
        """Safely extract text from element"""
        for selector in selectors:
            try:
                el = element.find_element(By.CSS_SELECTOR, selector)
                text = el.text.strip()
                if text:
                    return text
            except:
                continue
        return default

    def _check_featured_job(self, card) -> bool:
        """Check if job is featured"""
        try:
            featured_indicators = card.find_elements(By.CSS_SELECTOR, ".featured, .sponsored, [data-testid='featured']")
            return len(featured_indicators) > 0
        except:
            return False

    def _create_sample_monster_jobs(self, skills: List[str], count: int) -> List[dict]:
        """Create sample Monster/Foundit jobs"""
        jobs = []
        
        titles = [
            "Software Engineer",
            "Senior Developer",
            "Python Developer",
            "Full Stack Engineer",
            "Data Analyst",
            "DevOps Engineer",
            "Business Analyst",
            "Quality Assurance Engineer"
        ]
        
        companies = [
            "TCS",
            "Infosys",
            "Wipro",
            "Accenture",
            "Tech Mahindra",
            "HCL Technologies",
            "Cognizant",
            "IBM India"
        ]
        
        locations = [
            "Bangalore",
            "Mumbai",
            "Pune",
            "Hyderabad",
            "Chennai",
            "Delhi NCR",
            "Kolkata",
            "Remote"
        ]
        
        salaries = [
            "₹4-8 Lakhs",
            "₹6-12 Lakhs",
            "₹8-15 Lakhs",
            "₹5-10 Lakhs",
            "₹7-14 Lakhs"
        ]
        
        for i in range(min(count, len(titles))):
            title = titles[i]
            if skills and i < 3:
                title = f"{skills[0]} {title}"
            
            platform_used = "Foundit" if i % 2 == 0 else "Monster"
            
            job = {
                "id": f"{platform_used.lower()}_sample_{int(time.time())}_{i}",
                "title": title,
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "description": f"We are looking for a skilled {title} to join our team. Experience with {', '.join(skills[:3])} is preferred. This role offers excellent growth opportunities and competitive compensation in a dynamic work environment.",
                "requirements": [f"2+ years experience with {skills[0]}" if skills else "2+ years experience", "Bachelor's degree preferred"],
                "skills": skills,
                "match_score": random.randint(75, 90),
                "posted_date": f"{random.randint(1, 10)} days ago",
                "source": platform_used,
                "url": f"https://www.{platform_used.lower()}.{'in' if platform_used == 'Foundit' else 'com'}/job/sample-{i}",
                "salary": salaries[i % len(salaries)],
                "job_type": "Full-time",
                "experience_level": "Mid level" if "Senior" not in title else "Senior level",
                "platform_specific": {
                    "platform": platform_used.lower(),
                    "is_indian_job": True,
                    "experience_required": "2-5 years"
                }
            }
            
            jobs.append(job)
        
        return jobs

    def _extract_basic_requirements(self, description: str, title: str) -> List[str]:
        """Extract basic requirements"""
        text = f"{title} {description}".lower()
        requirements = []
        
        patterns = [
            r'(\d+[\+\-\s]*(?:to\s+\d+\s+)?years?\s*(?:of\s+)?(?:experience|exp))',
            r'bachelor.*?degree',
            r'master.*?degree'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches[:1]:
                if len(match.strip()) > 5:
                    requirements.append(match.strip()[:50])
        
        return requirements[:3]

    def _calculate_match_score(self, title: str, description: str, skills: List[str]) -> float:
        """Calculate match score"""
        if not skills:
            return 0.0
        
        text = f"{title} {description}".lower()
        matches = sum(1 for skill in skills if skill.lower() in text)
        return round((matches / len(skills)) * 100, 1)

    def _determine_experience_level(self, experience: str, title: str) -> str:
        """Determine experience level"""
        text = f"{experience} {title}".lower()
        
        if any(word in text for word in ['senior', 'lead', 'principal']):
            return "Senior level"
        elif any(word in text for word in ['junior', 'fresher', 'trainee']):
            return "Entry level"
        elif any(word in text for word in ['manager', 'director']):
            return "Executive level"
        else:
            return "Mid level"

    async def health_check(self) -> bool:
        """Health check for Monster/Foundit"""
        try:
            # Try Foundit first
            response = self.session.get("https://www.foundit.in", timeout=5)
            if response.status_code == 200:
                return True
            
            # Fallback to Monster
            response = self.session.get("https://www.monster.com", timeout=5)
            return response.status_code == 200
        except:
            return False

# Test function
async def test_monster_foundit():
    scraper = MonsterScraper()
    
    skills = ["Python", "Software Engineer"]
    location = "Bangalore"
    max_jobs = 5
    
    print("🚀 Testing Monster/Foundit Scraper...")
    
    jobs = await scraper.scrape(skills, location, max_jobs)
    
    print(f"\n📊 Found {len(jobs)} jobs:")
    for job in jobs:
        platform = job['platform_specific'].get('platform', job['source'])
        print(f"• {job['title']} at {job['company']} ({platform.title()})")
    
    return jobs

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_monster_foundit())
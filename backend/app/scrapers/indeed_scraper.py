import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import random
from urllib.parse import quote_plus
import time

logger = logging.getLogger(__name__)

class IndeedScraper:
    """Scraper for Indeed job platform"""
    
    def __init__(self):
        self.base_url = "https://www.indeed.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.delay_range = (1, 3)  # Random delay between requests
    
    async def scrape_jobs(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[Dict[str, Any]]:
        """Scrape jobs from Indeed based on skills"""
        try:
            logger.info(f"Starting Indeed scraping for skills: {skills[:3]}...")
            
            # Create search query from skills
            query = self._create_search_query(skills)
            jobs = []
            
            # Try multiple search variations if needed
            search_variations = [
                query,
                f"{skills[0]} developer",  # Use primary skill
                " ".join(skills[:2])       # Use top 2 skills
            ]
            
            for search_query in search_variations:
                if len(jobs) >= max_jobs:
                    break
                    
                try:
                    batch_jobs = await self._scrape_jobs_for_query(search_query, location, max_jobs - len(jobs))
                    jobs.extend(batch_jobs)
                    
                    # Add delay between different queries
                    await asyncio.sleep(random.uniform(*self.delay_range))
                    
                except Exception as e:
                    logger.warning(f"Error scraping Indeed with query '{search_query}': {str(e)}")
                    continue
            
            # Remove duplicates and limit results
            unique_jobs = self._remove_duplicates(jobs)[:max_jobs]
            
            logger.info(f"Indeed scraping completed: {len(unique_jobs)} unique jobs found")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"Indeed scraping failed: {str(e)}")
            return []
    
    async def _scrape_jobs_for_query(self, query: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Scrape jobs for a specific search query"""
        jobs = []
        
        try:
            # Construct search URL
            search_url = self._build_search_url(query, location)
            logger.debug(f"Scraping Indeed URL: {search_url}")
            
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                # Scrape multiple pages if needed
                for page in range(0, min(3, (max_jobs // 10) + 1)):  # Max 3 pages
                    if len(jobs) >= max_jobs:
                        break
                    
                    page_url = f"{search_url}&start={page * 10}"
                    
                    try:
                        page_jobs = await self._scrape_single_page(session, page_url)
                        jobs.extend(page_jobs)
                        
                        # Add delay between pages
                        if page < 2:  # Don't delay after the last page
                            await asyncio.sleep(random.uniform(*self.delay_range))
                            
                    except Exception as e:
                        logger.warning(f"Error scraping Indeed page {page + 1}: {str(e)}")
                        break
            
            return jobs[:max_jobs]
            
        except Exception as e:
            logger.error(f"Error in _scrape_jobs_for_query: {str(e)}")
            return []
    
    async def _scrape_single_page(self, session: aiohttp.ClientSession, url: str) -> List[Dict[str, Any]]:
        """Scrape a single page of job results"""
        jobs = []
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Indeed page returned status {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find job cards - Indeed uses different selectors
                job_cards = soup.find_all(['div'], class_=re.compile(r'job_seen_beacon|result|jobsearch-SerpJobCard'))
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.find_all(['div'], attrs={'data-jk': True})
                
                if not job_cards:
                    logger.warning("No job cards found on Indeed page")
                    return []
                
                logger.debug(f"Found {len(job_cards)} job cards on Indeed page")
                
                for card in job_cards:
                    try:
                        job_data = self._extract_job_data(card)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.debug(f"Error extracting Indeed job data: {str(e)}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping Indeed page: {str(e)}")
        
        return jobs
    
    def _extract_job_data(self, card) -> Optional[Dict[str, Any]]:
        """Extract job data from a job card"""
        try:
            # Extract title
            title_elem = card.find(['h2', 'a'], attrs={'data-jk': True}) or \
                        card.find(['span'], title=True) or \
                        card.find(['a'], class_=re.compile(r'jobTitle'))
            
            if not title_elem:
                return None
            
            title = title_elem.get('title', '') or title_elem.get_text(strip=True)
            if not title:
                return None
            
            # Extract company
            company_elem = card.find(['span', 'a'], class_=re.compile(r'companyName')) or \
                          card.find(['span'], attrs={'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = card.find(['div', 'span'], attrs={'data-testid': 'job-location'}) or \
                           card.find(['div'], class_=re.compile(r'companyLocation'))
            location = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Extract job URL
            job_link = card.find('a', attrs={'data-jk': True})
            job_url = ""
            if job_link and job_link.get('href'):
                job_url = self.base_url + job_link['href']
            
            # Extract salary if available
            salary_elem = card.find(['span'], class_=re.compile(r'salary|estimated-salary'))
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            # Extract job description snippet
            description_elem = card.find(['div'], class_=re.compile(r'summary|job-snippet'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract posted date
            date_elem = card.find(['span'], class_=re.compile(r'date'))
            posted_date = date_elem.get_text(strip=True) if date_elem else "Unknown"
            
            # Extract requirements/skills from description
            requirements = self._extract_requirements_from_text(title + " " + description)
            
            return {
                'id': f"indeed_{hash(job_url or title + company)}",
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirements': requirements,
                'skills': requirements,  # Use requirements as skills for now
                'posted_date': posted_date,
                'source': 'Indeed',
                'url': job_url,
                'salary': salary,
                'job_type': 'Full-time',  # Default
                'experience_level': self._extract_experience_level(title + " " + description)
            }
            
        except Exception as e:
            logger.debug(f"Error extracting Indeed job data: {str(e)}")
            return None
    
    def _create_search_query(self, skills: List[str]) -> str:
        """Create search query from skills list"""
        # Use top 3-4 skills to avoid too broad search
        primary_skills = skills[:4]
        return " ".join(primary_skills)
    
    def _build_search_url(self, query: str, location: str) -> str:
        """Build Indeed search URL"""
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(location)
        
        return f"{self.base_url}/jobs?q={encoded_query}&l={encoded_location}&sort=date"
    
    def _extract_requirements_from_text(self, text: str) -> List[str]:
        """Extract technical requirements/skills from job text"""
        if not text:
            return []
        
        # Common technical skills to look for
        tech_skills = [
            'Python', 'JavaScript', 'Java', 'React', 'Node.js', 'Angular', 'Vue',
            'TypeScript', 'PHP', 'Ruby', 'Go', 'Rust', 'C++', 'C#', 'Swift',
            'HTML', 'CSS', 'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'Jenkins',
            'Django', 'Flask', 'Spring', 'Express', 'Laravel', 'Rails'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in tech_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to top 10
    
    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from job text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['senior', 'lead', 'principal', 'staff']):
            return 'Senior'
        elif any(word in text_lower for word in ['junior', 'entry', 'graduate', 'intern']):
            return 'Junior'
        else:
            return 'Mid-level'
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def test_connection(self) -> bool:
        """Test if Indeed is accessible"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.base_url}/jobs?q=python&l=remote", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Indeed connection test failed: {str(e)}")
            return False
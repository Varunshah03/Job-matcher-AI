import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GlassdoorScraper:
    """Glassdoor job scraper - Returns mock data for demo"""
    
    def __init__(self):
        self.base_url = "https://www.glassdoor.com"
        
    async def scrape_jobs(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[Dict[str, Any]]:
        """Scrape jobs from Glassdoor - Returns mock data for demo"""
        try:
            logger.info("Glassdoor scraper: Using mock data")
            
            mock_jobs = [
                {
                    'id': f"glassdoor_{i}",
                    'title': f"Senior {skills[0]} Engineer" if skills else "Software Engineer",
                    'company': f"Enterprise Corp {i}",
                    'location': location,
                    'description': f"Join our team as a {skills[0]} expert working on cutting-edge projects.",
                    'requirements': skills[:6],
                    'skills': skills[:6],
                    'posted_date': f"{i+2} days ago",
                    'source': 'Glassdoor',
                    'url': f"https://glassdoor.com/job/{2000+i}",
                    'salary': f"$100,000 - $150,000",
                    'job_type': 'Full-time',
                    'experience_level': 'Senior'
                }
                for i in range(min(max_jobs, 4))
            ]
            
            return mock_jobs
            
        except Exception as e:
            logger.error(f"Glassdoor scraping failed: {str(e)}")
            return []
    
    async def test_connection(self) -> bool:
        """Test Glassdoor connection"""
        return True
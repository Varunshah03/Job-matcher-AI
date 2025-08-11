from abc import ABC, abstractmethod
from typing import List

class BaseScraper(ABC):
    def __init__(self, platform: str, base_url: str):
        self.platform = platform
        self.base_url = base_url

    @abstractmethod
    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        """Scrape jobs based on skills and location."""
        pass
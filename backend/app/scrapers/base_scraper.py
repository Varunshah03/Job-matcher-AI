from abc import ABC, abstractmethod
from typing import List
import sys
import os
from pathlib import Path

# Add parent directory to path for env_loader and chrome_driver_utils
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now we can import from the app directory
try:
    from env_loader import get_credentials
    from chrome_driver_utils import create_stealth_driver, login_to_site
except ImportError as e:
    print(f"Warning: Could not import utilities: {e}")
    # Provide fallback functions
    def get_credentials(platform):
        return None, None
    def create_stealth_driver():
        return None
    def login_to_site(*args, **kwargs):
        return False

class BaseScraper(ABC):
    def __init__(self, platform: str, base_url: str):
        self.platform = platform
        self.base_url = base_url
        
        # Get credentials for this platform
        self.email, self.password = get_credentials(platform.lower())

    @abstractmethod
    async def scrape(self, skills: List[str], location: str = "Remote", max_jobs: int = 10) -> List[dict]:
        """Scrape jobs based on skills and location."""
        pass
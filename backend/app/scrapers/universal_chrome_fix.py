import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

async def create_universal_chrome_driver(page_load_timeout=30):
    """
    Universal Chrome driver that works across different Chrome versions
    Use this exact function in ALL your scrapers
    """
    chrome_options = Options()
    
    # Basic headless options that work on all Chrome versions
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User agent (helps avoid detection)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Performance optimizations
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--disable-javascript")  # Many sites work without JS
    
    # Try multiple driver creation methods
    driver = None
    
    # Method 1: Try undetected-chromedriver (best for avoiding detection)
    try:
        logger.info("Trying undetected-chromedriver...")
        driver = uc.Chrome(options=chrome_options, version_main=None)
        logger.info("✅ Using undetected-chromedriver")
    except Exception as e:
        logger.warning(f"Undetected-chromedriver failed: {e}")
        
        # Method 2: Try regular Selenium WebDriver
        try:
            logger.info("Trying regular Chrome WebDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Using regular Chrome WebDriver")
        except Exception as e2:
            logger.warning(f"Regular WebDriver failed: {e2}")
            
            # Method 3: Try with explicit service
            try:
                logger.info("Trying Chrome with Service...")
                service = Service()
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Using Chrome with Service")
            except Exception as e3:
                logger.error(f"All driver methods failed: {e3}")
                raise Exception("Could not create Chrome driver with any method")
    
    if driver:
        driver.set_page_load_timeout(page_load_timeout)
        
        # Basic anti-detection (works on all versions)
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except:
            pass  # Some versions don't support this
    
    return driver

# REPLACEMENT CODE FOR ALL SCRAPERS
# Replace the _create_driver method in ALL your scrapers with this:

"""
async def _create_driver(self) -> webdriver.Chrome:
    '''Create compatible Chrome driver'''
    from universal_chrome_fix import create_universal_chrome_driver
    return await create_universal_chrome_driver(self.page_load_timeout)
"""
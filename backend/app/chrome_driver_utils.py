# chrome_driver_utils.py - Modern Chrome driver setup
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

def create_stealth_driver(headless=False, proxy=None):
    """Create a stealth Chrome driver with modern options"""
    try:
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent rotation
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Performance optimizations
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Remove if JS is needed
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        if headless:
            options.add_argument('--headless=new')
        
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        
        # Create driver with version management
        driver = uc.Chrome(options=options, version_main=None)
        
        # Execute script to hide automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        print(f"Failed to create driver: {e}")
        return None

def login_to_site(driver, email, password, login_url, email_selector, password_selector, submit_selector):
    """Generic login function for job sites"""
    try:
        driver.get(login_url)
        time.sleep(random.uniform(2, 4))
        
        # Wait for email field and enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_selector))
        )
        email_field.clear()
        email_field.send_keys(email)
        time.sleep(random.uniform(1, 2))
        
        # Enter password
        password_field = driver.find_element(By.CSS_SELECTOR, password_selector)
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(random.uniform(1, 2))
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, submit_selector)
        submit_button.click()
        
        # Wait for redirect/login completion
        time.sleep(random.uniform(3, 5))
        
        return True
        
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def handle_anti_bot_measures(driver):
    """Handle common anti-bot measures"""
    try:
        # Check for CAPTCHA
        captcha_selectors = [
            'div[class*="captcha"]',
            'div[class*="recaptcha"]',
            '#captcha',
            '.g-recaptcha'
        ]
        
        for selector in captcha_selectors:
            try:
                captcha = driver.find_element(By.CSS_SELECTOR, selector)
                if captcha.is_displayed():
                    print("CAPTCHA detected - manual intervention needed")
                    input("Please solve CAPTCHA and press Enter to continue...")
                    break
            except:
                continue
                
        # Check for access denied pages
        page_source = driver.page_source.lower()
        if any(phrase in page_source for phrase in ['access denied', 'blocked', 'forbidden']):
            print("Access blocked detected")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error handling anti-bot measures: {e}")
        return False

def add_random_delays():
    """Add human-like delays"""
    time.sleep(random.uniform(1, 3))

def scroll_page(driver, pause_time=2):
    """Scroll page to simulate human behavior"""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(pause_time)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause_time)
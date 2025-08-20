# final_scraper_test.py
"""
Test your scrapers with the working Chrome configuration
"""

import asyncio
import sys
import time
import types
from pathlib import Path
sys.path.append('..')
from env_loader import get_credentials
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Setup paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "scrapers"))

# Create BaseScraper
class BaseScraper:
    def __init__(self, platform: str, base_url: str):
        self.platform = platform
        self.base_url = base_url

    async def scrape(self, skills, location="Remote", max_jobs=10):
        pass

# Add to modules
base_module = types.ModuleType('base_scraper')
base_module.BaseScraper = BaseScraper
sys.modules['base_scraper'] = base_module
sys.modules['scrapers.base_scraper'] = base_module

def create_working_chrome_driver():
    """Create Chrome driver using the working configuration"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=chrome_options, version_main=138)
    driver.set_page_load_timeout(30)
    return driver

def patch_scraper_driver_creation(scraper_instance):
    """Replace the scraper's driver creation with our working version"""
    
    async def patched_create_driver(self):
        return create_working_chrome_driver()
    
    # Replace the method
    scraper_instance._create_driver = patched_create_driver.__get__(scraper_instance, type(scraper_instance))
    scraper_instance._create_optimized_driver = patched_create_driver.__get__(scraper_instance, type(scraper_instance))

def import_and_patch_scraper(module_name, class_name):
    """Import scraper and patch its driver creation"""
    try:
        file_path = current_dir / "scrapers" / f"{module_name}.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix imports
        content = content.replace("from .base_scraper import BaseScraper", "from base_scraper import BaseScraper")
        
        # Create module
        module = types.ModuleType(module_name)
        exec(content, module.__dict__)
        
        # Get the class and create instance
        scraper_class = getattr(module, class_name)
        scraper_instance = scraper_class()
        
        # Patch the driver creation method
        if hasattr(scraper_instance, '_create_driver'):
            patch_scraper_driver_creation(scraper_instance)
            print(f"   🔧 Patched Chrome driver for {class_name}")
        
        return scraper_instance
        
    except Exception as e:
        print(f"❌ Failed to import/patch {class_name}: {e}")
        return None

async def test_scraper_with_working_chrome(name, scraper):
    """Test a scraper with working Chrome configuration"""
    print(f"\n🧪 Testing {name} with fixed Chrome...")
    
    try:
        # Quick scrape test
        start_time = time.time()
        result = await asyncio.wait_for(
            scraper.scrape(skills=["Python"], location="Remote", max_jobs=2),
            timeout=25  # Shorter timeout since Chrome is working
        )
        
        execution_time = time.time() - start_time
        
        # Handle results
        if isinstance(result, tuple):
            jobs = result[0]
        else:
            jobs = result
        
        job_count = len(jobs) if jobs else 0
        
        print(f"   ✅ Completed in {execution_time:.1f}s")
        print(f"   📊 Found {job_count} jobs")
        
        if jobs and len(jobs) > 0:
            sample = jobs[0]
            title = sample.get('title', 'No title')[:50]
            company = sample.get('company', 'No company')[:30]
            print(f"   📝 Sample: {title} at {company}")
        
        return job_count > 0
        
    except asyncio.TimeoutError:
        print(f"   ⏰ {name} timed out (25s)")
        return False
    except Exception as e:
        print(f"   ❌ {name} error: {str(e)[:100]}")
        return False

async def main():
    print("🚀 FINAL SCRAPER TEST WITH WORKING CHROME")
    print("="*50)
    
    # Test scrapers in order of likelihood to work
    scrapers_to_test = [
        ("Himalayas", "himalayas_scraper", "HimalayasScraper"),  # API-based, should work
        ("Indeed", "indeed_scraper", "IndeedScraper"),          # Popular, good chance
        ("Naukri", "naukri_scraper", "NaukriScraper"),          # Your enhanced version
        ("Monster", "monster_scraper", "MonsterScraper"),       # Simpler structure
        ("Dice", "dice_scraper", "DiceScraper"),                # Tech-focused
    ]
    
    working_scrapers = []
    failed_scrapers = []
    
    for name, module, class_name in scrapers_to_test:
        print(f"\n📦 Setting up {name}...")
        
        scraper = import_and_patch_scraper(module, class_name)
        
        if scraper:
            success = await test_scraper_with_working_chrome(name, scraper)
            if success:
                working_scrapers.append(name)
            else:
                failed_scrapers.append(name)
        else:
            failed_scrapers.append(name)
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    # Final results
    print(f"\n{'='*50}")
    print("🎉 FINAL RESULTS")
    print(f"{'='*50}")
    print(f"✅ Working scrapers: {working_scrapers}")
    print(f"❌ Failed scrapers: {failed_scrapers}")
    print(f"📊 Success rate: {len(working_scrapers)}/{len(scrapers_to_test)} ({len(working_scrapers)/len(scrapers_to_test)*100:.1f}%)")
    
    if working_scrapers:
        print(f"\n🎯 SUCCESS! You have {len(working_scrapers)} working job scrapers!")
        print("💡 You can now use these for your job matching system.")
        
        if failed_scrapers:
            print(f"\n🔧 To improve further:")
            print(f"   - Failed scrapers might need site-specific fixes")
            print(f"   - Some sites may be blocking automated access")
            print(f"   - Try running at different times or with proxies")
    else:
        print(f"\n🚨 No scrapers worked completely.")
        print(f"   This might be due to:")
        print(f"   - Website anti-bot measures")
        print(f"   - Network connectivity issues")
        print(f"   - Sites requiring login/authentication")

if __name__ == "__main__":
    asyncio.run(main())
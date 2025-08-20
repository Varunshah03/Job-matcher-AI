# fixed_simple_test.py
"""
Fixed version that handles the relative import issues by manually resolving them
"""

import asyncio
import sys
import time
import importlib.util
from pathlib import Path

print("🔧 FIXING IMPORT ISSUES AND TESTING SCRAPERS")
print("="*60)

current_dir = Path(__file__).parent
scrapers_dir = current_dir / "scrapers"

print(f"📁 Current directory: {current_dir}")
print(f"📁 Scrapers directory: {scrapers_dir}")

# Add to Python path
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(scrapers_dir))

def create_base_scraper_module():
    """Create the BaseScraper class manually to fix import issues"""
    
    base_scraper_code = '''
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
'''
    
    # Create the module
    spec = importlib.util.spec_from_loader("base_scraper", loader=None)
    module = importlib.util.module_from_spec(spec)
    
    # Execute the code
    exec(base_scraper_code, module.__dict__)
    
    # Add to sys.modules so imports can find it
    sys.modules["base_scraper"] = module
    sys.modules["scrapers.base_scraper"] = module
    
    return module

def fix_scraper_imports(file_path, module_name):
    """Fix a scraper's imports by replacing relative imports"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the relative import
        content = content.replace(
            "from .base_scraper import BaseScraper",
            "from base_scraper import BaseScraper"
        )
        
        # Create and execute the module
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules first
        sys.modules[module_name] = module
        sys.modules[f"scrapers.{module_name}"] = module
        
        # Execute the fixed code
        exec(content, module.__dict__)
        
        return module
        
    except Exception as e:
        print(f"❌ Error fixing imports for {module_name}: {e}")
        return None

def import_scraper_class(module_name, class_name):
    """Import a scraper class with fixed imports"""
    file_path = scrapers_dir / f"{module_name}.py"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"📦 Importing {class_name} from {module_name}...")
    
    # Fix imports and load module
    module = fix_scraper_imports(file_path, module_name)
    
    if module is None:
        return None
    
    try:
        scraper_class = getattr(module, class_name)
        print(f"✅ Successfully imported {class_name}")
        return scraper_class
    except AttributeError:
        print(f"❌ Class {class_name} not found in {module_name}")
        return None

async def test_scraper(scraper_name, scraper_class):
    """Test a single scraper"""
    print(f"\n{'='*50}")
    print(f"🧪 TESTING: {scraper_name}")
    print(f"{'='*50}")
    
    try:
        # Create instance
        print("1. Creating scraper instance...")
        scraper = scraper_class()
        print("   ✅ Instance created successfully")
        
        # Test health check
        print("2. Testing health check...")
        if hasattr(scraper, 'health_check'):
            try:
                health_result = await scraper.health_check()
                
                if isinstance(health_result, tuple):
                    is_healthy = health_result[0]
                else:
                    is_healthy = bool(health_result)
                
                print(f"   {'✅' if is_healthy else '❌'} Health check: {'PASSED' if is_healthy else 'FAILED'}")
            except Exception as e:
                print(f"   ⚠️  Health check error: {e}")
        else:
            print("   ⚠️  No health check method")
        
        # Test scraping
        print("3. Testing scrape method...")
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                scraper.scrape(skills=["Python"], location="Remote", max_jobs=2),
                timeout=30  # Short timeout for testing
            )
            
            execution_time = time.time() - start_time
            
            # Handle different return types
            if isinstance(result, tuple):
                jobs = result[0]
            else:
                jobs = result
            
            job_count = len(jobs) if jobs else 0
            
            print(f"   ✅ Scraping completed in {execution_time:.1f}s")
            print(f"   📊 Jobs found: {job_count}")
            
            if jobs and len(jobs) > 0:
                sample = jobs[0]
                print(f"   📝 Sample: {sample.get('title', 'No title')} at {sample.get('company', 'No company')}")
            
            print(f"   🎉 RESULT: {'✅ SUCCESS' if job_count > 0 else '⚠️ NO JOBS (but working)'}")
            return True
            
        except asyncio.TimeoutError:
            print("   ❌ TIMEOUT: Took longer than 30 seconds")
            return False
        except Exception as e:
            print(f"   ❌ SCRAPING ERROR: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ SETUP ERROR: {e}")
        return False

async def main():
    print("🔧 Setting up base scraper...")
    create_base_scraper_module()
    print("✅ Base scraper ready")
    
    # List of scrapers to test
    scrapers_to_test = [
        ("Himalayas", "himalayas_scraper", "HimalayasScraper"),     # API-based, should be fastest
        ("Naukri", "naukri_scraper", "NaukriScraper"),             # Your main scraper
        ("Indeed", "indeed_scraper", "IndeedScraper"),             # Popular platform
        ("Monster", "monster_scraper", "MonsterScraper"),          # Simple structure
        ("Dice", "dice_scraper", "DiceScraper"),                   # Tech-focused
    ]
    
    successful = 0
    failed = 0
    
    print(f"\n🚀 Starting tests for {len(scrapers_to_test)} scrapers...")
    
    for scraper_name, module_name, class_name in scrapers_to_test:
        try:
            scraper_class = import_scraper_class(module_name, class_name)
            
            if scraper_class is None:
                failed += 1
                continue
            
            # Test the scraper
            success = await test_scraper(scraper_name, scraper_class)
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Brief pause between tests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to test {scraper_name}: {e}")
            failed += 1
    
    # Final results
    print(f"\n{'='*60}")
    print("🎉 TESTING COMPLETE!")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {successful + failed}")
    
    if successful > 0:
        success_rate = (successful / (successful + failed)) * 100
        print(f"🎯 Success rate: {success_rate:.1f}%")
        print("✨ Great! Some scrapers are working!")
    else:
        print("🚨 All scrapers failed. Check:")
        print("   1. Internet connection")
        print("   2. ChromeDriver installation")
        print("   3. Website accessibility")

if __name__ == "__main__":
    asyncio.run(main())
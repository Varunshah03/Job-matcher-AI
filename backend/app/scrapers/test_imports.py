# test_imports.py - Place this in your scrapers/ folder to test imports
import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

print("🔧 Testing imports...")

# Test 1: Import utilities from parent directory
try:
    from env_loader import get_credentials
    print("✅ env_loader imported successfully")
    
    # Test credentials
    email, password = get_credentials('naukri')
    if email and password:
        print(f"✅ Credentials loaded: {email} / {'*' * len(password)}")
    else:
        print("⚠️  No credentials found (check .env file)")
        
except ImportError as e:
    print(f"❌ Failed to import env_loader: {e}")

try:
    from chrome_driver_utils import create_stealth_driver
    print("✅ chrome_driver_utils imported successfully")
except ImportError as e:
    print(f"❌ Failed to import chrome_driver_utils: {e}")

# Test 2: Import base scraper from same directory
try:
    from base_scraper import BaseScraper
    print("✅ BaseScraper imported successfully")
except ImportError as e:
    print(f"❌ Failed to import BaseScraper: {e}")

# Test 3: Import specific scrapers
scrapers_to_test = [
    ("indeed_scraper", "IndeedScraper"),
    ("himalayas_scraper", "HimalayasScraper"),
    ("naukri_scraper", "NaukriScraper")
]

for module_name, class_name in scrapers_to_test:
    try:
        module = __import__(module_name)
        scraper_class = getattr(module, class_name)
        
        # Try to instantiate
        scraper = scraper_class()
        print(f"✅ {class_name} imported and instantiated successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import {class_name}: {e}")
    except Exception as e:
        print(f"❌ Failed to instantiate {class_name}: {e}")

print("\n🎯 Import test completed!")
print("If you see ✅ for most items, your imports are working correctly.")
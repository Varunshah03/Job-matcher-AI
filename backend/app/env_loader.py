# env_loader.py - Fixed version for your backend/app directory
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LinkedIn credentials
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    
    # Indeed credentials
    INDEED_EMAIL = os.getenv('INDEED_EMAIL')
    INDEED_PASSWORD = os.getenv('INDEED_PASSWORD')
    
    # Naukri credentials
    NAUKRI_EMAIL = os.getenv('NAUKRI_EMAIL')
    NAUKRI_PASSWORD = os.getenv('NAUKRI_PASSWORD')
    
    # Glassdoor credentials
    GLASSDOOR_EMAIL = os.getenv('GLASSDOOR_EMAIL')
    GLASSDOOR_PASSWORD = os.getenv('GLASSDOOR_PASSWORD')
    
    # Dice credentials
    DICE_EMAIL = os.getenv('DICE_EMAIL')
    DICE_PASSWORD = os.getenv('DICE_PASSWORD')
    
    # Foundit credentials
    FOUNDIT_EMAIL = os.getenv('FOUNDIT_EMAIL')
    FOUNDIT_PASSWORD = os.getenv('FOUNDIT_PASSWORD')
    
    # ZipRecruiter credentials
    ZIPRECRUITER_EMAIL = os.getenv('ZIPRECRUITER_EMAIL')
    ZIPRECRUITER_PASSWORD = os.getenv('ZIPRECRUITER_PASSWORD')

# Usage function
def get_credentials(platform):
    """Get credentials for a specific platform"""
    credentials = {
        'linkedin': (Config.LINKEDIN_EMAIL, Config.LINKEDIN_PASSWORD),
        'indeed': (Config.INDEED_EMAIL, Config.INDEED_PASSWORD),
        'naukri': (Config.NAUKRI_EMAIL, Config.NAUKRI_PASSWORD),
        'glassdoor': (Config.GLASSDOOR_EMAIL, Config.GLASSDOOR_PASSWORD),
        'dice': (Config.DICE_EMAIL, Config.DICE_PASSWORD),
        'foundit': (Config.FOUNDIT_EMAIL, Config.FOUNDIT_PASSWORD),
        'ziprecruiter': (Config.ZIPRECRUITER_EMAIL, Config.ZIPRECRUITER_PASSWORD)
    }
    return credentials.get(platform.lower(), (None, None))

# Test function to verify credentials are loaded
def test_credentials():
    """Test if credentials are loaded correctly"""
    print("🔐 Testing credential loading...")
    
    platforms = ['linkedin', 'indeed', 'naukri', 'glassdoor', 'dice', 'foundit', 'ziprecruiter']
    
    for platform in platforms:
        email, password = get_credentials(platform)
        if email and password:
            print(f"✅ {platform.capitalize()}: {email} / {'*' * len(password)}")
        else:
            print(f"❌ {platform.capitalize()}: Missing credentials")

if __name__ == "__main__":
    test_credentials()
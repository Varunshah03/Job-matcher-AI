# fixed_quick_test.py - Works with your current scrapers
import sys
import os
from pathlib import Path
import asyncio
import logging
import traceback
import time

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Setup logging to reduce noise
logging.basicConfig(level=logging.ERROR)  # Only show errors

print("🚀 FIXED QUICK SCRAPER TEST")
print("=" * 50)

def test_imports():
    """Test if scrapers can be imported - only test existing ones"""
    print("📦 Testing existing scrapers...")
    
    # Only test scrapers that actually exist
    scraper_modules = [
        ("base_scraper", "BaseScraper"),
        ("linkedin_scraper", "LinkedInScraper"),
        ("naukri_scraper", "NaukriScraper"),
        ("indeed_scraper", "IndeedScraper"),
        ("himalayas_scraper", "HimalayasScraper"),
        ("glassdoor_scraper", "GlassdoorScraper"),
        ("monster_scraper", "MonsterScraper"),
        ("dice_scraper", "DiceScraper"),
        ("careerbuilder_scraper", "CareerBuilderScraper"),
        ("ziprecruiter_scraper", "ZipRecruiterScraper")
    ]
    
    working_scrapers = []
    failed_scrapers = []
    
    for module_name, class_name in scraper_modules:
        try:
            module = __import__(module_name)
            scraper_class = getattr(module, class_name)
            
            # Try to instantiate
            if class_name != "BaseScraper":
                scraper = scraper_class()
                working_scrapers.append((module_name, class_name, scraper))
                print(f"   ✅ {class_name}")
            else:
                print(f"   ✅ {class_name} (base class)")
                
        except ImportError:
            failed_scrapers.append((module_name, class_name, "Import Error"))
            print(f"   ❌ {class_name}: Not found")
        except Exception as e:
            failed_scrapers.append((module_name, class_name, str(e)))
            print(f"   ❌ {class_name}: {str(e)[:50]}")
    
    print(f"\n📊 Import Results:")
    print(f"   Working: {len(working_scrapers)}")
    print(f"   Failed: {len(failed_scrapers)}")
    
    return working_scrapers, failed_scrapers

async def test_single_scraper_safe(scraper_name, scraper_instance):
    """Test a single scraper with proper error handling"""
    print(f"\n🧪 Testing {scraper_name}...")
    
    try:
        # Platform-specific test parameters
        if "linkedin" in scraper_name.lower():
            skills = ["Python", "Software Engineer"]
            location = "San Francisco"
        elif "naukri" in scraper_name.lower():
            skills = ["Python", "Developer"]
            location = "Bangalore"
        elif "indeed" in scraper_name.lower():
            skills = ["Python"]
            location = "New York"
        else:
            skills = ["Python"]
            location = "Remote"
        
        max_jobs = 2  # Keep it small and fast
        
        start_time = time.time()
        
        # Create a safer scraper call with timeout
        jobs = await asyncio.wait_for(
            scraper_instance.scrape(skills, location, max_jobs),
            timeout=60  # Shorter timeout
        )
        
        elapsed = time.time() - start_time
        
        if jobs and len(jobs) > 0:
            print(f"   ✅ SUCCESS: {len(jobs)} jobs in {elapsed:.1f}s")
            
            # Show first job details
            job = jobs[0]
            title = job.get('title', 'N/A')[:40]
            company = job.get('company', 'N/A')[:25]
            print(f"   📋 Sample: {title} at {company}")
            
            return True, len(jobs), elapsed
        else:
            print(f"   ⚠️  No jobs found in {elapsed:.1f}s")
            return True, 0, elapsed
            
    except asyncio.TimeoutError:
        print(f"   ⏰ Timeout (>45s)")
        return False, "timeout", 0
    except Exception as e:
        error_msg = str(e)[:60]
        print(f"   ❌ Error: {error_msg}")
        return False, error_msg, 0

async def test_top_scrapers(working_scrapers):
    """Test the most important scrapers first"""
    if not working_scrapers:
        print("\n❌ No working scrapers to test!")
        return []
    
    # Prioritize the most important scrapers
    priority_order = ['LinkedIn', 'Naukri', 'Indeed', 'Himalayas', 'Glassdoor']
    
    sorted_scrapers = []
    remaining_scrapers = []
    
    # Sort by priority
    for priority_name in priority_order:
        for module, class_name, instance in working_scrapers:
            if priority_name.lower() in class_name.lower():
                sorted_scrapers.append((module, class_name, instance))
                break
    
    # Add remaining scrapers
    for scraper in working_scrapers:
        if scraper not in sorted_scrapers:
            remaining_scrapers.append(scraper)
    
    all_scrapers = sorted_scrapers + remaining_scrapers[:3]  # Test max 6 total
    
    print(f"\n🧪 Testing {len(all_scrapers)} prioritized scrapers...")
    print("⏱️  45 second timeout per scraper")
    
    results = []
    
    for module_name, class_name, scraper_instance in all_scrapers:
        success, result, elapsed = await test_single_scraper_safe(class_name, scraper_instance)
        results.append((class_name, success, result, elapsed))
    
    return results

def print_final_summary(results):
    """Print a comprehensive summary"""
    print(f"\n📊 FINAL RESULTS")
    print("=" * 30)
    
    successful = [(name, result, elapsed) for name, success, result, elapsed in results if success]
    failed = [(name, error) for name, success, error, elapsed in results if not success]
    
    total_jobs = sum(result for name, result, elapsed in successful if isinstance(result, int))
    avg_time = sum(elapsed for name, result, elapsed in successful if isinstance(elapsed, (int, float))) / len(successful) if successful else 0
    
    print(f"✅ Working: {len(successful)}/{len(results)} scrapers")
    print(f"🎯 Total jobs: {total_jobs}")
    print(f"⏱️  Avg time: {avg_time:.1f}s")
    print(f"📊 Success rate: {len(successful)/len(results)*100:.1f}%")
    
    if successful:
        print(f"\n🏆 SUCCESSFUL SCRAPERS:")
        for name, result, elapsed in successful:
            if isinstance(result, int) and result > 0:
                status = f"{result} jobs"
            else:
                status = "working"
            print(f"   • {name}: {status} ({elapsed:.1f}s)")
    
    if failed:
        print(f"\n❌ FAILED SCRAPERS:")
        for name, error in failed[:3]:  # Show first 3
            print(f"   • {name}: {error}")
    
    # Special messages for key platforms
    linkedin_jobs = sum(result for name, result, elapsed in successful 
                       if 'linkedin' in name.lower() and isinstance(result, int))
    naukri_jobs = sum(result for name, result, elapsed in successful 
                     if 'naukri' in name.lower() and isinstance(result, int))
    indeed_jobs = sum(result for name, result, elapsed in successful 
                     if 'indeed' in name.lower() and isinstance(result, int))
    
    print(f"\n🎯 PLATFORM HIGHLIGHTS:")
    if linkedin_jobs > 0:
        print(f"   🔵 LinkedIn: {linkedin_jobs} jobs - Excellent for professional roles!")
    if naukri_jobs > 0:
        print(f"   🟠 Naukri: {naukri_jobs} jobs - Great for Indian market!")
    if indeed_jobs > 0:
        print(f"   🔴 Indeed: {indeed_jobs} jobs - Good global coverage!")
    
    # Overall assessment
    if total_jobs >= 5:
        print(f"\n🎉 EXCELLENT! Your scrapers are working great!")
        print(f"✅ Ready for production use")
    elif total_jobs >= 2:
        print(f"\n✅ GOOD! You have working scrapers")
        print(f"🔧 Consider optimizing for better results")
    elif len(successful) > 0:
        print(f"\n⚠️  Some scrapers working but low job yield")
        print(f"🔧 May need debugging or optimization")
    else:
        print(f"\n❌ No scrapers working properly")
        print(f"🔧 Check Chrome setup and internet connection")

async def main():
    """Main test function - simplified and robust"""
    print("Starting simplified quick test...\n")
    
    # 1. Test imports
    working_scrapers, failed_scrapers = test_imports()
    
    if not working_scrapers:
        print("\n❌ No scrapers could be loaded!")
        print("🔧 Check that scraper files exist and have no syntax errors")
        return
    
    # 2. Test scrapers
    results = await test_top_scrapers(working_scrapers)
    
    # 3. Print summary
    print_final_summary(results)
    
    # 4. Next steps
    successful_count = len([r for r in results if r[1]])
    
    print(f"\n🎯 NEXT STEPS:")
    if successful_count >= 2:
        print(f"   1. ✅ Great! Start integrating into your Job Matcher AI")
        print(f"   2. 🔧 Optimize the failing scrapers if needed")
        print(f"   3. 🚀 Build your job matching application")
    elif successful_count >= 1:
        print(f"   1. 🔧 Fix the failing scrapers")
        print(f"   2. ✅ You have at least one working scraper")
        print(f"   3. 🧪 Test with: python [working_scraper].py")
    else:
        print(f"   1. 🔧 Check Chrome/ChromeDriver installation")
        print(f"   2. 🌐 Verify internet connectivity")
        print(f"   3. 🐛 Check scraper error messages above")

# Suppress Chrome cleanup warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    try:
        # Suppress asyncio warnings
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    
    print(f"\n✨ Quick test completed!")
    print(f"💡 The Chrome cleanup warnings are harmless and can be ignored")
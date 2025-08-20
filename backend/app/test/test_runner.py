# test_runner.py
"""
Simple test runner for your job scrapers
Put this file in your backend directory
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory and scrapers to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "scrapers"))

print(f"🔧 Current directory: {current_dir}")
print(f"🔧 Python path: {sys.path[-2:]}")

# Import the testing framework (you'll need to have the framework file)
try:
    from job_scraper_test_framework import JobScraperTester, TestCase
    print("✅ Testing framework imported successfully")
except ImportError as e:
    print(f"❌ Failed to import testing framework: {e}")
    print("📝 Make sure you have the job_scraper_test_framework.py file in this directory")
    sys.exit(1)

# Try to import your scrapers
scrapers_imported = {}

# List of your scraper files (based on what I see in your VS Code)
scraper_files = [
    ("naukri_scraper", "EnhancedNaukriScraper"),
    ("ziprecruiter_scraper", "ZipRecruiterScraper"), 
    ("careerbuilder_scraper", "CareerBuilderScraper"),
    ("dice_scraper", "DiceScraper"),
    ("monster_scraper", "MonsterScraper"),
    ("himalayas_scraper", "HimalayasScraper")
]

print("\n🔍 Attempting to import scrapers...")

for module_name, class_name in scraper_files:
    try:
        # Try to import from scrapers directory
        module = __import__(f"scrapers.{module_name}", fromlist=[class_name])
        scraper_class = getattr(module, class_name)
        scrapers_imported[class_name.replace("Scraper", "")] = scraper_class
        print(f"✅ {class_name} imported successfully")
    except ImportError as e:
        print(f"⚠️  Failed to import {class_name}: {e}")
    except AttributeError as e:
        print(f"⚠️  Class {class_name} not found in {module_name}: {e}")

if not scrapers_imported:
    print("❌ No scrapers could be imported!")
    print("📝 Check that your scraper files exist and have the correct class names")
    sys.exit(1)

print(f"\n✅ Successfully imported {len(scrapers_imported)} scrapers")

async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🚀 JOB SCRAPER TESTING SUITE")
    print("="*60)
    
    # Initialize tester
    tester = JobScraperTester(output_dir="test_results")
    
    # Register scrapers
    print("\n🔧 Registering scrapers...")
    registered_count = 0
    
    for scraper_name, scraper_class in scrapers_imported.items():
        try:
            # Try to create an instance of the scraper
            scraper_instance = scraper_class()
            tester.register_scraper(scraper_name, scraper_instance)
            print(f"✅ Registered {scraper_name}")
            registered_count += 1
        except Exception as e:
            print(f"❌ Failed to register {scraper_name}: {e}")
    
    if registered_count == 0:
        print("❌ No scrapers could be registered!")
        return
    
    print(f"\n📊 Ready to test {registered_count} scrapers")
    
    # Simple menu
    while True:
        print("\n" + "="*40)
        print("SELECT TESTING MODE:")
        print("1. Health Check Only (Quick)")
        print("2. Simple Test (1-2 jobs per scraper)")
        print("3. Quick Test (Official)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🏥 Running Health Checks...")
            await run_health_checks(tester)
            
        elif choice == "2":
            print("\n🧪 Running Simple Tests...")
            await run_simple_tests(tester)
            
        elif choice == "3":
            print("\n🚀 Running Quick Tests...")
            await run_quick_tests(tester)
            
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

async def run_health_checks(tester):
    """Run health checks on all scrapers"""
    print("Checking scraper health...")
    
    for scraper_name, scraper in tester.scrapers.items():
        print(f"\n🔍 Testing {scraper_name}...")
        
        try:
            # Check if health_check method exists
            if hasattr(scraper, 'health_check'):
                if asyncio.iscoroutinefunction(scraper.health_check):
                    health_result = await scraper.health_check()
                else:
                    health_result = scraper.health_check()
                
                # Handle different return types
                if isinstance(health_result, tuple):
                    is_healthy = health_result[0]
                    details = health_result[1] if len(health_result) > 1 else {}
                else:
                    is_healthy = bool(health_result)
                    details = {}
                
                status = "✅ HEALTHY" if is_healthy else "❌ ISSUES"
                print(f"   Health Status: {status}")
                
                if details and isinstance(details, dict):
                    for key, value in details.items():
                        print(f"   {key}: {value}")
                        
            else:
                print("   ⚠️  No health_check method found")
                
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")

async def run_simple_tests(tester):
    """Run simple tests with basic skills"""
    
    # Simple test case
    test_case = TestCase(
        name="simple_python_test",
        skills=["Python"],
        location="Remote",
        expected_min_jobs=0,  # Don't require minimum jobs
        max_jobs=2,           # Only get 2 jobs to be fast
        timeout_seconds=45    # Shorter timeout
    )
    
    print(f"Testing with: {test_case.skills} in {test_case.location}")
    
    for scraper_name in tester.scrapers:
        print(f"\n🔍 Testing {scraper_name}...")
        
        try:
            results = await tester.test_single_scraper(scraper_name, [test_case])
            
            if results:
                result = results[0]
                status_emoji = "✅" if result.result.value == "PASS" else "❌"
                
                print(f"   {status_emoji} Result: {result.result.value}")
                print(f"   Jobs Found: {result.jobs_found}")
                print(f"   Time: {result.execution_time:.1f}s")
                
                if result.error_message:
                    print(f"   Error: {result.error_message}")
                    
                # Show sample job if available
                if result.jobs_sample and len(result.jobs_sample) > 0:
                    job = result.jobs_sample[0]
                    title = job.get('title', 'No title')
                    company = job.get('company', 'No company')
                    print(f"   Sample: {title} at {company}")
                    
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
        
        # Small delay between scrapers
        await asyncio.sleep(2)

async def run_quick_tests(tester):
    """Run the official quick tests"""
    try:
        report = await tester.test_all_scrapers(test_mode="quick")
        
        # Show results
        total_tests = report.passed_tests + report.failed_tests
        success_rate = (report.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎉 Quick Test Results:")
        print(f"   Tests Passed: {report.passed_tests}")
        print(f"   Tests Failed: {report.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {report.execution_time:.1f} seconds")
        
        # Save results
        tester.save_results(report)
        print(f"   📁 Results saved in test_results/ directory")
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
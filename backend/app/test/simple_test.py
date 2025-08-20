# corrected_simple_test.py
"""
Updated simple scraper tester with the correct class names from your actual code
"""

import asyncio
import sys
import time
from pathlib import Path

# Add scrapers directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "scrapers"))

print(f"🔧 Testing from: {current_dir}")

async def test_single_scraper(scraper_name, scraper_class):
    """Test a single scraper"""
    print(f"\n{'='*50}")
    print(f"🧪 TESTING: {scraper_name}")
    print(f"{'='*50}")
    
    try:
        # Try to create scraper instance
        print("1. Creating scraper instance...")
        scraper = scraper_class()
        print("   ✅ Scraper created successfully")
        
        # Try health check if available
        print("2. Running health check...")
        if hasattr(scraper, 'health_check'):
            try:
                if asyncio.iscoroutinefunction(scraper.health_check):
                    health = await scraper.health_check()
                else:
                    health = scraper.health_check()
                
                # Handle different return types from your scrapers
                if isinstance(health, tuple):
                    health_status = health[0]
                    health_details = health[1] if len(health) > 1 else {}
                else:
                    health_status = bool(health)
                    health_details = {}
                
                print(f"   {'✅' if health_status else '❌'} Health check: {'PASSED' if health_status else 'FAILED'}")
                
                if health_details and isinstance(health_details, dict):
                    for key, value in health_details.items():
                        if key != 'checks':  # Don't print the full checks dict
                            print(f"      {key}: {value}")
                        
            except Exception as e:
                print(f"   ⚠️  Health check error: {e}")
        else:
            print("   ⚠️  No health check method found")
        
        # Try simple scrape test
        print("3. Testing scrape functionality...")
        start_time = time.time()
        
        # Simple test parameters
        test_skills = ["Python"]
        test_location = "Remote"
        max_jobs = 2
        
        print(f"   Searching for: {test_skills} in {test_location}")
        
        # Try to scrape
        try:
            result = await asyncio.wait_for(
                scraper.scrape(skills=test_skills, location=test_location, max_jobs=max_jobs),
                timeout=45  # Reduced timeout for quicker testing
            )
            
            execution_time = time.time() - start_time
            
            # Handle different return types from your scrapers
            if isinstance(result, tuple):
                jobs = result[0]  # If scraper returns (jobs, metrics)
                metrics = result[1] if len(result) > 1 else None
            else:
                jobs = result
                metrics = None
            
            job_count = len(jobs) if jobs else 0
            
            print(f"   ✅ Scrape completed in {execution_time:.1f} seconds")
            print(f"   📊 Jobs found: {job_count}")
            
            # Show sample job if available
            if jobs and len(jobs) > 0:
                sample_job = jobs[0]
                title = sample_job.get('title', 'No title')
                company = sample_job.get('company', 'No company')
                location = sample_job.get('location', 'No location')
                print(f"   📝 Sample job: {title} at {company} ({location})")
                
                # Show more details if available
                if sample_job.get('salary'):
                    print(f"      💰 Salary: {sample_job['salary']}")
                if sample_job.get('match_score'):
                    print(f"      🎯 Match score: {sample_job['match_score']}%")
                if sample_job.get('url'):
                    print(f"      🔗 URL: {sample_job['url'][:60]}...")
            
            # Show metrics if available
            if metrics:
                print(f"   📈 Metrics: {type(metrics).__name__}")
                if hasattr(metrics, 'success_rate'):
                    print(f"      Success rate: {metrics.success_rate:.1f}%")
                if hasattr(metrics, 'duration'):
                    print(f"      Duration: {metrics.duration:.1f}s")
            
            # Overall result
            if job_count > 0:
                print(f"   🎉 TEST RESULT: ✅ SUCCESS")
            else:
                print(f"   🤔 TEST RESULT: ⚠️  NO JOBS FOUND (but no errors)")
                
        except asyncio.TimeoutError:
            print(f"   ❌ TIMEOUT: Scraper took longer than 45 seconds")
        except Exception as scrape_error:
            print(f"   ❌ SCRAPE ERROR: {scrape_error}")
            
    except Exception as e:
        print(f"   ❌ SETUP ERROR: Failed to create scraper: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")

async def main():
    print("🚀 CORRECTED JOB SCRAPER TESTER")
    print("="*60)
    
    # Correct scraper list based on your actual code
    scrapers_to_test = [
        # These should work based on your code structure
        ("Himalayas", "himalayas_scraper", "HimalayasScraper"),           # Known to work (uses API)
        ("Naukri", "naukri_scraper", "NaukriScraper"),                   # Your enhanced version
        ("ZipRecruiter", "ziprecruiter_scraper", "EnhancedZipRecruiterScraper"),  # Note: Enhanced prefix
        ("CareerBuilder", "careerbuilder_scraper", "CareerBuilderScraper"),
        ("Dice", "dice_scraper", "DiceScraper"),
        ("Glassdoor", "glassdoor_scraper", "GlassdoorScraper"),
        ("Indeed", "indeed_scraper", "IndeedScraper"),
        ("LinkedIn", "linkedin_scraper", "LinkedInScraper"),
        ("Monster", "monster_scraper", "MonsterScraper"),
    ]
    
    print(f"🔍 Testing {len(scrapers_to_test)} scrapers")
    
    successful_tests = 0
    failed_tests = 0
    
    for display_name, module_name, class_name in scrapers_to_test:
        try:
            # Try to import the scraper
            print(f"\n📦 Importing {display_name}...")
            
            # Try different import approaches to handle your setup
            scraper_class = None
            import_attempts = [
                f"scrapers.{module_name}",
                f"app.scrapers.{module_name}",
                module_name
            ]
            
            for import_path in import_attempts:
                try:
                    # Handle the relative import issue in your scrapers
                    if 'scrapers.' in import_path:
                        # This handles your relative imports like "from .base_scraper import BaseScraper"
                        import importlib.util
                        import os
                        
                        # Get the actual file path
                        file_path = current_dir / "scrapers" / f"{module_name}.py"
                        if file_path.exists():
                            spec = importlib.util.spec_from_file_location(module_name, file_path)
                            module = importlib.util.module_from_spec(spec)
                            
                            # Fix relative imports by adding to sys.modules
                            sys.modules[f"scrapers.{module_name}"] = module
                            
                            # Import base_scraper first to resolve dependencies
                            try:
                                base_path = current_dir / "scrapers" / "base_scraper.py"
                                base_spec = importlib.util.spec_from_file_location("base_scraper", base_path)
                                base_module = importlib.util.module_from_spec(base_spec)
                                sys.modules["scrapers.base_scraper"] = base_module
                                base_spec.loader.exec_module(base_module)
                                
                                # Now execute the scraper module
                                spec.loader.exec_module(module)
                                
                            except Exception as exec_error:
                                print(f"      Error executing module: {exec_error}")
                                continue
                    else:
                        module = __import__(import_path, fromlist=[class_name])
                    
                    scraper_class = getattr(module, class_name)
                    print(f"   ✅ Successfully imported from {import_path}")
                    break
                    
                except (ImportError, AttributeError) as e:
                    print(f"      Failed {import_path}: {str(e)}")
                    continue
            
            if scraper_class is None:
                print(f"   ❌ Could not import {class_name}")
                failed_tests += 1
                continue
            
            # Test the scraper
            await test_single_scraper(display_name, scraper_class)
            successful_tests += 1
            
            # Small delay between tests
            print("\n⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"   ❌ Failed to test {display_name}: {e}")
            failed_tests += 1
    
    # Final summary
    print("\n" + "="*60)
    print("🎉 TESTING COMPLETE!")
    print("="*60)
    print(f"✅ Successful tests: {successful_tests}")
    print(f"❌ Failed tests: {failed_tests}")
    print(f"📊 Total scrapers tested: {successful_tests + failed_tests}")
    
    if successful_tests > 0:
        success_rate = (successful_tests / (successful_tests + failed_tests)) * 100
        print(f"🎯 Success rate: {success_rate:.1f}%")
        print("\n✨ Great! At least some scrapers are working.")
        if failed_tests > 0:
            print("💡 For failed scrapers, check:")
            print("   1. Selenium/ChromeDriver installation")
            print("   2. Internet connectivity") 
            print("   3. Website accessibility (some may be blocking automated access)")
            print("   4. Required dependencies")
    else:
        print("\n🚨 No scrapers worked completely. Common fixes:")
        print("   1. Install/update ChromeDriver: pip install undetected-chromedriver")
        print("   2. Check internet connection")
        print("   3. Some sites may be temporarily blocking automated access")
        print("   4. Run: pip install selenium asyncio aiohttp")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
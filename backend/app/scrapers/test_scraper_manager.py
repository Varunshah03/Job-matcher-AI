import asyncio
from scraper_manager import ScraperManager

async def main():
    manager = ScraperManager()

    print("\n✅ Available platforms:", manager.get_available_platforms())
    print("✅ Platform status:", manager.get_platform_status())

    # Run health checks
    print("\n🔎 Running health checks...")
    health = await manager.health_check_all()
    for platform, status in health.items():
        print(f"   {platform}: {'✅ Healthy' if status else '❌ Failed'}")

    # Try scraping with a sample
    print("\n🚀 Scraping jobs...")
    results = await manager.scrape_all_platforms(
        skills=["Python", "FastAPI"],
        location="Remote",
        max_jobs_per_platform=2
    )

    print(f"\n📊 Total unique jobs found: {results['metadata'].get('total_jobs_found', 0)}")
    print("📌 Platform distribution:", results['metadata'].get('platform_distribution', {}))

if __name__ == "__main__":
    asyncio.run(main())

# filename: careerbuilder_scraper.py
"""
Layered access strategy for CareerBuilder:
  - Normal requests
  - Rotating HTTP proxies
  - Residential/geo-targeted proxies (same interface, but better quality)
  - Selenium headful (stealth) fallback for JS/WAF pages
  - Caching of 'unavailable' per-country to avoid hammering

Public API:
  - await scraper.scrape(query, location=None, country_code=None, max_pages=1, proxies=None, use_selenium=False)
    returns dict like other scrapers: { portal, available, reason, jobs }
"""

from __future__ import annotations
import asyncio
import random
import time
import typing as t
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# Optional selenium imports (only required if you enable selenium fallback)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

# ---------- dataclasses ----------
@dataclass
class JobItem:
    portal: str
    job_id: t.Optional[str]
    title: str
    company: t.Optional[str]
    location: t.Optional[str]
    posted_at: t.Optional[str]
    salary: t.Optional[str]
    job_url: t.Optional[str]
    source_url: str

@dataclass
class ScrapeResult:
    portal: str
    available: bool
    reason: t.Optional[str]
    jobs: t.Union[str, t.List[JobItem]]  # "N/A" or list[JobItem]

# ---------- scraper with access layers ----------
class CareerBuilderScraper:
    BASE = "https://www.careerbuilder.com/"
    SEARCH_PATH = "jobs"
    PORTAL = "careerbuilder"

    GEO_BLOCKED_COUNTRIES = {"IN"}  # still keep this as quick-check

    DEFAULT_HEADERS_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    ]

    def __init__(self):
        self.timeout_s = 15
        self.per_page_delay_s = (0.8, 1.6)
        self.session = self._build_session()
        # small in-memory cache for country -> (ts, unavailable_reason) to avoid re-checking too often
        self.unavail_cache: dict[str, float] = {}
        # default proxies list (can be replaced from manager via kwargs)
        self.proxy_pool: list[str] = []  # proxies in form "http://user:pass@host:port" or "http://host:port"

    # ---------------- public async interface (manager expects awaitable) ----------------
    async def scrape(
        self,
        query: str,
        location: t.Optional[str] = None,
        country_code: t.Optional[t.Union[str, int]] = None,
        max_pages: int = 1,
        proxies: t.Optional[list[str]] = None,
        use_selenium: bool = False,
        selenium_options: dict | None = None,
        residential_provider: dict | None = None,
        cache_unavailable_for_s: int = 300,
    ) -> dict:
        """
        - proxies: list of proxy URLs (http://...) to try rotating
        - use_selenium: boolean to allow Selenium fallback
        - residential_provider: optional dict with provider config (example: {'name': 'brightdata', 'token': '...', 'endpoint': '...'})
        - cache_unavailable_for_s: if blocked in a country, cache 'N/A' for this many seconds
        """
        # normalize country code robustly
        country = (str(country_code).strip().upper() if country_code is not None else None)

        # quick cache check: if we recently found it unavailable for this country, don't retry now
        if country and country in self.unavail_cache:
            ts = self.unavail_cache[country]
            if time.time() - ts < cache_unavailable_for_s:
                return {"portal": self.PORTAL, "available": False, "reason": f"Recently detected unavailable in {country}", "jobs": "N/A"}
            else:
                del self.unavail_cache[country]

        # store runtime params then call synchronous core via thread
        self.keywords = query or ""
        self.location = location
        self.country_code = country
        self.max_pages = max(1, int(max_pages))
        if proxies:
            self.proxy_pool = proxies[:]
        # optional residential provider config
        self.residential_provider = residential_provider
        self.use_selenium = use_selenium
        self.selenium_options = selenium_options or {}

        result: ScrapeResult = await asyncio.to_thread(self._scrape_core)
        # if unavailable due to geographic block, record in cache
        if not result.available and self.country_code:
            self.unavail_cache[self.country_code] = time.time()
        return {
            "portal": result.portal,
            "available": result.available,
            "reason": result.reason,
            "jobs": "N/A" if result.jobs == "N/A" else [asdict(j) for j in result.jobs],
        }

    # ---------------- core synchronous scraper ----------------
    def _scrape_core(self) -> ScrapeResult:
        portal = self.PORTAL

        # quick local geo check
        if self.country_code and self.country_code in self.GEO_BLOCKED_COUNTRIES:
            return ScrapeResult(portal, False, f"Geo-blocked (local list) in {self.country_code}", "N/A")

        # 1) Try no-proxy simple request
        ok, reason = self._is_available()
        if not ok:
            # 2) Try rotating proxy pool if provided
            if self.proxy_pool:
                ok2, reason2 = self._is_available_with_proxy_rotation()
                if not ok2:
                    # 3) Try residential provider proxy (if provided)
                    if getattr(self, "residential_provider", None):
                        ok3, reason3 = self._is_available_with_residential()
                        if not ok3:
                            # 4) optional selenium fallback
                            if self.use_selenium and SELENIUM_AVAILABLE:
                                ok4, reason4 = self._is_available_with_selenium()
                                if not ok4:
                                    return ScrapeResult(portal, False, f"Blocked after all layers: {reason4}", "N/A")
                            else:
                                return ScrapeResult(portal, False, f"Blocked after proxies: {reason2}", "N/A")
                        # if residential ok - continue to scraping pages using residential proxy
                    else:
                        # no residential provider - optionally use selenium
                        if self.use_selenium and SELENIUM_AVAILABLE:
                            ok4, reason4 = self._is_available_with_selenium()
                            if not ok4:
                                return ScrapeResult(portal, False, f"Blocked after proxy rotation + selenium: {reason4}", "N/A")
                        else:
                            return ScrapeResult(portal, False, f"Blocked (proxy rotation failed): {reason2}", "N/A")
            else:
                # no proxies configured; either allow selenium or bail
                if self.use_selenium and SELENIUM_AVAILABLE:
                    ok4, reason4 = self._is_available_with_selenium()
                    if not ok4:
                        return ScrapeResult(portal, False, f"Blocked (selenium failed): {reason4}", "N/A")
                else:
                    return ScrapeResult(portal, False, f"Blocked: {reason}", "N/A")

        # If we reach here, site is reachable via one of the above layers.
        # We'll attempt to scrape pages, preferring non-selenium requests and falling back to the working layer.
        jobs: list[JobItem] = []
        for page in range(1, self.max_pages + 1):
            url = self._build_search_url(page)
            html = self._fetch_with_best_method(url)
            if not html:
                if page == 1:
                    return ScrapeResult(portal, False, "Failed to load first search page", "N/A")
                break

            batch = self._parse_listings(html, source_url=url)
            if not batch:
                if page == 1:
                    return ScrapeResult(portal, True, "No results", [])
                break
            jobs.extend(batch)
            time.sleep(random.uniform(*self.per_page_delay_s))

        return ScrapeResult(portal, True, None, jobs)

    # ---------------- layered availability checks ----------------
    def _is_available(self) -> tuple[bool, t.Optional[str]]:
        try:
            r = self._requests_get(self.BASE)
        except Exception as e:
            return False, f"Network error: {e}"
        if r is None:
            return False, "No response"
        if r.status_code == 403:
            return False, "403 Access denied"
        if r.status_code // 100 != 2:
            return False, f"HTTP {r.status_code}"
        text = (r.text or "").lower()
        for sig in ("access denied", "blocked", "verify you are a human", "region not supported"):
            if sig in text:
                return False, "Blocked by WAF/captcha text"
        return True, None

    def _is_available_with_proxy_rotation(self) -> tuple[bool, t.Optional[str]]:
        for proxy in self.proxy_pool:
            try:
                r = self._requests_get(self.BASE, proxy=proxy)
            except Exception as e:
                continue
            if r is None:
                continue
            if r.status_code // 100 == 2 and "access denied" not in (r.text or "").lower():
                # found a working proxy
                # Make the working proxy first in pool to prefer it for scraping
                self.proxy_pool.insert(0, self.proxy_pool.pop(self.proxy_pool.index(proxy)))
                return True, None
        return False, "All proxies failed or blocked"

    def _is_available_with_residential(self) -> tuple[bool, t.Optional[str]]:
        """
        Example residential provider usage:
          - Many providers expose a single endpoint you route through (e.g. http://USERNAME:TOKEN@proxy.provider:PORT)
          - Or they provide an endpoint you append a target country to.
        This method should be adapted to the exact provider integration you have.
        """
        cfg = getattr(self, "residential_provider", None)
        if not cfg:
            return False, "No residential provider config"
        # Provider config may contain 'endpoint' that already encodes auth
        proxy_url = cfg.get("endpoint")
        if not proxy_url:
            return False, "Residential provider missing endpoint"
        try:
            r = self._requests_get(self.BASE, proxy=proxy_url)
        except Exception as e:
            return False, f"Residential network error: {e}"
        if r and r.status_code // 100 == 2 and "access denied" not in (r.text or "").lower():
            # mark it as preferred proxy for later
            self.proxy_pool.insert(0, proxy_url)
            return True, None
        return False, "Residential proxy blocked or failed"

    def _is_available_with_selenium(self) -> tuple[bool, t.Optional[str]]:
        if not SELENIUM_AVAILABLE:
            return False, "Selenium not available in environment"
        try:
            html = self._selenium_fetch(self.BASE)
            if not html:
                return False, "Selenium fetch returned no content"
            txt = html.lower()
            for sig in ("access denied", "blocked", "verify you are a human"):
                if sig in txt:
                    return False, "Selenium page indicates block/captcha"
            return True, None
        except Exception as e:
            return False, f"Selenium error: {e}"

    # ---------------- fetching helpers ----------------
    def _fetch_with_best_method(self, url: str) -> t.Optional[str]:
        """
        Prefer fast requests without proxy, then with working proxy, then selenium if enabled.
        """
        # 1. Try without proxy first
        html = self._requests_text(url)
        if html:
            return html

        # 2. Try proxy pool in preference order
        for proxy in self.proxy_pool:
            html = self._requests_text(url, proxy=proxy)
            if html:
                return html

        # 3. Try residential (if configured)
        cfg = getattr(self, "residential_provider", None)
        if cfg and cfg.get("endpoint"):
            html = self._requests_text(url, proxy=cfg.get("endpoint"))
            if html:
                return html

        # 4. Selenium fallback
        if self.use_selenium and SELENIUM_AVAILABLE:
            return self._selenium_fetch(url)

        return None

    def _requests_get(self, url: str, proxy: str | None = None) -> requests.Response | None:
        """
        returns requests.Response or None
        proxy: "http://user:pass@host:port" or "http://host:port"
        """
        headers = {"User-Agent": random.choice(self.DEFAULT_HEADERS_POOL), "Accept-Language": "en-US,en;q=0.9"}
        kwargs = {"timeout": self.timeout_s, "headers": headers}
        if proxy:
            kwargs["proxies"] = {"http": proxy, "https": proxy}
        # Use session with retry adapter
        try:
            r = self.session.get(url, **kwargs)
            return r
        except Exception:
            return None

    def _requests_text(self, url: str, proxy: str | None = None) -> t.Optional[str]:
        r = self._requests_get(url, proxy=proxy)
        if not r:
            return None
        if r.status_code // 100 == 2:
            # If the server returned a JS challenge page, it may contain "verify" words - allow upstream checks to detect
            return r.text
        return None

    # ---------------- selenium fetch (last-resort) ----------------
    def _selenium_fetch(self, url: str) -> t.Optional[str]:
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("selenium not installed or unavailable in this environment")
        opts = Options()
        # Headless may still be detected by some WAFs — consider using headful option in production
        if not self.selenium_options.get("headful", False):
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # add additional args from selenium_options
        for arg in self.selenium_options.get("extra_args", []):
            opts.add_argument(arg)
        # instantiate webdriver
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
        try:
            driver.set_page_load_timeout(self.timeout_s)
            driver.get(url)
            # Optionally wait a bit for JS to render
            time.sleep(self.selenium_options.get("wait", 2))
            html = driver.page_source
            return html
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    # ---------------- helpers: build URL and parse ----------------
    def _build_search_url(self, page: int) -> str:
        params = {"keywords": self.keywords}
        if self.location:
            params["location"] = self.location
        if page > 1:
            params["page_number"] = page
        return urljoin(self.BASE, f"{self.SEARCH_PATH}?{urlencode(params)}")

    def _parse_listings(self, html: str, source_url: str) -> list[JobItem]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("div[data-jobid]") or soup.select("div.data-results-content-parent [data-jobid]")
        jobs: list[JobItem] = []
        for card in cards:
            title_a = card.select_one("h2 a, h3 a, a.data-results-content")
            if not title_a:
                continue
            title = title_a.get_text(strip=True)
            href = title_a.get("href")
            job_url = href if (href and href.startswith("http")) else (urljoin(self.BASE, href) if href else None)
            job_id = card.get("data-jobid") or title_a.get("data-jobid")
            company_tag = (card.select_one("[data-cname]") or card.select_one(".company-name") or card.select_one(".data-details span"))
            company = company_tag.get_text(strip=True) if company_tag else None
            location_tag = card.select_one(".job-location") or card.select_one("[data-location]")
            if location_tag is not None:
                if hasattr(location_tag, "has_attr") and location_tag.has_attr("data-location"):
                    location = location_tag.get("data-location")
                else:
                    location = location_tag.get_text(strip=True)
            else:
                location = None
            time_tag = card.select_one("time")
            posted_at = (time_tag.get("datetime") if time_tag and time_tag.has_attr("datetime") else (time_tag.get_text(strip=True) if time_tag else None))
            salary_tag = card.select_one(".data-salary, [data-salary], .estimated-salary")
            if salary_tag is not None:
                salary = salary_tag.get("data-salary") if salary_tag.has_attr("data-salary") else salary_tag.get_text(strip=True)
            else:
                salary = None
            jobs.append(JobItem("careerbuilder", job_id, title, company, location, posted_at, salary, job_url, source_url))
        return jobs

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504])
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))
        return s

# ---------------- CLI test (example) ----------------
if __name__ == "__main__":
    import asyncio, os

    async def main():
        scraper = CareerBuilderScraper()
        # example proxies list (replace with real proxies)
        proxy_list = [
            # "http://user:pass@proxy1.example:8080",
            # "http://user:pass@proxy2.example:8080",
        ]
        # Example residential provider config (placeholder)
        residential_cfg = {
            # 'endpoint': 'http://USER:TOKEN@residential.provider:port',
            # 'name': 'my_provider',
        }
        # Attempt scraping with proxy rotation and selenium allowed
        res = await scraper.scrape("software developer", location="Remote", country_code="US", max_pages=1,
                                   proxies=proxy_list, residential_provider=residential_cfg, use_selenium=False)
        print(res)

    asyncio.run(main())

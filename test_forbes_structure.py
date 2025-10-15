#!/usr/bin/env python3
"""
Test Forbes page structure to find the correct XPath
"""

from cortex.departments.intelligence import StealthWebCrawler
from cortex.departments.intelligence.stealth_web_crawler import XPathSource
from datetime import datetime

def test_forbes_structure():
    """Fetch Forbes page and test various XPaths"""

    url = "https://www.forbes.com/real-time-billionaires/"

    print("=" * 80)
    print("Forbes Real-Time Billionaires - Structure Analysis")
    print("=" * 80)
    print(f"URL: {url}")
    print()

    crawler = StealthWebCrawler()

    # Test different XPaths that might work
    test_xpaths = [
        ("//h1", "Page title (h1)"),
        ("//title", "HTML title"),
        ("//div[@class='fbs-table']", "Table container by class"),
        ("//table", "Any table element"),
        ("//div[contains(@class, 'billionaire')]", "Divs with 'billionaire' in class"),
        ("//div[contains(@class, 'rtb')]", "Divs with 'rtb' in class"),
        ("//*[@id='rtb-table']", "Element with ID rtb-table"),
        ("//script[contains(text(), 'billionaire')]", "Scripts mentioning billionaires"),
        ("//body/*[1]", "First child of body"),
        ("//div[@data-testid]", "Divs with data-testid"),
    ]

    print("Testing various XPaths to find page structure...")
    print()

    found_any = False

    for xpath, description in test_xpaths:
        source = XPathSource(
            id=f"test_{hash(xpath)}",
            name=f"Test: {description}",
            url=url,
            xpath=xpath,
            description=description,
            category="test",
            refresh_interval_hours=0,
            created_at=datetime.now(),
            last_validated=None,
            validation_status="pending",
            last_error=None,
            enabled=True
        )

        print(f"Testing: {description}")
        print(f"  XPath: {xpath}")

        result = crawler.validate_xpath(source)

        if result.success and result.elements_found > 0:
            print(f"  ✅ SUCCESS: Found {result.elements_found} element(s)")
            if result.sample_data:
                print(f"  Sample data:")
                for i, sample in enumerate(result.sample_data[:3], 1):
                    preview = sample[:100] + "..." if len(sample) > 100 else sample
                    print(f"    {i}. {preview}")
            found_any = True
        else:
            print(f"  ❌ FAILED: {result.error}")

        print()

    if not found_any:
        print("⚠️  No XPaths returned data. This suggests:")
        print("  1. The page is heavily JavaScript-rendered (needs browser automation)")
        print("  2. Forbes is blocking automated access")
        print("  3. The page structure is very different than expected")
        print()
        print("Recommendation: Use a headless browser (Selenium/Playwright) to render JS")
    else:
        print("✅ Found some working XPaths! Use them as starting points.")

    # Also try to scrape and show raw structure
    print()
    print("=" * 80)
    print("Attempting to fetch raw HTML snippet...")
    print("=" * 80)

    source = XPathSource(
        id="test_body",
        name="Body content",
        url=url,
        xpath="//body",
        description="Get body element",
        category="test",
        refresh_interval_hours=0,
        created_at=datetime.now(),
        last_validated=None,
        validation_status="pending",
        last_error=None,
        enabled=True
    )

    scrape_result = crawler.scrape(source)

    if scrape_result.success and scrape_result.data:
        body_content = scrape_result.data[0] if scrape_result.data else ""
        print(f"Body content length: {len(body_content)} characters")
        print()
        print("First 1000 characters:")
        print("-" * 80)
        print(body_content[:1000])
        print("-" * 80)
    else:
        print(f"Failed to fetch body: {scrape_result.error}")

if __name__ == "__main__":
    test_forbes_structure()

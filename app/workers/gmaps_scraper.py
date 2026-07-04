"""Google Maps scraper using Playwright.

For each (location, niche) pair it:
  1. Navigates to Google Maps and searches "<niche> in <location>".
  2. Scrolls the results panel to load up to max_results listings.
  3. Clicks each card, extracts: name, phone, website, address, rating, category.
  4. Visits the website (if present) to harvest an email.
  5. Also checks the Maps listing itself for an email link.
"""
import asyncio
import re
from typing import List, Optional
from playwright.async_api import async_playwright, Page
from app.workers.email_extractor import extract_email_from_site

PHONE_RE = re.compile(r"[\+]?[\d\s\-().]{7,20}")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


async def _scroll_results(page: Page, max_results: int) -> None:
    panel_sel = '[role="feed"]'
    try:
        await page.wait_for_selector(panel_sel, timeout=15000)
    except Exception:
        return
    seen = 0
    # Each scroll loads ~5-7 more results; iterate enough times to reach max
    max_scrolls = (max_results // 5) + 20
    for _ in range(max_scrolls):
        count = await page.locator('[role="article"]').count()
        if count >= max_results:
            break
        if count == seen:
            # hit the bottom — no more results
            break
        seen = count
        await page.locator(panel_sel).evaluate("el => el.scrollBy(0, 1200)")
        await asyncio.sleep(1.0)


async def _parse_card(page: Page) -> dict:
    data: dict = {}
    try:
        data["name"] = await page.locator('h1.DUwDvf, h1[data-attrid]').first.inner_text(timeout=5000)
    except Exception:
        data["name"] = None
    try:
        data["rating"] = float(
            await page.locator('[data-value="Stars"] span[aria-hidden]').first.inner_text(timeout=3000)
        )
    except Exception:
        data["rating"] = None
    try:
        data["category"] = await page.locator('button[jsaction*="category"]').first.inner_text(timeout=3000)
    except Exception:
        data["category"] = None
    try:
        data["address"] = await page.locator('[data-item-id*="address"]').first.inner_text(timeout=3000)
    except Exception:
        data["address"] = None
    try:
        data["phone"] = await page.locator('[data-item-id*="phone"]').first.inner_text(timeout=3000)
    except Exception:
        data["phone"] = None
    try:
        data["website"] = await page.locator('[data-item-id*="authority"] a').first.get_attribute("href", timeout=3000)
    except Exception:
        data["website"] = None

    # Try to find an email directly on the Maps page (some listings show mailto: links)
    try:
        page_html = await page.content()
        emails = EMAIL_RE.findall(page_html)
        data["gmaps_email"] = emails[0].lower() if emails else None
    except Exception:
        data["gmaps_email"] = None

    return data


async def scrape_gmaps(
    location: str,
    niche: str,
    max_results: int = 20,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> List[dict]:
    """Return a list of lead dicts from Google Maps."""
    sem = semaphore or asyncio.Semaphore(1)
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        query = f"{niche} in {location}"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            await browser.close()
            return []

        # Dismiss cookie consent if present
        try:
            await page.locator('button:has-text("Accept all"), button:has-text("Reject all")').first.click(timeout=3000)
        except Exception:
            pass

        await asyncio.sleep(2)
        await _scroll_results(page, max_results)

        cards = await page.locator('[role="article"] a[href*="/maps/place/"]').all()
        for card in cards[:max_results]:
            try:
                async with sem:
                    await card.click(timeout=5000)
                    await asyncio.sleep(1.5)
                    data = await _parse_card(page)

                    # Email priority: 1) from Maps page, 2) from website
                    email = data.pop("gmaps_email", None)
                    if not email and data.get("website"):
                        email = await extract_email_from_site(data["website"])
                    data["email"] = email
                    data["location"] = location
                    data["niche"] = niche
                    data["source"] = "gmaps"
                    results.append(data)
            except Exception:
                continue

        await browser.close()
    return results

"""Google Maps scraper using Playwright.

For each (location, niche) pair it:
  1. Navigates to Google Maps and searches "<niche> in <location>".
  2. Scrolls the results panel to load up to max_pages * 20 results.
  3. Clicks each card, extracts: name, phone, website, address, rating, category.
  4. Visits the website (if present) to extract an email.
"""
import asyncio
import json
import re
from typing import AsyncGenerator, Optional
from playwright.async_api import async_playwright, Page
from app.workers.email_extractor import extract_email_from_site

PHONE_RE = re.compile(r"[\+]?[\d\s\-().]{7,20}")


async def _scroll_results(page: Page, max_results: int) -> None:
    panel_sel = '[role="feed"]'
    try:
        await page.wait_for_selector(panel_sel, timeout=10000)
    except Exception:
        return
    seen = 0
    for _ in range(max_results // 5 + 5):
        count = await page.locator('[role="article"]').count()
        if count >= max_results:
            break
        if count == seen:
            break
        seen = count
        await page.locator(panel_sel).evaluate("el => el.scrollBy(0, 800)")
        await asyncio.sleep(1.2)


async def _parse_card(page: Page) -> dict:
    data: dict = {}
    try:
        data["name"] = await page.locator('h1[data-attrid], h1.DUwDvf').first.inner_text(timeout=4000)
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
    return data


async def scrape_gmaps(
    location: str,
    niche: str,
    max_results: int = 20,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> AsyncGenerator[dict, None]:
    """Async generator yielding lead dicts from Google Maps."""
    sem = semaphore or asyncio.Semaphore(1)

    async def _run():
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
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
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            await _scroll_results(page, max_results)

            cards = await page.locator('[role="article"] a[href*="/maps/place/"]').all()
            for card in cards[:max_results]:
                try:
                    async with sem:
                        await card.click(timeout=5000)
                        await asyncio.sleep(1.5)
                        data = await _parse_card(page)
                        if data.get("website"):
                            data["email"] = await extract_email_from_site(data["website"])
                        else:
                            data["email"] = None
                        data["location"] = location
                        data["niche"] = niche
                        data["source"] = "gmaps"
                        results.append(data)
                except Exception:
                    continue
            await browser.close()
        return results

    return await _run()

"""Playwright-based deep-page renderer for JS-heavy sites."""
import asyncio
from typing import Optional, Set
from loguru import logger


async def render_page(
    url: str,
    proxy: Optional[str] = None,
    timeout: int = 20000,
    wait_for: str = "networkidle",
) -> Optional[str]:
    """
    Render a URL with Playwright (Chromium headless) and return the fully
    rendered HTML. Falls back gracefully if Playwright is not installed.

    Args:
        url:       Page URL to render.
        proxy:     Optional proxy URL string, e.g. 'http://user:pass@host:port'.
        timeout:   Navigation timeout in milliseconds.
        wait_for:  Playwright wait_until strategy.

    Returns:
        Rendered HTML string or None on failure.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed — falling back to httpx fetch.")
        from app.services.scraper_service import fetch_page_async
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None
        return await fetch_page_async(url, proxy_dict)

    try:
        async with async_playwright() as pw:
            launch_opts = {"headless": True}
            if proxy:
                launch_opts["proxy"] = {"server": proxy}

            browser = await pw.chromium.launch(**launch_opts)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                ignore_https_errors=True,
            )
            page = await context.new_page()

            # Block heavy assets to speed up rendering
            await page.route(
                "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,eot,mp4,mp3}",
                lambda r: r.abort(),
            )

            await page.goto(url, timeout=timeout, wait_until=wait_for)
            html = await page.content()
            await browser.close()
            return html

    except Exception as exc:
        logger.debug(f"Playwright render failed for {url}: {exc}")
        return None


async def crawl_site_playwright(
    start_url: str,
    max_pages: int = 30,
    proxy: Optional[str] = None,
    same_domain: bool = True,
) -> Set[str]:
    """
    BFS crawl of a site using Playwright. Collects all emails found.
    Returns a set of discovered email addresses.
    """
    from app.services.scraper_service import extract_emails, extract_links
    from collections import deque
    from urllib.parse import urlparse

    visited: Set[str] = set()
    queue: deque = deque([start_url])
    all_emails: Set[str] = set()
    base_domain = urlparse(start_url).netloc

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        html = await render_page(url, proxy=proxy)
        if not html:
            continue

        emails = extract_emails(html)
        all_emails.update(emails)

        if same_domain:
            links = extract_links(html, url, same_domain=True)
            for link in links:
                if link not in visited and urlparse(link).netloc == base_domain:
                    queue.append(link)

        await asyncio.sleep(0.5)  # polite crawl delay

    return all_emails

"""Sitemap-based URL discovery — Firecrawl-style approach."""
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
from loguru import logger


async def fetch_sitemap_urls(
    base_url: str,
    proxy_dict: Optional[dict] = None,
    max_urls: int = 200,
) -> List[str]:
    """
    Fetch and parse sitemap.xml (including sitemap index files).
    Returns a list of page URLs found in the sitemap.
    """
    from app.services.scraper_service import fetch_page_async

    candidates = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
        urljoin(base_url, "/sitemap-index.xml"),
        urljoin(base_url, "/sitemaps/sitemap.xml"),
    ]

    urls: List[str] = []
    for sitemap_url in candidates:
        xml_text = await fetch_page_async(sitemap_url, proxy_dict, timeout=10)
        if not xml_text:
            continue
        found = _parse_sitemap_xml(xml_text, base_url)
        urls.extend(found)
        if urls:
            break

    return list(dict.fromkeys(urls))[:max_urls]  # dedupe + limit


def _parse_sitemap_xml(xml_text: str, base_url: str) -> List[str]:
    """Parse sitemap XML and return all <loc> URLs."""
    urls = []
    try:
        root = ET.fromstring(xml_text)
        ns = _detect_namespace(root)
        # Sitemap index: contains <sitemap> children
        for sitemap in root.findall(f"{ns}sitemap"):
            loc = sitemap.find(f"{ns}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
        # Regular sitemap: contains <url> children
        for url_el in root.findall(f"{ns}url"):
            loc = url_el.find(f"{ns}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    except ET.ParseError as e:
        logger.debug(f"Sitemap XML parse error: {e}")
    return urls


def _detect_namespace(root: ET.Element) -> str:
    tag = root.tag
    if tag.startswith("{"):
        return "{" + tag.split("}")[0][1:] + "}"
    return ""


async def discover_urls_for_domain(
    domain: str,
    proxy_dict: Optional[dict] = None,
    max_urls: int = 100,
) -> List[str]:
    """
    Combined discovery: sitemap first, then robots.txt fallback,
    then a shallow BFS crawl of the homepage.
    """
    from app.services.scraper_service import fetch_page_async, extract_links

    base = f"https://{domain}" if not domain.startswith("http") else domain
    urls: Set[str] = set()

    # 1. Try sitemap
    sitemap_urls = await fetch_sitemap_urls(base, proxy_dict, max_urls)
    urls.update(sitemap_urls)

    # 2. Parse robots.txt for Sitemap: directives
    robots = await fetch_page_async(urljoin(base, "/robots.txt"), proxy_dict, timeout=8)
    if robots:
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                sm_url = line.split(":", 1)[1].strip()
                extra = await fetch_sitemap_urls(sm_url, proxy_dict, max_urls)
                urls.update(extra)

    # 3. Shallow BFS from homepage if sitemap was empty
    if not urls:
        html = await fetch_page_async(base, proxy_dict)
        if html:
            links = extract_links(html, base, same_domain=True)
            urls.update(links[:max_urls])

    return list(urls)[:max_urls]

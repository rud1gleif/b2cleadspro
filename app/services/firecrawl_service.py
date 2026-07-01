"""Firecrawl API client — site-map + scrape endpoints."""
import httpx
from typing import List, Optional, Dict, Any
from loguru import logger
from app.config import settings


class FirecrawlClient:
    def __init__(self):
        self.base_url = settings.firecrawl_api_url.rstrip("/")
        self.api_key  = settings.firecrawl_api_key

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def scrape(self, url: str, formats: List[str] = None) -> Optional[Dict]:
        """Scrape a single URL; returns Firecrawl ScrapeResponse dict."""
        formats = formats or ["html", "markdown"]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.base_url}/v1/scrape",
                    headers=self._headers(),
                    json={"url": url, "formats": formats},
                )
                r.raise_for_status()
                return r.json()
        except Exception as exc:
            logger.debug(f"Firecrawl scrape failed for {url}: {exc}")
            return None

    async def crawl(self, url: str, max_depth: int = 2, limit: int = 20) -> List[str]:
        """Start a crawl job and return list of discovered page URLs."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Kick off crawl
                r = await client.post(
                    f"{self.base_url}/v1/crawl",
                    headers=self._headers(),
                    json={"url": url, "maxDepth": max_depth, "limit": limit},
                )
                r.raise_for_status()
                job = r.json()
                crawl_id = job.get("id") or job.get("jobId")
                if not crawl_id:
                    return []

                # Poll until done
                import asyncio
                for _ in range(30):
                    await asyncio.sleep(2)
                    status_r = await client.get(
                        f"{self.base_url}/v1/crawl/{crawl_id}",
                        headers=self._headers(),
                    )
                    status_r.raise_for_status()
                    data = status_r.json()
                    if data.get("status") == "completed":
                        return [p.get("url", "") for p in data.get("data", []) if p.get("url")]
                    if data.get("status") == "failed":
                        break
        except Exception as exc:
            logger.debug(f"Firecrawl crawl failed for {url}: {exc}")
        return []

    async def map(self, url: str, search: Optional[str] = None) -> List[str]:
        """Use Firecrawl /map to get all URLs on a site quickly."""
        try:
            payload: Dict[str, Any] = {"url": url}
            if search:
                payload["search"] = search
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    f"{self.base_url}/v1/map",
                    headers=self._headers(),
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
                return data.get("links", [])
        except Exception as exc:
            logger.debug(f"Firecrawl map failed for {url}: {exc}")
        return []


firecrawl = FirecrawlClient()

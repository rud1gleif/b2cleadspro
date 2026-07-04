"""Central NordVPN SOCKS5 proxy config — imported by all scrapers."""

NORD_PROXY = "socks5://vK5tA2pF75BFhSXMtXpo67ZX:rZmnhPFs3rSjsjAt6sDKtvPP@socks5.nordvpn.com:1080"

# httpx proxy dict used in AsyncClient(proxies=...)
PROXIES = {"all://": NORD_PROXY}

# Shared browser-like headers
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

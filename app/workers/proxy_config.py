"""Central NordVPN SOCKS5 proxy config — imported by all scrapers.

NordVPN deprecated socks5.nordvpn.com — current servers use nordhold.net.
Full list: nl, se, us, amsterdam.nl, atlanta.us, chicago.us, dallas.us, stockholm.se
All on port 1080.
"""

USER = "vK5tA2pF75BFhSXMtXpo67ZX"
PASS = "rZmnhPFs3rSjsjAt6sDKtvPP"

# Rotate through US servers for best performance
NORD_SERVERS = [
    "us.socks.nordhold.net",
    "atlanta.us.socks.nordhold.net",
    "chicago.us.socks.nordhold.net",
    "dallas.us.socks.nordhold.net",
]

# Primary proxy (us.socks.nordhold.net)
NORD_PROXY = f"socks5://{USER}:{PASS}@us.socks.nordhold.net:1080"

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


def proxy_for_server(server: str) -> dict:
    """Return a PROXIES dict for a specific Nord server."""
    return {"all://": f"socks5://{USER}:{PASS}@{server}:1080"}

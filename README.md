# B2C Leads Pro

A self-hosted, open-source B2C/B2B email lead generation platform with location-based scraping, proxy rotation, and email verification.

## Stack

- **FastAPI** — REST API
- **Playwright** — Browser automation for JS-heavy pages
- **Firecrawl** — URL discovery and crawling
- **Reacher** — Self-hosted email verification
- **Rota** — Proxy rotation engine
- **PostgreSQL** — Lead storage
- **Redis** — Job queues
- **Docker Compose** — Local orchestration

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation: structure, schema, Docker, FastAPI skeleton, models | ✅ Done |
| 2 | Location normalization + world-cities dataset + geocoder | 🔜 Next |
| 3 | Discovery worker + Firecrawl integration | 🔜 |
| 4 | Playwright browser worker | 🔜 |
| 5 | Proxy router + Rota integration | 🔜 |
| 6 | Reacher email verifier worker | 🔜 |
| 7 | Lead scoring engine | 🔜 |
| 8 | REST API endpoints | 🔜 |
| 9 | Admin UI | 🔜 |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rud1gleif/b2cleadspro.git
cd b2cleadspro

# Copy env file
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

## Environment Variables

See `.env.example` for all required configuration.

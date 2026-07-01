# B2C Leads Pro

> Location-based B2C email lead generation — scrape, verify, and export worldwide consumer email leads filtered by country, city, or region.

---

## What it does

- **Location search** — pick one or many locations (country, city, region) at job creation time
- **Multi-source crawling** — seed URLs from local directories, Google Maps-style queries, Yelp, YellowPages, and more
- **Playwright rendering** — JS-heavy sites rendered with Chromium headless
- **Sitemap discovery** — Firecrawl-style `sitemap.xml` + robots.txt deep-crawl
- **Proxy rotation** — per-request proxy selection with automatic fail-over
- **4-stage email verification** — syntax → disposable-domain blocklist → MX record → Reacher SMTP
- **Auto-updating blocklist** — 50k+ disposable domains refreshed every 24 h from open-source sources
- **Redis job queue** — scrape and verify jobs queued via Redis; falls back to BackgroundTasks if Redis is offline
- **Dashboard UI** — built-in web dashboard with live job progress, lead filters, CSV export, proxy manager
- **REST API** — full OpenAPI docs at `/docs`

---

## Stack

| Layer | Tool |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 (SQLite for local dev) |
| Queue | Redis 7 |
| Crawler | httpx + BeautifulSoup4 |
| JS rendering | Playwright (Chromium) |
| SMTP verify | Reacher (self-hosted, no API key needed) |
| Migrations | Alembic |
| Containerization | Docker + Docker Compose |

---

## Quick Start (Docker — recommended)

### 1. Clone and configure

```bash
git clone https://github.com/rud1gleif/b2cleadspro.git
cd b2cleadspro
cp .env.example .env
```

Open `.env` and set at minimum:
```env
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_long_random_secret
REACHER_FROM_EMAIL=verify@yourdomain.com
REACHER_HELLO_NAME=yourdomain.com
```

### 2. Start everything

```bash
make up
# or: docker compose up --build -d
```

This starts 5 containers: **postgres**, **redis**, **reacher**, **api**, **worker**.

Alembic migrations run automatically on first boot.

### 3. Open the dashboard

```
http://localhost:8000          ← Dashboard
http://localhost:8000/docs     ← API docs (Swagger)
```

### 4. Run your first job

1. Go to **Dashboard → New Job**
2. Search for locations (e.g. "Toronto", "Amsterdam", "Sydney")
3. Add optional niches (e.g. "restaurants", "dentists")
4. Click **Launch Job**
5. Watch progress on the **Jobs** page
6. Export leads as CSV from the **Leads** page

---

## Local Development (no Docker)

```bash
# 1. Install dependencies
make setup

# 2. Run migrations (creates local SQLite DB)
make migrate-local

# 3. Start API
make dev
# → http://localhost:8000

# 4. (Optional) Start queue dispatcher in a second terminal
make worker-local
```

> Without Redis, jobs run directly via FastAPI BackgroundTasks — no queue setup needed.
> Without Reacher, verification skips SMTP and still gives up to 80/100 score.

---

## Environment Variables

See [`.env.example`](.env.example) for all options. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | SQLite (local) / Postgres (Docker) | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `REACHER_URL` | `http://localhost:8080` (Docker) | Reacher SMTP verifier URL |
| `REACHER_FROM_EMAIL` | `verify@example.com` | HELO identity for SMTP probes |
| `POSTGRES_PASSWORD` | `change_me_in_production` | **Change this** |
| `SECRET_KEY` | `change-me-...` | **Change this** |
| `DEFAULT_CONCURRENCY` | `5` | Parallel scrape requests per job |
| `DEFAULT_MAX_PAGES` | `50` | Max pages crawled per job |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check + blocklist stats |
| `GET/POST` | `/api/locations` | Search / add locations |
| `GET/POST` | `/api/jobs` | List / create scrape jobs |
| `GET` | `/api/jobs/{id}/status` | Live job status from Redis |
| `POST` | `/api/jobs/{id}/verify` | Re-verify all leads from a job |
| `GET` | `/api/leads` | Filter + paginate leads |
| `GET` | `/api/leads/export/csv` | Export filtered leads as CSV |
| `POST` | `/api/verify/single` | Verify one email address |
| `POST` | `/api/verify/bulk` | Verify up to 500 emails |
| `POST` | `/api/verify/re-verify` | Bulk re-verify DB leads |
| `GET` | `/api/verify/blocklist/stats` | Disposable blocklist statistics |
| `GET` | `/api/stats/overview` | KPI overview |
| `GET` | `/api/stats/leads-by-country` | Lead counts by country |
| `GET/POST/DELETE` | `/api/proxies` | Manage proxies |
| `POST` | `/api/proxies/{id}/check` | Test proxy latency |

---

## Verification Scoring

```
+40  syntax valid
+20  not a disposable domain
+20  MX record found
+20  Reacher SMTP confirmed deliverable
─────────────────
 100  max score
```

Leads scoring **≥ 80** are considered high-quality.

---

## Useful Commands

```bash
make help            # Show all commands
make logs            # Tail all container logs
make logs-api        # API logs only
make health          # Check /health endpoint
make test-reacher    # Test Reacher with a live email
make migrate         # Run Alembic migrations in Docker
make shell           # Shell into API container
make down            # Stop everything
```

---

## Legal & Compliance

- Only scrape **publicly visible** contact information
- Store `source_url` and `created_at` for every lead (built-in)
- Implement suppression/unsubscribe lists before outreach
- GDPR (EU), CAN-SPAM (US), CASL (Canada) apply — consult legal advice for your jurisdiction
- Do not scrape sites that prohibit it in their `robots.txt` or Terms of Service

---

## Project Structure

```
b2cleadspro/
├── app/
│   ├── api/           # FastAPI routers (jobs, leads, proxies, verify, stats, ui)
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic (scraper, playwright, sitemap, verify, disposable, queue, proxy)
│   ├── workers/       # Background workers (scrape_worker, verify_worker, queue_dispatcher)
│   ├── config.py      # Settings from .env
│   ├── database.py    # DB session factory
│   └── main.py        # FastAPI app entry point
├── alembic/           # DB migrations
├── ui/                # Dashboard HTML + static assets
├── data/              # Persistent data volume mount
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
└── .env.example
```

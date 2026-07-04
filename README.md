# B2C Leads Pro

Unified lead generation tool combining **Google Maps** and **directory scrapers** (Yelp, YellowPages, Angi) into one UI.

## Engines

| Engine | Source | Data Points |
|---|---|---|
| Google Maps | Playwright headless browser | Name, phone, website, address, rating, category + email (extracted from site) |
| Directory | httpx + BeautifulSoup | Name, phone, email, website, address (Yelp / YellowPages / Angi) |

## Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/rud1gleif/b2cleadspro
cd b2cleadspro
cp .env.example .env

# 2. Build & run
docker compose up --build

# 3. Run DB migrations
docker compose exec api alembic upgrade head

# 4. Open the UI
open http://localhost:8000
```

## How to Use

1. **Locations** — type a city name and press Enter to add it as a tag (add multiple)
2. **Niches** — optional comma-separated list (e.g. `plumber, roofer, dentist`)
3. **Sources** — toggle which engines to use (Google Maps, Yelp, YellowPages, Angi)
4. **Max Pages** — how many result pages to scrape per source (1–50)
5. **Concurrency** — parallel browser/HTTP sessions (1–10)
6. Click **🚀 Launch Job** — leads appear in the table in real time
7. Click **⬇ Export CSV** to download all leads for a job

## Project Structure

```
app/
  models/         — SQLAlchemy models (Job, Lead)
  schemas/        — Pydantic schemas
  api/            — FastAPI routers (jobs, leads, ui)
  workers/
    gmaps_scraper.py      — Google Maps engine (Playwright)
    directory_scraper.py  — Yelp / YellowPages / Angi engine (httpx + BS4)
    email_extractor.py    — Email extraction util
    job_runner.py         — Orchestrator: dispatches scrapers, saves to DB
alembic/          — DB migrations
ui/
  index.html      — Single-page UI
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | postgres://... | PostgreSQL connection string |
| `CONCURRENCY` | 5 | Default parallel workers |
| `MAX_PAGES` | 10 | Default pages per source |

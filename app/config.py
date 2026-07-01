from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "changeme"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://b2c:changeme@localhost:5432/b2cleadspro"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_discovery: str = "queue:discovery"
    redis_queue_scrape: str = "queue:scrape"
    redis_queue_verify: str = "queue:verify"
    redis_queue_score: str = "queue:score"

    # Firecrawl
    firecrawl_api_url: str = "http://firecrawl:3002"
    firecrawl_api_key: Optional[str] = None

    # Reacher
    reacher_url: str = "http://reacher:8080"
    reacher_api_key: Optional[str] = None

    # Rota
    rota_url: str = "http://rota:8000"
    rota_api_key: Optional[str] = None

    # Scraper
    scraper_concurrency: int = 5
    scraper_default_timeout: int = 30
    scraper_retry_limit: int = 3
    scraper_delay_min: float = 1.0
    scraper_delay_max: float = 4.0

    # Playwright
    playwright_headless: bool = True
    playwright_browser: str = "chromium"

    # Cities DB
    cities_db_path: str = "./data/cities.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

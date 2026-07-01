"""Application settings loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "sqlite:///./b2cleads.db"

    # --- PostgreSQL (used by Docker Compose to provision the DB) ---
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_scrape: str = "b2c:scrape"
    redis_queue_verify: str = "b2c:verify"
    redis_queue_discovery: str = "b2c:discovery"

    # --- Reacher SMTP Verification (self-hosted) ---
    # Run Reacher: docker run -p 8080:8080 reacherhq/backend:latest
    reacher_url: Optional[str] = None   # e.g. "http://localhost:8080"
    reacher_api_key: Optional[str] = None
    reacher_from_email: Optional[str] = None   # HELO/From identity for SMTP probing
    reacher_hello_name: Optional[str] = None   # EHLO hostname for SMTP probing

    # --- Scraping ---
    default_concurrency: int = 5
    default_max_pages: int = 50
    request_timeout: int = 20
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # --- App ---
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production-please"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

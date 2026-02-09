from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    scheduler_enabled: bool = False
    scheduler_tickers: str = "AAPL"

    scheduler_mode: str = "interval"
    scheduler_every_minutes: int = 5

    scheduler_hour_utc: int = 22
    scheduler_minute_utc: int = 0

    ingest_period: str = "1y"
    ingest_interval: str = "1d"

    model_window: int = 20

settings = Settings()

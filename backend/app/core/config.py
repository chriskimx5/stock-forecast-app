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

    # Alpaca paper trading — fill in when ready
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Email notifications — fill in when ready
    notify_email_to: str = ""
    notify_email_from: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Risk management
    paper_capital: float = 10000.0
    max_risk_per_trade_pct: float = 2.0   # 2% of capital = $200 max loss per trade
    take_profit_pct: float = 4.0          # 4% target
    stop_loss_pct: float = 2.0            # 2% stop loss

settings = Settings()

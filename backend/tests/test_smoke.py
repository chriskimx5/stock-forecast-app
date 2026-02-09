import os
import pytest
from fastapi.testclient import TestClient

# Make sure env is present for app import
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/stocks")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app  # noqa: E402

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_ready():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_ingest_and_prices():
    # Ingest a small window to keep test fast
    r = client.post("/api/v1/ingest/AAPL?period=1mo&interval=1d")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == "AAPL"
    assert data["rows"] > 0

    r2 = client.get("/api/v1/prices/AAPL?limit=3")
    assert r2.status_code == 200
    arr = r2.json()
    assert isinstance(arr, list)
    assert len(arr) > 0
    for k in ["ts", "open", "high", "low", "close", "volume"]:
        assert k in arr[0]

import os
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/stocks")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app  # noqa: E402

client = TestClient(app)

def test_train_and_predict_cached():
    # Ensure data exists
    r0 = client.post("/api/v1/ingest/AAPL?period=6mo&interval=1d")
    assert r0.status_code == 200
    assert r0.json()["rows"] > 0

    # Train
    r1 = client.post("/api/v1/train/AAPL?window=20")
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1["ticker"] == "AAPL"
    assert j1["window"] == 20

    # Predict twice to confirm caching
    r2 = client.get("/api/v1/predict/AAPL?ttl=60")
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["ticker"] == "AAPL"
    assert isinstance(j2["pred_close"], (int, float))
    assert j2["cached"] in (True, False)

    r3 = client.get("/api/v1/predict/AAPL?ttl=60")
    assert r3.status_code == 200
    j3 = r3.json()
    assert j3["cached"] is True

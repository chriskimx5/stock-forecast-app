# Stock Forecasting Web App

Full-stack stock forecasting app:
- Frontend: TypeScript + Next.js
- Backend: FastAPI + Postgres + Redis
- Pipeline: ingestion → storage → training → inference
- Scheduler: automated ingestion + retraining (APScheduler)

## Features
- Ticker-based historical price charting (Postgres-backed)
- Market-data ingestion (yfinance → normalized OHLCV → Postgres upsert)
- Training pipeline (model artifacts persisted as joblib)
- Inference endpoint (next-close prediction + uncertainty band)
- Redis caching for prediction responses
- Health + readiness checks
- Pytest coverage for core routes

## Project structure
- `frontend/` Next.js UI
- `backend/` FastAPI API + scheduler + ML services
- `docker-compose.yml` Postgres + Redis for local dev

## Local setup

### Prereqs
- Docker + Docker Compose
- Python 3.11
- Poetry
- Node.js + npm

### Start infra (Postgres + Redis)
From repo root:

```bash
docker compose up -d postgres redis



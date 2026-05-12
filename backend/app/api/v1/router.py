from fastapi import APIRouter
from app.api.v1.routes import prices, tickers, ingest, ml, model, watchlist, dashboard, journal, positions, signals

api_router = APIRouter()
api_router.include_router(tickers.router, prefix="/tickers", tags=["tickers"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(ml.router, tags=["ml"])
api_router.include_router(model.router, tags=["model"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(journal.router, prefix="/journal", tags=["journal"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])

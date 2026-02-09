from fastapi import APIRouter
from app.api.v1.routes import prices, tickers, ingest, ml, model

api_router = APIRouter()
api_router.include_router(tickers.router, prefix="/tickers", tags=["tickers"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(ml.router, tags=["ml"])
api_router.include_router(model.router, tags=["model"])

from fastapi import FastAPI
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import redis

from app.api.v1.router import api_router
from app.db.session import engine
from app.core.config import settings

from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.services.scheduler import start_scheduler, stop_scheduler

from dotenv import load_dotenv
load_dotenv()



@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.scheduler_enabled:
        start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title = "Stock Forecasting API",
    lifespan=lifespan,
    )



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ready")
def ready():
    # DB check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        return {"ok": False, "db": str(e)}

    # Redis check
    try:
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
    except Exception as e:
        return {"ok": False, "redis": str(e)}

    return {"ok": True}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

app.include_router(api_router, prefix="/api/v1")

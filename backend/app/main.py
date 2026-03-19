"""FastAPI main application entry point."""
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.scheduler import start_scheduler, scheduler
from app.routers import auth, users, tracking, backtest, optimize, fundamentals, notifications
from app.routers.market import router as market_router, test_router as alert_test_router
from app.routers.optimize import router as optimize_router
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
import os
import logging
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel
from typing import Optional, Any

settings = get_settings()

# Setup backend logger
logging.basicConfig(
    handlers=[RotatingFileHandler("backend.log", maxBytes=10485760, backupCount=5)],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)

# Setup frontend logger
frontend_logger = logging.getLogger("frontend")
frontend_logger.setLevel(logging.INFO)
fh = RotatingFileHandler("frontend.log", maxBytes=10485760, backupCount=5)
fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [FRONTEND] %(message)s"))
frontend_logger.addHandler(fh)
frontend_logger.propagate = False

class LogMessage(BaseModel):
    level: str
    message: str
    details: Optional[Any] = None
    url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="Finance Dashboard API",
    description="Investment tracking, backtest, optimization, and alerts API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", settings.app_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tracking.router)
app.include_router(backtest.router)
app.include_router(optimize.router)
app.include_router(fundamentals.router)
app.include_router(market_router)
app.include_router(alert_test_router)
app.include_router(optimize_router)
app.include_router(notifications.router)

@app.on_event("startup")
async def startup_event():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=False)
        FastAPICache.init(RedisBackend(redis), prefix="fin-cache")
    except Exception as e:
        print(f"Warning: Failed to connect to Redis: {e}. Caching will not work.")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@app.post("/api/logs")
async def receive_frontend_logs(log: LogMessage):
    log_text = f"{log.url} - {log.message}"
    if log.details:
        log_text += f" - {log.details}"
    
    print(f"[FRONTEND_LOG] {log_text}")
    
    if log.level.lower() == "error":
        frontend_logger.error(log_text)
    elif log.level.lower() in ["warn", "warning"]:
        frontend_logger.warning(log_text)
    else:
        frontend_logger.info(log_text)
        
    return {"status": "ok"}


@app.post("/api/admin/sync-tw-etf")
async def trigger_tw_etf_sync(background_tasks: BackgroundTasks):
    """Admin endpoint: immediately sync TW ETF list from TWSE into Supabase."""
    from app.services.tw_etf_sync import sync_tw_etf_list
    background_tasks.add_task(sync_tw_etf_list)
    return {"status": "sync_started", "message": "TW ETF sync has been started in the background."}


@app.post("/api/admin/sync-us-etf")
async def trigger_us_etf_sync(background_tasks: BackgroundTasks):
    """Admin endpoint: immediately sync US ETF list from Yahoo Finance into Supabase."""
    from app.services.us_etf_sync import sync_us_etf_list
    background_tasks.add_task(sync_us_etf_list)
    return {"status": "sync_started", "message": "US ETF sync has been started in the background."}

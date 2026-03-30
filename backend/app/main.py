"""FastAPI main application entry point."""
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.scheduler import start_scheduler, scheduler
from app.routers import auth, users, tracking, backtest, optimize, fundamentals, notifications, line, briefing as briefing_router
from app.routers.market import router as market_router, test_router as alert_test_router
from app.routers.optimize import router as optimize_router
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from redis import asyncio as aioredis
import os
import socket
import logging
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel
from typing import Optional, Any

settings = get_settings()

# syslog 格式：hostname process[pid]: message（時間由 PM2 提供）
_HOSTNAME = socket.gethostname()
_SYSLOG_FORMAT = f"{_HOSTNAME} %(name)s[%(process)d]: %(message)s"

# Setup backend logger
logging.basicConfig(
    handlers=[
        RotatingFileHandler("backend.log", maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format=_SYSLOG_FORMAT,
)

# Setup frontend logger
frontend_logger = logging.getLogger("frontend")
frontend_logger.setLevel(logging.INFO)
_frontend_formatter = logging.Formatter(
    f"{_HOSTNAME} FRONTEND[%(process)d]: %(message)s",
)
_fh = RotatingFileHandler("frontend.log", maxBytes=10485760, backupCount=5)
_fh.setFormatter(_frontend_formatter)
frontend_logger.addHandler(_fh)
_sh = logging.StreamHandler()
_sh.setFormatter(_frontend_formatter)
frontend_logger.addHandler(_sh)
frontend_logger.propagate = False

class LogMessage(BaseModel):
    level: str
    message: str
    details: Optional[Any] = None
    url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 覆寫 uvicorn loggers 的 formatter，統一輸出格式
    _uv_formatter = logging.Formatter(
        f"{_HOSTNAME} %(name)s[%(process)d]: %(message)s",
    )
    for _uv_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        for _handler in logging.getLogger(_uv_name).handlers:
            _handler.setFormatter(_uv_formatter)

    # Log current configuration
    logger = logging.getLogger("app.main")
    logger.info(f"Allowed CORS origins: {['http://localhost:5173', 'http://localhost:3100', settings.app_base_url]}")
    logger.info(f"Effective APP_BASE_URL: {settings.app_base_url}")
    
    # Initialize Cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=False)
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="fin-cache")
        logger.info("✅ Cache initialized with Redis")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to InMemoryBackend for caching.")
        FastAPICache.init(InMemoryBackend(), prefix="fin-cache")

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

# Request logger middleware to debug CORS / Origin issues
@app.middleware("http")
async def log_request_origin(request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    path = request.url.path
    
    # Log incoming request details for debugging domain/cors issues
    if path.startswith("/api"):
        logger = logging.getLogger("app.middleware")
        logger.info(f"Incoming Request: {method} {path} | Origin: {origin}")
        
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3100", settings.app_base_url],
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
app.include_router(line.router)
app.include_router(briefing_router.router)



@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@app.post("/api/logs")
async def receive_frontend_logs(log: LogMessage):
    log_text = f"{log.url} - {log.message}"
    if log.details:
        log_text += f" - {log.details}"
    
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

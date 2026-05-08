import asyncio
import logging
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from .api import router, limiter, metrics
from .db import init_db
from .ingestion import ingestion_buffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Incident Management System API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

async def metrics_printer():
    while True:
        await asyncio.sleep(5)
        now = time.time()
        elapsed = now - metrics["last_reset"]
        if elapsed > 0:
            tps = metrics["processed_signals"] / elapsed
            logger.info(f"Throughput: {tps:.2f} signals/sec (Total: {metrics['processed_signals']})")
            
        metrics["processed_signals"] = 0
        metrics["last_reset"] = now

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(ingestion_buffer.worker())
    asyncio.create_task(metrics_printer())
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    ingestion_buffer.running = False
    logger.info("Application shutting down.")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Postgres
engine = create_async_engine(settings.asyncpg_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# MongoDB
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB]
signal_collection = mongo_db["signals"]

# Redis
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

async def init_db():
    from .models import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Postgres initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Postgres: {e}")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

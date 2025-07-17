import asyncio
import asyncpg
from typing import Optional
from settings import DSN
from utils.log import logger
_pool: Optional[asyncpg.Pool] = None


async def init_pool(dsn: str) -> asyncpg.Pool:
    """Initialize the database connection pool."""
    global _pool
    if _pool is None:
        logger.info("Initializing database connection pool.")
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=15,
            max_inactive_connection_lifetime=60.0 # seconds
        )
        logger.info(f"Database connection pool initialized.")
    return _pool


def get_pool() -> asyncpg.Pool:
    """Return the database connection pool."""
    if _pool is None:
        logger.error("Database pool has not been initialized.")
        raise RuntimeError("Database pool has not been initialized.")
    return _pool


async def close_pool():
    """Attempts to gracefully close the database connection pool."""
    global _pool
    if _pool is not None:
        await asyncio.wait_for(_pool.close(), timeout=15)
        _pool = None


async def setup(bot):
    await init_pool(DSN)
async def teardown(bot):
    if _pool is None:
        logger.error("Database pool has not been initialized. Cannot close it.")
    await close_pool()

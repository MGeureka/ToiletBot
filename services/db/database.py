import asyncio
import asyncpg
from typing import Optional
import itertools
from contextlib import asynccontextmanager
from settings import DSN
from utils.log import db_logger, logger


class Database:
    def __init__(self, dsn: str):
        """Initialize the DatabaseConn class."""
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_count = itertools.count()


    async def start_pool(self):
        """Initialize the database connection pool."""
        if self.pool is None:
            logger.info("Initializing database connection pool.")
            db_logger.info("Initializing database connection pool.")
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=2,
                max_size=15,
                max_inactive_connection_lifetime=60.0, # seconds
            )
            logger.info("Database connection pool initialized.")
            db_logger.info("Database connection pool initialized.")
        return self.pool


    def get_pool(self) -> asyncpg.Pool:
        """Return the database connection pool."""
        if self.pool is None:
            logger.error("Database pool has not been initialized.")
            db_logger.error("Database pool has not been initialized.")
            raise RuntimeError("Database pool has not been initialized.")
        return self.pool


    async def close_pool(self):
        """Attempts to gracefully close the database connection pool."""
        if self.pool is not None:
            await asyncio.wait_for(self.pool.close(), timeout=15)
            logger.info("Database pool has successfully been closed.")
            db_logger.info("Database pool has successfully been closed.")
            self.pool = None


    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self.pool is None:
            logger.error("Database pool has not been initialized.")
            db_logger.error("Database pool has not been initialized.")
            raise RuntimeError("Database pool has not been initialized.")
        count = next(self.connection_count)
        pool: asyncpg.Pool = await self.get_pool()
        conn: asyncpg.Connection = await pool.acquire()

        stats = self.get_stats()
        db_logger.info(f"Acquired connection: {count} | "
                       f"Pool stats: {stats['size']} ({stats['idle']})")
        try:
            yield conn
        finally:
            await pool.release(conn)
            stats = self.get_stats()
            db_logger.info(f"Released connection: {count} | "
                           f"Pool stats: {stats['size']} ({stats['idle']})")


    def get_stats(self):
        """Get the current statistics of the database connection pool."""
        if self.pool is None:
            logger.error("Database pool has not been initialized.")
            db_logger.error("Database pool has not been initialized.")
            raise RuntimeError("Database pool has not been initialized.")

        stats = {
            "size": self.pool.get_size(),
            "idle": self.pool.get_idle_size(),
        }
        return stats


    async def execute(self, query: str, *args):
        """Execute a commit operation on the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.execute(query, *args)
                return result
            except Exception as e:
                raise


    async def executemany(self, query: str, args: list[tuple]):
        """Execute a commit operation with multiple values on the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.executemany(query, args)
                return result
            except Exception as e:
                raise


    async def fetchmany(self, query: str, *args):
        """Fetch multiple rows from the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.fetch(query, *args)
                return result
            except Exception as e:
                raise


    async def fetchval(self, query: str, *args):
        """Fetch a single value from the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.fetchval(query, *args)
                return result
            except Exception as e:
                raise


async def init_db_pool(dsn: str):
    """Initialize the DatabaseConn class."""
    db = Database(dsn)
    await db.start_pool()
    return db


async def setup(bot):
    bot.db = await asyncio.wait_for(init_db_pool(DSN), timeout=15)
async def teardown(bot):
    await bot.db.close_pool()

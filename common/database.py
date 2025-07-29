import asyncio
import asyncpg
from typing import Optional
import itertools
from contextlib import asynccontextmanager
from common.log import db_logger, logger


class Database:
    def __init__(self, dsn: str, max_pool_size: int, min_pool_size: int):
        """Initialize the DatabaseConn class."""
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_count = itertools.count()
        self.max_pool_size = max_pool_size  # Maximum size of the connection pool
        self.min_pool_size = min_pool_size  # Minimum size of the connection pool

    async def start_pool(self):
        """Initialize the database connection pool."""
        if self.pool is None:
            db_logger.info("Initializing database connection pool.")
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                max_inactive_connection_lifetime=60.0, # seconds
            )
            db_logger.info("Database connection pool initialized.")
        return self.pool


    def get_pool(self) -> asyncpg.Pool:
        """Return the database connection pool."""
        if self.pool is None:
            db_logger.error("Database pool has not been initialized.")
            raise RuntimeError("Database pool has not been initialized.")
        return self.pool


    async def close_pool(self):
        """Attempts to gracefully close the database connection pool."""
        if self.pool is not None:
            await asyncio.wait_for(self.pool.close(), timeout=15)
            db_logger.info("Database pool has successfully been closed.")
            self.pool = None


    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self.pool is None:
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
                db_logger.info(f"Execute Query executed: {query} "
                               f"with args: {args}")
                return result
            except Exception as e:
                db_logger.error(f"Error Execute query: {query} "
                                f"with args: {args} - {e}")
                raise


    async def executemany(self, query: str, args: list[tuple]):
        """Execute a commit operation with multiple values on the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.executemany(query, args)
                db_logger.info(f"Executemany Query executed: {query} "
                               f"with args: {args}")
                return result
            except Exception as e:
                db_logger.error(f"Error Executemany query: {query} "
                                f"with args: {args} - {e}")
                raise


    async def fetchmany(self, query: str, *args):
        """Fetch multiple rows from the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.fetch(query, *args)
                db_logger.info(f"Fetchmany Query executed: {query} "
                               f"with args: {args}")
                return result
            except Exception as e:
                db_logger.error(f"Error Fetchmany query: {query} "
                                f"with args: {args} - {e}")
                raise


    async def fetchval(self, query: str, *args):
        """Fetch a single value from the database."""
        async with self.acquire() as conn:
            try:
                result = await conn.fetchval(query, *args)
                db_logger.info(f"Fetchval Query executed: {query} "
                               f"with args: {args}")
                return result
            except Exception as e:
                db_logger.error(f"Error Fetchval query: {query} "
                                f"with args: {args} - {e}")
                raise

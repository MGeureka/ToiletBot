import asyncio
import asyncpg
from datetime import datetime, timezone
from services.db.database import Database
from settings import LEADERBOARD_TYPES, DEFAULT_LEADERBOARD_STATE


async def update_guild(db: Database, guild_id: int, guild_name: str):
    """Add a new guild to the database."""
    query = """
    INSERT INTO guilds.guilds (guild_id, guild_name, added_date, 
    last_updated, is_active)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (guild_id) DO UPDATE SET
    guild_name = EXCLUDED.guild_name,
    last_updated = EXCLUDED.last_updated,
    is_active = EXCLUDED.is_active;
    """
    now = datetime.now(timezone.utc)
    await db.execute(query, guild_id, guild_name, now, now, True)


async def update_guild_settings(db: Database, guild_id: int,
                                leaderboard_channel_id: int | None,
                                leaderboard_message_id: int | None):
    """Update guild settings in the database."""
    query = """
    INSERT INTO guilds.guild_settings (guild_id, leaderboard_channel_id, 
    leaderboard_message_id, last_updated)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (guild_id) DO UPDATE SET
    leaderboard_channel_id = EXCLUDED.leaderboard_channel_id,
    leaderboard_message_id = EXCLUDED.leaderboard_message_id,
    last_updated = EXCLUDED.last_updated;
    """
    now = datetime.now(timezone.utc)
    await db.execute(
        query,
        guild_id,
        leaderboard_channel_id,
        leaderboard_message_id,
        now
    )


async def update_guild_leaderboard_settings(
    db: Database, guild_id: int, is_enabled: list[bool]
):
    """Update the guild's leaderboard settings."""
    query = """
    INSERT INTO guilds.guild_leaderboard_settings (guild_id, leaderboard_type, 
    is_enabled, last_updated)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (guild_id, leaderboard_type) DO UPDATE SET
        is_enabled = EXCLUDED.is_enabled;
    """
    now = datetime.now(timezone.utc)
    data = [(guild_id, lb_type, enabled, now)
        for lb_type, enabled in zip(LEADERBOARD_TYPES, is_enabled)
    ]
    await db.executemany(query, data)


async def initialize_guild(db: Database, guild_id: int, guild_name: str):
    """Initialize a guild in the database."""
    await update_guild(db, guild_id, guild_name)
    await update_guild_settings(db, guild_id, leaderboard_channel_id=None,
                                leaderboard_message_id=None)
    await update_guild_leaderboard_settings(db, guild_id, DEFAULT_LEADERBOARD_STATE)


async def set_guild_inactive(db: Database, guild_id: int):
    """Set a guild as inactive in the database."""
    query = """
    UPDATE guilds.guilds
    SET is_active = FALSE, last_updated = $1
    WHERE guild_id = $2;
    """
    now = datetime.now(timezone.utc)
    await db.execute(query, now, guild_id)


async def setup(bot): pass
async def teardown(bot): pass

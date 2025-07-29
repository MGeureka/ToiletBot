from datetime import datetime, timezone
from services.db.database import Database
from common.log import db_logger


async def update_discord_profile(db: Database, discord_id: int,
                                  discord_username: str, discord_avatar_key):
    """Adds/Updates a discord profile in the database."""
    query = """
    INSERT INTO profiles.discord_profiles (discord_id, discord_username, 
    discord_avatar_key, date_added, last_updated, is_active)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (discord_id) DO UPDATE SET
        discord_username = EXCLUDED.discord_username,
        discord_avatar_key = EXCLUDED.discord_avatar_key,
        last_updated = EXCLUDED.last_updated,
        is_active = EXCLUDED.is_active;
    """
    now = datetime.now(timezone.utc)
    db_logger.info(f"Updating discord profile for user {discord_username} "
                   f"({discord_id})")
    await db.execute(query, discord_id, discord_username,
                     discord_avatar_key, now, now, True)


async def update_guild_membership(db: Database, discord_id: int, guild_id: int):
    """Updates the discord profile for a specific guild."""
    query = """
    INSERT INTO guilds.guild_membership (guild_id, discord_id, date_added, 
    is_active)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (discord_id, guild_id) DO UPDATE SET
        is_active = EXCLUDED.is_active;
    """
    now = datetime.now(timezone.utc)
    db_logger.info(f"Updating guild membership for user {discord_id} in guild "
                   f"{guild_id}")
    await db.execute(query, guild_id, discord_id, now, True)


async def initialize_discord_profile(db: Database, discord_id: int,
                                     discord_username: str, discord_avatar_key,
                                     guild_id: int):
    """Initializes a discord profile in the database."""
    db_logger.info(f"Initializing discord profile for user {discord_username} "
                   f"({discord_id}) in guild {guild_id}")
    await update_discord_profile(db, discord_id, discord_username,
                                  discord_avatar_key)
    await update_guild_membership(db, discord_id, guild_id)


async def check_discord_profile_exists(db: Database, discord_id: int,
                                       guild_id: int):
    """Checks if a discord profile exists in the database."""
    query = """
    SELECT EXISTS (
        SELECT 1 FROM guilds.guild_membership
        WHERE discord_id = $1 AND guild_id = $2
    );
    """
    result = await db.fetchmany(query, discord_id, guild_id)
    db_logger.info(f"Checking discord profile exists for user {discord_id} in "
                   f"guild {guild_id}")
    return result[0]["exists"]


async def setup(bot): pass
async def teardown(bot): pass

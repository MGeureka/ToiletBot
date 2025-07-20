from datetime import datetime, timezone
from services.db.database import Database


async def update_discord_profile(db: Database, discord_id: str,
                                  discord_username: int, discord_avatar_key):
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
    values = (discord_id, discord_username, discord_avatar_key, now, now, True)
    await db.execute(query, values)


async def update_guild_membership(db: Database, discord_id: str, guild_id: int):
    """Updates the discord profile for a specific guild."""
    query = """
    INSERT INTO profiles.guild_membership (guild_id, discord_id, date_added, 
    is_active)
    VALUES ($1, $2)
    ON CONFLICT (discord_id, guild_id) DO UPDATE SET
        is_active = EXCLUDED.is_active;
    """
    now = datetime.now(timezone.utc)
    values = (discord_id, guild_id, now)
    await db.execute(query, values)


async def initialize_discord_profile(db: Database, discord_id: str,
                                     discord_username: int, discord_avatar_key,
                                     guild_id: int):
    """Initializes a discord profile in the database."""
    await update_discord_profile(db, discord_id, discord_username,
                                  discord_avatar_key)
    await update_guild_membership(db, discord_id, guild_id)


async def setup(bot): pass
async def teardown(bot): pass

from datetime import datetime, timezone
import asyncpg

from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profile_from_db)
from utils.log import db_logger
from services.db.discord_database import update_discord_profile
from services.db.database import Database


async def untrack_orphaned_aimlabs_account(db: Database, aimlabs_id: str):
    """Checks if an aimlabs account is orphaned (not linked to any profile)."""
    query1 = """
             SELECT COUNT(*) FROM profiles.aimlabs_profiles
             WHERE aimlabs_id = $1 AND is_active = TRUE;
             """
    count = await db.fetchval(query1, aimlabs_id)
    if count:
        return
    query2 = """
             UPDATE accounts.global_aimlabs_accounts SET is_tracked = False
             WHERE aimlabs_id = $1;
             """
    await db.execute(query2, aimlabs_id)


async def check_aimlabs_profile_exists_in_guild(db: Database, aimlabs_id: str,
                                                guild_id: int) -> bool:
    """Checks if an aimlabs profile exists in the database."""
    query = """
            SELECT EXISTS (
                SELECT 1 FROM profiles.aimlabs_profiles
                WHERE aimlabs_id = $1 AND guild_id = $2 AND is_active = TRUE
            ); \
            """
    return await db.fetchval(query, aimlabs_id, guild_id)


async def add_aimlabs_account_todb(db: Database, aimlabs_id: str,
                                   aimlabs_username: str):
    """Adds an aimlabs account to the global table in the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO accounts.global_aimlabs_accounts (aimlabs_id,
    aimlabs_username, date_added, last_updated, is_tracked)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (aimlabs_id) DO UPDATE SET
        aimlabs_username = excluded.aimlabs_username,
        last_updated = excluded.last_updated,
        is_tracked = excluded.is_tracked;
    """
    db_logger.info(f"Adding aimlabs account to global database {aimlabs_username}")
    await db.execute(query, aimlabs_id, aimlabs_username, now, now, True)


async def add_aimlabs_profile_todb(db: Database, discord_id: int,
                                   guild_id: int, aimlabs_id: str):
    """Adds a aimlabs profile to the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO profiles.aimlabs_profiles (discord_id, guild_id,
    aimlabs_id, date_added, last_updated, is_active)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (discord_id, guild_id) DO UPDATE SET
        aimlabs_id = excluded.aimlabs_id,
        last_updated = excluded.last_updated,
        is_active = excluded.is_active;
            """
    db_logger.info(f"Adding aimlabs profile to database for user {discord_id}"
                   f" in guild {guild_id}")
    await db.execute(query, discord_id, guild_id, aimlabs_id,
                     now, now, True)


async def initialize_aimlabs_profile(db: Database,
                                     aimlabs_username: str, aimlabs_id: str,
                                     discord_id: int, guild_id: int) -> tuple:
    """Adds or updates aimlabs profile in db. Returns (True, str) if
    process is a relink of an existing inactive profile. (False, None)
    otherwise.
    """
    if await check_aimlabs_profile_exists_in_guild(db, aimlabs_id, guild_id):
        raise UsernameAlreadyExists(f"This account had already been claimed. "
                                    f"Please enter a different username.")
    existing_aimlabs_profile = await get_profile_from_db(db, discord_id, guild_id,"aimlabs")
    relink = False
    if existing_aimlabs_profile:
        if not existing_aimlabs_profile["is_active"]:
            relink = True
        else:
            raise UsernameAlreadyExists(
                f"You already have a aimlabs username "
                f"`{existing_aimlabs_profile['aimlabs_username']}` in the "
                f"database. Update it using `/update_aimlabs_profile`")
    db_logger.info(f"Initializing aimlabs profile for user {discord_id}")
    await add_aimlabs_account_todb(db, aimlabs_id, aimlabs_username)
    await add_aimlabs_profile_todb(db, discord_id, guild_id, aimlabs_id)
    if relink:
        await untrack_orphaned_aimlabs_account(db, existing_aimlabs_profile["aimlabs_id"])
        return True, existing_aimlabs_profile["aimlabs_username"]
    return False, None


async def remove_aimlabs_username_fromdb(db: Database, discord_id: int,
                                         guild_id: int) -> None:
    """Sets aimlabs profile to inactive in the database."""
    existing_aimlabs_profile = await get_profile_from_db(db, discord_id,
                                                         guild_id,
                                                         profile="aimlabs")
    if (not existing_aimlabs_profile or
            not existing_aimlabs_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a aimlabs profile "
                                   f"in the database. Add it using "
                                   f"`/add_aimlabs_profile`")

    query = """
            UPDATE profiles.aimlabs_profiles SET is_active = False
            WHERE discord_id = $1 AND guild_id = $2; \
            """
    await db.execute(query, discord_id, guild_id)
    await untrack_orphaned_aimlabs_account(db, existing_aimlabs_profile["aimlabs_id"])


async def update_aimlabs_username_indb(
        db: Database,
        aimlabs_username: str,
        aimlabs_id: str,
        discord_id: int,
        guild_id: int
):
    """ Updates aimlabs profile in the database."""
    if await check_aimlabs_profile_exists_in_guild(db, aimlabs_id, guild_id):
        raise UsernameAlreadyExists(f"This account has already been claimed. "
                                    f"Please enter a different username.")
    existing_aimlabs_profile = await get_profile_from_db(
        db, discord_id, guild_id, profile="aimlabs"
    )
    if (not existing_aimlabs_profile or
            not existing_aimlabs_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a aimlabs profile "
                                   f"in the database. Add it using "
                                   f"`/add_aimlabs_profile`")
    await add_aimlabs_account_todb(db, aimlabs_id, aimlabs_username)
    query = f"""
    UPDATE profiles.aimlabs_profiles SET
    aimlabs_id = $1
    WHERE discord_id = $2 AND guild_id = $3;
    """
    await db.execute(query, aimlabs_id, discord_id, guild_id)
    await untrack_orphaned_aimlabs_account(db, existing_aimlabs_profile['aimlabs_id'])


async def setup(bot): pass
async def teardown(bot): pass

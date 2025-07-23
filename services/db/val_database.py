from datetime import datetime, timezone
import asyncpg

from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profile_from_db)
from utils.log import db_logger
from services.db.discord_database import update_discord_profile
from services.db.database import Database


async def untrack_orphaned_val_account(db: Database, valorant_id: str):
    """Checks if a valorant account is orphaned (not linked to any profile)."""
    query1 = """
             SELECT COUNT(*) FROM profiles.valorant_profiles
             WHERE valorant_id = $1 AND is_active = TRUE;
             """
    count = await db.fetchval(query1, valorant_id)
    if count:
        return
    query2 = """
             UPDATE accounts.global_valorant_accounts SET is_tracked = False
             WHERE valorant_id = $1;
             """
    await db.execute(query2, valorant_id)


async def check_val_profile_exists_in_guild(db: Database, valorant_id: str,
                                                guild_id: int) -> bool:
    """Checks if a valorant profile exists in the database."""
    query = """
            SELECT EXISTS (
                SELECT 1 FROM profiles.valorant_profiles
                WHERE valorant_id = $1 AND guild_id = $2 AND is_active = TRUE
            ); \
            """
    return await db.fetchval(query, valorant_id, guild_id)


async def add_val_account_todb(db: Database, valorant_id: str, valorant_username: str, valorant_tag: str,
                                   region: str):
    """Adds a valorant account to the global table in the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO accounts.global_valorant_accounts (valorant_id, 
    valorant_username, valorant_tag, region, date_added, last_updated, 
    is_tracked)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (valorant_id) DO UPDATE SET
        valorant_username = excluded.valorant_username,
        valorant_tag = excluded.valorant_tag,
        region = excluded.region,
        last_updated = excluded.last_updated,
        is_tracked = excluded.is_tracked;
            """
    db_logger.info(f"Adding valorant account to global database "
                   f"{valorant_username}#{valorant_tag}")
    await db.execute(query, valorant_id, valorant_username,
                     valorant_tag, region, now, now, True)


async def add_val_profile_todb(db: Database, discord_id: int,
                                   guild_id: int, valorant_id: str):
    """Adds a valorant profile to the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO profiles.valorant_profiles (discord_id, guild_id,
    valorant_id, date_added, last_updated, is_active)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (discord_id, guild_id) DO UPDATE SET
        valorant_id = excluded.valorant_id,
        last_updated = excluded.last_updated,
        is_active = excluded.is_active;
            """
    db_logger.info(f"Adding valorant profile to database for user {discord_id}"
                   f" in guild {guild_id}")
    await db.execute(query, discord_id, guild_id, valorant_id,
                     now, now, True)


async def initialize_val_profile(db: Database,
                                 valorant_username: str, valorant_id: str, valorant_tag: str,
                                 region: str, discord_id: int, guild_id: int) -> tuple:
    """Adds or updates valorant profile in db. Returns (True, str) if
    process is a relink of an existing inactive profile. (False, None)
    otherwise.
    """
    if await check_val_profile_exists_in_guild(db, valorant_id, guild_id):
        raise UsernameAlreadyExists(f"This account had already been claimed. "
                                    f"Please enter a different username.")
    existing_val_profile = await get_profile_from_db(db, discord_id, guild_id,"val")
    relink = False
    if existing_val_profile:
        if not existing_val_profile["is_active"]:
            relink = True
        else:
            raise UsernameAlreadyExists(
                f"You already have a valorant profile "
                f"`{existing_val_profile['valorant_username']}#"
                f"{existing_val_profile['valorant_tag']}` in the "
                f"database. Update it using `/update_valorant_profile`")
    db_logger.info(f"Initializing valorant profile for user {discord_id}")
    await add_val_account_todb(db, valorant_id, valorant_username,
                               valorant_tag, region)
    await add_val_profile_todb(db, discord_id, guild_id, valorant_id)
    if relink:
        await untrack_orphaned_val_account(db, existing_val_profile["valorant_id"])
        return True, (f"{existing_val_profile['valorant_username']}#"
                      f"{existing_val_profile['valorant_tag']}")
    return False, None


async def remove_val_username_fromdb(db: Database, discord_id: int,
                                         guild_id: int) -> None:
    """Sets valorant profile to inactive in the database."""
    existing_valorant_profile = await get_profile_from_db(db, discord_id,
                                                         guild_id,
                                                         profile="val")
    if (not existing_valorant_profile or
            not existing_valorant_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a valorant profile "
                                   f"in the database. Add it using "
                                   f"`/add_valorant_profile`")

    query = """
            UPDATE profiles.valorant_profiles SET is_active = False
            WHERE discord_id = $1 AND guild_id = $2;
            """
    await db.execute(query, discord_id, guild_id)
    await untrack_orphaned_val_account(db, existing_valorant_profile["valorant_id"])


async def update_val_username_indb(
        db: Database,
        valorant_username: str,
        valorant_id: str,
        valorant_tag: str,
        region: str,
        discord_id: int,
        guild_id: int
):
    """ Updates valorant profile in the database."""
    if await check_val_profile_exists_in_guild(db, valorant_id, guild_id):
        raise UsernameAlreadyExists(f"This account has already been claimed. "
                                    f"Please enter a different username.")
    existing_valorant_profile = await get_profile_from_db(
        db, discord_id, guild_id, profile="val"
    )
    if (not existing_valorant_profile or
            not existing_valorant_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a valorant profile "
                                   f"in the database. Add it using "
                                   f"`/add_valorant_profile`")
    await add_val_account_todb(
        db, valorant_id, valorant_username, valorant_tag, region
    )
    query = f"""
    UPDATE profiles.valorant_profiles SET
    valorant_id = $1
    WHERE discord_id = $2 AND guild_id = $3;
    """
    await db.execute(query, valorant_id, discord_id, guild_id)
    await untrack_orphaned_val_account(db, existing_valorant_profile['valorant_id'])


async def setup(bot): pass
async def teardown(bot): pass

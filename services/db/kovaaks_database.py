from datetime import datetime, timezone

import asyncpg

from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profile_from_db, execute_commit)
from services.db.discord_database import update_discord_profile
from services.db.database import Database


async def add_kovaaks_account_todb(db: Database, kovaaks_id: str, kovaaks_username: str, steam_id: str,
                                    steam_username: str):
    """Adds a kovaaks account to the global table in the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO accounts.global_kovaaks_accounts (kovaaks_id, 
    kovaaks_username, steam_id, steam_username, date_added, last_updated)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (kovaaks_id) DO UPDATE SET
        steam_id = excluded.steam_id,
        kovaaks_username = excluded.kovaaks_username,
        steam_username = excluded.steam_username,
        last_updated = excluded.last_updated;
    """
    await db.execute(query, kovaaks_id, kovaaks_username,
                     steam_id, steam_username, now, 1, now)


async def add_kovaaks_profile_todb(db: Database, discord_id: int,
                                    guild_id: int, kovaaks_id: str):
    """Adds a kovaaks profile to the database."""
    now = datetime.now(timezone.utc)
    query = """
    INSERT INTO profiles.kovaaks_profiles (discord_id, guild_id, 
    kovaaks_id, date_added, last_updated, is_active)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (discord_id, guild_id) DO UPDATE SET
        last_updated = excluded.last_updated,
        is_active = excluded.is_active;
    """
    await db.execute(query, discord_id, guild_id, kovaaks_id,
                     now, now, True)


async def initialize_kovaaks_profile(db: Database,
        kovaaks_username: str, kovaaks_id: str, steam_username: str,
        steam_id: str, discord_username: str, discord_id: int,
        guild_id: int) -> tuple:
    """Adds or updates kovaaks profile in db. Returns (True, str) if
    process is a relink of an existing inactive profile. (False, None)
    otherwise.
    """
    existing_kovaaks_profile = await get_profile_from_db(db, discord_id, guild_id,"kovaaks")
    relink = False
    if existing_kovaaks_profile:
        if existing_kovaaks_profile["is_active"] == 0:
            relink = True
        else:
            raise UsernameAlreadyExists(f"You already have a kovaaks username "
                                        f"`{existing_kovaaks_profile[1]}` in the "
                                        f"database. Update it using "
                                        f"`/update_kovaaks_profile`")
    await add_kovaaks_profile_todb(db, discord_id, guild_id, kovaaks_id)
    await add_kovaaks_account_todb(db, kovaaks_id, kovaaks_username,
                                    steam_id, steam_username)
    if relink:
        return True, existing_kovaaks_profile["kovaaks_username"]
    return False, None


async def remove_kovaaks_username_fromdb(db: Database, discord_id: int,
                                         guild_id: int) -> None:
    """Sets kovaaks profile to inactive in the database."""
    existing_kovaaks_profile = await get_profile_from_db(db, discord_id,
                                                         guild_id,
                                                         profile="kovaaks")
    if (not existing_kovaaks_profile or
            not existing_kovaaks_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a kovaaks profile "
                                   f"in the database. Add it using "
                                   f"`/add_kovaaks_profile`")

    query = """
    UPDATE profiles.kovaaks_profiles SET is_active = False 
    WHERE discord_id = $1 AND guild_id = $2;
    """
    await db.execute(query, discord_id, guild_id)


async def untrack_orphaned_kovaaks_account(db: Database, kovaaks_id: str):
    """Checks if a kovaaks account is orphaned (not linked to any profile)."""
    query1 = """
    SELECT COUNT(*) FROM profiles.kovaaks_profiles 
    WHERE kovaaks_id = $1;
    """
    count = await db.fetchval(query1, kovaaks_id)
    if count:
        return
    query2 = """
    UPDATE accounts.global_kovaaks_accounts SET is_tracked = False 
    WHERE kovaaks_id = $1;
    """
    await db.execute(query2, kovaaks_id)


async def update_kovaaks_username_indb(
        db: Database,
        kovaaks_username: str,
        kovaaks_id: str,
        steam_username: str,
        steam_id: str,
        discord_id: int,
        guild_id: int
):
    """ Updates kovaaks profile in the database."""
    existing_kovaaks_profile = await get_profile_from_db(
        db, discord_id, guild_id, profile="kovaaks"
    )

    if (not existing_kovaaks_profile or
            not existing_kovaaks_profile["is_active"]):
        raise UsernameDoesNotExist(f"You do not have a kovaaks profile "
                                   f"in the database. Add it using "
                                   f"`/add_kovaaks_profile`")
    await add_kovaaks_account_todb(
        db, kovaaks_id, kovaaks_username, steam_id, steam_username
    )
    sql_statement = f"""
    UPDATE profiles.kovaaks_profiles SET
    kovaaks_id = $1
    WHERE discord_id = $2 AND guild_id = $3;
    """
    await db.execute(sql_statement, kovaaks_id, discord_id, guild_id)


async def setup(bot): pass
async def teardown(bot): pass

#
# if __name__ == "__main__":
#     import asyncio
#     new_loop = asyncio.new_event_loop()
#     new_loop.run_until_complete(calculate_energy())

from datetime import datetime, timezone
from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profiles_from_db, execute_commit)
from services.db.discord_database import update_discord_profile


async def add_aimlabs_username_todb(
        aimlabs_username: str, aimlabs_id: str,
        discord_username: str, discord_id: int) -> tuple:
    """Adds or updates aimlabs profile in db. Returns (True, str) if
    process is a relink of an existing inactive profile, (False, None)
    otherwise.

    :param str aimlabs_username: Aimlabs username
    :param str aimlabs_id: Aimlabs ID
    :param str discord_username: Discord username
    :param int discord_id: Discord ID
    :returns: (bool, str|None)
    """
    await update_discord_profile(discord_username, discord_id)
    existing_aimlabs_profile = await get_profiles_from_db(discord_id,
                                                          "aimlabs")
    relink = False
    if existing_aimlabs_profile:
        if existing_aimlabs_profile[2] == 0:
            relink = True
        else:
            raise UsernameAlreadyExists(f"You already have an aimlabs profile "
                                        f"`{existing_aimlabs_profile[1]}` in the "
                                        f"database. Update it using "
                                        f"`/update_aimlabs_profile`")
    sql_statement = """
    INSERT INTO aimlabs_profiles (discord_id, discord_username, 
                                    aimlabs_username, aimlabs_id, date_updated, 
                                    is_active, last_active)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(discord_id) DO UPDATE SET
        aimlabs_username = excluded.aimlabs_username,
        aimlabs_id = excluded.aimlabs_id,
        date_updated = excluded.date_updated,
        is_active = excluded.is_active,
        last_active = excluded.last_active
    """
    now = datetime.now(timezone.utc).isoformat()
    values = (discord_id,
              discord_username, aimlabs_username, aimlabs_id, now, 1, now)
    await execute_commit(sql_statement, values, "aimlabs_profiles",
                         "UPSERT")
    if relink:
        return True, existing_aimlabs_profile[1]
    return False, None


async def remove_aimlabs_username_fromdb(discord_id: int,
                                         discord_username: str) -> None:
    """Sets aimlabs profile to inactive in database.

    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_aimlabs_profile = await get_profiles_from_db(discord_id,
                                                          "aimlabs")
    if not existing_aimlabs_profile or existing_aimlabs_profile[2] == 0:
        raise UsernameDoesNotExist(f"You do not have an aimlabs profile "
                                   f"in the database. Add it using "
                                   f"`/add_aimlabs_profile`")

    sql_statement = """
    UPDATE aimlabs_profiles SET is_active = 0 WHERE discord_id = ?
    """
    values = (discord_id,)
    await execute_commit(sql_statement, values, "aimlabs_profiles",
                         "UPDATE")


async def update_aimlabs_username_indb(aimlabs_username: str, aimlabs_id: str,
                                       discord_username: str, discord_id: int
                                       ) -> None:
    """ Updates aimlabs username and id in the database.

    :param str aimlabs_username: Aimlabs username
    :param str aimlabs_id: Aimlabs ID
    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_aimlabs_profile = await get_profiles_from_db(discord_id,
                                                          "aimlabs")
    if not existing_aimlabs_profile or existing_aimlabs_profile[2] == 0:
        raise UsernameDoesNotExist(f"You do not have an aimlabs profile "
                                   f"in the database. Add it using "
                                   f"`/add_aimlabs_profile`")
    sql_statement = f"""
    UPDATE aimlabs_profiles SET
    aimlabs_username = ?,
    aimlabs_id = ?,
    is_active = 1
    WHERE discord_id = ?
    """
    values = (aimlabs_username, aimlabs_id, discord_id)
    await execute_commit(sql_statement, values, "aimlabs_profiles",
                         "UPDATE")


async def setup(bot): pass
async def teardown(bot): pass

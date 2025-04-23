from datetime import datetime, timezone

from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profiles_from_db, execute_commit)
from services.db.database import update_discord_profile


async def add_kovaaks_username_todb(
        kovaaks_username: str, kovaaks_id: str, steam_username: str,
        steam_id: str, discord_username: str, discord_id: int) -> tuple:
    """Adds or updates kovaaks profile in db. Returns (True, str) if
    process is a relink of an existing inactive profile. (False, None)
    otherwise.

    :param str kovaaks_username: Kovaaks username
    :param str kovaaks_id: Kovaaks ID
    :param str steam_username: Steam username
    :param str steam_id: Steam ID
    :param str discord_username: Discord username
    :param int discord_id: Discord ID
    :returns: (bool, str|None)
    """
    await update_discord_profile(discord_username, discord_id)
    existing_kovaaks_profile = await get_profiles_from_db(discord_id,
                                                          "kovaaks")
    relink = False
    if existing_kovaaks_profile:
        if existing_kovaaks_profile[4] == 0:
            relink = True
        else:
            raise UsernameAlreadyExists(f"You already have a kovaaks username "
                                        f"`{existing_kovaaks_profile[1]}` in the "
                                        f"database. Update it using "
                                        f"`/update_kovaaks_profile`")
    sql_statement = """
    INSERT INTO kovaaks_profiles (discord_id, discord_username, kovaaks_id, 
    kovaaks_username, steam_id, steam_username, date_updated, is_active, 
    last_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (discord_id) DO UPDATE SET
        kovaaks_username = excluded.kovaaks_username,
        kovaaks_id = excluded.kovaaks_id,
        steam_id = excluded.steam_id,
        steam_username = excluded.steam_username,
        date_updated = excluded.date_updated,
        is_active = excluded.is_active,
        last_active = excluded.last_active
    """
    now = datetime.now(timezone.utc).isoformat()
    values = (discord_id, discord_username, kovaaks_id, kovaaks_username,
              steam_id, steam_username, now, 1, now)
    await execute_commit(sql_statement, values, "kovaaks_profiles",
                         "UPSERT")
    if relink:
        return True, existing_kovaaks_profile[1]
    return False, None


async def remove_kovaaks_username_fromdb(discord_id, discord_username):
    """Sets kovaaks profile to inactive in the database.

    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_kovaaks_profile = await get_profiles_from_db(discord_id,
                                                          "kovaaks")
    if not existing_kovaaks_profile or existing_kovaaks_profile[4] == 0:
        raise UsernameDoesNotExist(f"You do not have a kovaaks profile "
                                   f"in the database. Add it using "
                                   f"`/add_kovaaks_profile`")

    sql_statement = """
    UPDATE kovaaks_profiles SET is_active = 0 WHERE discord_id = ?
    """
    values = (discord_id,)
    await execute_commit(sql_statement, values, "valorant_profiles",
                         "UPDATE")


async def update_kovaaks_username_indb(kovaaks_username: str, kovaaks_id: str,
                                       steam_username: str, steam_id: str,
                                       discord_username: str, discord_id: int
                                       ) -> None:
    """ Updates kovaaks profile in the database.

    :param str kovaaks_username: Kovaaks username
    :param str kovaaks_id: Kovaaks ID
    :param str steam_username: Steam username
    :param str steam_id: Steam ID
    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_kovaaks_profile = await get_profiles_from_db(discord_id,
                                                          "kovaaks")
    if not existing_kovaaks_profile or existing_kovaaks_profile[4] == 0:
        raise UsernameDoesNotExist(f"You do not have a kovaaks profile "
                                   f"in the database. Add it using "
                                   f"`/add_kovaaks_profile`")
    sql_statement = f"""
    UPDATE kovaaks_profiles SET
    kovaaks_username = ?,
    kovaaks_id = ?,
    steam_username = ?,
    steam_id = ?,
    is_active = 1
    WHERE discord_id = ?
    """
    values = (kovaaks_username, kovaaks_id, steam_username, steam_id,
              discord_id)
    await execute_commit(sql_statement, values, "kovaaks_profiles",
                         "UPDATE")


async def setup(bot): pass
async def teardown(bot): pass

#
# if __name__ == "__main__":
#     import asyncio
#     new_loop = asyncio.new_event_loop()
#     new_loop.run_until_complete(calculate_energy())

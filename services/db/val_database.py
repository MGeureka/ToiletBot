from datetime import datetime, timezone
from utils.errors import UsernameAlreadyExists, UsernameDoesNotExist
from utils.database_helper import (get_profiles_from_db, execute_commit)
from services.db.database import update_discord_profile


async def add_valorant_username_todb(valorant_username: str, valorant_tag: str,
                                     valorant_id: str, discord_username: str,
                                     discord_id: int, region: str) -> tuple:
    """Adds or updates aimlabs profile in db. Returns (True, str) if process
    is a relink of an existing inactive profile, (False, None) otherwise.

    :param str valorant_username: Valorant username
    :param str valorant_tag: Valorant tag
    :param str valorant_id: Valorant ID
    :param str discord_username: Discord username
    :param int discord_id: Discord ID
    :param str region: Region
    :returns: (bool, str|None)
    """
    await update_discord_profile(discord_username, discord_id)
    existing_valorant_profile = await get_profiles_from_db(discord_id,
                                                           "val")
    relink = False
    if existing_valorant_profile:
        if existing_valorant_profile[3] == 0:
            relink = True
        else:
            raise UsernameAlreadyExists(f"You already have a valorant profile "
                                        f"`{existing_valorant_profile[1]}#"
                                        f"{existing_valorant_profile[2]}` in "
                                        f"the database. Update it using "
                                        f"`/update_valorant_profile`")
    sql_statement = """
    INSERT INTO valorant_profiles (discord_id, discord_username, valorant_id, 
                                    valorant_username, valorant_tag, region, 
                                    date_updated, is_active, last_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (discord_id) DO UPDATE SET
        valorant_id = excluded.valorant_id,
        valorant_username = excluded.valorant_username,
        valorant_tag = excluded.valorant_tag,
        region = excluded.region,
        date_updated = excluded.date_updated,
        is_active = excluded.is_active,
        last_active = excluded.last_active
    """
    now = datetime.now(timezone.utc).isoformat()
    values = (discord_id, discord_username, valorant_id,
              valorant_username, valorant_tag, region, now, 1, now)
    await execute_commit(sql_statement, values, "valorant_profiles",
                         "UPSERT")
    if relink:
        return True, (f"{existing_valorant_profile[1]}#"
                      f"{existing_valorant_profile[2]}")
    return False, None


async def remove_valorant_username_fromdb(discord_id, discord_username):
    """Sets valorant profile to inactive in database.

    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_valorant_profile = await get_profiles_from_db(discord_id,
                                                           "val")
    if not existing_valorant_profile or existing_valorant_profile[3] == 0:
        raise UsernameDoesNotExist(f"You do not have a valorant profile "
                                   f"in the database. Add it using "
                                   f"`/add_valorant_profile`")

    sql_statement = """
    UPDATE valorant_profiles SET is_active = 0 WHERE discord_id = ?
    """
    values = (discord_id,)
    await execute_commit(sql_statement, values, "valorant_profiles",
                         "UPDATE")


async def update_valorant_username_indb(valorant_username: str,
                                        valorant_id: str, valorant_tag: str,
                                        discord_username: str, discord_id: int
                                        ) -> None:
    """ Updates valorant username, id, and tag in the database.

    :param str valorant_username: Valorant username
    :param str valorant_tag: Valorant tag
    :param str valorant_id: Valorant ID
    :param int discord_id: Discord ID
    :param str discord_username: Discord username
    :return: None
    """
    await update_discord_profile(discord_username, discord_id)
    existing_valorant_profile = await get_profiles_from_db(discord_id,
                                                           "val")
    if not existing_valorant_profile or existing_valorant_profile[3] == 0:
        raise UsernameDoesNotExist(f"You do not have a kovaaks profile "
                                   f"in the database. Add it using "
                                   f"`/add_valorant_profile`")
    sql_statement = f"""
    UPDATE aimlabs_profiles SET
    valorant_username = ?,
    valorant_tag = ?,
    valorant_id = ?,
    is_active = 1
    WHERE discord_id = ?
    """
    values = (valorant_username, valorant_tag, valorant_id, discord_id)
    await execute_commit(sql_statement, values, "valorant_profiles",
                         "UPDATE")


async def setup(bot): pass
async def teardown(bot): pass

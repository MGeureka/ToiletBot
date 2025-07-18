from datetime import datetime, timezone
from utils.database_helper import execute_commit


async def update_discord_profile(discord_username:str, discord_id: int) -> bool:
    """Updates discord_profiles table with discord_username, discord_id
    and current time (date_added). If profile doesn't exist, it will be created

    :param str discord_username: Discord username
    :param int discord_id: Discord id
    :return: True if update was successful, False otherwise
    """
    sql_statement = """
    INSERT INTO discord_profiles (discord_id, discord_username, date_updated)
    VALUES (?, ?, ?)
    ON CONFLICT(discord_id) DO UPDATE SET 
        discord_username = excluded.discord_username,
        date_updated = excluded.date_updated;
    """
    now = datetime.now(timezone.utc).isoformat()
    values = (discord_id, discord_username, now)
    await execute_commit(sql_statement, values, "discord_profiles",
                         "UPSERT")


async def setup(bot): pass
async def teardown(bot): pass

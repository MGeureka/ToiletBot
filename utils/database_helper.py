from settings import DB_PATH
import aiosqlite
import uuid, aiofiles, json
from utils.log import log_transaction
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from settings import (S5_VOLTAIC_BENCHMARKS_CONFIG,
                      S5_VOLTAIC_RANKS,
                      S5_VOLTAIC_RANKS_COMPLETE,
                      S1_VOLTAIC_VAL_BENCHMARKS_CONFIG,
                      S1_VAL_VOLTAIC_RANKS,
                      S1_VAL_VOLTAIC_RANKS_COMPLETE)
from utils.energy_calculation import tier_energy


def get_datetime(datetime_str: str):
    return datetime.fromisoformat(datetime_str)


async def execute_commit(query: str, values: tuple, table_name: str,
                         operation: str) -> None:
    transaction_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        try:
            async with db.execute(query, values) as cur:
                affected_rows = cur.rowcount if hasattr(cur, 'rowcount') else 0
                await db.commit()
                await log_transaction(
                    db=db,
                    transaction_id=transaction_id,
                    operation=operation,
                    table_name=table_name,
                    query=query,
                    parameters=values,
                    status="SUCCESS",
                    error_message=None,
                    affected_rows=affected_rows
                )

        except Exception as e:
            await db.rollback()
            await log_transaction(
                db=db,
                transaction_id=transaction_id,
                operation=operation,
                table_name=table_name,
                query=query,
                parameters=values,
                status="ERROR",
                error_message=str(e),
                affected_rows=0
            )

            raise e


async def executemany_commit(query: str, values: list[tuple], table_name: str,
                         operation: str) -> None:
    transaction_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        try:
            async with db.executemany(query, values) as cur:
                affected_rows = cur.rowcount if hasattr(cur, 'rowcount') else 0
                await db.commit()
                await log_transaction(
                    db=db,
                    transaction_id=transaction_id,
                    operation=operation,
                    table_name=table_name,
                    query=query,
                    parameters=values,
                    status="SUCCESS",
                    error_message=None,
                    affected_rows=affected_rows
                )

        except Exception as e:
            await db.rollback()
            await log_transaction(
                db=db,
                transaction_id=transaction_id,
                operation=operation,
                table_name=table_name,
                query=query,
                parameters=values,
                status="ERROR",
                error_message=str(e),
                affected_rows=0
            )

            raise e


async def execute_fetch(query: str, values: tuple, table_name: str) -> list:
    transaction_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        try:
            async with db.execute(query, values) as cur:
                results = await cur.fetchall()

                await log_transaction(
                    db=db,
                    transaction_id=transaction_id,
                    operation="SELECT",
                    table_name=table_name,
                    query=query,
                    parameters=values,
                    status="SUCCESS",
                    error_message=None,
                    affected_rows=len(results)
                )
                return results
        except Exception as e:
            await log_transaction(
                db=db,
                transaction_id=transaction_id,
                operation="SELECT",
                table_name=table_name,
                query=query,
                parameters=values,
                status="ERROR",
                error_message=str(e),
                affected_rows=0
            )
            raise e


async def check_profile_indb(discord_id: str, profile: str,
                             active_status: int) -> bool:
    """Returns True if the username is in the database. False otherwise.

    discord_id: the discord id
    profile: The profile name, gives table to check for profile
    """
    match profile:
        case "discord":
            sql_statement = """SELECT id FROM 
                        discord_profiles WHERE discord_id = ?"""
            table_name = "discord_profiles"
        case "val":
            sql_statement = f"""SELECT id FROM valorant_profiles WHERE 
                            discord_id = ? AND is_active = {active_status}"""
            table_name = "valorant_profiles"
        case "aimlabs":
            sql_statement = f"""SELECT id FROM aimlabs_profiles WHERE 
                                discord_id = ? AND is_active = {active_status}"""
            table_name = "aimlabs_profiles"
        case "kovaaks":
            raise NotImplementedError
        case _:
            sql_statement = ""
            table_name = ""

    values = (discord_id,)
    data = await execute_fetch(sql_statement, values, table_name=table_name)
    return True if data else False


async def get_profiles_from_db(discord_id: int, profile: str) -> tuple:
    """Returns a tuple of the profile and activity status

    discord_id: The discord id
    profile: The profile name, gives table to check for profile
    """
    match profile:
        case "discord":
            sql_statement = f"""SELECT discord_username 
                                FROM discord_profiles WHERE discord_id = ?"""
            table_name = "discord_profiles"
        case "val":
            sql_statement = f"""SELECT valorant_id, valorant_username, 
                                valorant_tag, is_active, region FROM 
                                valorant_profiles WHERE discord_id = ?"""
            table_name = "valorant_profiles"
        case "aimlabs":
            sql_statement = f"""SELECT aimlabs_id, aimlabs_username, is_active
                                FROM aimlabs_profiles WHERE discord_id = ?"""
            table_name = "aimlabs_profiles"
        case "kovaaks":
            sql_statement = f"""SELECT kovaaks_id, kovaaks_username, steam_id, 
                                steam_username, is_active
                                FROM kovaaks_profiles WHERE discord_id = ?"""
            table_name = "kovaaks_profiles"
        case _:
            sql_statement = ""
            table_name = ""
    values = (discord_id,)
    profile = await execute_fetch(sql_statement, values, table_name)
    return profile[0] if profile else None


async def get_date_updated(discord_id: int, table_name: str):
    sql_statement = f"""
        SELECT date_updated FROM {table_name} WHERE discord_id = ?
        """
    values = (discord_id,)
    data = await execute_fetch(sql_statement, values, table_name)
    return get_datetime(data[0][0]) if data else None


async def get_valorant_profiles():
    sql_statement = """
        SELECT discord_id, discord_username, valorant_id, valorant_username, 
        valorant_tag, region FROM valorant_profiles WHERE is_active = 1
        """

    data = await execute_fetch(sql_statement, tuple(),
                               "valorant_profiles")
    return data


async def get_discord_profiles():
    sql_statement = """
        SELECT discord_id, discord_username FROM discord_profiles
        """

    data = await execute_fetch(sql_statement, tuple(),
                               "discord_profiles")
    return data


async def get_leaderboard_message_state():
    sql_statement = """
    SELECT message_id FROM leaderboard_message WHERE id = 1
    """
    data = await execute_fetch(sql_statement, tuple(),
                               table_name="leaderboard_message")
    return int(data[0][0]) if data else None


async def update_leaderboard_message_state(message_id: int):
    sql_statement = """
    INSERT INTO leaderboard_message (id, message_id)
    VALUES(?, ?)
    ON CONFLICT (id) DO UPDATE SET
        message_id = excluded.message_id
    """
    values = (1, message_id)
    await execute_commit(sql_statement, values,
                         table_name="leaderboard_message", operation="UPSERT")


async def get_kovaaks_profiles():
    sql_statement = """
        SELECT discord_id, discord_username, kovaaks_id, kovaaks_username, 
        steam_id, steam_username FROM kovaaks_profiles WHERE is_active = 1
        """
    data = await execute_fetch(sql_statement, tuple(),
                               "kovaaks_profiles")
    return data


async def get_aimlabs_profiles():
    sql_statement = """
        SELECT discord_id, discord_username, aimlabs_id, aimlabs_username
        FROM aimlabs_profiles WHERE is_active = 1
        """
    data = await execute_fetch(sql_statement, tuple(),
                               "aimlabs_profiles")
    return data


async def add_scores_to_config(config, scores):
    for scenario, score in zip(config, scores):
        scenario["score"] = score
    return config


async def calculate_energy(novice, intermediate, advanced, bench_type: str):
    if bench_type == "val":
        path = S1_VOLTAIC_VAL_BENCHMARKS_CONFIG
        ranks_complete = S1_VAL_VOLTAIC_RANKS_COMPLETE
        ranks = S1_VAL_VOLTAIC_RANKS
    else:
        path = S5_VOLTAIC_BENCHMARKS_CONFIG
        ranks_complete = S5_VOLTAIC_RANKS_COMPLETE
        ranks = S5_VOLTAIC_RANKS
    async with aiofiles.open(
            path, "r", encoding="utf-8"
    ) as f:
        content = await f.read()
        config = json.loads(content)
    scores = [novice, intermediate, advanced]
    novice_scores = await add_scores_to_config(
        config['novice_scenarios'],novice
    )
    intermediate_scores = await add_scores_to_config(
        config['intermediate_scenarios'], intermediate
    )
    advanced_scores = await add_scores_to_config(
        config['advanced_scenarios'], advanced
    )
    tiers = config['tier_energies']
    categories = config['categories']
    novice_energy = tier_energy(tiers, 0,
                                novice_scores,
                                categories)
    intermediate_energy = tier_energy(tiers, 1,
                                      intermediate_scores,
                                      categories)
    advanced_energy = tier_energy(tiers, 2,
                                  advanced_scores,
                                  categories)
    energies = [novice_energy, intermediate_energy, advanced_energy]
    energy = max(energies)
    max_index = energies.index(energy)
    rounded_energy = min(((energy // 100) * 100), 1200)
    complete = True if all(score >= rounded_energy
                           for score in scores[max_index]) else False
    print(f"{energy=}")
    print(f"{rounded_energy=}")
    print(f"{scores[max_index]=}")
    print(f"{complete=}")
    if complete:
        return (ranks_complete[rounded_energy]['name'],
                ranks_complete[rounded_energy]['id'], energy)
    return (ranks[rounded_energy]['name'],
            ranks[rounded_energy]['id'], energy)


def get_last_monday_12am_est() -> datetime:
    now_utc = datetime.now(timezone.utc)
    now_est = now_utc.astimezone(ZoneInfo("America/New_York"))
    days_since_monday = now_est.weekday()  # Monday is 0
    last_monday = now_est - timedelta(days=days_since_monday)
    last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return last_monday.astimezone(timezone.utc)


async def setup(bot): pass
async def teardown(bot): pass

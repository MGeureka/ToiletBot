from datetime import datetime, timezone
import asyncio, json
from utils.database_helper import (get_valorant_profiles, executemany_commit,
                                   get_date_updated, get_datetime,
                                   execute_fetch, get_kovaaks_profiles,
                                   calculate_energy, get_aimlabs_profiles,
                                   get_last_monday_12am_est)
from services.api.val_api import fetch_rating, fetch_dms
from services.api.kovaaks_api import (get_s5_novice_benchmark_scores,
                                      get_s5_intermediate_benchmark_scores,
                                      get_s5_advance_benchmark_scores)
from services.api.aimlabs_api import fetch_s1_val_benchmarks


async def update_valorant_rank_leaderboard():
    sql_statement = """
        INSERT INTO valorant_rank_leaderboard (
            discord_id, discord_username, valorant_id, 
            valorant_username, valorant_tag, current_rank, 
            current_rank_id, current_rr, peak_rank, peak_rank_id, date_updated
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (discord_id) DO UPDATE SET
            current_rank = excluded.current_rank,
            current_rank_id = excluded.current_rank_id,
            current_rr = excluded.current_rr,
            peak_rank = excluded.peak_rank,
            peak_rank_id = excluded.peak_rank_id,
            date_updated = excluded.date_updated
    """
    valorant_profiles = await get_valorant_profiles()
    async def process_profile(profile):
        (discord_id, discord_username, valorant_id, valorant_username,
         valorant_tag, region) = profile

        ratings = await fetch_rating(valorant_id, region)
        (current_rank, current_rank_id, current_rr, peak_rank,
         peak_rank_id) = ratings

        return (discord_id, discord_username, valorant_id, valorant_username,
                valorant_tag, current_rank, current_rank_id, current_rr,
                peak_rank, peak_rank_id, datetime.now(timezone.utc).isoformat())

    all_values = await asyncio.gather(*[process_profile(profile) for profile in valorant_profiles])

    await executemany_commit(sql_statement, all_values,
                             "valorant_rank_leaderboard",
                             "UPSERT")


async def update_valorant_dm_leaderboard():
    sql_statement = """
        INSERT INTO valorant_dm_leaderboard (
            discord_id, discord_username, valorant_id, 
            valorant_username, valorant_tag, date_updated, dm, dm_count
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (discord_id) DO UPDATE SET
            dm = excluded.dm,
            dm_count = excluded.dm_count,
            date_updated = excluded.date_updated
    """
    valorant_profiles = await get_valorant_profiles()

    async def process_profile(profile):
        (discord_id, discord_username, valorant_id, valorant_username,
         valorant_tag, region) = profile
        dm_json = await execute_fetch(f"SELECT dm from "
                                      f"valorant_dm_leaderboard "
                                      f"WHERE discord_id = ?",
                                      (discord_id,),
                                      "valorant_dm_leaderboard")
        print(dm_json)
        dms = json.loads(dm_json[0][0]) if dm_json[0][0] else []
        lower_bound_dt = get_last_monday_12am_est()
        dms = [match for match in dms if get_datetime(match['date']) >= lower_bound_dt]
        data_dm, data_tdm = \
            await asyncio.gather(
                fetch_dms(valorant_id, region,"deathmatch"),
                fetch_dms(valorant_id,region,"teamdeathmatch")
            )

        new_matches = [{"id": match['metadata']['match_id'],
                        "date": match['metadata']['started_at']}
                       for match in (data_dm['data'] + data_tdm['data'])
                       if get_datetime(match['metadata']['started_at']) >= lower_bound_dt]

        existing_ids = {match["id"] for match in dms}
        for match in new_matches:
            if match["id"] not in existing_ids:
                dms.append(match)

        dm_json_str = json.dumps(dms)
        dm_count = len(dms)
        return (discord_id, discord_username, valorant_id, valorant_username,
                valorant_tag, datetime.now(timezone.utc).isoformat(),
                dm_json_str, dm_count)

    all_values = await asyncio.gather(*[process_profile(profile) for profile in valorant_profiles])
    await executemany_commit(sql_statement, all_values,
                             "valorant_dm_leaderboard",
                             "UPSERT")


async def update_voltaic_s5_leaderboard():
    sql_statement = """
        INSERT INTO voltaic_S5_benchmarks_leaderboard (
            discord_id, discord_username, kovaaks_id, kovaaks_username, 
            steam_id, steam_username, current_rank, current_rank_id, 
            current_rank_rating, date_updated
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (discord_id) DO UPDATE SET
            current_rank = excluded.current_rank,
            current_rank_id = excluded.current_rank_id,
            current_rank_rating = excluded.current_rank_rating,
            date_updated = excluded.date_updated
    """
    kovaaks_profiles = await get_kovaaks_profiles()

    async def process_profile(profile):
        now = datetime.now(timezone.utc).isoformat()
        (discord_id, discord_username, kovaaks_id, kovaaks_username,
         steam_id, steam_username) = profile
        novice_scores, intermediate_scores, advance_scores = \
            await asyncio.gather(
                get_s5_novice_benchmark_scores(steam_id),
                get_s5_intermediate_benchmark_scores(steam_id),
                get_s5_advance_benchmark_scores(steam_id)
            )
        current_rank, current_rank_id, current_rank_rating = \
            await calculate_energy(novice_scores,
                                   intermediate_scores,
                                   advance_scores,
                                   "voltaic")
        return (discord_id, discord_username, kovaaks_id, kovaaks_username,
                steam_id, steam_username, current_rank, current_rank_id,
                current_rank_rating, now)

    all_values = await asyncio.gather(*[process_profile(profile)
                                        for profile in kovaaks_profiles])
    await executemany_commit(sql_statement, all_values,
                             "voltaic_S5_benchmarks_leaderboard",
                             "UPSERT")


async def update_voltaic_val_s1_leaderboard():
    sql_statement = """
        INSERT INTO voltaic_S1_valorant_benchmarks_leaderboard (
            discord_id, discord_username, aimlabs_id, aimlabs_username, 
            current_rank, current_rank_id, current_rank_rating, date_updated
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (discord_id) DO UPDATE SET
            current_rank = excluded.current_rank,
            current_rank_id = excluded.current_rank_id,
            current_rank_rating = excluded.current_rank_rating,
            date_updated = excluded.date_updated
    """
    aimlabs_profiles = await get_aimlabs_profiles()

    async def process_profile(profile):
        now = datetime.now(timezone.utc).isoformat()
        (discord_id, discord_username, aimlabs_id, aimlabs_username) = profile
        novice_scores, intermediate_scores, advance_scores = \
            await fetch_s1_val_benchmarks(aimlabs_id)
        current_rank, current_rank_id, current_rank_rating = \
            await calculate_energy(novice_scores,
                                   intermediate_scores,
                                   advance_scores,
                                   "val")
        return (discord_id, discord_username, aimlabs_id, aimlabs_username,
                current_rank, current_rank_id, current_rank_rating, now)

    all_values = await asyncio.gather(*[process_profile(profile)
                                        for profile in aimlabs_profiles])
    await executemany_commit(sql_statement, all_values,
                             "voltaic_S5_benchmarks_leaderboard",
                             "UPSERT")


async def get_dm_matches_fromdb():
    valorant_profiles = await get_valorant_profiles()
    profile_ids = [profile[0] for profile in valorant_profiles]
    sql_statement = f"""
        SELECT dm
        FROM valorant_dm_leaderboard WHERE discord_id in 
        ({', '.join('?' for _ in profile_ids)})
    """
    data = await execute_fetch(sql_statement, tuple(profile_ids),
                               "valorant_dm_leaderboard")
    return [i[0] for i in data]


async def get_valorant_rank_leaderboard_data():
    valorant_profiles = await get_valorant_profiles()
    profile_ids = [profile[0] for profile in valorant_profiles]
    sql_statement = f"""
        SELECT discord_id, discord_username, current_rank, current_rank_id, 
        current_rr FROM valorant_rank_leaderboard WHERE discord_id in 
        ({', '.join('?' for _ in profile_ids)}) ORDER BY current_rank_id DESC
    """
    data = await execute_fetch(sql_statement, tuple(profile_ids),
                               "valorant_rank_leaderboard")
    sorted_data = sorted(data, key=lambda x: (int(x[3]), int(x[4])), reverse=True)
    return sorted_data


async def get_valorant_dm_leaderboard_data():
    valorant_profiles = await get_valorant_profiles()
    profile_ids = [profile[0] for profile in valorant_profiles]
    sql_statement = f"""
        SELECT discord_id, discord_username, dm_count
        FROM valorant_dm_leaderboard WHERE discord_id in 
        ({', '.join('?' for _ in profile_ids)})
    """
    data = await execute_fetch(sql_statement, tuple(profile_ids),
                               "valorant_dm_leaderboard")

    sorted_data = sorted(data, key=lambda x: int(x[2]), reverse=True)
    return sorted_data


async def get_voltaic_s5_benchmarks_leaderboard_data():
    kovaaks_profiles = await get_kovaaks_profiles()
    profile_ids = [profile[0] for profile in kovaaks_profiles]
    sql_statement = f"""
        SELECT discord_id, discord_username, current_rank, current_rank_id, 
        current_rank_rating
        FROM voltaic_S5_benchmarks_leaderboard WHERE discord_id in 
        ({', '.join('?' for _ in profile_ids)}) 
        ORDER BY current_rank_rating DESC
    """
    data = await execute_fetch(sql_statement, tuple(profile_ids),
                               "voltaic_S5_benchmarks_leaderboard")
    sorted_data = sorted(data, key=lambda x: int(x[4]), reverse=True)
    return sorted_data


async def get_voltaic_s1_val_benchmarks_leaderboard_data():
    aimlabs_profiles = await get_aimlabs_profiles()
    profile_ids = [profile[0] for profile in aimlabs_profiles]
    sql_statement = f"""
        SELECT discord_id, discord_username, current_rank, current_rank_id, 
        current_rank_rating
        FROM voltaic_S1_valorant_benchmarks_leaderboard WHERE discord_id in 
        ({', '.join('?' for _ in profile_ids)}) 
        ORDER BY current_rank_rating DESC
    """
    data = await execute_fetch(
        sql_statement,
        tuple(profile_ids),
        "voltaic_S1_valorant_benchmarks_leaderboard")
    sorted_data = sorted(data, key=lambda x: int(x[4]), reverse=True)
    return sorted_data


# if __name__ == "__main__":
#     import asyncio
#     from services.api.val_api import setup, teardown
#     new_loop = asyncio.new_event_loop()
#     new_loop.run_until_complete(setup(None))
#     data = new_loop.run_until_complete(update_valorant_dm_leaderboard())
#     new_loop.run_until_complete(teardown(None))
#     # print(data)

async def setup(bot): pass
async def teardown(bot): pass

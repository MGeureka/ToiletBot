from functools import partial
import aiohttp
from typing import Any

from utils.api_helper import update_benchmark_scenario_list
from utils.errors import (ErrorFetchingData, ProfileDoesntExist)
from utils.api_helper import AsyncRateLimiter
from utils.log import logger, api_logger
from settings import S5_VOLTAIC_BENCHMARKS_CONFIG

SCENARIO_LIST_URL = \
    "https://beta.voltaic.gg/api/v1/kovaaks/benchmarks/kovaaks_s5"

kovaaks_api_rate_limiter = AsyncRateLimiter("kovaaks")
kovaaks_api_session: aiohttp.ClientSession | None = None
update_config: Any = None


async def get_session():
    global kovaaks_api_session
    if kovaaks_api_session is None or kovaaks_api_session.closed:
        kovaaks_api_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
    api_logger.info("Connection established to kovaaks API")
    logger.info(f"Connection established to kovaaks API")
    return kovaaks_api_session


async def close_session():
    global kovaaks_api_session
    if kovaaks_api_session and not kovaaks_api_session.closed:
        api_logger.info("Connection closed to kovaaks API")
        logger.info(f"Connection closed to kovaaks API")
        await kovaaks_api_session.close()
        kovaaks_api_session = None


@kovaaks_api_rate_limiter
async def get_s5_novice_benchmark_scores(steam_id: str):
    """Gets S5 benchmark scores """
    await update_config()
    try:
        async with kovaaks_api_session.get(
            f"https://kovaaks.com/webapp-backend/benchmarks/"
            f"player-progress-rank-benchmark?"
            f"benchmarkId=432&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


@kovaaks_api_rate_limiter
async def get_s5_intermediate_benchmark_scores(steam_id: str):
    """Gets S5 benchmark scores """
    await update_config()
    try:
        async with kovaaks_api_session.get(
                f"https://kovaaks.com/webapp-backend/benchmarks/"
                f"player-progress-rank-benchmark?"
                f"benchmarkId=431&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


@kovaaks_api_rate_limiter
async def get_s5_advance_benchmark_scores(steam_id: str):
    """Gets S5 benchmark scores """
    await update_config()
    try:
        async with kovaaks_api_session.get(
                f"https://kovaaks.com/webapp-backend/benchmarks/"
                f"player-progress-rank-benchmark?"
                f"benchmarkId=427&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


@kovaaks_api_rate_limiter
async def check_kovaaks_username(username: str):
    """Checks if kovaaks username is valid, returns playerId and steamId"""
    try:
        async with kovaaks_api_session.get(
            f"https://kovaaks.com/webapp-backend/user/profile/"
            f"by-username?username={username}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()
            return ((data['playerId'], data['steamId'],
                     data['steamAccountName']), headers)
    except Exception as e:
        if response:
            if response.status == 409:
                raise ProfileDoesntExist(f"Kovaaks profile `{username}` "
                                         f"doesn't exist.")
        raise ErrorFetchingData(f"Error while checking "
                                f"kovaaks username `{username}`. "
                                f"Either the username doesn't exist or "
                                f"it's an API error"
                                f"\n\nStatus code: {response.status}. {str(e)}")


@kovaaks_api_rate_limiter
async def get_scenario_id(scenario_name: str):
    """Queries for scenario details"""
    try:
        async with kovaaks_api_session.get(
            f"https://kovaaks.com/webapp-backend/scenario/popular?"
            f"page=0&max=1&scenarioNameSearch={scenario_name}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()

            return (data['scenarioId'], headers)
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching scenario data for "
                                f"scenario name `{scenario_name}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def setup(bot):
    global kovaaks_api_session
    global update_config
    kovaaks_api_session = await get_session()
    update_config = partial(update_benchmark_scenario_list,
                            url=SCENARIO_LIST_URL,
                            path=S5_VOLTAIC_BENCHMARKS_CONFIG,
                            session=kovaaks_api_session)
    await update_config()


async def teardown(bot):
    await close_session()


# if __name__ == "__main__":
#     import asyncio
#     new_loop = asyncio.new_event_loop()
#     new_loop.run_until_complete(setup(None))
#     new_loop.run_until_complete(get_s5_advance_benchmark_scores("76561198839916720"))

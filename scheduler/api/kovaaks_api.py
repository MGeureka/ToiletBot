import aiohttp
import asyncio

from errors import (ErrorFetchingData, ProfileDoesntExist)

SCENARIO_LIST_URL = \
    "https://beta.voltaic.gg/api/v1/kovaaks/benchmarks/kovaaks_s5"


async def get_s5_novice_benchmark_scores(session: aiohttp.ClientSession,
                                         steam_id: str):
    """Gets S5 benchmark scores """
    try:
        async with session.get(
            f"https://kovaaks.com/webapp-backend/benchmarks/"
            f"player-progress-rank-benchmark?"
            f"benchmarkId=432&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def get_s5_intermediate_benchmark_scores(session: aiohttp.ClientSession,
                                               steam_id: str):
    """Gets S5 benchmark scores """
    try:
        async with session.get(
                f"https://kovaaks.com/webapp-backend/benchmarks/"
                f"player-progress-rank-benchmark?"
                f"benchmarkId=431&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def get_s5_advance_benchmark_scores(session: aiohttp.ClientSession,
                                          steam_id: str):
    """Gets S5 benchmark scores """
    try:
        async with session.get(
                f"https://kovaaks.com/webapp-backend/benchmarks/"
                f"player-progress-rank-benchmark?"
                f"benchmarkId=427&steamId={steam_id}"
        ) as response:
            response.raise_for_status()
            data = await response.json()
            scores = []
            for category in data["categories"]:
                for scenario in data["categories"][category]["scenarios"]:
                    score = data["categories"][category]["scenarios"][scenario]["score"]
                    scores.append(score//100)
            return scores
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching leaderboard data for "
                                f"steam ID `{steam_id}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def check_kovaaks_username(session: aiohttp.ClientSession, username: str):
    """Checks if kovaaks username is valid, returns playerId and steamId"""
    try:
        async with session.get(
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


async def get_scenario_id(session: aiohttp.ClientSession, scenario_name: str):
    """Queries for scenario details"""
    try:
        async with session.get(
            f"https://kovaaks.com/webapp-backend/scenario/popular?"
            f"page=0&max=1&scenarioNameSearch={scenario_name}"
        ) as response:
            response.raise_for_status()
            headers = response.headers
            data = await response.json()

            return data['scenarioId'], headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching scenario data for "
                                f"scenario name `{scenario_name}`. "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def get_voltaic_s5_scores(session: aiohttp.ClientSession, steam_id: str):
    """Gets S5 Voltaic benchmark scores for a specific scenario"""
    nov, intern, adv = await asyncio.gather(
        get_s5_novice_benchmark_scores(session, steam_id),
        get_s5_intermediate_benchmark_scores(session, steam_id),
        get_s5_advance_benchmark_scores(session, steam_id)
    )
    return nov, intern, adv

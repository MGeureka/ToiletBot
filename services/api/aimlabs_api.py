import json
import aiohttp, aiofiles
from functools import partial
from typing import Any

from services.api.kovaaks_api import update_benchmark_scenario_list
from settings import S1_VOLTAIC_VAL_BENCHMARKS_CONFIG
from utils.errors import ErrorFetchingData, ProfileDoesntExist
from utils.api_helper import AsyncRateLimiter
from utils.log import logger, api_logger

# API Endpoint
API_ENDPOINT = "https://api.aimlab.gg/graphql"
aimlabs_api_rate_limiter = AsyncRateLimiter("aimlabs")

SCENARIO_LIST_URL = \
    "https://beta.voltaic.gg/api/v1/aimlabs/benchmarks/valorant_s1"
aimlabs_api_session: aiohttp.ClientSession | None = None
update_config: Any = None

GET_LEADERBOARD_INPUT = """
query LeaderboardEntry($leaderboardInput: LeaderboardInput!) {
    aimlab {
        leaderboard(input: $leaderboardInput) {
            leaderboardEntries {
                data
                play {
                    gridshieldStatus
                }
            }
        }
    }
}
"""


# GraphQL Queries
GET_USER_INFO = """
query GetProfile($username: String) {
    aimlabProfile(username: $username) {
        username
            user {
                id
            }
    }
}
"""


async def get_session():
    global aimlabs_api_session
    if aimlabs_api_session is None or aimlabs_api_session.closed:
        aimlabs_api_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
        api_logger.info("Connection established to aimlabs API")
        logger.info(f"Connection established to aimlabs API")
    return aimlabs_api_session


async def close_session():
    global aimlabs_api_session
    if aimlabs_api_session and not aimlabs_api_session.closed:
        api_logger.info("Connection closed to aimlabs API")
        logger.info(f"Connection closed to aimlabs API")
        await aimlabs_api_session.close()
        aimlabs_api_session = None


@aimlabs_api_rate_limiter
async def fetch_leaderboard_entries(aimlabs_id: str, task_id: str,
                                    weapon_id: str):
    try:
        variables = {
            "leaderboardInput": {
                "clientId": "aimlab",
                "taskId": task_id,
                "userId": aimlabs_id,
                "taskMode": 42,
                "inputDevice": "MOUSE",
                "source": "cache",
                "weaponId": weapon_id
            }
        }
        async with aimlabs_api_session.post(
            url=API_ENDPOINT,
            json={"query": GET_LEADERBOARD_INPUT, "variables": variables},
        ) as response:
            headers = response.headers
            response.raise_for_status()
            data = await response.json()
            if not data['data']['aimlab']['leaderboard']['leaderboardEntries']:
                return 0, headers
            if data['data']['aimlab']['leaderboard']['leaderboardEntries']\
                [0]['play']['gridshieldStatus'] == "APPROVED":
                return (data['data']['aimlab']['leaderboard']\
                            ['leaderboardEntries'][0]['data']['score'],
                        headers)
            return 0, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error fetching task stats from Aimlabs API"
                                f"\n{str(e)}")


async def fetch_s1_val_benchmarks(aimlabs_id: str):
    await update_config()
    async with aiofiles.open(S1_VOLTAIC_VAL_BENCHMARKS_CONFIG) as f:
        content = await f.read()
        config = json.loads(content)
    async def process_scenario(scenario):
        score = await fetch_leaderboard_entries(
            aimlabs_id=aimlabs_id,
            task_id=scenario['task_id'],
            weapon_id=scenario['weapon_id']
        )
        return score
    novice, intermediate, advanced = await asyncio.gather(
        asyncio.gather(*[process_scenario(scenario) for scenario in config['novice_scenarios']]),
        asyncio.gather(*[process_scenario(scenario) for scenario in config['intermediate_scenarios']]),
        asyncio.gather(*[process_scenario(scenario) for scenario in config['advanced_scenarios']]),
    )
    return novice, intermediate, advanced


@aimlabs_api_rate_limiter
async def check_aimlabs_username(username:str):
    """Queries aimlabs api and checks if username exists."""
    try:
        async with aimlabs_api_session.post(
        url=API_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json={"query": GET_USER_INFO, "variables": {"username": username}}
        ) as response:
            headers = response.headers
            response.raise_for_status()
            data = await response.json()

            if 'data' not in data or data['data']['aimlabProfile'] is None:
                raise ProfileDoesntExist(f"Profile with username "
                                         f"`{username}` doesn't exist",
                                         headers=headers,
                                         username=username)
            return data['data']['aimlabProfile']['user']['id'], headers

    except aiohttp.ClientResponseError as e:
        raise ErrorFetchingData(f"API returned status "
                                f"`{response.status}` Reason: {e.reason}",
                                headers=headers,
                                username=username)
    except aiohttp.ClientError as e:
        raise ErrorFetchingData(f"AIOHTTP error occurred: {str(e)}",
                                headers=headers, username=username)
    except Exception as error:
        raise error


async def setup(bot):
    global aimlabs_api_session
    global update_config
    aimlabs_api_session = await get_session()
    update_config = partial(update_benchmark_scenario_list,
                            url=SCENARIO_LIST_URL,
                            path=S1_VOLTAIC_VAL_BENCHMARKS_CONFIG,
                            session=aimlabs_api_session)
async def teardown(bot):
    await close_session()


if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(setup(None))
    loop.run_until_complete(fetch_s1_val_benchmarks(aimlabs_id="ADC126093FDFBA6"))


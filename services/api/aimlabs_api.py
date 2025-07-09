import json
import aiohttp, aiofiles, asyncio
from functools import partial
from typing import Any
from collections import defaultdict

from services.api.kovaaks_api import update_benchmark_scenario_list
from settings import S1_VOLTAIC_VAL_BENCHMARKS_CONFIG
from utils.errors import ErrorFetchingData, ProfileDoesntExist
from utils.api_helper import AsyncRateLimiter, UpdatedAsyncRateLimiter
from utils.log import logger, api_logger

# API Endpoint
API_ENDPOINT = "https://api.aimlab.gg/graphql"
# aimlabs_api_rate_limiter = AsyncRateLimiter("aimlabs")
aimlabs_api_rate_limiter = UpdatedAsyncRateLimiter("aimlabs")

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


GET_USER_PLAYS_AGG = """
query GetAimlabProfileAgg($where: AimlabPlayWhere!) {
    aimlab {
        plays_agg(where: $where) {
            group_by {
                task_id
                task_name
                user_id
            }
            aggregate {
                max {
                    score
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
async def fetch_user_plays(user_ids: list[str], all_task_ids: list[str],
                           max_min=False):
    # Prepare variables for the API query
    variables = {
        "where": {
            "is_practice": {"_eq": False},
            "task_id": {"_in": all_task_ids},
            "user_id": {"_in": user_ids},
            "task_mode": {"_eq": 42},
        }
    }
    try:
        async with aimlabs_api_session.post(
                url=API_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json={"query": GET_USER_PLAYS_AGG, "variables": variables}
        ) as response:
            headers = response.headers
            response.raise_for_status()
            data = await response.json()
            # Process the response
            if not data.get('data', {}).get('aimlab', {}).get('plays_agg'):
                return {}, headers

            # Create a dictionary to store scores: {user_id: {task_id: score}}
            user_scores = {}
            task_scores = defaultdict(list)
            for entry in data['data']['aimlab']['plays_agg']:
                user_id = entry['group_by']['user_id']
                task_id = entry['group_by']['task_id']
                score = entry['aggregate']['max']['score']

                if user_id not in user_scores:
                    user_scores[user_id] = {}
                if score >= 0:
                    task_scores[task_id].append(score)
                user_scores[user_id][task_id] = score
            task_min_max = None
            if max_min:
                task_min_max = {
                    task_id: {
                        'min': min(scores),
                        'max': max(scores),
                        'scores': scores  # Optional: Keep all scores if needed
                    }
                    for task_id, scores in task_scores.items() if scores
                }
            _data = {"user_scores": user_scores, "task_min_max": task_min_max}
            with open(r'C:\Users\partt\PycharmProjects\aimlabs_api_data\temp\data.json', 'w', encoding='utf-8') as f:
                json.dump(_data, f, ensure_ascii=False, indent=4)
            return (user_scores, task_min_max), headers
    except Exception as e:
        raise ErrorFetchingData(f"API returned status "
                                f"`{response.status}` Reason: {str(e)}",
                                headers=headers)


@aimlabs_api_rate_limiter
async def check_aimlabs_username(username:str):
    """Queries aimlabs api and checks if username exists."""
    try:
        async with aimlabs_api_session.post(
                url=API_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json={"query": GET_USER_INFO, "variables":
                    {"username": username}}
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
                                f"`{response.status}` Reason: {str(e)}",
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


# if __name__ == "__main__":
#     import asyncio
#     loop = asyncio.new_event_loop()
#     loop.run_until_complete(setup(None))
#     loop.run_until_complete(fetch_user_plays(user_ids=["ADC126093FDFBA6"], all_task_ids=[
#         "CsLevel.VT Lowgravity56.VT Dynam.SEML1U",
#         "CsLevel.VT Lowgravity56.VT Lorys.SII0N0",
#         "CsLevel.Lowgravity56.VT Straf.RX8M65",
#         "CsLevel.VT Lowgravity56.VT Angle.SX9GAE"
#     ]))


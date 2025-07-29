import json
import aiohttp
from collections import defaultdict

from errors import ErrorFetchingData, ProfileDoesntExist


# API Endpoint
API_ENDPOINT = "https://api.aimlab.gg/graphql"

SCENARIO_LIST_URL = \
    "https://beta.voltaic.gg/api/v1/aimlabs/benchmarks/valorant_s1"


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


async def fetch_user_plays(session: aiohttp.ClientSession,
                           user_ids: list[str], all_task_ids: list[str],
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
        async with session.post(
                url=API_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json={"query": GET_USER_PLAYS_AGG, "variables": variables}
        ) as response:
            headers = response.headers
            response.raise_for_status()
            data = await response.json()
            # Process the response
            if not data.get('data', {}).get('aimlab', {}).get('plays_agg'):
                print("Empty response or no plays found for the given criteria.")
                return ({}, {}), headers

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
            return (user_scores, task_min_max), headers
    except Exception as e:
        raise ErrorFetchingData(f"API returned status "
                                f"`{response.status}` Reason: {str(e)}",
                                headers=headers)


async def check_aimlabs_username(session: aiohttp.ClientSession, username:str):
    """Queries aimlabs api and checks if username exists."""
    try:
        async with session.post(
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

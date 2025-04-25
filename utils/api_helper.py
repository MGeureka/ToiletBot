from datetime import datetime, timezone
import asyncio, aiofiles
import time, os
from functools import wraps

import aiohttp

from settings import API_HEADER_FIELDS
from utils.log import api_logger
from utils.errors import ErrorFetchingData, UnableToDecodeJson
import json
FILE_LOCK = asyncio.Lock()


class AsyncRateLimiter:
    def __init__(self, api_type):
        self.api_type = api_type
        self.remaining_calls = API_HEADER_FIELDS[api_type]["rate_limit"]
        self.reset_time = 0
        self.lock = asyncio.Lock()


    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.lock:
                if self.api_type != "kovaaks":
                    current_time = time.time()

                    # If reset time has passed, reset our counter
                    if current_time > self.reset_time:
                        self.remaining_calls = API_HEADER_FIELDS[self.api_type]["rate_limit"]

                    # Wait if we're out of calls
                    if self.remaining_calls <= 3:
                        wait_time = max(0, self.reset_time - current_time)
                        if wait_time > 0:
                            api_logger.warning(f"Hit {self.api_type} rate limit waiting {wait_time} seconds.")
                            await asyncio.sleep(wait_time)
                            self.remaining_calls = API_HEADER_FIELDS[self.api_type]["rate_limit"]

            # Execute the API call
            data, headers = {}, {}
            runtime = -1000
            try:
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                runtime = end_time - start_time
                data, headers = result
                return data
            except Exception as e:
                if hasattr(e, "context"):
                    headers = e.context.get("headers", {})
                raise e
            finally:
                if self.api_type != "kovaaks":
                    await self.update_calls(headers, func, runtime)
                else:
                    api_logger.info(f"Made call to {self.api_type} api from function "
                                    f"{func.__name__} ({runtime:.2f} s): rate limit "
                                    f"N/A, reset_time N/A")

        return wrapper


    async def update_calls(self, headers, func, runtime):
        async with self.lock:
            try:
                self.remaining_calls = int(headers.get(
                    API_HEADER_FIELDS[self.api_type]["rate_limit_field"]))

                reset_time = float(headers.get(
                    API_HEADER_FIELDS[self.api_type]["reset_time_field"]))
                api_logger.info(f"Made call to {self.api_type} api from function "
                            f"{func.__name__} ({runtime:.2f} s): rate limit "
                            f"{self.remaining_calls}, reset_time "
                            f"{reset_time:.2f} s.")
                self.reset_time = time.time() + reset_time
            except Exception as e:
                api_logger.error(f"Failed to update rate limit for "
                             f"{self.api_type}: {e}")


async def update_benchmark_scenario_list(url: str, path: str, session):
    """Gets S5 benchmark scenario list """
    now = datetime.now(timezone.utc).timestamp()
    if os.path.exists(path):
        if now - os.path.getmtime(path) < 86400:
            return None, None
    try:
        async with session.get(
                url=url
        ) as response:
            response.raise_for_status()
            headers = response.headers
            config = await response.json()
            categories = [
                {
                    "id": category["id"],
                    "subcategories": [{"id": sub["id"]} for sub in
                                      category["subcategories"]]
                } for category in config["categories"]
            ]
            tier_energies = [
                [
                    j['energy_threshold'] for j in config['ranks'] if j['tier_id'] == i
                ] for i in [2, 3, 4]
            ]
            novice_scenarios, intermediate_scenarios, advanced_scenarios = [[
                {
                    "thresholds": tier['thresholds'],
                    "subcategoryId": scenario['subcategory_id'],
                    "score": None,
                    "task_id": scenario.get('task_id', None),
                    "weapon_id": scenario.get('weapon_id', None)
                }
                for scenario in config["scenarios"]
                for tier in scenario["tiers"]
                if tier['tier_id'] == tier_number
            ] for tier_number in [2, 3, 4]]
            final_json = {
                "categories": categories,
                "tier_energies": tier_energies,
                "novice_scenarios": novice_scenarios,
                "intermediate_scenarios": intermediate_scenarios,
                "advanced_scenarios": advanced_scenarios
            }
            async with FILE_LOCK:
                async with aiofiles.open(
                        path, "w",
                        encoding="utf-8"
                ) as f:
                    await f.write(json.dumps(final_json,
                                             ensure_ascii=False, indent=4))
            return config, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching scenario "
                                f"list for S5 benchmarks "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def get_json(response: aiohttp.ClientResponse):
    try:
        data = await response.json()
        return data
    except Exception as e:
        raise UnableToDecodeJson(" ")


async def setup(bot): pass
async def teardown(bot): pass

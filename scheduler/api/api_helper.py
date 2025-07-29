from datetime import datetime, timezone
import asyncio, aiofiles
import os

import aiohttp

from errors import ErrorFetchingData, UnableToDecodeJson
import json
FILE_LOCK = asyncio.Lock()


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

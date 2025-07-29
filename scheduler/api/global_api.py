import aiohttp
import asyncio
import aiofiles
import json
from config import (DOJO_AIMLABS_PLAYLIST_BALANCED,
                    DOJO_AIMLABS_PLAYLIST_ADVANCED,
                    S1_VOLTAIC_VAL_BENCHMARKS_CONFIG)
from api.val_api import fetch_all_dms, fetch_rating
from api.aimlabs_api import fetch_user_plays
from api.kovaaks_api import get_voltaic_s5_scores


async def fetch_val_data(session: aiohttp.ClientSession, valorant_id: str, region: str, is_dojo: bool):
    """Fetches Valorant data for a given Valorant ID and region."""
    if is_dojo:
        (dms, headers1), (ranks, headers2) = await asyncio.gather(
            fetch_all_dms(session, valorant_id, region),
            fetch_rating(session, valorant_id, region)
        )
    else:
        (dms, headers1), (ranks, headers2) = await asyncio.gather(
            fetch_all_dms(session, valorant_id, region),
            fetch_rating(session, valorant_id, region)
        )
    return (dms, ranks), headers1


async def fetch_aimlabs_data(session: aiohttp.ClientSession, aimlabs_id: str, is_dojo: bool):
    """Fetches Aimlabs data for a given Aimlabs ID."""
    async with aiofiles.open(S1_VOLTAIC_VAL_BENCHMARKS_CONFIG) as f:
        content = await f.read()
        config = json.loads(content)
    all_task_ids = []
    for category in ['novice_scenarios', 'intermediate_scenarios', 'advanced_scenarios']:
        all_task_ids.extend([scenario['task_id'] for scenario in config[category]])

    if is_dojo:
        ((val_vol_s1, headers1),
         (dojo_balanced, headers2),
         (dojo_advanced, headers3)) = await asyncio.gather(
            fetch_user_plays(session, [aimlabs_id],
                             all_task_ids),
            fetch_user_plays(session, [aimlabs_id],
                             DOJO_AIMLABS_PLAYLIST_BALANCED),
            fetch_user_plays(session, [aimlabs_id],
                             DOJO_AIMLABS_PLAYLIST_ADVANCED)
        )
        return (val_vol_s1, dojo_balanced, dojo_advanced), headers1

    val_vol_s1, headers = await fetch_user_plays(session, [aimlabs_id],
                                                 all_task_ids)
    return val_vol_s1, headers


async def fetch_kovaaks_data(session: aiohttp.ClientSession, steam_id: str, is_dojo: bool):
    """Fetches Kovaaks data for a given Steam ID."""
    return await get_voltaic_s5_scores(session, steam_id)


async def queue_writer(redis_client, task_data):
    """Writes a task to the specified Redis stream."""


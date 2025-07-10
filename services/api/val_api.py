import aiohttp
import traceback

from utils.errors import (ErrorFetchingData, ProfileDoesntExist,
                          UnableToDecodeJson)
from settings import VALO_API_KEY
from utils.api_helper import AsyncRateLimiter, get_json, UpdatedAsyncRateLimiter
from utils.log import logger, api_logger
from aiolimiter import AsyncLimiter

# val_api_rate_limiter = AsyncRateLimiter("val")
val_api_rate_limiter = UpdatedAsyncRateLimiter("val")
val_api_session: aiohttp.ClientSession | None = None
valorant_api_limiter = AsyncLimiter(max_rate=1, time_period=0.7)

PLATFORM = "pc"


async def get_session():
    global val_api_session
    if val_api_session is None or val_api_session.closed:
        val_api_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
    api_logger.info("Connection established to val API")
    logger.info(f"Connection established to val API")
    return val_api_session


async def close_session():
    global val_api_session
    if val_api_session and not val_api_session.closed:
        api_logger.info("Connection closed to val API")
        logger.info(f"Connection closed to val API")
        await val_api_session.close()
        val_api_session = None


async def fetch_dms(puuid: str, region: str, dm_type: str):
    data = None
    try:
        async with valorant_api_limiter:
            async with val_api_session.get(
                    f"https://api.henrikdev.xyz/valorant/v4/by-puuid/matches"
                    f"/{region}/{PLATFORM}/{puuid}?mode={dm_type}&size=5",
                    headers={"Authorization": f"{VALO_API_KEY}"}
            ) as response:
                headers = response.headers
                data = await get_json(response)
                response.raise_for_status()
                return data
    except UnableToDecodeJson as e:
        raise ErrorFetchingData(f"Unable to decode Valorant API "
                                f"response.\n"
                                f"{str(e)}\n{traceback.format_exc()}",
                                headers=headers)
    except Exception as e:
        if data:
            raise ErrorFetchingData(f"Status code: "
                                    f"{data['errors'][0]['status']}. "
                                    f"Error code: {data['errors'][0]['code']}. "
                                    f"{data['errors'][0]['message']}",
                                    headers=headers,
                                    puuid=puuid,
                                    region=region,
                                    )
        ErrorFetchingData(f"Error when querying valorant API. "
                          f"{str(e)}\n{traceback.format_exc()}",
                          headers=headers,
                          puuid=puuid,
                          region=region,
                          )


async def fetch_rating(puuid: str, region: str):
    try:
        async with valorant_api_limiter:
            async with val_api_session.get(
                    f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/"
                    f"{region}/{PLATFORM}/{puuid}",
                    headers={"Authorization": f"{VALO_API_KEY}"},
            ) as response:
                headers = response.headers
                data = await get_json(response)
                response.raise_for_status()
            current_rank = data['data']['current']['tier']['name']
            current_rank_id = data['data']['current']['tier']['id']
            current_rr = data['data']['current']['rr']
            peak_rank = data['data']['peak']['tier']['name']
            peak_rank_id = data['data']['peak']['tier']['id']

            return (current_rank, current_rank_id, current_rr, peak_rank,
                    peak_rank_id)
    except UnableToDecodeJson as e:
        raise ErrorFetchingData(f"Unable to decode Valorant API "
                                f"response.\n"
                                f"{str(e)}",
                                headers=headers)
    except Exception as e:
        if response:
            raise ErrorFetchingData(f"Status code: "
                                    f"{data['errors'][0]['status']}. "
                                    f"Error code: {data['errors'][0]['code']}. "
                                    f"{data['errors'][0]['message']}",
                                    headers=headers,
                                    puuid=puuid,
                                    region=region,
                                    )
        raise ErrorFetchingData(f"Unknown error when querying "
                                f"valorant API. \n"
                                f"{str(e)}\n{traceback.format_exc()}",)


async def check_valorant_username(username: str, tag: str):
    """Checks if valorant username and tag is valid, returns PUUID and region"""
    try:
        async with valorant_api_limiter:
            async with val_api_session.get(
                    f"https://api.henrikdev.xyz/valorant/v1/account/{username}/"
                    f"{tag}",
                    headers={"Authorization": f"{VALO_API_KEY}"},
            ) as response:
                headers = response.headers
                response.raise_for_status()
                data = await response.json()
            return (data['data']['puuid'],
                    data['data']['region'])
    except Exception as e:
        raise ErrorFetchingData(f"Error while checking "
                                f"valorant username `{username}#{tag}`. "
                                f"Either the username doesn't exist or "
                                f"it's an API error",
                                headers=headers,
                                username=username,
                                tag=tag
                                )


async def setup(bot):
    global val_api_session
    val_api_session = await get_session()
async def teardown(bot):
    await close_session()

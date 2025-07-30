import aiohttp
import traceback
import asyncio
from errors import (ErrorFetchingData, UnableToDecodeJson)
from config import VALO_API_KEY
from api.api_helper import get_json


PLATFORM = "pc"


async def fetch_dms(session: aiohttp.ClientSession, puuid: str, region: str,
                    dm_type: str, logger):
    logger.info(f"Fetching {dm_type} DMs for PUUID: {puuid} in region: {region}")
    data = None
    try:
        async with session.get(
                f"https://api.henrikdev.xyz/valorant/v4/by-puuid/matches"
                f"/{region}/{PLATFORM}/{puuid}?mode={dm_type}&size=5",
                headers={"Authorization": f"{VALO_API_KEY}"}
        ) as response:
            headers = response.headers
            data = await get_json(response)
            response.raise_for_status()
            return data, headers
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


async def fetch_rating(session: aiohttp.ClientSession, puuid: str, region: str):
    try:
        async with session.get(
                f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/"
                f"{region}/{PLATFORM}/{puuid}",
                headers={"Authorization": f"{VALO_API_KEY}"},
                allow_redirects=False
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
                    peak_rank_id), headers
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


async def check_valorant_username(session: aiohttp.ClientSession, username: str,
                                  tag: str):
    """Checks if valorant username and tag is valid, returns PUUID and region"""
    try:
        async with session.get(
                f"https://api.henrikdev.xyz/valorant/v1/account/{username}/"
                f"{tag}",
                headers={"Authorization": f"{VALO_API_KEY}"},
        ) as response:
            headers = response.headers
            response.raise_for_status()
            data = await response.json()
            return (data['data']['puuid'],
                    data['data']['region']), headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while checking "
                                f"valorant username `{username}#{tag}`. "
                                f"Either the username doesn't exist or "
                                f"it's an API error",
                                headers=headers,
                                username=username,
                                tag=tag
                                )


async def fetch_all_dms(session: aiohttp.ClientSession, puuid: str,
                        region: str):
    """Fetches all DMs for a given PUUID and region"""
    (dms, _), (tdms, headers) = await asyncio.gather(
        fetch_dms(session, puuid, region, "deathmatch"),
        fetch_dms(session, puuid, region, "teamdeathmatch")
    )
    return (dms, tdms), headers

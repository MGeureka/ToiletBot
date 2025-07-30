import time, json, asyncio
import redis.asyncio as redis
from consumer import UpdateScheduler, RateLimiter
from common.log import sch_logger as logger
from api.val_api import fetch_all_dms, fetch_rating


class ValorantWorker(UpdateScheduler):
    def __init__(self, redis_client: redis.client.Redis):
        """Initialize the ValorantWorker with a unique ID and name."""
        super().__init__(redis_client, consumer_type='val',
                         dojo_tokens_needed=3, tokens_needed=3, interval=60/30)
        # Consumer-specific rate limiter
        self.rate_limiter = RateLimiter(
            tokens=30,
            window_seconds=60,
            consumer_type='Valorant'
        )


    async def dojo_call_api(self, valorant_id: str, region: str):
        """Call the Valorant API to fetch data for a given Valorant ID."""
        call_time = time.time()
        parsed_dms = {}
        (dms, tdms), _ = await fetch_all_dms(self.session, valorant_id, region)
        ranks, headers = await fetch_rating(self.session, valorant_id, region)
        parsed_dms = [{"id": match['metadata']['match_id'],
                       "date": match['metadata']['started_at']}
                      for match in (dms['data'] + tdms['data'])
                      ]
        return (parsed_dms, ranks), headers, call_time


    async def call_api(self, valorant_id: str, region: str):
        """Call the Valorant API to fetch data for a given Valorant ID."""
        call_time = time.time()
        (dms, tdms), _ = await fetch_all_dms(self.session, valorant_id, region)
        ranks, headers = await fetch_rating(self.session, valorant_id, region)
        parsed_dms = [{"id": match['metadata']['match_id'],
                       "date": match['metadata']['started_at']}
                      for match in (dms['data'] + tdms['data'])
                      ]
        return (parsed_dms, ranks), headers, call_time


    async def dojo_process_task(self, data, stream, message_id):
        """Process a Dojo task from the Valorant stream."""
        valorant_id = data.get("valorant_id")
        region = data.get("params").get("region")
        dedupe_key = data.get("dedupe_key")

        if not valorant_id or not dedupe_key:
            logger.error(f"Invalid task data: {data}")
            return
        try:
            # Acquire rate limit tokens
            start_time = time.time()
            await self.rate_limiter.acquire(self.dojo_tokens_needed)
            valorant_data, headers, call_time = await self.dojo_call_api(valorant_id, region)
            logger.info(f"[ValorantWorker] Dojo {valorant_id} ({data['task_id']}) "
                        f"({time.time() - start_time}) -> Tokens: "
                        f"{self.rate_limiter.tokens} "
                        f"({self.rate_limiter.reset_time:.3f}s)")
            await self.rate_limiter.update_limits(
                int(headers.get("x-ratelimit-remaining")),
                float(headers.get("x-ratelimit-reset")),
                call_time
            )
            logger.info(f"[ValorantWorker] Headers: Tokens Remaining: {int(headers.get('x-ratelimit-remaining'))} "
                        f"(Reset Time: {float(headers.get('x-ratelimit-reset')):.3f}s)")
            if not valorant_data:
                logger.warning(f"No Valorant data found for Valorant ID: {valorant_id}")
                return

            await self.ack_task(stream, message_id, data['dedupe_key'])

        except Exception as e:
            logger.error(f"Error processing task for Valorant ID {valorant_id}: {str(e)}", exc_info=True)


    async def process_task(self, data, stream, message_id):
        """Process a task from the Valorant stream."""
        valorant_id = data.get("valorant_id")
        region = data.get("params").get("region")
        dedupe_key = data.get("dedupe_key")

        if not valorant_id or not dedupe_key:
            logger.error(f"Invalid task data: {data}")
            return

        try:
            # Acquire rate limit tokens
            if data.get("is_dojo"):
                start_time = time.time()
                await self.rate_limiter.acquire(self.dojo_tokens_needed)
                valorant_data, headers, call_time = await self.dojo_call_api(valorant_id, region)
                logger.info(f"[ValorantWorker] Dojo {valorant_id} ({data['task_id']}) "
                            f"({time.time() - start_time}) -> Tokens: "
                            f"{self.rate_limiter.tokens} "
                            f"({self.rate_limiter.reset_time:.3f}s)")
            else:
                start_time = time.time()
                await self.rate_limiter.acquire(self.tokens_needed)
                valorant_data, headers, call_time = await self.call_api(valorant_id, region)
                logger.info(f"[ValorantWorker] {valorant_id} "
                            f"({time.time() - start_time}) -> Tokens: "
                            f"{self.rate_limiter.tokens} "
                            f"({self.rate_limiter.reset_time:.3f}s)")
            await self.rate_limiter.update_limits(
                int(headers.get("x-ratelimit-remaining")),
                float(headers.get("x-ratelimit-reset")),
                call_time
            )
            logger.info(f"[ValorantWorker] Headers: Tokens Remaining: {int(headers.get('x-ratelimit-remaining'))} "
                        f"(Reset Time: {float(headers.get('x-ratelimit-reset')):.3f}s)")
            if not valorant_data:
                logger.warning(f"No Valorant data found for Valorant ID: {valorant_id}")
                return

            await self.ack_task(stream, message_id, data['dedupe_key'])
        except Exception as e:
            logger.error(f"Error processing task for Valorant ID {valorant_id}: {str(e)}", exc_info=True)


    async def dojo_write_db(self):
        """Write the Dojo data to the database."""
        raise NotImplementedError("Dojo write DB is not implemented for AimlabsWorker.")


    async def write_db(self):
        """Write the Aimlabs data to the database."""
        raise NotImplementedError("Write DB is not implemented for AimlabsWorker.")

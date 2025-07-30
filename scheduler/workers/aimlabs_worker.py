import time, json, asyncio
import redis.asyncio as redis
from consumer import UpdateScheduler, RateLimiter
from common.log import sch_logger as logger
from api.aimlabs_api import fetch_user_plays
from config import (DOJO_AIMLABS_PLAYLIST_BALANCED,
                    DOJO_AIMLABS_PLAYLIST_ADVANCED,
                    S1_VOLTAIC_VAL_BENCHMARKS_CONFIG)


class AimlabsWorker(UpdateScheduler):
    def __init__(self, redis_client: redis.client.Redis):
        """Initialize the AimlabsWorker with a unique ID and name."""
        super().__init__(redis_client, consumer_type='aimlabs',
                         dojo_tokens_needed=3, tokens_needed=1,
                         interval=60/10000)
        # Consumer-specific rate limiter
        self.rate_limiter = RateLimiter(
            tokens=10000,
            window_seconds=60,
            consumer_type='Aimlabs'
        )
        with open(S1_VOLTAIC_VAL_BENCHMARKS_CONFIG) as f:
            config = json.load(f)
        self.all_task_ids = []
        for category in ['novice_scenarios', 'intermediate_scenarios', 'advanced_scenarios']:
            self.all_task_ids.extend([scenario['task_id'] for scenario in config[category]])


    async def dojo_call_api(self, aimlabs_id: str):
        call_time = time.time()
        (voltaic_val, _), _ = await fetch_user_plays(
            self.session, [aimlabs_id], self.all_task_ids
        )
        (dojo_balanced, balanced_max_min), _ = await fetch_user_plays(
            self.session, [aimlabs_id], DOJO_AIMLABS_PLAYLIST_BALANCED,
            max_min=True
        )
        (dojo_advanced, advanced_max_min), headers = await fetch_user_plays(
            self.session, [aimlabs_id], DOJO_AIMLABS_PLAYLIST_ADVANCED,
            max_min=True
        )
        return {
            "voltaic_val": voltaic_val,
            "dojo_balanced": dojo_balanced,
            "balanced_max_min": balanced_max_min,
            "dojo_advanced": dojo_advanced,
            "advanced_max_min": advanced_max_min
        }, headers, call_time


    async def call_api(self, aimlabs_id: str):
        """Call the Aimlabs API to fetch data for a given Aimlabs ID."""
        call_time = time.time()
        (voltaic_val, _), headers = await fetch_user_plays(
            self.session, [aimlabs_id], self.all_task_ids
        )
        return {"voltaic_val": voltaic_val}, headers, call_time


    async def dojo_process_task(self, data, stream, message_id):
        """Process a Dojo task from the Aimlabs stream."""
        aimlabs_id = data.get("aimlabs_id")
        dedupe_key = data.get("dedupe_key")

        if not aimlabs_id or not dedupe_key:
            logger.error(f"Invalid task data: {data}")
            return

        try:
            # Acquire rate limit tokens
            start_time = time.time()
            await self.rate_limiter.acquire(self.dojo_tokens_needed)
            aimlabs_data, headers, call_time = await self.dojo_call_api(aimlabs_id)
            logger.info(f"[AimlabsWorker] Dojo {aimlabs_id} "
                        f"({time.time() - start_time}) -> Tokens: "
                        f"{self.rate_limiter.tokens} "
                        f"({self.rate_limiter.reset_time:.3f}s)")
            await self.rate_limiter.update_limits(
                int(headers.get("ip-ratelimit-remaining")),
                float(headers.get("ip-ratelimit-reset")),
                call_time
            )
            if not aimlabs_data:
                logger.warning(f"No Aimlabs data found for Aimlabs ID: {aimlabs_id}")
                return

            await self.ack_task(stream, message_id, data['dedupe_key'])

        except Exception as e:
            logger.error(f"Error processing task for Aimlabs ID {aimlabs_id}: {str(e)}", exc_info=True)


    async def process_task(self, data, stream, message_id):
        """Process a task from the Aimlabs stream."""
        aimlabs_id = data.get("aimlabs_id")
        dedupe_key = data.get("dedupe_key")

        if not aimlabs_id or not dedupe_key:
            logger.error(f"Invalid task data: {data}")
            return

        try:
            start_time = time.time()
            await self.rate_limiter.acquire(self.tokens_needed)
            aimlabs_data, headers, call_time = await self.call_api(aimlabs_id)
            logger.info(f"[AimlabsWorker] {aimlabs_id} "
                        f"({time.time() - start_time}) -> Tokens: "
                        f"{self.rate_limiter.tokens} "
                        f"({self.rate_limiter.reset_time:.3f}s)")
            await self.rate_limiter.update_limits(
                int(headers.get("ip-ratelimit-remaining")),
                float(headers.get("ip-ratelimit-reset")),
                call_time
            )
            if not aimlabs_data:
                logger.warning(f"No Aimlabs data found for Aimlabs ID: {aimlabs_id}")
                return

            await self.ack_task(stream, message_id, data['dedupe_key'])

        except Exception as e:
            logger.error(f"Error processing task for Aimlabs ID {aimlabs_id}: {str(e)}", exc_info=True)


    async def dojo_write_db(self):
        """Write the Dojo data to the database."""
        raise NotImplementedError("Dojo write DB is not implemented for AimlabsWorker.")


    async def write_db(self):
        """Write the Aimlabs data to the database."""
        raise NotImplementedError("Write DB is not implemented for AimlabsWorker.")

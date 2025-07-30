import time, json, asyncio
import redis.asyncio as redis
from consumer import UpdateScheduler, RateLimiter
from common.log import sch_logger as logger
from api.kovaaks_api import get_voltaic_s5_scores


class KovaaksRateLimiter(RateLimiter):
    def __init__(self, tokens: int, window_seconds: int):
        """Initialize the rate limiter with tokens and reset time."""
        super().__init__(tokens, window_seconds, consumer_type="Kovaaks")
        self.max_reset_time = window_seconds
        self.window_start = time.time()


    async def acquire(self, tokens_needed: int):
        """Acquire tokens for the Kovaaks worker."""
        while True:
            async with self.lock:
                now = time.time()
                if self.tokens == self.max_tokens:
                    self.window_start = now

                if self.window_start + self.max_reset_time < now:
                    self.tokens = self.max_tokens

                # If we have enough tokens, proceed
                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    self.reset_time = max((self.window_start + self.max_reset_time - now), float(0))
                    return

            async with self.lock:
                self.reset_time = max((self.window_start + self.max_reset_time - now), float(0))
            logger.warning(f"Kovaaks rate limit exceeded, sleeping for "
                           f"{self.reset_time:.3f}s...")
            await asyncio.sleep(self.reset_time)
            async with self.lock:
                self.tokens = self.max_tokens


class KovaaksWorker(UpdateScheduler):
    def __init__(self, redis_client: redis.client.Redis):
        """Initialize the KovaaksWorker with a unique ID and name."""
        super().__init__(redis_client, consumer_type='kovaaks',
                         dojo_tokens_needed=3, tokens_needed=3, interval=60/100)
        # Consumer-specific rate limiter
        self.rate_limiter = KovaaksRateLimiter(
            tokens=100,
            window_seconds=60
        )


    async def call_api(self, steam_id: str):
        """Call the Kovaaks API to fetch data for a given Steam ID."""
        nov, intern, adv = await get_voltaic_s5_scores(self.session, steam_id)
        return {
            "novice_scenarios": nov,
            "intermediate_scenarios": intern,
            "advanced_scenarios": adv
        }


    async def process_task(self, data, stream, message_id):
        """Process a task from the Kovaaks stream."""
        steam_id = data.get("steam_id")
        dedupe_key = data.get("dedupe_key")

        if not steam_id or not dedupe_key:
            logger.error(f"Invalid task data: {data}")
            return

        try:
            # Acquire rate limit tokens
            await self.rate_limiter.acquire(self.tokens_needed)
            start_time = time.time()
            # Fetch Kovaaks data
            kovaaks_data = await self.call_api(steam_id)
            logger.info(f"[KovaaksWorker] {steam_id} "
                        f"({time.time() - start_time}) -> Tokens: "
                        f"{self.rate_limiter.tokens} "
                        f"({self.rate_limiter.reset_time:.3f}s)")
            if not kovaaks_data:
                logger.warning(f"No Kovaaks data found for Steam ID: {steam_id}")
                return

            await self.queue_writer(kovaaks_data, data)
            await self.ack_task(stream, message_id, data['dedupe_key'])

        except Exception as e:
            logger.error(f"Error processing task for Steam ID {steam_id}: {str(e)}", exc_info=True)


    async def queue_writer(self, kovaaks_data, data):
        """Write the Kovaaks data to the Redis stream."""
        raise NotImplementedError("Queue writer not implemented for KovaaksWorker")

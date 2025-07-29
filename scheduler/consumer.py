import asyncio
import aiohttp
import json, time, traceback
import redis.asyncio as redis
from errors import WeakError
from common.log import sch_logger as logger
import msgpack


class RateLimiter:
    def __init__(self, tokens: int, window_seconds: int, consumer_type: str):
        self.max_tokens = tokens
        self.tokens = tokens
        self.reset_time = float(window_seconds)
        self.lock = asyncio.Lock()
        self.consumer_type = consumer_type
        self.last_updated = time.time()

    async def acquire(self, tokens_needed: int):
        while True:
            async with self.lock:

                # If we have enough tokens, proceed
                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    return

            logger.warning(f"{self.consumer_type} rate limit exceeded, "
                           f"sleeping for "
                           f"{self.reset_time:.3f}s...")
            await asyncio.sleep(self.reset_time)
            async with self.lock:
                self.tokens = self.max_tokens


    async def update_limits(self, tokens: int, reset_time: float):
        """Update the rate limit parameters"""
        async with self.lock:
            self.reset_time = reset_time


class UpdateScheduler:
    def __init__(self, redis_client: redis.client.Redis, consumer_type: str,
                 dojo_tokens_needed: int, tokens_needed: int, interval: float):
        self.session = None
        self.redis = redis_client
        self.consumer_type = consumer_type
        self.consumer_group = f"{consumer_type}-group"
        self.high_priority_stream = f"{consumer_type}_high_priority_tasks"
        self.low_priority_stream = f"{consumer_type}_low_priority_tasks"
        self.dojo_tokens_needed = dojo_tokens_needed
        self.tokens_needed = tokens_needed
        self.interval = interval


    async def setup_streams(self):
        """Create consumer groups for the consumer's specific streams."""
        for stream in [self.high_priority_stream, self.low_priority_stream]:
            try:
                await self.redis.xgroup_create(stream, self.consumer_group,
                                               id='0', mkstream=True)
                logger.info(f"Created consumer group '{self.consumer_group}' "
                            f"for stream '{stream}'.")
            except redis.ResponseError as e:
                if "consumer group name already exists" in str(e).lower():
                    logger.info(f"Consumer group '{self.consumer_group}' "
                                f"already exists for stream '{stream}'.")
                else:
                    raise


    async def get_task(self, stream_name: str):
        """Get a single task from a specific stream for this consumer."""
        response = await self.redis.xreadgroup(
            self.consumer_group, self.consumer_type,
            {stream_name: '>'}, count=1, block=1000
        )
        if not response:
            return None
        stream, messages = response[0]
        message_id, data = messages[0]
        # data = {k.decode(): v.decode() for k, v in data.items()}
        # task_data = json.loads(data["data"])
        return stream, message_id, json.loads(data["data"])


    async def start(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
        await self.setup_streams()
        try:
            await self.run()
        finally:
            await self.session.close()
            logger.info("aiohttp session closed.")


    async def ack_task(self, stream, message_id, dedupe_key):
        """Acknowledge the task in the Redis stream."""
        await self.redis.xack(stream, self.consumer_group, message_id)
        await self.redis.xdel(stream, message_id)
        await self.redis.srem("queued_profiles", dedupe_key)


    async def queue_writer(self, api_data, task_data):
        """Write a task to the specified Redis stream."""
        await self.redis.rpush("writer_queue", msgpack.packb([api_data, task_data]))


    async def process_task(self, data):
        """Process a single task message."""
        raise NotImplementedError

    async def get_pending_count(self) -> int:
        try:
            result1 = await self.redis.xpending(self.low_priority_stream, self.consumer_group)
            result2 = await self.redis.xpending(self.high_priority_stream, self.consumer_group)
            return result1['pending'] + result2['pending']
        except Exception as e:
            logger.error(f"Error checking pending entries: {e}", exc_info=True)
            return 0  # Fallback: assume zero if there's an error


    async def run(self):
        """Main loop to process tasks from the Valorant streams."""
        logger.info(f"Consumer '{self.consumer_type}' started. Listening on streams.")
        while True:
            try:
                pending = await self.get_pending_count()
                if pending >= 5:
                    logger.info(f"Pending tasks in {self.consumer_type} stream: {pending}. "
                                f"Sleeping for 10 seconds...")
                    await asyncio.sleep(10)
                    continue
                # Always check high-priority stream first
                task = await self.get_task(self.high_priority_stream)
                if not task:
                    task = await self.get_task(self.low_priority_stream)

                if task:
                    stream, message_id, data = task
                    # logger.info(f"Processing task {data['task_id']}: ")
                    await self.process_task(data)

                    # Acknowledge the task after processing
                    await self.ack_task(stream, message_id, data['dedupe_key'])

                    if data['is_dojo']:
                        await asyncio.sleep(self.interval * self.dojo_tokens_needed)
                    else:
                        await asyncio.sleep(self.interval * self.tokens_needed)
                else:
                    logger.info(f"No tasks found in {self.consumer_type} stream. "
                                f"Sleeping...")
                    await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in {self.consumer_type} consumer: {str(e)}", exc_info=True)
                await asyncio.sleep(10)

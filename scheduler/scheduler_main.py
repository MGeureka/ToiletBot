import asyncio
import time
import redis.asyncio as redis
from common.log import sch_logger as logger
from config import REDIS_URL, DSN
from common.database import Database
from workers.aimlabs_worker import AimlabsWorker
from workers.kovaaks_worker import KovaaksWorker
from workers.valorant_worker import ValorantWorker
from producer import UpdateProducer


async def init_consumers():
    """Sets up and runs all the stream consumers concurrently."""
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    consumers = [
        ValorantWorker(redis_client=redis_client),
        AimlabsWorker(redis_client=redis_client),
        KovaaksWorker(redis_client=redis_client),
    ]
    # Run all consumer loops concurrently
    consumer_tasks = [asyncio.create_task(consumer.start()) for consumer in consumers]
    await asyncio.gather(*consumer_tasks)


async def init_producers():
    """Initialize and run all producers if needed."""
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    db = Database(DSN, max_pool_size=8, min_pool_size=2)
    await db.start_pool()
    producer = UpdateProducer(redis_client=redis_client, db=db)
    await producer.run()


async def main():
    """Main entry point to initialize and run all consumers/producers."""
    try:
        await asyncio.gather(init_consumers(), init_producers())
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        time.sleep(5)  # Allow time for Redis to start
        logger.info("Starting scheduler...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler shutting down.")

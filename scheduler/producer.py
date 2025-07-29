import asyncio
import asyncpg
import json
import uuid
from collections import defaultdict
import redis.asyncio as redis
from datetime import datetime, timedelta, timezone
from common.log import sch_logger as logger
from common.database import Database
from config import DOJO_GUILD_ID

UPDATE_INTERVAL_MINUTES = 3
UPDATE_INTERVAL_SECONDS = UPDATE_INTERVAL_MINUTES * 60
STALE_THRESHOLD_MINUTES = 5

class UpdateProducer:
    """Producer class to enqueue tasks for updating Valorant, Aimlabs, and
    Kovaaks"""
    def __init__(self, redis_client: redis.client.Redis, db: Database):
        self.redis = redis_client
        self.db = db
        self.val_stream = "val_low_priority_tasks"
        self.aimlabs_stream = "aimlabs_low_priority_tasks"
        self.kovaaks_stream = "kovaaks_low_priority_tasks"

    async def produce(self, payload: dict, stream: str):
        """Produce a task to the appropriate stream."""
        await self.redis.xadd(stream, {"data": json.dumps(payload)})


    async def fetch_stale_val_profiles(self) -> dict[str: list[dict]]:
        """Fetch profiles that have not been updated within the stale threshold."""
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        query = """
        SELECT
            g.valorant_id,
            g.region,
            p.profile_id,
            p.guild_id,
            p.discord_id
        FROM accounts.global_valorant_accounts g
        JOIN profiles.valorant_profiles p ON p.valorant_id = g.valorant_id
        WHERE (g.last_updated < $1 or g.last_updated IS NULL)
        AND p.is_active = TRUE;
        """
        grouped = defaultdict(list)
        db_result = await self.db.fetchmany(query, stale_threshold)
        for row in db_result:
            grouped[row['valorant_id']].append({
                "region": row['region'],
                "profile_id": row["profile_id"],
                "guild_id": row["guild_id"],
                "discord_id": row["discord_id"],
                "is_dojo": row["guild_id"] == DOJO_GUILD_ID
            })
        return grouped


    async def fetch_stale_aimlabs_profiles(self):
        """Fetch Aim Lab profiles that have not been updated within the stale threshold."""
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        query = """
        SELECT 
            g.aimlabs_id,
            p.profile_id,
            p.guild_id,
            p.discord_id
        FROM accounts.global_aimlabs_accounts g 
        JOIN profiles.aimlabs_profiles p ON p.aimlabs_id = g.aimlabs_id
        WHERE (g.last_updated < $1 or g.last_updated IS NULL)
          AND p.is_active = TRUE;
        """
        grouped = defaultdict(list)
        db_result = await self.db.fetchmany(query, stale_threshold)
        for row in db_result:
            grouped[row['aimlabs_id']].append({
                "profile_id": row["profile_id"],
                "guild_id": row["guild_id"],
                "discord_id": row["discord_id"],
                "is_dojo": row["guild_id"] == DOJO_GUILD_ID,
            })
        return grouped


    async def fetch_stale_kovaaks_profiles(self):
        """Fetch Kovaaks profiles that have not been updated within the stale threshold."""
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        query = """
        SELECT 
            g.steam_id,
            p.profile_id,
            p.guild_id,
            p.discord_id
        FROM accounts.global_kovaaks_accounts g 
        JOIN profiles.kovaaks_profiles p ON p.kovaaks_id = g.kovaaks_id
        WHERE (g.last_updated < $1 or g.last_updated IS NULL)
          AND p.is_active = TRUE;
        """
        grouped = defaultdict(list)
        db_result = await self.db.fetchmany(query, stale_threshold)
        for row in db_result:
            grouped[row['steam_id']].append({
                "profile_id": row["profile_id"],
                "guild_id": row['guild_id'],
                "discord_id": row['discord_id'],
                "is_dojo": row['guild_id'] == DOJO_GUILD_ID,
            })
        return grouped


    async def queue_valorant_tasks(self):
        """Enqueue tasks for Valorant profiles that need updates."""
        stale_profiles = await self.fetch_stale_val_profiles()
        for valorant_id, profiles in stale_profiles.items():
            dedupe_key = f"{self.val_stream}:{valorant_id}"
            task_data = {
                "task_id": str(uuid.uuid4()),
                "task_type": "fetch_val_data",
                "valorant_id": valorant_id,
                "profiles": profiles,
                "is_dojo": any(d.get("is_dojo") for d in profiles),
                "params": {
                    "valorant_id": valorant_id,
                    "region": profiles[0]['region'],
                },
                "dedupe_key": dedupe_key,
            }
            added = await self.redis.sadd("queued_profiles", dedupe_key)
            if added:
                stream_size = await self.redis.xlen(self.val_stream)
                if stream_size > 150:
                    logger.warning(f"Aimlabs stream size is large: {stream_size}. Skipping enqueue.")
                    break
                await self.produce(task_data, self.val_stream)
            else:
                logger.info(f"Skipped duplicate profile_id: {dedupe_key}")


    async def queue_aimlabs_tasks(self):
        """Enqueue tasks for Aimlabs profiles that need updates."""
        stale_profiles = await self.fetch_stale_aimlabs_profiles()
        for aimlabs_id, profiles in stale_profiles.items():
            dedupe_key = f"{self.aimlabs_stream}:{aimlabs_id}"
            task_data = {
                "task_id": str(uuid.uuid4()),
                "task_type": "fetch_aimlabs_data",
                "aimlabs_id": aimlabs_id,
                "profiles": profiles,
                "is_dojo": any(d.get("is_dojo") for d in profiles),
                "params": {
                    "aimlabs_id": aimlabs_id
                },
                "dedupe_key": dedupe_key,
            }
            added = await self.redis.sadd("queued_profiles", dedupe_key)
            if added:
                stream_size = await self.redis.xlen(self.aimlabs_stream)
                if stream_size > 100:
                    logger.warning(f"Aimlabs stream size is large: {stream_size}. Skipping enqueue.")
                    break
                await self.produce(task_data, self.aimlabs_stream)
            else:
                logger.info(f"Skipped duplicate profile_id: {dedupe_key}")


    async def queue_kovaaks_tasks(self):
        """Enqueue tasks for Kovaaks profiles that need updates."""
        stale_profiles = await self.fetch_stale_kovaaks_profiles()
        for steam_id, profiles in stale_profiles.items():
            dedupe_key = f"{self.kovaaks_stream}:{steam_id}"
            task_data = {
                "task_id": str(uuid.uuid4()),
                "task_type": "fetch_kovaaks_data",
                "steam_id": steam_id,
                "profiles": profiles,
                "is_dojo": any(d.get("is_dojo") for d in profiles),
                "params": {
                    "steam_id": steam_id,
                },
                "dedupe_key": dedupe_key,
            }
            added = await self.redis.sadd("queued_profiles", dedupe_key)
            if added:
                stream_size = await self.redis.xlen(self.kovaaks_stream)
                if stream_size > 50:
                    logger.warning(f"Kovaaks stream size is large: {stream_size}. Skipping enqueue.")
                    break
                await self.produce(task_data, self.kovaaks_stream)
            else:
                logger.info(f"Skipped duplicate profile_id: {dedupe_key}")


    async def run(self):
        """Main loop to periodically check for stale data and enqueue
        update tasks."""
        while True:
            try:
                logger.info("Producer cycle started.")
                await asyncio.gather(
                    self.queue_valorant_tasks(),
                    self.queue_aimlabs_tasks(),
                    self.queue_kovaaks_tasks()
                )

                logger.info(f"Producer sleeping for {UPDATE_INTERVAL_SECONDS} seconds...")
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Error in producer loop: {e}", exc_info=True)
                await asyncio.sleep(10)  # Short pause to avoid rapid crashing

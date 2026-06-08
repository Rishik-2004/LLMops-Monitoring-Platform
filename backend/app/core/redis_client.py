"""
Redis client configuration
"""

import redis.asyncio as aioredis
from app.core.config import settings
import structlog

logger = structlog.get_logger()

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    max_connections=settings.REDIS_POOL_SIZE,
)


async def get_redis():
    """Dependency to get Redis client"""
    return redis_client


class CacheManager:
    """Redis cache utility"""

    def __init__(self, client: aioredis.Redis):
        self.client = client

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(self, key: str, value: str, expire: int = 300):
        await self.client.setex(key, expire, value)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def increment(self, key: str, expire: int = 3600) -> int:
        pipe = self.client.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, expire)
        results = await pipe.execute()
        return results[0]

    async def get_json(self, key: str):
        import json
        val = await self.get(key)
        return json.loads(val) if val else None

    async def set_json(self, key: str, value: dict, expire: int = 300):
        import json
        await self.set(key, json.dumps(value), expire)


cache_manager = CacheManager(redis_client)

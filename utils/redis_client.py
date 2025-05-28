from contextlib import asynccontextmanager
from urllib.parse import urlparse

import redis.asyncio as redis

from config.settings import loaded_config


class RedisClient:
    """
    A class that manages Redis operations with an async client.
    """

    def __init__(self, payment_url=None):
        redis_url = payment_url or loaded_config.redis_payments_url
        parsed_url = urlparse(redis_url)
        self.redis_host = parsed_url.hostname
        self.redis_port = parsed_url.port
        self.redis_db = int(parsed_url.path.strip("/")) if parsed_url.path.strip("/") else 0

        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )

    @asynccontextmanager
    async def connect(self):
        """
        Provides an async Redis client via a context manager.
        """
        try:
            yield self.client
        finally:
            await self.client.close()

    async def add_key(self, key: str, value: str, expiration: int = None):
        """
        Adds a key-value pair to Redis with an optional expiration time.

        :param key: The key to add.
        :param value: The value to associate with the key.
        :param expiration: Expiration time in seconds (optional).
        """
        async with self.connect() as client:
            if expiration:
                await client.set(key, value, ex=expiration)
            else:
                await client.set(key, value)

    async def delete_key(self, key: str):
        """
        Deletes a key from Redis.

        :param key: The key to delete.
        """
        async with self.connect() as client:
            await client.delete(key)

    async def exists_key(self, key: str) -> bool:
        """
        Deletes a key from Redis.

        :param key: The key to delete.
        """
        async with self.connect() as client:
            return await client.exists(key)

    async def get_key(self, key: str):
        """
        Retrieves the value of a key from Redis.

        :param key: The key to retrieve.
        :return: The value of the key, or None if the key does not exist.
        """
        async with self.connect() as client:
            value = await client.get(key)
            try:
                return value.decode('utf-8') if value else None
            except Exception as e:
                return value

    async def get_keys(self, pattern: str):
        """
        Retrieve all keys based on pattern

        :param pattern:
        :return: Keys matching pattern
        """
        keys = []
        try:
            async with self.connect() as client:
                async for key in client.scan_iter(match=pattern):
                    try:
                        keys.append(key.decode())
                    except Exception as exp:
                        keys.append(key)
        except Exception as e:
            pass
        return keys

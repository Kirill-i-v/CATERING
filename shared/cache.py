"""
CACHE PROPERTIES:
    set(key: str, value: dict)
    get(key: str)
    delete(key: str)
"""

import json
import redis
from dataclasses import asdict, dataclass
from typing import Any
from django.conf import settings


class CacheService:
    def __init__(self, connection_string: str | None = None):
        self.connection: redis.Redis = redis.Redis.from_url(
            connection_string or settings.CACHE_CONNECTION_STRING
        )

    @staticmethod
    def _build_key(namespace: str, key: str):
        return f"{namespace}:{key}"

    def set(
        self, namespace: str, key: Any, instance: dict | Any, ttl: int | None = 259200
    ):
        if not isinstance(instance, dict):
            instance = asdict(instance)

        payload: str = json.dumps(instance)
        self.connection.set(
            name=self._build_key(namespace, str(key)), value=payload, ex=ttl
        )

    def get(self, namespace: str, key: Any) -> dict:
        result: str = self.connection.get(self._build_key(namespace, str(key)))  # type: ignore
        return json.loads(result)

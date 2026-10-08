import hashlib
import json
from typing import Any

from app.core.config import settings

_redis_client: Any = None


def get_redis_client() -> Any | None:
    global _redis_client
    if settings.REDIS_URL is None:
        return None
    if _redis_client is None:
        from redis import Redis

        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def get_cached_catalog(signature: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    client.set("catalog:version", 1, nx=True)
    version = client.get("catalog:version")
    key = f"catalog:{version}:{hashlib.sha256(signature.encode()).hexdigest()}"
    value = client.get(key)
    return json.loads(value) if value is not None else None


def set_cached_catalog(signature: str, value: Any) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.set("catalog:version", 1, nx=True)
    version = client.get("catalog:version")
    key = f"catalog:{version}:{hashlib.sha256(signature.encode()).hexdigest()}"
    client.set(key, json.dumps(value), ex=60)


def invalidate_catalog_cache() -> None:
    client = get_redis_client()
    if client is not None:
        client.incr("catalog:version")

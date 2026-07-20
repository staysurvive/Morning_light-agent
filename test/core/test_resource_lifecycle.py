from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src import main
from src.infra import redis_cache


@pytest.mark.asyncio
async def test_redis_client_and_external_pool_are_closed(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(redis_cache, "_redis_client", client)

    await redis_cache.close_redis_client()

    client.aclose.assert_awaited_once_with(close_connection_pool=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("raise_during_lifespan", [False, True])
async def test_lifespan_always_closes_all_resources(monkeypatch, raise_during_lifespan):
    closed = []

    monkeypatch.setattr(main, "setup_logger", lambda: None)
    monkeypatch.setattr(main, "ensure_bucket_exists", lambda: True)
    monkeypatch.setattr(
        main,
        "close_redis_client",
        AsyncMock(side_effect=lambda: closed.append("redis")),
    )
    monkeypatch.setattr(main, "close_minio_client", lambda: closed.append("minio"))
    monkeypatch.setattr(
        main,
        "engine",
        SimpleNamespace(
            dispose=AsyncMock(side_effect=lambda: closed.append("database"))
        ),
    )

    if raise_during_lifespan:
        with pytest.raises(RuntimeError, match="stop"):
            async with main.lifespan(main.app):
                raise RuntimeError("stop")
    else:
        async with main.lifespan(main.app):
            pass

    assert closed == ["redis", "minio", "database"]


@pytest.mark.asyncio
async def test_lifespan_continues_cleanup_after_redis_close_failure(monkeypatch):
    closed = []

    async def close_redis():
        closed.append("redis")
        raise RuntimeError("redis close failed")

    monkeypatch.setattr(main, "setup_logger", lambda: None)
    monkeypatch.setattr(main, "ensure_bucket_exists", lambda: True)
    monkeypatch.setattr(main, "close_redis_client", close_redis)
    monkeypatch.setattr(main, "close_minio_client", lambda: closed.append("minio"))
    monkeypatch.setattr(
        main,
        "engine",
        SimpleNamespace(
            dispose=AsyncMock(side_effect=lambda: closed.append("database"))
        ),
    )

    with pytest.raises(RuntimeError, match="redis close failed"):
        async with main.lifespan(main.app):
            pass

    assert closed == ["redis", "minio", "database"]

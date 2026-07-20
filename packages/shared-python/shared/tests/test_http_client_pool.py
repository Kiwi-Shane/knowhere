from __future__ import annotations

import pytest

import shared.services.http.client_pool as client_pool


def test_shared_sync_client_does_not_follow_redirects_by_default() -> None:
    client = client_pool.get_sync_client()
    try:
        assert client.follow_redirects is False
    finally:
        client_pool.close_sync_client()


@pytest.mark.asyncio
async def test_shared_async_client_does_not_follow_redirects_by_default() -> None:
    client = client_pool.get_async_client()
    try:
        assert client.follow_redirects is False
    finally:
        await client_pool.close_async_client()

"""Tests for client teardown in `You.__exit__` / `You.__aexit__`.

Both exits close *both* transports, so a sync `with` block also disposes of
the SDK-owned async client (and vice versa). Two properties matter:

  1. SDK-owned clients get closed; caller-supplied ones do not.
  2. A failure while closing never replaces the exception propagating out of
     the `with` block — that would hide the error the user actually cares
     about behind an unrelated teardown error.
"""

import httpx
import pytest

from youdotcom import You


def _mock_transport() -> httpx.MockTransport:
    """A transport with no connection pool.

    The `_Boom*` clients below raise on close by design, so they can never be
    disposed of normally. Backing every client here with a mock transport means
    there is no pool to leak when that happens.
    """
    return httpx.MockTransport(lambda request: httpx.Response(200, json={}))


class _RecordingClient(httpx.Client):
    closed = False

    def __init__(self):
        super().__init__(transport=_mock_transport())

    def close(self):
        type(self).closed = True
        super().close()


class _RecordingAsyncClient(httpx.AsyncClient):
    closed = False

    def __init__(self):
        super().__init__(transport=_mock_transport())

    async def aclose(self):
        type(self).closed = True
        await super().aclose()


class _BoomClient(httpx.Client):
    def __init__(self):
        super().__init__(transport=_mock_transport())

    def close(self):
        raise RuntimeError("sync close boom")


class _BoomAsyncClient(httpx.AsyncClient):
    def __init__(self):
        super().__init__(transport=_mock_transport())

    async def aclose(self):
        raise RuntimeError("async close boom")


def _client() -> httpx.Client:
    return httpx.Client(transport=_mock_transport())


def _async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=_mock_transport())


def _owned(you: You) -> You:
    """Mark both transports as SDK-owned so the exit paths will close them."""
    you.sdk_configuration.client_supplied = False
    you.sdk_configuration.async_client_supplied = False
    return you


class TestSyncExit:
    def test_closes_both_clients(self):
        sync_client = _RecordingClient()
        async_client = _RecordingAsyncClient()
        _RecordingClient.closed = _RecordingAsyncClient.closed = False

        with _owned(You(api_key_auth="k", client=sync_client, async_client=async_client)):
            pass

        assert _RecordingClient.closed
        assert _RecordingAsyncClient.closed

    def test_drops_references(self):
        with _owned(You(api_key_auth="k", client=_client())) as you:
            pass
        assert you.sdk_configuration.client is None
        assert you.sdk_configuration.async_client is None

    def test_supplied_clients_are_not_closed(self):
        sync_client = _RecordingClient()
        _RecordingClient.closed = False

        # client_supplied stays True — the caller owns this transport.
        with You(api_key_auth="k", client=sync_client):
            pass

        assert not _RecordingClient.closed
        sync_client.close()

    def test_async_close_failure_does_not_mask_body_exception(self):
        you = _owned(
            You(api_key_auth="k", client=_client(), async_client=_BoomAsyncClient())
        )
        with pytest.raises(ValueError, match="the real error"):
            with you:
                raise ValueError("the real error")

    def test_sync_close_failure_does_not_mask_body_exception(self):
        you = _owned(You(api_key_auth="k", client=_BoomClient()))
        with pytest.raises(ValueError, match="the real error"):
            with you:
                raise ValueError("the real error")

    def test_close_failure_does_not_raise_on_clean_exit(self):
        you = _owned(You(api_key_auth="k", client=_BoomClient()))
        with you:
            pass  # must not raise


class TestAsyncExit:
    @pytest.mark.asyncio
    async def test_closes_both_clients(self):
        sync_client = _RecordingClient()
        async_client = _RecordingAsyncClient()
        _RecordingClient.closed = _RecordingAsyncClient.closed = False

        async with _owned(
            You(api_key_auth="k", client=sync_client, async_client=async_client)
        ):
            pass

        assert _RecordingClient.closed
        assert _RecordingAsyncClient.closed

    @pytest.mark.asyncio
    async def test_drops_references(self):
        async with _owned(You(api_key_auth="k", async_client=_async_client())) as you:
            pass
        assert you.sdk_configuration.client is None
        assert you.sdk_configuration.async_client is None

    @pytest.mark.asyncio
    async def test_close_failure_does_not_mask_body_exception(self):
        you = _owned(You(api_key_auth="k", async_client=_BoomAsyncClient()))
        with pytest.raises(ValueError, match="the real error"):
            async with you:
                raise ValueError("the real error")

    @pytest.mark.asyncio
    async def test_sync_exit_inside_running_loop_does_not_raise(self):
        """`with You(...)` used from async code must not trip over the live loop."""
        with _owned(You(api_key_auth="k", async_client=_async_client())):
            pass

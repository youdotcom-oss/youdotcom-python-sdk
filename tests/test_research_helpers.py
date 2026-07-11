"""Tests for research background-mode helpers in youdotcom.research_helpers."""

import os
import uuid

import httpx
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.models import (
    ResearchEffort,
    TaskDetail,
    TaskResponse,
)
from youdotcom.research_helpers import (
    RawStreamEvent,
    research_and_wait,
    research_and_wait_async,
    research_background,
    research_background_async,
    poll_research_task,
    poll_research_task_async,
    stream_research_events_raw,
    stream_research_events_raw_async,
    _decode_raw_event,
)


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return "test-api-key"


# ---------------------------------------------------------------------------
# research_background[Async]: assert TaskResponse return type without
# forcing callers to narrow Union[ResearchResponse, TaskResponse].
# ---------------------------------------------------------------------------

class TestResearchBackground:
    def test_research_background_returns_task_response(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research-background")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = research_background(
                you,
                input="Compare NVIDIA, AMD, and Intel revenue over 5 years",
                research_effort=ResearchEffort.DEEP,
                server_url=server_url,
            )

        assert isinstance(res, TaskResponse)
        assert res.task_id == "00000000-0000-0000-0000-000000000001"
        assert res.type == "research"
        assert res.status.value == "queued"

    @pytest.mark.asyncio
    async def test_research_background_async_returns_task_response(self, server_url, api_key):
        async_client = httpx.AsyncClient(
            headers={
                "x-speakeasy-test-name": "post_/v1/research-background",
                "x-speakeasy-test-instance-id": str(uuid.uuid4()),
            },
            follow_redirects=True,
        )

        async with You(
            server_url=server_url, async_client=async_client, api_key_auth=api_key
        ) as you:
            res = await research_background_async(
                you,
                input="Compare NVIDIA, AMD, and Intel revenue over 5 years",
                research_effort=ResearchEffort.DEEP,
                server_url=server_url,
            )

        assert isinstance(res, TaskResponse)
        assert res.task_id == "00000000-0000-0000-0000-000000000001"


# ---------------------------------------------------------------------------
# poll_research_task[Async]: poll get_research_task until terminal and
# return the completed TaskDetail with result payload.
# ---------------------------------------------------------------------------

class TestPollResearchTask:
    def test_poll_returns_completed_task_detail(self, server_url, api_key):
        client = create_test_http_client("get_/v1/research/{task_id}")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            detail = poll_research_task(
                you,
                "00000000-0000-0000-0000-000000000001",
                interval_s=0.01,
                timeout_s=2.0,
            )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"
        assert detail.result is not None

    @pytest.mark.asyncio
    async def test_poll_async_returns_completed_task_detail(self, server_url, api_key):
        async_client = httpx.AsyncClient(
            headers={
                "x-speakeasy-test-name": "get_/v1/research/{task_id}",
                "x-speakeasy-test-instance-id": str(uuid.uuid4()),
            },
            follow_redirects=True,
        )

        async with You(
            server_url=server_url, async_client=async_client, api_key_auth=api_key
        ) as you:
            detail = await poll_research_task_async(
                you,
                "00000000-0000-0000-0000-000000000001",
                interval_s=0.01,
                timeout_s=2.0,
            )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"


# ---------------------------------------------------------------------------
# research_and_wait: submit background + poll + return TaskDetail.
# The Result model uses extra="allow" so detail.result.model_dump()
# recovers the full payload; the helper returns TaskDetail.
# ---------------------------------------------------------------------------

class TestResearchAndWait:
    def test_and_wait_poll_returns_completed_detail(self, server_url, api_key):
        client_post = create_test_http_client("post_/v1/research-background")

        with You(server_url=server_url, client=client_post, api_key_auth=api_key) as you:
            detail = research_and_wait(
                you,
                mode="poll",
                interval_s=0.01,
                timeout_s=2.0,
                server_url=server_url,
                input="Compare NVIDIA, AMD, and Intel revenue over 5 years",
                research_effort=ResearchEffort.DEEP,
            )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"


# ---------------------------------------------------------------------------
# Tolerant SSE stream raw events. Verifies:
#   (a) helper accepts documented event types as before;
#   (b) helper accepts unknown event types without raising
#       pydantic.ValidationError, surfacing them as RawStreamEvent(event="...").
# Uses an httpx.MockTransport to inject a fake SSE server response -- this
# path doesn't depend on the Go mockserver so unknown event names can be
# emitted safely without adding new mockserver fixtures.
# ---------------------------------------------------------------------------

class TestStreamResearchEventsTolerant:
    def test_tolerant_stream_yields_all_events_with_unknown_name(self):
        # Inject a fake SSE stream with one workflow-internal event type
        # (research.searching) that's NOT in the documented enum. The strict
        # speakeasy decoder would raise ValidationError on it; our tolerant
        # helper must surface it as RawStreamEvent(event="research.searching").
        recorded_ua: dict = {}

        def record_send(request):
            recorded_ua["value"] = request.headers.get("User-Agent")
            chunks = [
                b"id: 0\nevent: connected\ndata: "
                b'{"type":"connected","task_id":"abc","status":"running"}\n\n',
                b"id: 1\nevent: research.searching\ndata: "
                b'{"query":"markets","phase":"searching"}\n\n',
                b"id: 2\nevent: response.done\ndata: "
                b'{"type":"response.done","task_id":"abc","status":"completed","sequence":2}\n\n',
            ]
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=chunks,
            )

        transport = httpx.MockTransport(record_send)
        sdk_client = httpx.Client(
            transport=transport,
            headers={
                "x-speakeasy-test-name": "get_/v1/research/{task_id}/stream",
                "x-speakeasy-test-instance-id": str(uuid.uuid4()),
            },
        )
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )

        events = list(
            stream_research_events_raw(
                you, "00000000-0000-0000-0000-000000000001",
            )
        )

        assert [e.event for e in events] == [
            "connected", "research.searching", "response.done",
        ]
        # Validate that the unknown event came through without raising.
        assert isinstance(events[1], RawStreamEvent)
        assert events[1].data == {"query": "markets", "phase": "searching"}
        # And confirm the SDK still set User-Agent on the underlying request
        # (the YDCUserAgentOverrideHook ran before send).
        assert recorded_ua["value"] == f"youdotcom-python-sdk/{you.sdk_configuration.sdk_version}"


# ---------------------------------------------------------------------------
# YDCUserAgentOverrideHook must respect sdk_configuration.user_agent
# overrides instead of unconditionally rewriting the header.
# ---------------------------------------------------------------------------

class TestYDCUserAgentOverrideHook:
    def test_default_user_agent_uses_youdotcom_format(self, server_url):
        # Default flow: hook returns youdotcom-python-sdk/<version>.
        client = create_test_http_client("post_/v1/research")

        you = You(server_url=server_url, client=client, api_key_auth="test")
        # The default config.user_agent is the speakeasy-encoded value.
        # Build a synthetic request and run the hook against it.
        from youdotcom._hooks.registration import YDCUserAgentOverrideHook
        from youdotcom._hooks.types import HookContext

        request = httpx.Request(
            "POST", f"{server_url}/v1/research",
            json={"input": "hello"},
        )
        hook = YDCUserAgentOverrideHook()
        hook_ctx = HookContext(
            config=you.sdk_configuration,
            base_url=server_url,
            operation_id="post_/v1/research",
            oauth2_scopes=None,
            security_source=None,
            tags=None,
            extensions=None,
        )
        result = hook.before_request(hook_ctx, request)
        assert result.headers.get("User-Agent") == f"youdotcom-python-sdk/{you.sdk_configuration.sdk_version}"

    def test_custom_user_agent_is_passthrough(self, server_url):
        client = create_test_http_client("post_/v1/research")
        you = You(server_url=server_url, client=client, api_key_auth="test")
        you.sdk_configuration.user_agent = "youdotcom-temporal/0.1.0"

        from youdotcom._hooks.registration import YDCUserAgentOverrideHook
        from youdotcom._hooks.types import HookContext

        request = httpx.Request(
            "POST", f"{server_url}/v1/research",
            json={"input": "hello"},
        )
        hook = YDCUserAgentOverrideHook()
        hook_ctx = HookContext(
            config=you.sdk_configuration,
            base_url=server_url,
            operation_id="post_/v1/research",
            oauth2_scopes=None,
            security_source=None,
            tags=None,
            extensions=None,
        )
        result = hook.before_request(hook_ctx, request)
        assert result.headers.get("User-Agent") == "youdotcom-temporal/0.1.0"


# ---------------------------------------------------------------------------
# _decode_raw_event sanity: known and unknown shapes.
# ---------------------------------------------------------------------------

class TestDecodeRawEvent:
    def test_known_event(self):
        import json
        ev = _decode_raw_event(json.dumps({"id": "1", "event": "response.done", "data": {"status": "completed"}}))
        assert isinstance(ev, RawStreamEvent)
        assert ev.id == "1"
        assert ev.event == "response.done"
        assert ev.data == {"status": "completed"}

    def test_unknown_event(self):
        import json
        ev = _decode_raw_event(json.dumps({"id": "2", "event": "some.workflow.step", "data": {"k": "v"}}))
        assert ev.event == "some.workflow.step"
        assert ev.data == {"k": "v"}


# ---------------------------------------------------------------------------
# Error path tests: poll timeout, poll failed status, and stream mode.
# ---------------------------------------------------------------------------

class TestPollResearchTaskErrorPaths:
    def test_poll_timeout_raises_timeout_error(self):
        """poll_research_task must raise TimeoutError when the task never
        reaches a terminal state within timeout_s."""
        import json

        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000001",
                    "task_type": "research",
                    "status": "running",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:00:01Z",
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete"):
            poll_research_task(
                you,
                "00000000-0000-0000-0000-000000000001",
                interval_s=0.01,
                timeout_s=0.05,
            )

    def test_poll_failed_status_raises_runtime_error(self):
        """poll_research_task must raise RuntimeError when the task ends
        in a non-completed terminal state (failed)."""
        import json

        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000002",
                    "task_type": "research",
                    "status": "failed",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:00:05Z",
                    "error": "upstream search timeout",
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="non-completed state: failed"):
            poll_research_task(
                you,
                "00000000-0000-0000-0000-000000000002",
                interval_s=0.01,
                timeout_s=2.0,
            )


class TestResearchAndWaitStreamMode:
    def test_and_wait_stream_returns_completed_detail(self):
        """research_and_wait with mode='stream' must read the SSE stream
        until response.done, then fetch the final TaskDetail via poll."""
        import json

        call_log: list = []

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                call_log.append("stream")
                chunks = [
                    b'id: 0\nevent: connected\ndata: {"type":"connected","task_id":"abc","status":"running"}\n\n',
                    b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
                ]
                return httpx.Response(
                    200,
                    headers={"content-type": "text/event-stream"},
                    content=chunks,
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                call_log.append("submit")
                return httpx.Response(
                    200,
                    headers={"content-type": "application/json"},
                    content=json.dumps({
                        "task_id": "00000000-0000-0000-0000-000000000001",
                        "type": "research",
                        "status": "queued",
                        "stream_url": "/v1/research/00000000-0000-0000-0000-000000000001/stream",
                        "created_at": "2026-07-09T00:00:00Z",
                    }),
                )
            # GET /v1/research/{task_id} — final poll after stream
            call_log.append("poll")
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000001",
                    "task_type": "research",
                    "status": "completed",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:02:30Z",
                    "completed_at": "2026-07-09T00:02:30Z",
                    "result": {"output": {"content": "done", "content_type": "text", "sources": []}},
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            mode="stream",
            interval_s=0.01,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"
        # Verify the call sequence: submit -> stream -> poll
        assert call_log == ["submit", "stream", "poll"]


class TestPollResearchTaskAsyncErrorPaths:
    @pytest.mark.asyncio
    async def test_poll_async_timeout_raises_timeout_error(self):
        """Async mirror of the sync timeout test."""
        import json

        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000003",
                    "task_type": "research",
                    "status": "running",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:00:01Z",
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete"):
            await poll_research_task_async(
                you,
                "00000000-0000-0000-0000-000000000003",
                interval_s=0.01,
                timeout_s=0.05,
            )

    @pytest.mark.asyncio
    async def test_poll_async_failed_status_raises_runtime_error(self):
        """Async mirror of the sync failed-status test."""
        import json

        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000004",
                    "task_type": "research",
                    "status": "failed",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:00:05Z",
                    "error": "upstream search timeout",
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="non-completed state: failed"):
            await poll_research_task_async(
                you,
                "00000000-0000-0000-0000-000000000004",
                interval_s=0.01,
                timeout_s=2.0,
            )


# ---------------------------------------------------------------------------
# Async streaming: mirror the sync TestStreamResearchEventsTolerant and
# TestResearchAndWaitStreamMode. These also exercise the try/finally cleanup
# path (replacing the broken contextlib.aclosing that called aclose()).

class _AsyncChunks(httpx.AsyncByteStream):
    """Wrap a list of bytes chunks in an AsyncByteStream for MockTransport
    + AsyncClient streaming responses (httpx MockTransport returns sync
    streams by default, which AsyncClient rejects for stream=True)."""

    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk


class TestStreamResearchEventsTolerantAsync:
    @pytest.mark.asyncio
    async def test_async_tolerant_stream_yields_all_events_with_unknown_name(self):
        """Async mirror of TestStreamResearchEventsTolerant — injects a
        fake SSE stream with an unknown event type and verifies it surfaces
        as RawStreamEvent without raising."""
        recorded_ua: dict = {}

        def record_send(request):
            recorded_ua["value"] = request.headers.get("User-Agent")
            chunks = [
                b"id: 0\nevent: connected\ndata: "
                b'{"type":"connected","task_id":"abc","status":"running"}\n\n',
                b"id: 1\nevent: research.searching\ndata: "
                b'{"query":"markets","phase":"searching"}\n\n',
                b"id: 2\nevent: response.done\ndata: "
                b'{"type":"response.done","task_id":"abc","status":"completed","sequence":2}\n\n',
            ]
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                stream=_AsyncChunks(chunks),
            )

        transport = httpx.MockTransport(record_send)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        events = [
            evt
            async for evt in stream_research_events_raw_async(
                you, "00000000-0000-0000-0000-000000000001",
            )
        ]

        assert [e.event for e in events] == [
            "connected", "research.searching", "response.done",
        ]
        assert isinstance(events[1], RawStreamEvent)
        assert events[1].data == {"query": "markets", "phase": "searching"}
        assert recorded_ua["value"] == f"youdotcom-python-sdk/{you.sdk_configuration.sdk_version}"


class TestResearchAndWaitStreamModeAsync:
    @pytest.mark.asyncio
    async def test_async_and_wait_stream_returns_completed_detail(self):
        """Async mirror of TestResearchAndWaitStreamMode — verifies the
        submit -> stream -> poll sequence and that the stream cleanup
        (try/finally close) does not raise."""
        import json

        call_log: list = []

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                call_log.append("stream")
                chunks = [
                    b'id: 0\nevent: connected\ndata: {"type":"connected","task_id":"abc","status":"running"}\n\n',
                    b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
                ]
                return httpx.Response(
                    200,
                    headers={"content-type": "text/event-stream"},
                    stream=_AsyncChunks(chunks),
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                call_log.append("submit")
                return httpx.Response(
                    200,
                    headers={"content-type": "application/json"},
                    content=json.dumps({
                        "task_id": "00000000-0000-0000-0000-000000000001",
                        "type": "research",
                        "status": "queued",
                        "stream_url": "/v1/research/00000000-0000-0000-0000-000000000001/stream",
                        "created_at": "2026-07-09T00:00:00Z",
                    }),
                )
            call_log.append("poll")
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000001",
                    "task_type": "research",
                    "status": "completed",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:02:30Z",
                    "completed_at": "2026-07-09T00:02:30Z",
                    "result": {"output": {"content": "done", "content_type": "text", "sources": []}},
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        detail = await research_and_wait_async(
            you,
            mode="stream",
            interval_s=0.01,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"
        assert call_log == ["submit", "stream", "poll"]


class TestModeValidation:
    def test_invalid_mode_raises_value_error(self):
        """research_and_wait with an invalid mode must raise ValueError
        before making any HTTP request."""
        transport = httpx.MockTransport(lambda req: httpx.Response(500))
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )
        with pytest.raises(ValueError, match="mode must be 'poll' or 'stream'"):
            research_and_wait(you, mode="bogus", input="test")

    @pytest.mark.asyncio
    async def test_invalid_mode_raises_value_error_async(self):
        """Async mirror — research_and_wait_async with invalid mode."""
        transport = httpx.MockTransport(lambda req: httpx.Response(500))
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )
        with pytest.raises(ValueError, match="mode must be 'poll' or 'stream'"):
            await research_and_wait_async(you, mode="bogus", input="test")


class TestResearchAndWaitAsyncPollMode:
    @pytest.mark.asyncio
    async def test_async_and_wait_poll_returns_completed_detail(self):
        """Async poll-mode test for research_and_wait_async — mirrors the
        sync TestResearchAndWait.test_and_wait_poll_returns_completed_detail
        using httpx.MockTransport on an AsyncClient."""
        import json

        def handler(request):
            url = str(request.url)
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200,
                    headers={"content-type": "application/json"},
                    content=json.dumps({
                        "task_id": "00000000-0000-0000-0000-000000000001",
                        "type": "research",
                        "status": "queued",
                        "stream_url": "/v1/research/00000000-0000-0000-0000-000000000001/stream",
                        "created_at": "2026-07-09T00:00:00Z",
                    }),
                )
            # GET /v1/research/{task_id} — poll returns completed
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "id": "00000000-0000-0000-0000-000000000001",
                    "task_type": "research",
                    "status": "completed",
                    "created_at": "2026-07-09T00:00:00Z",
                    "updated_at": "2026-07-09T00:02:30Z",
                    "completed_at": "2026-07-09T00:02:30Z",
                    "result": {"output": {"content": "done", "content_type": "text", "sources": []}},
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        detail = await research_and_wait_async(
            you,
            mode="poll",
            interval_s=0.01,
            timeout_s=2.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

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
    stream_research,
    stream_research_async,
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


class TestResearchBackgroundTypeError:
    """Tests that research_background raises TypeError when the server
    returns a ResearchResponse instead of TaskResponse (e.g. when the
    server-side background-mode flag is disabled)."""

    def test_research_background_raises_type_error_on_sync_response(self):
        """When the server ignores background=true and returns a
        ResearchResponse, research_background must raise TypeError."""
        import json

        def handler(request):
            # Server ignores background=true, returns a sync ResearchResponse
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "output": {
                        "content_type": "text",
                        "content": "The capital of France is Paris.",
                        "sources": [],
                    },
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url="http://mock.local",
            client=sdk_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(TypeError, match="TaskResponse"):
            research_background(
                you,
                input="What is the capital of France?",
                research_effort=ResearchEffort.STANDARD,
            )

    @pytest.mark.asyncio
    async def test_research_background_async_raises_type_error_on_sync_response(self):
        """Async mirror: TypeError when server returns ResearchResponse."""
        import json

        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "output": {
                        "content_type": "text",
                        "content": "The capital of France is Paris.",
                        "sources": [],
                    },
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_async_client = httpx.AsyncClient(transport=transport)
        you = You(
            server_url="http://mock.local",
            async_client=sdk_async_client,
            api_key_auth="test-api-key",
        )

        with pytest.raises(TypeError, match="TaskResponse"):
            await research_background_async(
                you,
                input="What is the capital of France?",
                research_effort=ResearchEffort.STANDARD,
            )
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
    def test_research_and_wait_returns_completed_detail(self):
        """research_and_wait submits, streams until terminal event,
        then fetches the final TaskDetail."""
        import json

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
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
            # GET /v1/research/{task_id} — final fetch after terminal event
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
            timeout_s=5.0,
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
            stream_research(
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
            async for evt in stream_research_async(
                you, "00000000-0000-0000-0000-000000000001",
            )
        ]

        assert [e.event for e in events] == [
            "connected", "research.searching", "response.done",
        ]
        assert isinstance(events[1], RawStreamEvent)
        assert events[1].data == {"query": "markets", "phase": "searching"}
        assert recorded_ua["value"] == f"youdotcom-python-sdk/{you.sdk_configuration.sdk_version}"


class TestResearchAndWaitAsync:
    @pytest.mark.asyncio
    async def test_async_research_and_wait_returns_completed_detail(self):
        """Async research_and_wait: submit, stream until terminal, fetch detail."""
        import json

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
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
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

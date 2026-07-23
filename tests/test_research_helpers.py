"""Tests for research background-mode helpers in youdotcom.research_helpers."""

import asyncio
import json
import os
import time
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
    _resolve_default_timeout,
    _FRONTIER_TIMEOUT_S,
    _DEFAULT_POLL_TIMEOUT_S,
)


# ---------------------------------------------------------------------------
# Shared test helpers: handler factories + mock stream classes.
# ---------------------------------------------------------------------------

_TASK_RESPONSE_JSON = json.dumps({
    "task_id": "00000000-0000-0000-0000-000000000001",
    "type": "research",
    "status": "queued",
    "stream_url": "/v1/research/00000000-0000-0000-0000-000000000001/stream",
    "created_at": "2026-07-09T00:00:00Z",
})

_DEFAULT_RESULT = {"output": {"content": "done", "content_type": "text", "sources": []}}

_CONNECTED_CHUNK = b'id: 0\nevent: connected\ndata: {"type":"connected","task_id":"abc","status":"running"}\n\n'


def _make_task_detail_json(status: str = "completed", result: dict | None = None) -> str:
    """Build a TaskDetail JSON body for GET /v1/research/{task_id} responses."""
    detail: dict = {
        "id": "00000000-0000-0000-0000-000000000001",
        "task_type": "research",
        "status": status,
        "created_at": "2026-07-09T00:00:00Z",
        "updated_at": "2026-07-09T00:02:30Z",
    }
    if status == "completed":
        detail["completed_at"] = "2026-07-09T00:02:30Z"
    if result is not None:
        detail["result"] = result
    return json.dumps(detail)


class _AsyncChunks(httpx.AsyncByteStream):
    """Wrap a list of bytes chunks in an AsyncByteStream for MockTransport
    + AsyncClient streaming responses."""

    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk


class _BlockingStream(httpx.SyncByteStream):
    """Yields one event then raises ReadTimeout to simulate a stalled server
    that stops sending data within the read timeout."""

    def __iter__(self):
        yield _CONNECTED_CHUNK
        raise httpx.ReadTimeout("read timeout")


class _BlockingAsyncStream(httpx.AsyncByteStream):
    """Yields one event then blocks so asyncio.wait_for times out."""

    async def __aiter__(self):
        yield _CONNECTED_CHUNK
        await asyncio.sleep(100)


def _make_wait_handler(
    *,
    stream_chunks: list[bytes] | None = None,
    stream_obj: httpx.SyncByteStream | httpx.AsyncByteStream | None = None,
    final_status: str = "completed",
    final_result: dict | None = _DEFAULT_RESULT,
    is_async: bool = False,
):
    """Create a MockTransport handler for research_and_wait tests.

    Returns SSE stream, POST TaskResponse, and GET TaskDetail responses.
    Pass ``stream_obj`` for custom stream behavior (e.g. ``_BlockingStream``).
    Pass ``stream_chunks`` for simple list-of-bytes streams.
    """
    final_json = _make_task_detail_json(status=final_status, result=final_result)

    def handler(request):
        url = str(request.url)
        if url.endswith("/stream") or "/stream?" in url:
            if stream_obj is not None:
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"}, stream=stream_obj,
                )
            if stream_chunks is not None:
                if is_async:
                    return httpx.Response(
                        200, headers={"content-type": "text/event-stream"},
                        stream=_AsyncChunks(stream_chunks),
                    )
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"}, content=stream_chunks,
                )
            return httpx.Response(200, content="{}")
        if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_TASK_RESPONSE_JSON,
            )
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=final_json,
        )

    return handler


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


# ---------------------------------------------------------------------------
# poll_research_task[Async]: poll GET /v1/research/{task_id} until terminal.
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
        handler = _make_wait_handler(stream_chunks=[
            _CONNECTED_CHUNK,
            b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
        ])
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
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

    def test_research_and_wait_error_event_raises_runtime_error(self):
        """research_and_wait raises RuntimeError when the stream emits an
        error terminal event."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: error\ndata: {"type":"error","task_id":"abc","message":"internal error"}\n\n',
            ],
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="non-completed state"):
            research_and_wait(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_research_and_wait_ok_event_but_get_non_completed_raises(self):
        """When the stream emits a terminal OK event (response.done) but the
        follow-up GET returns a non-completed status, research_and_wait raises
        RuntimeError. This covers the defensive branch in _resolve_from_final_get."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
            ],
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="stream signalled completion but GET returned status=running after 3 attempts"):
            research_and_wait(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_research_and_wait_ok_event_but_get_failed_raises_immediately(self):
        """When the stream emits a terminal OK event but the follow-up GET
        returns a terminal non-completed status (failed), research_and_wait
        raises RuntimeError immediately without exhausting re-poll attempts."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
            ],
            final_status="failed",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="ended in non-completed state: failed"):
            research_and_wait(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_research_and_wait_ok_event_repoll_succeeds(self):
        """When the stream emits a terminal OK event and the first GET returns
        running (backend commit race), research_and_wait re-polls and returns
        the completed detail once the status catches up."""
        call_count = {"get": 0}

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"},
                    content=[
                        _CONNECTED_CHUNK,
                        b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
                    ],
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"}, content=_TASK_RESPONSE_JSON,
                )
            # GET: first call returns running, second returns completed
            call_count["get"] += 1
            if call_count["get"] == 1:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_make_task_detail_json(status="running", result=None),
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"
        assert call_count["get"] == 2  # first running, second completed

    def test_research_and_wait_timeout_raises_timeout_error(self):
        """research_and_wait raises TimeoutError when the stream never sends
        a terminal event within timeout_s. The _BlockingStream simulates a
        stalled server by raising httpx.ReadTimeout after the first event."""
        handler = _make_wait_handler(
            stream_obj=_BlockingStream(),
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete within"):
            research_and_wait(
                you,
                timeout_s=0.5,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_research_and_wait_timeout_falls_back_to_get(self):
        """When the stream times out (ReadTimeout) but the task has completed,
        the final GET fallback returns the completed detail."""
        handler = _make_wait_handler(
            stream_obj=_BlockingStream(),
            final_status="completed",
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            timeout_s=0.5,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    def test_research_and_wait_stream_close_falls_back_to_get(self):
        """When the stream closes without a terminal event, research_and_wait
        does a final GET and returns the detail if completed."""
        handler = _make_wait_handler(
            stream_chunks=[_CONNECTED_CHUNK],
            final_status="completed",
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    def test_research_and_wait_stream_close_task_running_raises_timeout(self):
        """When the stream closes without a terminal event and the final GET
        shows the task is still running, research_and_wait raises TimeoutError."""
        handler = _make_wait_handler(
            stream_chunks=[_CONNECTED_CHUNK],
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="still running"):
            research_and_wait(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_research_and_wait_total_deadline_not_stall_timeout(self):
        """research_and_wait enforces a total wall-clock deadline, not just a
        per-read stall timeout. If the server keeps sending non-terminal
        events forever, the total deadline fires and raises TimeoutError.
        This matches the async variant's asyncio.wait_for semantics."""
        class _NonTerminalStream(httpx.SyncByteStream):
            """Yields non-terminal events fast enough to not trip the per-read
            timeout, but never emits a terminal event."""
            def __iter__(self):
                for _ in range(10000):
                    yield b'id: 0\nevent: ping\ndata: {"type":"ping"}\n\n'
                    time.sleep(0.01)

        handler = _make_wait_handler(
            stream_obj=_NonTerminalStream(),
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete within"):
            research_and_wait(
                you,
                timeout_s=0.5,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_stream_open_transport_error_falls_back_to_poll(self):
        """When _open_raw_stream raises a TransportError (can't reach server),
        research_and_wait falls back to poll_research_task and returns the
        completed detail."""
        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                raise httpx.ConnectError("connection refused")
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_TASK_RESPONSE_JSON,
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    def test_stream_open_401_propagates_typed_error(self):
        """When _open_raw_stream gets a 401, the typed
        StreamResearchTaskUnauthorizedError propagates instead of falling
        back to polling."""
        from youdotcom.errors import StreamResearchTaskUnauthorizedError

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                return httpx.Response(
                    401,
                    headers={"content-type": "application/json"},
                    content='{"error": "unauthorized"}',
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_TASK_RESPONSE_JSON,
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="bad-key",
        )

        with pytest.raises(StreamResearchTaskUnauthorizedError):
            research_and_wait(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    def test_mid_stream_transport_error_falls_back_to_poll(self):
        """When a TransportError occurs mid-stream (dropped connection),
        research_and_wait falls back to poll_research_task."""
        class _DroppedStream(httpx.SyncByteStream):
            def __iter__(self):
                yield _CONNECTED_CHUNK
                raise httpx.RemoteProtocolError("connection dropped")

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"},
                    stream=_DroppedStream(),
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_TASK_RESPONSE_JSON,
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            timeout_s=5.0,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"


# ---------------------------------------------------------------------------
# Stream research tolerant decoder: verify that
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
# _resolve_default_timeout: auto-adjust timeout based on research_effort.
# ---------------------------------------------------------------------------

class TestResolveDefaultTimeout:
    def test_frontier_returns_4_hour_timeout(self):
        assert _resolve_default_timeout({"research_effort": ResearchEffort.FRONTIER}) == _FRONTIER_TIMEOUT_S

    def test_frontier_string_returns_4_hour_timeout(self):
        assert _resolve_default_timeout({"research_effort": "frontier"}) == _FRONTIER_TIMEOUT_S

    def test_standard_returns_default_timeout(self):
        assert _resolve_default_timeout({"research_effort": ResearchEffort.STANDARD}) == _DEFAULT_POLL_TIMEOUT_S

    def test_deep_returns_default_timeout(self):
        assert _resolve_default_timeout({"research_effort": ResearchEffort.DEEP}) == _DEFAULT_POLL_TIMEOUT_S

    def test_exhaustive_returns_default_timeout(self):
        assert _resolve_default_timeout({"research_effort": ResearchEffort.EXHAUSTIVE}) == _DEFAULT_POLL_TIMEOUT_S

    def test_no_effort_returns_default_timeout(self):
        assert _resolve_default_timeout({}) == _DEFAULT_POLL_TIMEOUT_S


# ---------------------------------------------------------------------------
# research_and_wait frontier auto-timeout: when timeout_s is omitted and
# research_effort=frontier, the helper should use 14400s (4 hours), not the
# 600s default. We verify by checking that a short stream timeout is NOT
# applied — instead the 4-hour deadline is used, so the stream consumes
# all events without a premature TimeoutError.
# ---------------------------------------------------------------------------

class TestResearchAndWaitFrontierAutoTimeout:
    def test_frontier_auto_timeout_completes_without_premature_timeout(self):
        """When research_effort=frontier and timeout_s is omitted, the
        auto-adjusted 4-hour timeout should not trip on a normal event
        sequence that would complete within seconds."""
        handler = _make_wait_handler(stream_chunks=[
            _CONNECTED_CHUNK,
            b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
        ])
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = research_and_wait(
            you,
            input="Evaluate the Gates Foundation's global-health impact",
            research_effort=ResearchEffort.FRONTIER,
            # timeout_s intentionally omitted — should auto-adjust to 14400
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    def test_explicit_timeout_overrides_auto_adjust(self):
        """When the user passes an explicit timeout_s, it takes precedence
        over the frontier auto-adjustment."""
        handler = _make_wait_handler(
            stream_obj=_BlockingStream(),
            final_status="running",
            final_result=None,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            client=httpx.Client(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete within 0.5"):
            research_and_wait(
                you,
                timeout_s=0.5,
                input="test query",
                research_effort=ResearchEffort.FRONTIER,
            )


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
# stream_research typed error mapping: non-200 responses must raise the
# same structured errors as the generated stream_research_task() method.
# ---------------------------------------------------------------------------

class TestStreamResearchTypedErrors:
    """Verify stream_research[_async] raise the same typed errors as the
    generated stream_research_task method for each status-code branch."""

    @staticmethod
    def _make_error_handler(status_code: int, body: dict | None = None):
        """Create a MockTransport handler that always returns an error response."""
        content = json.dumps(body or {"detail": "error"})
        def handler(request):
            return httpx.Response(
                status_code,
                headers={"content-type": "application/json"},
                content=content,
            )
        return handler

    @staticmethod
    def _sync_you(handler):
        return You(
            server_url="http://mock.local",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            api_key_auth="test-api-key",
        )

    @staticmethod
    def _async_you(handler):
        return You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            api_key_auth="test-api-key",
        )

    _TASK = "00000000-0000-0000-0000-000000000001"

    def test_401_raises_unauthorized_error(self):
        from youdotcom.errors import StreamResearchTaskUnauthorizedError
        with pytest.raises(StreamResearchTaskUnauthorizedError):
            list(stream_research(self._sync_you(self._make_error_handler(401)), self._TASK))

    def test_403_raises_forbidden_error(self):
        from youdotcom.errors import StreamResearchTaskForbiddenError
        with pytest.raises(StreamResearchTaskForbiddenError):
            list(stream_research(self._sync_you(self._make_error_handler(403)), self._TASK))

    def test_404_raises_not_found_error(self):
        from youdotcom.errors import StreamResearchTaskNotFoundError
        with pytest.raises(StreamResearchTaskNotFoundError):
            list(stream_research(self._sync_you(self._make_error_handler(404)), self._TASK))

    def test_500_raises_internal_server_error(self):
        from youdotcom.errors import StreamResearchTaskInternalServerError
        with pytest.raises(StreamResearchTaskInternalServerError):
            list(stream_research(self._sync_you(self._make_error_handler(500)), self._TASK))

    def test_4xx_fallback_raises_default_error(self):
        from youdotcom.errors import YouDefaultError
        with pytest.raises(YouDefaultError):
            list(stream_research(self._sync_you(self._make_error_handler(400)), self._TASK))

    def test_5xx_fallback_raises_default_error(self):
        from youdotcom.errors import YouDefaultError
        with pytest.raises(YouDefaultError):
            list(stream_research(self._sync_you(self._make_error_handler(502)), self._TASK))

    @pytest.mark.asyncio
    async def test_async_401_raises_unauthorized_error(self):
        from youdotcom.errors import StreamResearchTaskUnauthorizedError
        with pytest.raises(StreamResearchTaskUnauthorizedError):
            async for _ in stream_research_async(self._async_you(self._make_error_handler(401)), self._TASK):
                pass

    @pytest.mark.asyncio
    async def test_async_403_raises_forbidden_error(self):
        from youdotcom.errors import StreamResearchTaskForbiddenError
        with pytest.raises(StreamResearchTaskForbiddenError):
            async for _ in stream_research_async(self._async_you(self._make_error_handler(403)), self._TASK):
                pass

    @pytest.mark.asyncio
    async def test_async_404_raises_not_found_error(self):
        from youdotcom.errors import StreamResearchTaskNotFoundError
        with pytest.raises(StreamResearchTaskNotFoundError):
            async for _ in stream_research_async(self._async_you(self._make_error_handler(404)), self._TASK):
                pass

    @pytest.mark.asyncio
    async def test_async_500_raises_internal_server_error(self):
        from youdotcom.errors import StreamResearchTaskInternalServerError
        with pytest.raises(StreamResearchTaskInternalServerError):
            async for _ in stream_research_async(self._async_you(self._make_error_handler(500)), self._TASK):
                pass


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
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
            ],
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
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

    @pytest.mark.asyncio
    async def test_async_frontier_auto_timeout_completes_without_premature_timeout(self):
        """Async mirror: when research_effort=frontier and timeout_s is omitted,
        the auto-adjusted 4-hour timeout should not trip on a normal event
        sequence that completes within seconds."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
            ],
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = await research_and_wait_async(
            you,
            input="Evaluate the Gates Foundation's global-health impact",
            research_effort=ResearchEffort.FRONTIER,
            # timeout_s intentionally omitted — should auto-adjust to 14400
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    @pytest.mark.asyncio
    async def test_async_research_and_wait_error_event_raises_runtime_error(self):
        """Async research_and_wait raises RuntimeError on error terminal event."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: error\ndata: {"type":"error","task_id":"abc","message":"internal error"}\n\n',
            ],
            final_status="running",
            final_result=None,
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="non-completed state"):
            await research_and_wait_async(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    @pytest.mark.asyncio
    async def test_async_research_and_wait_ok_event_repoll_succeeds(self):
        """Async mirror: stream OK + first GET running, second GET completed."""
        call_count = {"get": 0}

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                return httpx.Response(
                    200, headers={"content-type": "text/event-stream"},
                    stream=_AsyncChunks([
                        _CONNECTED_CHUNK,
                        b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
                    ]),
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"}, content=_TASK_RESPONSE_JSON,
                )
            call_count["get"] += 1
            if call_count["get"] == 1:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_make_task_detail_json(status="running", result=None),
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
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
        assert call_count["get"] == 2

    @pytest.mark.asyncio
    async def test_async_research_and_wait_ok_event_but_get_failed_raises_immediately(self):
        """Async mirror: stream OK + GET returns terminal failed raises
        immediately without exhausting re-poll attempts."""
        handler = _make_wait_handler(
            stream_chunks=[
                _CONNECTED_CHUNK,
                b'id: 1\nevent: response.done\ndata: {"type":"response.done","task_id":"abc","status":"completed","sequence":1}\n\n',
            ],
            final_status="failed",
            final_result=None,
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(RuntimeError, match="ended in non-completed state: failed"):
            await research_and_wait_async(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    @pytest.mark.asyncio
    async def test_async_research_and_wait_timeout_raises_timeout_error(self):
        """Async research_and_wait raises TimeoutError when the stream never
        sends a terminal event and the task is still running. asyncio.wait_for
        cancels the blocked _consume() coroutine."""
        handler = _make_wait_handler(
            stream_obj=_BlockingAsyncStream(),
            final_status="running",
            final_result=None,
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="did not complete within"):
            await research_and_wait_async(
                you,
                timeout_s=0.5,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    @pytest.mark.asyncio
    async def test_async_research_and_wait_httpx_readtimeout_falls_back_to_get(self):
        """Async research_and_wait catches httpx.ReadTimeout (not just
        asyncio.TimeoutError) and falls back to a final GET. Mirrors the
        sync _BlockingStream test. Without catching httpx.TimeoutException,
        the raw ReadTimeout would propagate uncaught."""
        class _ReadTimeoutAsyncStream(httpx.AsyncByteStream):
            """Yields one event then raises httpx.ReadTimeout to simulate
            a stalled server with an explicit read timeout."""
            async def __aiter__(self):
                yield _CONNECTED_CHUNK
                raise httpx.ReadTimeout("read timeout")

        handler = _make_wait_handler(
            stream_obj=_ReadTimeoutAsyncStream(),
            final_status="completed",
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = await research_and_wait_async(
            you,
            timeout_s=0.5,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    @pytest.mark.asyncio
    async def test_async_research_and_wait_timeout_falls_back_to_get(self):
        """When the async stream times out but the task completed, the final
        GET fallback returns the completed detail."""
        handler = _make_wait_handler(
            stream_obj=_BlockingAsyncStream(),
            final_status="completed",
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        detail = await research_and_wait_async(
            you,
            timeout_s=0.5,
            input="test query",
            research_effort=ResearchEffort.STANDARD,
        )

        assert isinstance(detail, TaskDetail)
        assert detail.status.value == "completed"

    @pytest.mark.asyncio
    async def test_async_research_and_wait_stream_close_falls_back_to_get(self):
        """When the stream closes without a terminal event, async
        research_and_wait does a final GET and returns the detail if completed."""
        handler = _make_wait_handler(
            stream_chunks=[_CONNECTED_CHUNK],
            final_status="completed",
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
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

    @pytest.mark.asyncio
    async def test_async_research_and_wait_stream_close_task_running_raises_timeout(self):
        """When the stream closes without a terminal event and the final GET
        shows the task is still running, async research_and_wait raises TimeoutError."""
        handler = _make_wait_handler(
            stream_chunks=[_CONNECTED_CHUNK],
            final_status="running",
            final_result=None,
            is_async=True,
        )
        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="test-api-key",
        )

        with pytest.raises(TimeoutError, match="still running"):
            await research_and_wait_async(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

    @pytest.mark.asyncio
    async def test_async_stream_open_transport_error_falls_back_to_poll(self):
        """Async mirror: TransportError on stream-open falls back to polling."""
        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                raise httpx.ConnectError("connection refused")
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_TASK_RESPONSE_JSON,
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
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

    @pytest.mark.asyncio
    async def test_async_stream_open_401_propagates_typed_error(self):
        """Async mirror: 401 on stream-open propagates typed error."""
        from youdotcom.errors import StreamResearchTaskUnauthorizedError

        def handler(request):
            url = str(request.url)
            if url.endswith("/stream") or "/stream?" in url:
                return httpx.Response(
                    401,
                    headers={"content-type": "application/json"},
                    content='{"error": "unauthorized"}',
                )
            if request.method == "POST" and "/v1/research" in url and "/stream" not in url:
                return httpx.Response(
                    200, headers={"content-type": "application/json"},
                    content=_TASK_RESPONSE_JSON,
                )
            return httpx.Response(
                200, headers={"content-type": "application/json"},
                content=_make_task_detail_json(status="completed", result=_DEFAULT_RESULT),
            )

        transport = httpx.MockTransport(handler)
        you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=transport),
            api_key_auth="bad-key",
        )

        with pytest.raises(StreamResearchTaskUnauthorizedError):
            await research_and_wait_async(
                you,
                timeout_s=5.0,
                input="test query",
                research_effort=ResearchEffort.STANDARD,
            )

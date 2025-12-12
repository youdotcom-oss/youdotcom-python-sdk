"""
Timing-instrumented HTTP client for measuring SDK performance.

This module provides a synchronous HTTP client that tracks timing at multiple layers:
- HTTP request/response timing
- Individual request tracking
- Thread-safe timing data collection
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional
import httpx


@dataclass
class RequestTiming:
    """Timing data for a single HTTP request."""
    
    endpoint: str
    method: str
    url: str
    http_start: float
    http_end: float
    status_code: int
    request_size: int = 0
    response_size: int = 0
    
    @property
    def http_duration_ms(self) -> float:
        """HTTP request duration in milliseconds."""
        return (self.http_end - self.http_start) * 1000
    
    @property
    def http_duration_s(self) -> float:
        """HTTP request duration in seconds."""
        return self.http_end - self.http_start


@dataclass
class SDKCallTiming:
    """Complete timing data for an SDK call including SDK overhead."""
    
    endpoint: str
    sdk_start: float
    sdk_end: float
    request_timing: RequestTiming
    
    @property
    def sdk_duration_ms(self) -> float:
        """Total SDK call duration in milliseconds."""
        return (self.sdk_end - self.sdk_start) * 1000
    
    @property
    def sdk_duration_s(self) -> float:
        """Total SDK call duration in seconds."""
        return self.sdk_end - self.sdk_start
    
    @property
    def overhead_ms(self) -> float:
        """SDK overhead in milliseconds (total - HTTP time)."""
        return self.sdk_duration_ms - self.request_timing.http_duration_ms
    
    @property
    def overhead_percentage(self) -> float:
        """SDK overhead as percentage of total time."""
        if self.sdk_duration_ms == 0:
            return 0.0
        return (self.overhead_ms / self.sdk_duration_ms) * 100


class TimingHTTPClient(httpx.Client):
    """HTTP client that tracks timing for each request."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timings: List[RequestTiming] = []
        self._lock = Lock()
    
    def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: httpx._types.AuthTypes | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: bool | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        """Send HTTP request with timing instrumentation."""
        http_start = time.perf_counter()
        
        response = super().send(
            request,
            stream=stream,
            auth=auth,
            follow_redirects=follow_redirects,
        )
        
        http_end = time.perf_counter()
        
        # Extract endpoint name from URL path
        endpoint = request.url.path
        
        # Calculate request size
        request_size = len(request.content) if request.content else 0
        
        # Calculate response size (read content if not streaming)
        response_size = 0
        if not stream and response.content:
            response_size = len(response.content)
        
        timing = RequestTiming(
            endpoint=endpoint,
            method=request.method,
            url=str(request.url),
            http_start=http_start,
            http_end=http_end,
            status_code=response.status_code,
            request_size=request_size,
            response_size=response_size,
        )
        
        with self._lock:
            self._timings.append(timing)
        
        return response
    
    def request(
        self,
        method: str,
        url: httpx.URL | str,
        *,
        content: httpx._types.RequestContent | None = None,
        data: httpx._types.RequestData | None = None,
        files: httpx._types.RequestFiles | None = None,
        json: Any | None = None,
        params: httpx._types.QueryParamTypes | None = None,
        headers: httpx._types.HeaderTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
        auth: httpx._types.AuthTypes | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: bool | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
        timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
        extensions: Dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with timing instrumentation."""
        http_start = time.perf_counter()
        
        response = super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )
        
        http_end = time.perf_counter()
        
        # Extract endpoint name from URL path
        if isinstance(url, str):
            url_obj = httpx.URL(url)
        else:
            url_obj = url
        endpoint = url_obj.path
        
        # Calculate sizes
        request_size = 0
        if content:
            request_size = len(content) if isinstance(content, bytes) else 0
        elif json:
            import json as json_module
            request_size = len(json_module.dumps(json).encode())
        
        # Read response to calculate size (already consumed by SDK)
        response_size = len(response.content) if response.content else 0
        
        timing = RequestTiming(
            endpoint=endpoint,
            method=method,
            url=str(url),
            http_start=http_start,
            http_end=http_end,
            status_code=response.status_code,
            request_size=request_size,
            response_size=response_size,
        )
        
        with self._lock:
            self._timings.append(timing)
        
        return response
    
    def get_timings(self) -> List[RequestTiming]:
        """Get all recorded timings."""
        with self._lock:
            return self._timings.copy()
    
    def get_last_timing(self) -> Optional[RequestTiming]:
        """Get the most recent timing."""
        with self._lock:
            return self._timings[-1] if self._timings else None
    
    def clear_timings(self) -> None:
        """Clear all recorded timings."""
        with self._lock:
            self._timings.clear()

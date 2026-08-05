"""Deprecated sub-SDK shims that delegate to direct methods on ``You``.

These exist for backward compatibility. The old access patterns still work
but emit ``DeprecationWarning``:

    you.search.unified(query=...)         → you.search(query=...)
    you.search.unified_async(query=...)   → you.search_async(query=...)
    you.contents.generate(urls=...)       → you.contents(urls=...)
    you.contents.generate_async(urls=...) → you.contents_async(urls=...)

The new direct-method API (``you.search(query=...)`` etc.) is preferred
and emits no warning.
"""

from __future__ import annotations

import warnings
from typing import Any, Iterable, List, Mapping, Optional

from youdotcom import models, utils
from youdotcom.types import OptionalNullable, UNSET


def _warn(old: str, new: str) -> None:
    warnings.warn(
        f"{old} is deprecated; use {new} instead",
        DeprecationWarning,
        stacklevel=3,
    )


def _split_csv(v: Optional[str]) -> Optional[List[str]]:
    if v is None:
        return None
    return [s.strip() for s in v.split(",") if s.strip()]


class SearchShim:
    """Callable shim for ``you.search``.

    ``you.search(query=...)`` → delegates to ``you._search_impl()`` (no warning).
    ``you.search.unified(query=...)`` → delegates with DeprecationWarning.
    """

    def __init__(self, you: Any) -> None:
        self._you = you

    def __call__(
        self,
        *,
        query: str,
        count: Optional[int] = 10,
        freshness: Optional[str] = None,
        offset: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        safesearch: Optional[str] = None,
        livecrawl: Optional[str] = None,
        livecrawl_formats: Optional[Iterable[str]] = None,
        include_domains: Optional[Iterable[str]] = None,
        exclude_domains: Optional[Iterable[str]] = None,
        boost_domains: Optional[Iterable[str]] = None,
        crawl_timeout: Optional[int] = 10,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.SearchResponse:
        return self._you._search_impl(
            query=query,
            count=count,
            freshness=freshness,
            offset=offset,
            country=country,
            language=language,
            safesearch=safesearch,
            livecrawl=livecrawl,
            livecrawl_formats=livecrawl_formats,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            boost_domains=boost_domains,
            crawl_timeout=crawl_timeout,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )

    def unified(
        self,
        *,
        query: str,
        count: Optional[int] = 10,
        freshness: Optional[str] = None,
        offset: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        safesearch: Optional[str] = None,
        livecrawl: Optional[str] = None,
        livecrawl_formats: Optional[Iterable[str]] = None,
        include_domains: Optional[str] = None,
        exclude_domains: Optional[str] = None,
        boost_domains: Optional[str] = None,
        crawl_timeout: Optional[int] = 10,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.SearchResponse:
        _warn("you.search.unified()", "you.search()")

        return self._you._search_impl(
            query=query,
            count=count,
            freshness=freshness,
            offset=offset,
            country=country,
            language=language,
            safesearch=safesearch,
            livecrawl=livecrawl,
            livecrawl_formats=livecrawl_formats,
            include_domains=_split_csv(include_domains),
            exclude_domains=_split_csv(exclude_domains),
            boost_domains=_split_csv(boost_domains),
            crawl_timeout=crawl_timeout,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )

    async def unified_async(
        self,
        *,
        query: str,
        count: Optional[int] = 10,
        freshness: Optional[str] = None,
        offset: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        safesearch: Optional[str] = None,
        livecrawl: Optional[str] = None,
        livecrawl_formats: Optional[Iterable[str]] = None,
        include_domains: Optional[str] = None,
        exclude_domains: Optional[str] = None,
        boost_domains: Optional[str] = None,
        crawl_timeout: Optional[int] = 10,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.SearchResponse:
        _warn("you.search.unified_async()", "you.search_async()")

        return await self._you._search_async_impl(
            query=query,
            count=count,
            freshness=freshness,
            offset=offset,
            country=country,
            language=language,
            safesearch=safesearch,
            livecrawl=livecrawl,
            livecrawl_formats=livecrawl_formats,
            include_domains=_split_csv(include_domains),
            exclude_domains=_split_csv(exclude_domains),
            boost_domains=_split_csv(boost_domains),
            crawl_timeout=crawl_timeout,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )


class ContentsShim:
    """Callable shim for ``you.contents``.

    ``you.contents(urls=...)`` → delegates to ``you._contents_impl()`` (no warning).
    ``you.contents.generate(urls=...)`` → delegates with DeprecationWarning.
    """

    def __init__(self, you: Any) -> None:
        self._you = you

    def __call__(
        self,
        *,
        urls: Optional[Iterable[str]] = None,
        formats: Optional[Iterable[models.ContentsFormats]] = None,
        crawl_timeout: Optional[int] = 10,
        max_age: OptionalNullable[int] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> List[models.ContentsResponse]:
        return self._you._contents_impl(
            urls=urls,
            formats=formats,
            crawl_timeout=crawl_timeout,
            max_age=max_age,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )

    def generate(
        self,
        *,
        urls: Optional[Iterable[str]] = None,
        formats: Optional[Iterable[models.ContentsFormats]] = None,
        crawl_timeout: Optional[int] = 10,
        max_age: OptionalNullable[int] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> List[models.ContentsResponse]:
        _warn("you.contents.generate()", "you.contents()")
        return self._you._contents_impl(
            urls=urls,
            formats=formats,
            crawl_timeout=crawl_timeout,
            max_age=max_age,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )

    async def generate_async(
        self,
        *,
        urls: Optional[Iterable[str]] = None,
        formats: Optional[Iterable[models.ContentsFormats]] = None,
        crawl_timeout: Optional[int] = 10,
        max_age: OptionalNullable[int] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> List[models.ContentsResponse]:
        _warn("you.contents.generate_async()", "you.contents_async()")
        return await self._you._contents_async_impl(
            urls=urls,
            formats=formats,
            crawl_timeout=crawl_timeout,
            max_age=max_age,
            retries=retries,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        )

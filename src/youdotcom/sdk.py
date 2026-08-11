

from .basesdk import BaseSDK
from .httpclient import AsyncHttpClient, ClientOwner, HttpClient, close_clients
from .sdkconfiguration import SDKConfiguration
from .utils.logger import Logger, get_default_logger
from .utils.retries import RetryConfig
import asyncio
import httpx
import warnings
import weakref
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Union,
    cast,
)
from youdotcom import errors, models, utils
from youdotcom._hooks import HookContext, SDKHooks
from youdotcom._shims import ContentsShim, SearchShim
from youdotcom.types import OptionalNullable, UNSET
from youdotcom.utils import eventstreaming, get_security_from_env
from youdotcom.utils.unmarshal_json_response import unmarshal_json_response


def _upper(value: Any) -> Any:
    """Normalize a plain-string enum value to its uppercase spelling.

    Used for ``country`` and ``language``, whose enum members are uppercase
    (``"us"`` -> ``"US"``). Non-strings (and ``None``) pass through untouched;
    enum members are ``str`` subclasses, so they normalize to themselves.
    """
    return value.upper() if isinstance(value, str) else value


def _lower(value: Any) -> Any:
    """Normalize a plain-string enum value to its lowercase spelling.

    Used for ``safesearch``, ``livecrawl``, and ``freshness``, whose enum
    members are lowercase (``"STRICT"`` -> ``"strict"``). Date-range freshness
    values are unaffected apart from the ``to`` separator, which the API
    expects in lowercase anyway.
    """
    return value.lower() if isinstance(value, str) else value


def _lower_each(values: Optional[Iterable[Any]]) -> Optional[List[Any]]:
    """Apply :func:`_lower` to every item of an optional iterable."""
    if values is None:
        return None
    return [_lower(v) for v in values]


def _build_search_request(
    *,
    query: str,
    count: Optional[int],
    freshness: Optional[str],
    offset: Optional[int],
    country: Optional[str],
    language: OptionalNullable[str],
    safesearch: Optional[str],
    livecrawl: Optional[str],
    livecrawl_formats: Optional[Iterable[str]],
    extraction: Optional[Union[models.Extraction, Mapping[str, Any]]],
    include_domains: Optional[Iterable[str]],
    exclude_domains: Optional[Iterable[str]],
    boost_domains: Optional[Iterable[str]],
    crawl_timeout: Optional[int],
) -> models.SearchRequestBody:
    r"""Build the ``POST /v1/search`` request body.

    Shared by the sync and async search paths so the extraction
    coercion/validation, deprecation warning, conflict check, and
    plus-value rule live in exactly one place.
    """
    # Coerce `extraction` to an Extraction instance so we can read
    # `.extraction_mode` for the plus-value rule below. Pydantic
    # raises ValidationError on strict-validation failures (unknown
    # keys, wrong-mode couplings, out-of-range max_tokens), matching
    # the server's 422 contract so callers fail-fast.
    extraction_model: Optional[models.Extraction] = None
    if extraction is not None:
        extraction_model = models.Extraction.model_validate(extraction)

    # Conflict: extraction and livecrawl/livecrawl_formats cannot
    # coexist (the server rejects both). Mirror locally so the caller
    # learns immediately rather than after a round-trip + 422.
    if extraction_model is not None and (
        livecrawl is not None or livecrawl_formats is not None
    ):
        raise ValueError(
            "extraction cannot be combined with livecrawl or livecrawl_formats"
        )

    # `livecrawl` and `livecrawl_formats` are deprecated; warn
    # with stacklevel=4 so the warning reports the user frame (the
    # helper adds one extra frame compared to the old inline warn).
    if livecrawl is not None or livecrawl_formats is not None:
        warnings.warn(
            "livecrawl is deprecated; use extraction instead",
            DeprecationWarning,
            stacklevel=4,
        )

    # Plus-value rule: extraction_mode == 'highlights' forbids
    # crawl_timeout on the wire. We strip crawl_timeout from the body
    # in that case so default callers (SDK default) reach the server
    # without violating the rule. Warn when the caller set a
    # non-default value so the silent strip is not surprising.
    strip_crawl_timeout = (
        extraction_model is not None
        and extraction_model.extraction_mode is models.ExtractionMode.HIGHLIGHTS
    )
    if (
        strip_crawl_timeout
        and crawl_timeout is not None
        and crawl_timeout
        != models.SearchRequestBody.model_fields["crawl_timeout"].default
    ):
        warnings.warn(
            "crawl_timeout is ignored when extraction_mode == 'highlights'",
            UserWarning,
            stacklevel=4,
        )

    body: dict[str, Any] = dict(
        query=query,
        count=count,
        freshness=_lower(freshness),
        offset=offset,
        country=_upper(country),
        safesearch=_lower(safesearch),
        livecrawl=_lower(livecrawl),
        livecrawl_formats=utils.unmarshal(
            _lower_each(livecrawl_formats), Optional[List[models.LiveCrawlFormats]]
        ),
        include_domains=utils.unmarshal(include_domains, Optional[List[str]]),
        exclude_domains=utils.unmarshal(exclude_domains, Optional[List[str]]),
        boost_domains=utils.unmarshal(boost_domains, Optional[List[str]]),
        extraction=extraction,
    )
    # Plus-value rule: extraction_mode == 'highlights' forbids
    # crawl_timeout on the wire. Send None so SearchRequestBody's
    # serializer drops the field (None is in optional_fields and
    # serializer skips optional Fields when None). Default callers
    # thus reach the server without violating the rule. Non-default
    # values are stripped too, but only after the warning above.
    body["crawl_timeout"] = None if strip_crawl_timeout else crawl_timeout
    # UNSET (the default) leaves the field off entirely so SearchRequestBody's
    # own `Language.EN` default applies. An explicit None is passed through and
    # dropped during serialization, which sends no language at all.
    if language is not UNSET:
        body["language"] = _upper(language)
    return models.SearchRequestBody(**body)


_EMPTY_API_KEY_MESSAGE = (
    "api_key_auth was an empty string. Every You.com endpoint requires an API "
    'key, so this is never valid. If you meant to read the key from the '
    "environment, pass None or omit the argument -- the SDK then reads "
    "YDC_API_KEY (falling back to YOU_API_KEY_AUTH). This usually comes from "
    'os.getenv("YDC_API_KEY", "") with the variable unset; use '
    'os.getenv("YDC_API_KEY") instead.'
)


class You(BaseSDK):
    r"""You.com API: Unified API for search, answers, research, and content from You.com
    Get the best search results from web and news sources
    Returns the HTML or Markdown of a target webpage
    Multi-step reasoning with comprehensive research capabilities
    Finance-focused multi-step research with competitive accuracy at same price points and latencies as the Research API
    Comprehensive API for You.com services:
    - **Answer API**: Get synthesized, citation-backed answers grounded in real-time web results
    - **Research API**: In-depth, multi-step research with citations and sources
    - **Finance Research API**: Finance-focused multi-step research with citations and sources
    - **Search API**: Get search results from web and news sources
    - **Contents API**: Retrieve and process web page content
    """

    def __init__(
        self,
        api_key_auth: Optional[
            Union[Optional[str], Callable[[], Optional[str]]]
        ] = None,
        server_idx: Optional[int] = None,
        url_params: Optional[Dict[str, str]] = None,
        server_url: Optional[str] = None,
        client: Optional[HttpClient] = None,
        async_client: Optional[AsyncHttpClient] = None,
        retry_config: OptionalNullable[RetryConfig] = UNSET,
        timeout_ms: Optional[int] = None,
        debug_logger: Optional[Logger] = None,
    ) -> None:
        r"""Instantiates the SDK configuring it with the provided parameters.

        :param api_key_auth: The api_key_auth required for authentication
        :param server_idx: The index of the server to use for all methods
        :param server_url: The server URL to use for all methods. Note: ``search()``/``search_async()`` and ``contents()``/``contents_async()`` default to ``ydc-index.io`` (via ``SEARCH_OP_SERVERS``/``CONTENTS_OP_SERVERS``) and are not affected by this parameter unless the per-method ``server_url`` argument is passed.
        :param url_params: Parameters to optionally template the server URL with
        :param client: The HTTP client to use for all synchronous methods
        :param async_client: The Async HTTP client to use for all asynchronous methods
        :param retry_config: The retry configuration to use for all supported methods
        :param timeout_ms: Optional request timeout applied to each operation in milliseconds
        """
        client_supplied = True
        if client is None:
            client = httpx.Client(follow_redirects=True)
            client_supplied = False

        assert issubclass(
            type(client), HttpClient
        ), "The provided client must implement the HttpClient protocol."

        async_client_supplied = True
        if async_client is None:
            async_client = httpx.AsyncClient(follow_redirects=True)
            async_client_supplied = False

        if debug_logger is None:
            debug_logger = get_default_logger()

        assert issubclass(
            type(async_client), AsyncHttpClient
        ), "The provided async_client must implement the AsyncHttpClient protocol."

        security: Any = None
        # Every endpoint requires a key, so an empty string is never a valid
        # argument -- it means the caller thought they were passing a key and
        # weren't, almost always `os.getenv("YDC_API_KEY", "")` with the variable
        # unset. Falling back to the environment there would run the request
        # under whatever identity the environment happens to hold, which is not
        # the one the code asked for. Reject it at construction instead, where
        # the message can name the actual mistake. `None` (the default) is the
        # supported way to ask for the environment lookup.
        if isinstance(api_key_auth, str) and not api_key_auth.strip():
            raise ValueError(_EMPTY_API_KEY_MESSAGE)

        if callable(api_key_auth):

            def _resolve_security() -> models.Security:
                key = api_key_auth()
                if not key or not key.strip():
                    raise ValueError(
                        "The api_key_auth callable returned an empty API key. "
                        + _EMPTY_API_KEY_MESSAGE
                    )
                return models.Security(api_key_auth=key)

            security = _resolve_security
        elif api_key_auth is not None:
            security = models.Security(api_key_auth=api_key_auth)
        else:
            security = None

        if server_url is not None:
            if url_params is not None:
                server_url = utils.template_url(server_url, url_params)

        BaseSDK.__init__(
            self,
            SDKConfiguration(
                client=client,
                client_supplied=client_supplied,
                async_client=async_client,
                async_client_supplied=async_client_supplied,
                security=security,
                server_url=server_url,
                server_idx=server_idx,
                retry_config=retry_config,
                timeout_ms=timeout_ms,
                debug_logger=debug_logger,
            ),
            parent_ref=self,
        )

        hooks = SDKHooks()

        # pylint: disable=protected-access
        self.sdk_configuration.__dict__["_hooks"] = hooks

        self.sdk_configuration = hooks.sdk_init(self.sdk_configuration)

        weakref.finalize(
            self,
            close_clients,
            cast(ClientOwner, self.sdk_configuration),
            self.sdk_configuration.client,
            self.sdk_configuration.client_supplied,
            self.sdk_configuration.async_client,
            self.sdk_configuration.async_client_supplied,
        )

        # Backward-compat shims: you.search.unified(), you.contents.generate()
        # still work but emit DeprecationWarning.
        # you.search(query=...), you.contents(urls=...) (the new API) go
        # through __call__ with no warning.
        self.search = SearchShim(self)
        self.contents = ContentsShim(self)

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    def _close_sync_client(self) -> None:
        """Close the SDK-owned sync client, if any, and drop the reference.

        Errors are swallowed (as in ``close_clients``) so that a failure while
        tearing down the client cannot replace an exception propagating out of
        the ``with`` block.
        """
        client = self.sdk_configuration.client
        self.sdk_configuration.client = None
        if client is not None and not self.sdk_configuration.client_supplied:
            try:
                client.close()
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    def _close_async_client_from_sync(self) -> None:
        """Close the SDK-owned async client from a synchronous context.

        Mirrors ``close_clients``: if a loop is already running, the close is
        scheduled on it; otherwise a throwaway loop drives it to completion.
        Errors are swallowed for the same reason as ``_close_sync_client``.
        """
        client = self.sdk_configuration.async_client
        self.sdk_configuration.async_client = None
        if client is None or self.sdk_configuration.async_client_supplied:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(client.aclose())
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        else:
            try:
                asyncio.run_coroutine_threadsafe(client.aclose(), loop)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    async def _close_async_client(self) -> None:
        """Close the SDK-owned async client, awaiting completion."""
        client = self.sdk_configuration.async_client
        self.sdk_configuration.async_client = None
        if client is not None and not self.sdk_configuration.async_client_supplied:
            try:
                await client.aclose()
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_sync_client()
        self._close_async_client_from_sync()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_async_client()
        self._close_sync_client()

    def answer(
        self,
        *,
        query: str,
        freshness: Optional[
            Union[models.FreshnessValue, models.FreshnessValueTypedDict]
        ] = None,
        country: Optional[Union[str, models.Country]] = None,
        language: Optional[Union[str, models.Language]] = None,
        include_domains: Optional[Iterable[str]] = None,
        exclude_domains: Optional[Iterable[str]] = None,
        boost_domains: Optional[Iterable[str]] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.AnswerResponse:
        r"""Returns a synthesized answer with citations from web search results.

        Provide a ``query`` and optional freshness, locale, and domain controls.
        The response includes a markdown answer with inline citations, a
        citations array with source URLs and supporting excerpts, and the web
        results used to generate the answer.

        :param query: The search query used to retrieve relevant web results.
            Max 400 characters. Search operators (``site:``, ``OR``, etc.) are
            not supported.
        :param freshness: Specifies the freshness of the results. One of ``day``,
            ``week``, ``month``, ``year``, or ``YYYY-MM-DDtoYYYY-MM-DD``.
        :param country: A supported country code that determines the geographical
            focus of the web results.
        :param language: A supported BCP 47 language tag that determines the
            language of the web results.
        :param include_domains: Domains to exclusively include. Cannot combine
            with ``exclude_domains`` or ``boost_domains``. Max 500.
        :param exclude_domains: Domains to exclude. Cannot combine with
            ``include_domains``. Can combine with ``boost_domains``. Max 500.
        :param boost_domains: Domains to prefer in ranking. Cannot combine with
            ``include_domains``. Can combine with ``exclude_domains``. Max 500.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for
            this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(None, None)

        body: dict = dict(
            query=query,
            freshness=_lower(freshness),
            country=_upper(country),
            language=_upper(language),
            include_domains=utils.unmarshal(include_domains, Optional[List[str]]),
            exclude_domains=utils.unmarshal(exclude_domains, Optional[List[str]]),
            boost_domains=utils.unmarshal(boost_domains, Optional[List[str]]),
        )
        request = models.AnswerRequestBody(**body)

        req = self._build_request(
            method="POST",
            path="/v1/answer",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.AnswerRequestBody
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="answer",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["answer"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.AnswerResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnauthorizedResponseErrorData, http_res
            )
            raise errors.UnauthorizedResponseError(response_data, http_res)
        if utils.match_response(http_res, "402", "application/json"):
            response_data = unmarshal_json_response(
                errors.PaymentRequiredResponseErrorData, http_res
            )
            raise errors.PaymentRequiredResponseError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ForbiddenResponseErrorData, http_res
            )
            raise errors.ForbiddenResponseError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityResponseErrorData, http_res
            )
            raise errors.UnprocessableEntityResponseError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorResponseData, http_res
            )
            raise errors.InternalServerErrorResponse(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def answer_async(
        self,
        *,
        query: str,
        freshness: Optional[
            Union[models.FreshnessValue, models.FreshnessValueTypedDict]
        ] = None,
        country: Optional[Union[str, models.Country]] = None,
        language: Optional[Union[str, models.Language]] = None,
        include_domains: Optional[Iterable[str]] = None,
        exclude_domains: Optional[Iterable[str]] = None,
        boost_domains: Optional[Iterable[str]] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.AnswerResponse:
        r"""Returns a synthesized answer with citations from web search results.

        Provide a ``query`` and optional freshness, locale, and domain controls.
        The response includes a markdown answer with inline citations, a
        citations array with source URLs and supporting excerpts, and the web
        results used to generate the answer.

        :param query: The search query used to retrieve relevant web results.
            Max 400 characters. Search operators (``site:``, ``OR``, etc.) are
            not supported.
        :param freshness: Specifies the freshness of the results. One of ``day``,
            ``week``, ``month``, ``year``, or ``YYYY-MM-DDtoYYYY-MM-DD``.
        :param country: A supported country code that determines the geographical
            focus of the web results.
        :param language: A supported BCP 47 language tag that determines the
            language of the web results.
        :param include_domains: Domains to exclusively include. Cannot combine
            with ``exclude_domains`` or ``boost_domains``. Max 500.
        :param exclude_domains: Domains to exclude. Cannot combine with
            ``include_domains``. Can combine with ``boost_domains``. Max 500.
        :param boost_domains: Domains to prefer in ranking. Cannot combine with
            ``include_domains``. Can combine with ``exclude_domains``. Max 500.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for
            this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(None, None)

        body: dict = dict(
            query=query,
            freshness=_lower(freshness),
            country=_upper(country),
            language=_upper(language),
            include_domains=utils.unmarshal(include_domains, Optional[List[str]]),
            exclude_domains=utils.unmarshal(exclude_domains, Optional[List[str]]),
            boost_domains=utils.unmarshal(boost_domains, Optional[List[str]]),
        )
        request = models.AnswerRequestBody(**body)

        req = self._build_request_async(
            method="POST",
            path="/v1/answer",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=False,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.AnswerRequestBody
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="answer",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["answer"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.AnswerResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnauthorizedResponseErrorData, http_res
            )
            raise errors.UnauthorizedResponseError(response_data, http_res)
        if utils.match_response(http_res, "402", "application/json"):
            response_data = unmarshal_json_response(
                errors.PaymentRequiredResponseErrorData, http_res
            )
            raise errors.PaymentRequiredResponseError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ForbiddenResponseErrorData, http_res
            )
            raise errors.ForbiddenResponseError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityResponseErrorData, http_res
            )
            raise errors.UnprocessableEntityResponseError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorResponseData, http_res
            )
            raise errors.InternalServerErrorResponse(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    def _contents_impl(
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
        r"""Returns the content of the web pages

        Returns the HTML or Markdown of a target webpage.

        :param urls: Array of URLs to fetch the contents from.
        :param formats: Array of content formats to return. All included formats are returned in the response. Include \"metadata\" to get JSON-LD and OpenGraph information, if available.
        :param crawl_timeout: Maximum time in seconds to wait for page content. Must be between 1 and 60 seconds. Default is 10 seconds.
        :param max_age: Maximum allowed age of cached content in seconds. When set, cached content older than this threshold is ignored and the page is re-fetched. Must be 0 or greater. Default: null (no age limit, cached content is returned regardless of age).
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(models.CONTENTS_OP_SERVERS[0], None)

        request = models.ContentsRequest(
            urls=utils.unmarshal(urls, Optional[List[str]]),
            formats=utils.unmarshal(formats, Optional[List[models.ContentsFormats]]),
            crawl_timeout=crawl_timeout,
            max_age=max_age,
        )

        req = self._build_request(
            method="POST",
            path="/v1/contents",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.ContentsRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="contents",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["contents"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(List[models.ContentsResponse], http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsUnauthorizedErrorData, http_res
            )
            raise errors.ContentsUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsForbiddenErrorData, http_res
            )
            raise errors.ContentsForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsInternalServerErrorData, http_res
            )
            raise errors.ContentsInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def contents_async(
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
        r"""Returns the content of the web pages

        Returns the HTML or Markdown of a target webpage.

        :param urls: Array of URLs to fetch the contents from.
        :param formats: Array of content formats to return. All included formats are returned in the response. Include \"metadata\" to get JSON-LD and OpenGraph information, if available.
        :param crawl_timeout: Maximum time in seconds to wait for page content. Must be between 1 and 60 seconds. Default is 10 seconds.
        :param max_age: Maximum allowed age of cached content in seconds. When set, cached content older than this threshold is ignored and the page is re-fetched. Must be 0 or greater. Default: null (no age limit, cached content is returned regardless of age).
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(models.CONTENTS_OP_SERVERS[0], None)

        request = models.ContentsRequest(
            urls=utils.unmarshal(urls, Optional[List[str]]),
            formats=utils.unmarshal(formats, Optional[List[models.ContentsFormats]]),
            crawl_timeout=crawl_timeout,
            max_age=max_age,
        )

        req = self._build_request_async(
            method="POST",
            path="/v1/contents",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.ContentsRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="contents",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["contents"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(List[models.ContentsResponse], http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsUnauthorizedErrorData, http_res
            )
            raise errors.ContentsUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsForbiddenErrorData, http_res
            )
            raise errors.ContentsForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.ContentsInternalServerErrorData, http_res
            )
            raise errors.ContentsInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    def _search_impl(
        self,
        *,
        query: str,
        count: Optional[int] = 10,
        freshness: Optional[str] = None,
        offset: Optional[int] = None,
        country: Optional[str] = None,
        language: OptionalNullable[str] = UNSET,
        safesearch: Optional[str] = None,
        livecrawl: Optional[str] = None,
        livecrawl_formats: Optional[Iterable[str]] = None,
        extraction: Optional[Union[models.Extraction, Mapping[str, Any]]] = None,
        include_domains: Optional[Iterable[str]] = None,
        exclude_domains: Optional[Iterable[str]] = None,
        boost_domains: Optional[Iterable[str]] = None,
        crawl_timeout: Optional[int] = 10,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.SearchResponse:
        r"""Search via POST /v1/search.

        Enum-typed parameters (``country``, ``language``, ``safesearch``,
        ``livecrawl``, ``livecrawl_formats``, ``freshness``) accept plain
        strings in any case -- the SDK normalizes them to the casing the API
        expects, so callers don't need to import enum classes.

        ``livecrawl`` and ``livecrawl_formats`` are deprecated; prefer
        ``extraction``. The two are mutually exclusive -- passing both
        raises :class:`ValueError`. Top-level ``crawl_timeout`` cannot
        combine with ``extraction.extraction_mode == "highlights"`` (the
        plus-value rule); the SDK strips ``crawl_timeout`` from the request
        body in that case so default callers do not 422.

        :param query: The search query used to retrieve relevant results from the web.
        :param count: Max results per section (1-100).
        :param freshness: ``"day"``, ``"week"``, ``"month"``, ``"year"``, or
            ``"YYYY-MM-DDtoYYYY-MM-DD"``.
        :param offset: Pagination offset (multiples of ``count``).
        :param country: Country code for geographical focus.
        :param language: BCP 47 language code. Omit the argument to use the API
            default (``"en"``); pass ``None`` to send no language at all.
        :param safesearch: ``"strict"``, ``"moderate"``, or ``"off"``.
        :param livecrawl: deprecated. ``"web"``, ``"news"``, or ``"all"``.
            Use ``extraction`` instead. Mutually exclusive with ``extraction``.
        :param livecrawl_formats: deprecated. ``["html"]``, ``["markdown"]``,
            or both. Use ``extraction`` instead. Mutually exclusive with
            ``extraction``.
        :param extraction: Controls how page content is attached to each
            result. ``None`` keeps snippets-only. Pass an ``Extraction``
            instance or a dict matching :class:`ExtractionTypedDict`.
            ``extraction_mode`` is required (``"highlights"`` returns
            ``results.web[].contents.highlights``; ``"full_page"`` returns
            ``results.web[].contents.html`` / ``contents.markdown``).
            Mutually exclusive with ``livecrawl`` / ``livecrawl_formats``.
        :param include_domains: Restrict results to these domains (<= 500).
        :param exclude_domains: Exclude these domains (<= 500).
        :param boost_domains: Boost these domains in ranking (<= 500).
        :param crawl_timeout: Max seconds to wait for livecrawl (1-60, default
            10). Stripped from the request body when ``extraction`` mode is
            ``"highlights"`` (plus-value rule); setting a non-default value
            there emits :class:`UserWarning` so the strip is not silent.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(models.SEARCH_OP_SERVERS[0], None)

        request = _build_search_request(
            query=query,
            count=count,
            freshness=freshness,
            offset=offset,
            country=country,
            language=language,
            safesearch=safesearch,
            livecrawl=livecrawl,
            livecrawl_formats=livecrawl_formats,
            extraction=extraction,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            boost_domains=boost_domains,
            crawl_timeout=crawl_timeout,
        )

        req = self._build_request(
            method="POST",
            path="/v1/search",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.SearchRequestBody
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="search",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["search"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.SearchResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnauthorizedResponseErrorData, http_res
            )
            raise errors.UnauthorizedResponseError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ForbiddenResponseErrorData, http_res
            )
            raise errors.ForbiddenResponseError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityResponseErrorData, http_res
            )
            raise errors.UnprocessableEntityResponseError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorResponseData, http_res
            )
            raise errors.InternalServerErrorResponse(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def search_async(
        self,
        *,
        query: str,
        count: Optional[int] = 10,
        freshness: Optional[str] = None,
        offset: Optional[int] = None,
        country: Optional[str] = None,
        language: OptionalNullable[str] = UNSET,
        safesearch: Optional[str] = None,
        livecrawl: Optional[str] = None,
        livecrawl_formats: Optional[Iterable[str]] = None,
        extraction: Optional[Union[models.Extraction, Mapping[str, Any]]] = None,
        include_domains: Optional[Iterable[str]] = None,
        exclude_domains: Optional[Iterable[str]] = None,
        boost_domains: Optional[Iterable[str]] = None,
        crawl_timeout: Optional[int] = 10,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.SearchResponse:
        r"""Search via POST /v1/search.

        Async variant of ``you.search()``. See :meth:`_search_impl` for the
        full parameter reference; ``language`` defaults to ``UNSET`` (use the
        API default ``"en"``) and accepts ``None`` to send no language at all.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(models.SEARCH_OP_SERVERS[0], None)

        request = _build_search_request(
            query=query,
            count=count,
            freshness=freshness,
            offset=offset,
            country=country,
            language=language,
            safesearch=safesearch,
            livecrawl=livecrawl,
            livecrawl_formats=livecrawl_formats,
            extraction=extraction,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            boost_domains=boost_domains,
            crawl_timeout=crawl_timeout,
        )

        req = self._build_request_async(
            method="POST",
            path="/v1/search",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.SearchRequestBody
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="search",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=["search"],
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.SearchResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnauthorizedResponseErrorData, http_res
            )
            raise errors.UnauthorizedResponseError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ForbiddenResponseErrorData, http_res
            )
            raise errors.ForbiddenResponseError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.UnprocessableEntityResponseErrorData, http_res
            )
            raise errors.UnprocessableEntityResponseError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.InternalServerErrorResponseData, http_res
            )
            raise errors.InternalServerErrorResponse(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    def research(
        self,
        *,
        input: str,
        research_effort: Optional[
            models.ResearchEffort
        ] = models.ResearchEffort.STANDARD,
        background: Optional[bool] = False,
        source_control: Optional[
            Union[models.SourceControl, models.SourceControlTypedDict]
        ] = None,
        output_schema: Optional[Mapping[str, Any]] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.ResearchResult:
        r"""Returns comprehensive research-grade answers with multi-step reasoning

        Research goes beyond a single web search. In response to your question, it runs multiple searches, reads through the sources, and synthesizes everything into a thorough, well-cited answer. Use it when a question is too complex for a simple lookup, and when you need a response you can actually trust and verify.

        :param input: The research question or complex query requiring in-depth investigation and multi-step reasoning.

            Note: The maximum length of the input is 40,000 characters.
        :param research_effort: Controls how much time and effort the Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

            Available levels:
            - `lite`: Returns answers quickly. Good for straightforward questions that just need a fast, reliable answer.
            - `standard`: The default. Balances speed and depth, a good fit for most questions.
            - `deep`: Spends more time researching and cross-referencing sources. Use this when accuracy and thoroughness matter more than speed.
            - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex research tasks where you want the highest quality result.
            - `frontier`: The highest-quality tier. Runs over longer durations with improved quality and accuracy. Only works with the task-based API (`background=true`); sending `frontier` without `background=true` returns a 422.
        :param background: When true, queue a research task and return a task handle immediately instead of waiting for the result inline. Defaults to synchronous. When enabled, the response is a TaskResponse object with a task_id and stream_url for polling progress via GET /v1/research/{task_id} or streaming via GET /v1/research/{task_id}/stream.
        :param source_control: Beta. Controls which web sources the research agent searches and visits. Use this to allow specific domains, block specific domains, boost specific domains, filter by recency, or focus web results by country.

            `include_domains` and `exclude_domains` cannot be used together. Each domain list is capped at 500 entries. `exclude_domains` also blocks the research agent from visiting pages on those domains during browsing. `boost_domains` gives matching domains a relative ranking boost without filtering out other domains. It can be combined with `exclude_domains` but cannot be combined with `include_domains`.
        :param output_schema: Beta. Requests structured JSON output in output.content using a supported JSON Schema subset. Supported only with research_effort values standard, deep, and exhaustive. Sending output_schema with research_effort: \"lite\" returns 422.

            Schema rules: Root must be a JSON object. Top-level anyOf is not allowed. Every object must define properties and set additionalProperties: false. Every property must be listed in required. Recursive schemas are not supported.

            Limits: Max nesting depth 5, max total properties 100, max total enum values 500, max total schema string budget 25,000.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.ResearchRequest(
            input=input,
            research_effort=research_effort,
            background=background,
            source_control=utils.get_pydantic_model(
                source_control, Optional[models.SourceControl]
            ),
            output_schema=utils.unmarshal(output_schema, Optional[Dict[str, Any]]),
        )

        req = self._build_request(
            method="POST",
            path="/v1/research",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.ResearchRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="research",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.ResearchResult, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchUnauthorizedErrorData, http_res
            )
            raise errors.ResearchUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchForbiddenErrorData, http_res
            )
            raise errors.ResearchForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchUnprocessableEntityErrorData, http_res
            )
            raise errors.ResearchUnprocessableEntityError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchInternalServerErrorData, http_res
            )
            raise errors.ResearchInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def research_async(
        self,
        *,
        input: str,
        research_effort: Optional[
            models.ResearchEffort
        ] = models.ResearchEffort.STANDARD,
        background: Optional[bool] = False,
        source_control: Optional[
            Union[models.SourceControl, models.SourceControlTypedDict]
        ] = None,
        output_schema: Optional[Mapping[str, Any]] = None,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.ResearchResult:
        r"""Returns comprehensive research-grade answers with multi-step reasoning

        Research goes beyond a single web search. In response to your question, it runs multiple searches, reads through the sources, and synthesizes everything into a thorough, well-cited answer. Use it when a question is too complex for a simple lookup, and when you need a response you can actually trust and verify.

        :param input: The research question or complex query requiring in-depth investigation and multi-step reasoning.

            Note: The maximum length of the input is 40,000 characters.
        :param research_effort: Controls how much time and effort the Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

            Available levels:
            - `lite`: Returns answers quickly. Good for straightforward questions that just need a fast, reliable answer.
            - `standard`: The default. Balances speed and depth, a good fit for most questions.
            - `deep`: Spends more time researching and cross-referencing sources. Use this when accuracy and thoroughness matter more than speed.
            - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex research tasks where you want the highest quality result.
            - `frontier`: The highest-quality tier. Runs over longer durations with improved quality and accuracy. Only works with the task-based API (`background=true`); sending `frontier` without `background=true` returns a 422.
        :param background: When true, queue a research task and return a task handle immediately instead of waiting for the result inline. Defaults to synchronous. When enabled, the response is a TaskResponse object with a task_id and stream_url for polling progress via GET /v1/research/{task_id} or streaming via GET /v1/research/{task_id}/stream.
        :param source_control: Beta. Controls which web sources the research agent searches and visits. Use this to allow specific domains, block specific domains, boost specific domains, filter by recency, or focus web results by country.

            `include_domains` and `exclude_domains` cannot be used together. Each domain list is capped at 500 entries. `exclude_domains` also blocks the research agent from visiting pages on those domains during browsing. `boost_domains` gives matching domains a relative ranking boost without filtering out other domains. It can be combined with `exclude_domains` but cannot be combined with `include_domains`.
        :param output_schema: Beta. Requests structured JSON output in output.content using a supported JSON Schema subset. Supported only with research_effort values standard, deep, and exhaustive. Sending output_schema with research_effort: \"lite\" returns 422.

            Schema rules: Root must be a JSON object. Top-level anyOf is not allowed. Every object must define properties and set additionalProperties: false. Every property must be listed in required. Recursive schemas are not supported.

            Limits: Max nesting depth 5, max total properties 100, max total enum values 500, max total schema string budget 25,000.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.ResearchRequest(
            input=input,
            research_effort=research_effort,
            background=background,
            source_control=utils.get_pydantic_model(
                source_control, Optional[models.SourceControl]
            ),
            output_schema=utils.unmarshal(output_schema, Optional[Dict[str, Any]]),
        )

        req = self._build_request_async(
            method="POST",
            path="/v1/research",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.ResearchRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="research",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.ResearchResult, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchUnauthorizedErrorData, http_res
            )
            raise errors.ResearchUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchForbiddenErrorData, http_res
            )
            raise errors.ResearchForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchUnprocessableEntityErrorData, http_res
            )
            raise errors.ResearchUnprocessableEntityError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.ResearchInternalServerErrorData, http_res
            )
            raise errors.ResearchInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    def get_research_task(
        self,
        *,
        task_id: str,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.TaskDetail:
        r"""Get the status of a background research task

        Poll the status of a background research task created with background=true. When the task is completed, the result is included in the response.

        :param task_id: The UUID of the research task.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.GetResearchTaskRequest(
            task_id=task_id,
        )

        req = self._build_request(
            method="GET",
            path="/v1/research/{task_id}",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=False,
            request_has_path_params=True,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="getResearchTask",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.TaskDetail, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskUnauthorizedErrorData, http_res
            )
            raise errors.GetResearchTaskUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskForbiddenErrorData, http_res
            )
            raise errors.GetResearchTaskForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "404", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskNotFoundErrorData, http_res
            )
            raise errors.GetResearchTaskNotFoundError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskInternalServerErrorData, http_res
            )
            raise errors.GetResearchTaskInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def get_research_task_async(
        self,
        *,
        task_id: str,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.TaskDetail:
        r"""Get the status of a background research task

        Poll the status of a background research task created with background=true. When the task is completed, the result is included in the response.

        :param task_id: The UUID of the research task.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.GetResearchTaskRequest(
            task_id=task_id,
        )

        req = self._build_request_async(
            method="GET",
            path="/v1/research/{task_id}",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=False,
            request_has_path_params=True,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="getResearchTask",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.TaskDetail, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskUnauthorizedErrorData, http_res
            )
            raise errors.GetResearchTaskUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskForbiddenErrorData, http_res
            )
            raise errors.GetResearchTaskForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "404", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskNotFoundErrorData, http_res
            )
            raise errors.GetResearchTaskNotFoundError(response_data, http_res)
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.GetResearchTaskInternalServerErrorData, http_res
            )
            raise errors.GetResearchTaskInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    def stream_research_task(
        self,
        *,
        task_id: str,
        from_id: Optional[int] = 0,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> eventstreaming.EventStream[models.ResearchTaskStreamEvent]:
        r"""Stream updates for a background research task

        Stream real-time updates for a background research task via Server-Sent Events (SSE). Supports reconnection via the from_id query parameter to replay missed events. The connection closes automatically when the task reaches a terminal state.

        :param task_id: The UUID of the research task.
        :param from_id: Resume from a sequence number for reconnection.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.StreamResearchTaskRequest(
            task_id=task_id,
            from_id=from_id,
        )

        req = self._build_request(
            method="GET",
            path="/v1/research/{task_id}/stream",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=False,
            request_has_path_params=True,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="text/event-stream",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="streamResearchTask",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            stream=True,
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "text/event-stream"):
            return eventstreaming.EventStream(
                http_res,
                lambda raw: unmarshal_json_response(
                    models.ResearchTaskStreamEvent, http_res, raw
                ),
                client_ref=self,
            )
        if utils.match_response(http_res, "401", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskUnauthorizedErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskUnauthorizedError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "403", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskForbiddenErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskForbiddenError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "404", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskNotFoundErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskNotFoundError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "500", "application/json"):
            http_res_text = utils.stream_to_text(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskInternalServerErrorData,
                http_res,
                http_res_text,
            )
            raise errors.StreamResearchTaskInternalServerError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        http_res_text = utils.stream_to_text(http_res)
        raise errors.YouDefaultError(
            "Unexpected response received", http_res, http_res_text
        )

    async def stream_research_task_async(
        self,
        *,
        task_id: str,
        from_id: Optional[int] = 0,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> eventstreaming.EventStreamAsync[models.ResearchTaskStreamEvent]:
        r"""Stream updates for a background research task

        Stream real-time updates for a background research task via Server-Sent Events (SSE). Supports reconnection via the from_id query parameter to replay missed events. The connection closes automatically when the task reaches a terminal state.

        :param task_id: The UUID of the research task.
        :param from_id: Resume from a sequence number for reconnection.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.StreamResearchTaskRequest(
            task_id=task_id,
            from_id=from_id,
        )

        req = self._build_request_async(
            method="GET",
            path="/v1/research/{task_id}/stream",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=False,
            request_has_path_params=True,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="text/event-stream",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="streamResearchTask",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            stream=True,
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "text/event-stream"):
            return eventstreaming.EventStreamAsync(
                http_res,
                lambda raw: unmarshal_json_response(
                    models.ResearchTaskStreamEvent, http_res, raw
                ),
                client_ref=self,
            )
        if utils.match_response(http_res, "401", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskUnauthorizedErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskUnauthorizedError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "403", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskForbiddenErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskForbiddenError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "404", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskNotFoundErrorData, http_res, http_res_text
            )
            raise errors.StreamResearchTaskNotFoundError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "500", "application/json"):
            http_res_text = await utils.stream_to_text_async(http_res)
            response_data = unmarshal_json_response(
                errors.StreamResearchTaskInternalServerErrorData,
                http_res,
                http_res_text,
            )
            raise errors.StreamResearchTaskInternalServerError(
                response_data, http_res, http_res_text
            )
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        http_res_text = await utils.stream_to_text_async(http_res)
        raise errors.YouDefaultError(
            "Unexpected response received", http_res, http_res_text
        )

    def finance_research(
        self,
        *,
        input: str,
        research_effort: Optional[
            models.FinanceResearchEffort
        ] = models.FinanceResearchEffort.DEEP,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.FinanceResearchResponse:
        r"""Returns comprehensive finance-grade research answers with multi-step reasoning

        The Finance Research API is purpose-built for financial questions. Like the Research API, it runs multiple searches, reads through sources, and synthesizes everything into a thorough, well-cited answer — but its retrieval index is optimized for financial data: earnings reports, SEC filings, analyst coverage, market data, and financial news.
        Use it when you need credible, sourced answers to financial questions: company fundamentals, market trends, competitive analysis, earnings summaries, or macroeconomic research.

        :param input: The financial research question or complex query requiring in-depth investigation and multi-step reasoning.

            Note: The maximum length of the input is 40,000 characters.
        :param research_effort: Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

            Available levels:
            - `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.
            - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.FinanceResearchRequest(
            input=input,
            research_effort=research_effort,
        )

        req = self._build_request(
            method="POST",
            path="/v1/finance_research",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.FinanceResearchRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = self.do_request(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="finance_research",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.FinanceResearchResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchUnauthorizedErrorData, http_res
            )
            raise errors.FinanceResearchUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchForbiddenErrorData, http_res
            )
            raise errors.FinanceResearchForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchUnprocessableEntityErrorData, http_res
            )
            raise errors.FinanceResearchUnprocessableEntityError(
                response_data, http_res
            )
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchInternalServerErrorData, http_res
            )
            raise errors.FinanceResearchInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = utils.stream_to_text(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

    async def finance_research_async(
        self,
        *,
        input: str,
        research_effort: Optional[
            models.FinanceResearchEffort
        ] = models.FinanceResearchEffort.DEEP,
        retries: OptionalNullable[utils.RetryConfig] = UNSET,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> models.FinanceResearchResponse:
        r"""Returns comprehensive finance-grade research answers with multi-step reasoning

        The Finance Research API is purpose-built for financial questions. Like the Research API, it runs multiple searches, reads through sources, and synthesizes everything into a thorough, well-cited answer — but its retrieval index is optimized for financial data: earnings reports, SEC filings, analyst coverage, market data, and financial news.
        Use it when you need credible, sourced answers to financial questions: company fundamentals, market trends, competitive analysis, earnings summaries, or macroeconomic research.

        :param input: The financial research question or complex query requiring in-depth investigation and multi-step reasoning.

            Note: The maximum length of the input is 40,000 characters.
        :param research_effort: Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

            Available levels:
            - `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.
            - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result.
        :param retries: Override the default retry configuration for this method
        :param server_url: Override the default server URL for this method
        :param timeout_ms: Override the default request timeout configuration for this method in milliseconds
        :param http_headers: Additional headers to set or replace on requests.
        """
        base_url = None
        url_variables = None
        if timeout_ms is None:
            timeout_ms = self.sdk_configuration.timeout_ms

        if server_url is not None:
            base_url = server_url
        else:
            base_url = self._get_url(base_url, url_variables)

        request = models.FinanceResearchRequest(
            input=input,
            research_effort=research_effort,
        )

        req = self._build_request_async(
            method="POST",
            path="/v1/finance_research",
            base_url=base_url,
            url_variables=url_variables,
            request=request,
            request_body_required=True,
            request_has_path_params=False,
            request_has_query_params=True,
            user_agent_header="user-agent",
            accept_header_value="application/json",
            http_headers=http_headers,
            security=self.sdk_configuration.security,
            get_serialized_body=lambda: utils.serialize_request_body(
                request, False, False, "json", models.FinanceResearchRequest
            ),
            allow_empty_value=None,
            timeout_ms=timeout_ms,
        )

        if retries == UNSET:
            if self.sdk_configuration.retry_config is not UNSET:
                retries = self.sdk_configuration.retry_config

        retry_config = None
        if isinstance(retries, utils.RetryConfig):
            retry_config = (retries, ["429", "500", "502", "503", "504"])

        http_res = await self.do_request_async(
            hook_ctx=HookContext(
                config=self.sdk_configuration,
                base_url=base_url or "",
                operation_id="finance_research",
                oauth2_scopes=None,
                security_source=get_security_from_env(
                    self.sdk_configuration.security, models.Security
                ),
                tags=None,
                extensions=None,
            ),
            request=req,
            is_error_status_code=lambda c: utils.match_status_codes(["4XX", "5XX"], c),
            retry_config=retry_config,
        )

        response_data: Any = None
        if utils.match_response(http_res, "200", "application/json"):
            return unmarshal_json_response(models.FinanceResearchResponse, http_res)
        if utils.match_response(http_res, "401", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchUnauthorizedErrorData, http_res
            )
            raise errors.FinanceResearchUnauthorizedError(response_data, http_res)
        if utils.match_response(http_res, "403", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchForbiddenErrorData, http_res
            )
            raise errors.FinanceResearchForbiddenError(response_data, http_res)
        if utils.match_response(http_res, "422", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchUnprocessableEntityErrorData, http_res
            )
            raise errors.FinanceResearchUnprocessableEntityError(
                response_data, http_res
            )
        if utils.match_response(http_res, "500", "application/json"):
            response_data = unmarshal_json_response(
                errors.FinanceResearchInternalServerErrorData, http_res
            )
            raise errors.FinanceResearchInternalServerError(response_data, http_res)
        if utils.match_response(http_res, "4XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)
        if utils.match_response(http_res, "5XX", "*"):
            http_res_text = await utils.stream_to_text_async(http_res)
            raise errors.YouDefaultError("API error occurred", http_res, http_res_text)

        raise errors.YouDefaultError("Unexpected response received", http_res)

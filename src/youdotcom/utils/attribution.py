"""Build the ``X-Client-Info`` header value for outbound SDK requests.

Emits a caller-identity header so the analytics layer can distinguish
SDK traffic from other sources. SDK traffic is uniquely identified by
the leading literal ``sdk``.

``build_client_info_header`` is called per-request from
``BaseSDK._build_request_with_client`` immediately after the
``User-Agent`` header is set. It does no module-level transport
imports — ``httpx`` is pulled in lazily at the top of the function
body (as is ``youdotcom`` itself, for the version pin) so that
``import youdotcom`` does not regress because of this module.
"""

from __future__ import annotations

import sys
from typing import Optional


# Leading literal that identifies the traffic source, matching the tokens the
# MCP server (`mcp`) and the you-research skill (`skill`) emit. It names the
# *channel*, not the language: `sdk` covers every You.com SDK, and the calling
# language stays recoverable from the `ua=` segment (`python/...` vs `node/...`)
# plus the `User-Agent` (`youdotcom-python-sdk/<version>`). A single lowercase
# word also parses under the analytics recipe as written, which a hyphenated
# token does not.
_SOURCE_TOKEN = "sdk"


def validate_attribution_arg(
    name: str, value: str, *, forbidden: str = ";"
) -> None:
    """Validate an attribution header argument.

    Allows printable ASCII (``\\x20``–``\\x7e``) except the characters in
    *forbidden*. Rejects non-ASCII, control characters, and delimiter
    characters to prevent segment forgery, header injection, and encoding
    errors.

    Args:
        name: Parameter name for error messages (e.g. ``"app_title"``).
        value: Value to validate.
        forbidden: Delimiter characters to reject. Always includes ``;``
            (the segment delimiter). ``app_name`` / ``app_version`` also
            reject ``/``, because the analytics side splits
            ``client=<name>/<version>`` on the first ``/``, so a ``/``
            inside either half silently corrupts both columns.

    Raises:
        ValueError: If *value* contains characters outside printable
            ASCII or any character in *forbidden*.
    """
    reasons = {
        ";": "the segment delimiter",
        "/": "the client=<name>/<version> delimiter",
    }
    for i, ch in enumerate(value):
        o = ord(ch)
        if o < 0x20 or o > 0x7E:
            raise ValueError(
                f"{name} must be printable ASCII; "
                f"got {ch!r} (U+{o:04X}) at position {i}"
            )
        if ch in forbidden:
            raise ValueError(
                f"{name} must not contain {ch!r} "
                f"({reasons.get(ch, 'a delimiter')}); found at position {i}"
            )


def build_client_info_header(
    *,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    app_title: Optional[str] = None,
    app_url: Optional[str] = None,
) -> str:
    r"""Build the ``X-Client-Info`` header value for an outbound SDK request.

    Grammar (segments joined by ``"; "``):

        sdk[; client=<name>[/<version>]][; title=<title>][; url=<url>]; ua=python/<V> httpx/<V>

    Optional segments are dropped entirely (no leading/trailing
    ``"; "`` left behind, no empty ``=``) when their value is falsy
    (``None`` or empty string). Values must be printable ASCII
    (``\\x20``–``\\x7e``) excluding ``;``; this is validated at
    construction time in ``You.__init__`` and re-checked here as
    defense-in-depth.

    Args:
        app_name: Optional name of the application or integration calling the
            SDK. Falsy values drop the ``client=`` segment entirely, matching
            how the MCP server omits it for callers that do not identify
            themselves.
        app_version: Optional version for ``app_name``. Ignored when
            ``app_name`` is unset; emitted as ``client=<name>/<version>``.
        app_title: Optional caller-facing application title. Falsy
            values drop the ``title=`` segment.
        app_url: Optional caller-facing application URL. Falsy values
            drop the ``url=`` segment. ``?x=1``-style query strings
            survive the segment delimiter.

    Returns:
        The header value to send over the wire.

    Raises:
        ValueError: If ``app_title`` or ``app_url`` contains non-ASCII
            characters, control characters, or ``;``.

    Side effects:
        Lazily imports ``httpx`` and ``youdotcom`` to inspect their
        version metadata. Both are already loaded by the time
        ``You.search(...)`` runs an actual request, so this is a
        no-op lookup in practice — but the lazy form keeps the
        import-time footprint of ``youdotcom`` minimal
        (``import youdotcom`` does not load ``httpx``).
    """
    # pylint: disable=import-outside-toplevel  # lazy to keep httpx out
    # of ``sys.modules`` at import time.
    import httpx

    parts: list[str] = [_SOURCE_TOKEN]

    # ``client=`` identifies whoever is calling the SDK, not the SDK itself --
    # the same meaning the MCP server gives it, where the segment is dropped
    # entirely for callers that do not identify themselves. The SDK's own
    # version travels in the ``User-Agent``. Emitting ``client=youdotcom/<v>``
    # here instead would make the field constant across every row and so
    # useless as an analytics dimension.
    if app_name:
        validate_attribution_arg("app_name", app_name, forbidden=";/")
        client = app_name
        if app_version:
            validate_attribution_arg("app_version", app_version, forbidden=";/")
            client = f"{client}/{app_version}"
        parts.append(f"client={client}")

    if app_title:
        validate_attribution_arg("app_title", app_title)
        parts.append(f"title={app_title}")

    if app_url:
        validate_attribution_arg("app_url", app_url)
        parts.append(f"url={app_url}")

    py = sys.version_info
    parts.append(
        f"ua=python/{py.major}.{py.minor}.{py.micro} "
        f"httpx/{httpx.__version__}"
    )

    return "; ".join(parts)

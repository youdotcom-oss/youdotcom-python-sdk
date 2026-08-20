"""Build the ``X-Client-Info`` header value for outbound SDK requests.

Emits a caller-identity header so the analytics layer can distinguish
SDK traffic from other sources. SDK traffic is uniquely identified by
the leading literal ``python-sdk``.

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


def validate_attribution_arg(name: str, value: str) -> None:
    """Validate an attribution header argument.

    Allows printable ASCII (``\\x20``–``\\x7e``) except ``;`` (the
    segment delimiter).  Rejects non-ASCII, control characters, and
    ``;`` to prevent segment forgery, header injection, and encoding
    errors.

    Args:
        name: Parameter name for error messages (e.g. ``"app_title"``).
        value: Value to validate.

    Raises:
        ValueError: If *value* contains characters outside printable
            ASCII or contains ``;``.
    """
    for i, ch in enumerate(value):
        o = ord(ch)
        if o < 0x20 or o > 0x7E:
            raise ValueError(
                f"{name} must be printable ASCII; "
                f"got {ch!r} (U+{o:04X}) at position {i}"
            )
        if ch == ";":
            raise ValueError(
                f"{name} must not contain ';' (the segment delimiter); "
                f"found at position {i}"
            )


def build_client_info_header(
    *,
    app_title: Optional[str] = None,
    app_url: Optional[str] = None,
) -> str:
    r"""Build the ``X-Client-Info`` header value for an outbound SDK request.

    Grammar (segments joined by ``"; "``):

        python-sdk; client=youdotcom/<version>[; title=<title>][; url=<url>]; ua=python/<V> httpx/<V>

    Optional segments are dropped entirely (no leading/trailing
    ``"; "`` left behind, no empty ``=``) when their value is falsy
    (``None`` or empty string). Values must be printable ASCII
    (``\\x20``–``\\x7e``) excluding ``;``; this is validated at
    construction time in ``You.__init__`` and re-checked here as
    defense-in-depth.

    Args:
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
    import youdotcom

    parts: list[str] = ["python-sdk"]

    parts.append(f"client=youdotcom/{youdotcom.__version__}")

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

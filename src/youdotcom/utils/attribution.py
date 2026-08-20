"""Build the ``X-Client-Info`` header value for outbound SDK requests.

Emits a caller-identity header so the analytics layer can distinguish
SDK traffic from other sources. SDK traffic is uniquely identified by
the leading literal ``python-sdk``.

``build_client_info_header`` is called per-request from
``BaseSDK._build_request_with_client`` immediately after the
``User-Agent`` header is set. It does no module-level
``httpx``/``urllib`` imports — both are pulled in lazily at the
top of the function body so that ``import youdotcom`` does
not regress because of this module.
"""

from __future__ import annotations

import sys
from typing import Optional


def build_client_info_header(
    *,
    app_title: Optional[str] = None,
    app_url: Optional[str] = None,
) -> str:
    r"""Build the ``X-Client-Info`` header value for an outbound SDK request.

    Grammar (segments joined by ``"; "``):

        python-sdk; client=youdotcom/<version>[; title=<title>][; url=<url>]; ua=python/<V> httpx/<V>

    Optional segments are dropped entirely (no leading/trailing
    ``"; "`` left behind, no empty ``=``) when their value is
    ``None``. The ``title=``/``url=``/``ua=`` segments may legally
    contain ``=`` (e.g., query strings in URLs), which the trailing
    semicolons preserve.

    Args:
        app_title: Optional caller-facing application title. Falls back
            to None → ``title=`` segment is dropped.
        app_url: Optional caller-facing application URL. Falls back
            to None → ``url=`` segment is dropped. ``?x=1``-style query
            strings survive the segment delimiter because the analytics
            parser splits on the *first* ``=`` only.

    Returns:
        The header value to send over the wire. Empty segment handles
        do not show up.

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

    if app_title is not None:
        parts.append(f"title={app_title}")

    if app_url is not None:
        parts.append(f"url={app_url}")

    py = sys.version_info
    parts.append(
        f"ua=python/{py.major}.{py.minor}.{py.micro} "
        f"httpx/{httpx.__version__}"
    )

    return "; ".join(parts)

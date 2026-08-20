"""Build the ``X-Client-Info`` header value for outbound SDK requests.

Emits a caller-identity header so the analytics layer can distinguish
SDK traffic from other sources. SDK traffic is uniquely identified by
the leading literal ``sdk``.

``build_client_info_header`` is called per-request from
``BaseSDK._build_request_with_client`` immediately after the
``User-Agent`` header is set. It does no module-level transport
imports: ``httpx`` is pulled in lazily at the top of the function body,
so ``import youdotcom`` does not regress because of this module.
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
        forbidden: Extra delimiter characters to reject, *in addition to*
            ``;``, which is always rejected because it separates segments.
            ``app_name`` / ``app_version`` pass ``"/"`` here, because the
            ``client=<name>/<version>`` value is split on ``/`` downstream,
            so a ``/`` inside either half silently corrupts both.

    Raises:
        ValueError: If *value* contains characters outside printable
            ASCII, ``;``, or any character in *forbidden*.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{name} must be a str; got {type(value).__name__}. "
            "Every attribution value is interpolated into the header verbatim, "
            "so a non-str would be rendered via repr() and corrupt the segment."
        )
    if value != value.strip():
        # Two failures in one: a whitespace-only value is treated as absent by
        # the falsy gates downstream, so it ships an empty-looking segment
        # (``client= /1.0``) -- the silent loss the app_name/app_version pairing
        # guard exists to prevent. And a padded value (``" acme "``) becomes a
        # distinct analytics key that never groups with the unpadded rows.
        # Reject rather than silently strip, so the caller sees the mistake.
        raise ValueError(
            f"{name} must not have leading or trailing whitespace; "
            f"got {value!r}"
        )
    reasons = {
        ";": "the segment delimiter",
        "/": "the client=<name>/<version> delimiter",
    }
    # ``;`` is unconditional: it is the delimiter this validator exists to
    # protect, so an override must never be able to drop it.
    rejected = ";" + forbidden
    for i, ch in enumerate(value):
        o = ord(ch)
        if o < 0x20 or o > 0x7E:
            raise ValueError(
                f"{name} must be printable ASCII; "
                f"got {ch!r} (U+{o:04X}) at position {i}"
            )
        if ch in rejected:
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
    (``\x20``–``\x7e``) excluding ``;``, and ``app_name`` / ``app_version``
    additionally exclude ``/``; this is validated at construction time in
    ``You.__init__`` and re-checked here as defense-in-depth.

    Args:
        app_name: Optional name of the application or integration calling the
            SDK. Falsy values drop the ``client=`` segment entirely, matching
            how the MCP server omits it for callers that do not identify
            themselves.
        app_version: Optional version for ``app_name``, emitted as
            ``client=<name>/<version>``. Ignored when ``app_name`` is falsy.
            Note this differs from ``You.__init__``, which rejects that
            combination outright: the constructor is where a caller mistake
            should surface, while this builder stays permissive so it can
            never be the thing that raises mid-request.
        app_title: Optional caller-facing application title. Falsy
            values drop the ``title=`` segment.
        app_url: Optional caller-facing application URL. Falsy values
            drop the ``url=`` segment. ``?x=1``-style query strings
            survive the segment delimiter.

    Returns:
        The header value to send over the wire.

    Raises:
        ValueError: If any argument contains non-ASCII characters, control
            characters, or a delimiter (``;`` for all of them, plus ``/``
            for ``app_name`` and ``app_version``).

    Side effects:
        Lazily imports ``httpx`` to read its version for the ``ua=``
        segment. It is already loaded by the time ``You.search(...)``
        runs a real request, so this is a no-op lookup in practice, but
        the lazy form is what keeps ``import youdotcom`` from pulling
        transport into ``sys.modules``.
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
    # Defensive: a vendored/forked/distro-patched httpx may lack the dunder or
    # carry a non-ASCII or ``;``-bearing version. This segment is generated, not
    # caller-supplied, so a bad value must degrade the analytics row rather than
    # break every request (a raw ``;`` would forge a segment, and non-ASCII dies
    # in httpx header encoding with no SDK frame in the traceback).
    httpx_version = str(getattr(httpx, "__version__", "unknown"))
    if not httpx_version.isascii() or any(c in httpx_version for c in ";/"):
        httpx_version = "unknown"
    parts.append(
        f"ua=python/{py.major}.{py.minor}.{py.micro} httpx/{httpx_version}"
    )

    return "; ".join(parts)

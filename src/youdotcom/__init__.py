"""Public surface for ``youdotcom``.

Imports are resolved lazily via PEP 562 module ``__getattr__`` so that
``import youdotcom`` does **not** pull transport-layer modules
(``httpx``, ``urllib.request``) into ``sys.modules``. This matters for
Temporal Workflow sandboxes, which reject transport imports at Worker
construction time and cannot be patched around with
``workflow.unsafe.imports_passed_through()`` because the parent package
import runs before any submodule body.

Public surface (via ``from youdotcom import <name>``):

- ``You`` — the unified API client (from ``.sdk``)
- ``VERSION`` / ``OPENAPI_DOC_VERSION`` / ``USER_AGENT`` — version pins
  populated from ``_version.py`` at module load

Backward-compatibility re-exports (previously available via
``from .sdk import *`` / ``from .sdkconfiguration import *``):

- ``SDKConfiguration``, ``SERVERS`` — from ``.sdkconfiguration``
- ``BaseSDK`` — from ``.basesdk``
- ``HttpClient``, ``AsyncHttpClient``, ``ClientOwner``, ``close_clients`` —
  from ``.httpclient``
- ``Logger``, ``get_default_logger`` — from ``.utils.logger``
- ``RetryConfig``, ``BackoffStrategy`` — from ``.utils.retries``
- ``HookContext``, ``SDKHooks`` — from ``._hooks``
- ``ContentsShim``, ``SearchShim`` — from ``._shims``
- ``OptionalNullable``, ``UNSET`` — from ``.types``

Sub-packages accessed as ``youdotcom.<name>.X``:

- ``models``, ``errors``, ``utils``, ``types``

Lazy-init port. Mirrors the pattern used in
``youdotcom.models.__init__`` (shipped in 3.0.0) at the SDK root.
"""

from typing import Any, TYPE_CHECKING

from youdotcom.utils.dynamic_imports import lazy_getattr, lazy_dir

from ._version import (
    __openapi_doc_version__,
    __title__,
    __user_agent__,
    __version__,
)

if TYPE_CHECKING:
    # The sub-packages are named in ``__all__`` (see the comment there), and a
    # type checker resolves ``__all__`` entries statically — it does not know
    # about the PEP 562 ``__getattr__`` that binds them at runtime. Without
    # these, pyright reports ``reportUnsupportedDunderAll`` for each one, and
    # this package ships ``py.typed``, so that lands in consumers' editors.
    # ``TYPE_CHECKING`` is ``False`` at runtime, so this costs no import.
    from . import errors, models, types, utils
    from .sdk import You
    from .sdkconfiguration import SDKConfiguration, SERVERS
    from .basesdk import BaseSDK
    from .httpclient import AsyncHttpClient, ClientOwner, HttpClient, close_clients
    from .utils.logger import Logger, get_default_logger
    from .utils.retries import BackoffStrategy, RetryConfig
    from ._hooks import HookContext, SDKHooks
    from ._shims import ContentsShim, SearchShim
    from .types import OptionalNullable, UNSET


__all__ = [
    "OPENAPI_DOC_VERSION",
    "USER_AGENT",
    "VERSION",
    "You",
    # NOTE: the ``__version__`` / ``__title__`` / ``__user_agent__`` /
    # ``__openapi_doc_version__`` dunders are deliberately NOT listed here.
    # Without ``__all__``, ``from youdotcom import *`` skips underscore names;
    # naming them would bind them, so a consumer package that sets its own
    # ``__version__`` and then star-imports the SDK would silently report the
    # SDK's version as its own. They stay reachable as plain attributes
    # (``youdotcom.__version__``, ``from youdotcom import __version__``),
    # exactly as they were through 3.1.1.
    # Backward-compatibility re-exports
    "SDKConfiguration",
    "SERVERS",
    "BaseSDK",
    "HttpClient",
    "AsyncHttpClient",
    "ClientOwner",
    "close_clients",
    "Logger",
    "get_default_logger",
    "RetryConfig",
    "BackoffStrategy",
    "HookContext",
    "SDKHooks",
    "ContentsShim",
    "SearchShim",
    "OptionalNullable",
    "UNSET",
    # Sub-packages. Listed here (not just in ``_sub_packages``) because
    # ``from youdotcom import *`` binds exactly the names in ``__all__``;
    # omitting them would silently stop `import *` followed by
    # ``models.SearchRequestBody(...)`` from resolving, which the eager
    # ``from .sdk import *`` surface supported through 3.1.1.
    "errors",
    "models",
    "types",
    "utils",
]


# Explicit module-level constants. These are cheap strings resolved
# eagerly from ``_version.py``, which doesn't pull transport-layer
# modules. Keeping them as real attributes (vs. routing through
# ``__getattr__``) preserves `from youdotcom import VERSION` ergonomics
# and avoids the overhead of an indirection on a one-line lookup.
VERSION: str = __version__
OPENAPI_DOC_VERSION: str = __openapi_doc_version__
USER_AGENT: str = __user_agent__


# Lazy mapping for public attributes that require importing a submodule
# on first access. Each entry maps a public name to its source module.
_dynamic_imports: dict[str, str] = {
    "You": ".sdk",
    "SDKConfiguration": ".sdkconfiguration",
    "SERVERS": ".sdkconfiguration",
    "BaseSDK": ".basesdk",
    "HttpClient": ".httpclient",
    "AsyncHttpClient": ".httpclient",
    "ClientOwner": ".httpclient",
    "close_clients": ".httpclient",
    "Logger": ".utils.logger",
    "get_default_logger": ".utils.logger",
    "RetryConfig": ".utils.retries",
    "BackoffStrategy": ".utils.retries",
    "HookContext": "._hooks",
    "SDKHooks": "._hooks",
    "ContentsShim": "._shims",
    "SearchShim": "._shims",
    "OptionalNullable": ".types",
    "UNSET": ".types",
}


# Sub-packages accessible as ``youdotcom.<name>`` (PEP 562 routes the
# attribute lookup through ``__getattr__`` so the submodule is imported
# on demand, the first time someone touches it).
_sub_packages: list[str] = [
    "errors",
    "models",
    "types",
    "utils",
]


def __getattr__(attr_name: str) -> Any:
    return lazy_getattr(
        attr_name,
        package=__package__,
        dynamic_imports=_dynamic_imports,
        sub_packages=_sub_packages,
    )


def __dir__():
    return sorted(
        set(
            lazy_dir(
                dynamic_imports=_dynamic_imports,
                sub_packages=_sub_packages,
            )
        )
        | set(__all__)
        # Version dunders are deliberately excluded from ``__all__`` (so a
        # star-import can't clobber a consumer's own ``__version__``), but
        # they are real module attributes and should remain discoverable
        # via ``dir()`` / IDE autocomplete.
        | {"__version__", "__title__", "__user_agent__", "__openapi_doc_version__"}
    )

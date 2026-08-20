"""Public surface for ``youdotcom``.

Imports are resolved lazily via PEP 562 module ``__getattr__`` so that
``import youdotcom`` does **not** pull transport-layer modules
(``httpx``, ``urllib.request``) into ``sys.modules``. This matters for
Temporal Workflow sandboxes, which reject transport imports at Worker
construction time and cannot be patched around with
``workflow.unsafe.imports_passed_through()`` because the parent package
import runs before any submodule body.

Public surface (trying out ``from youdotcom import <name>``):

- ``You`` — the unified API client (from ``.sdk``)
- ``VERSION`` / ``OPENAPI_DOC_VERSION`` / ``USER_AGENT`` — version pins
  populated from ``_version.py`` at module load

Sub-packages accessed as ``youdotcom.<name>.X``:

- ``models``, ``errors``, ``utils``, ``types``, ``_hooks``, ``_shims``

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
    from .sdk import You


__all__ = [
    "OPENAPI_DOC_VERSION",
    "USER_AGENT",
    "VERSION",
    "You",
    "__openapi_doc_version__",
    "__title__",
    "__user_agent__",
    "__version__",
]


# Explicit module-level constants. These are cheap strings resolved
# eagerly from ``_version.py``, which doesn't pull transport-layer
# modules. Keeping them as real attributes (vs. routing through
# ``__getattr__``) preserves `from youdotcom import VERSION` ergonomics
# and avoids the overhead of an indirection on a one-line lookup.
VERSION: str = __version__
OPENAPI_DOC_VERSION: str = __openapi_doc_version__
USER_AGENT: str = __user_agent__


# Lazy mapping for the single non-constant public attribute, ``You``.
_dynamic_imports: dict[str, str] = {
    "You": ".sdk",
}


# Sub-packages accessible as ``youdotcom.<name>`` (PEP 562 routes the
# attribute lookup through ``__getattr__`` so the submodule is imported
# on demand, the first time someone touches it).
_sub_packages: list[str] = [
    "_hooks",
    "_shims",
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
    )

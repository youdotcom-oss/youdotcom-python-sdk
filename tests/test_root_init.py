"""Tests for the ``youdotcom`` package root module.

Importing the package must not pull transport-layer modules
(``httpx``, ``urllib.request``) into ``sys.modules``. This matters for
Temporal Workflow sandboxes, which reject transport imports at Worker
construction time and cannot be patched around with
``workflow.unsafe.imports_passed_through()`` because the parent package
import runs before any submodule body.

The transport invariant is enforced in a **subprocess** so that the
assertion holds against the real module-loading order. An in-process
test could pass even when the eager import sneaks in, because earlier
test-side imports may already have populated ``sys.modules`` for
httpx / urllib.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap


def _run_in_subprocess(snippet: str) -> tuple[int, str, str]:
    """Run ``snippet`` in a fresh Python subprocess and return (rc, stdout, stderr).

    Uses ``sys.executable`` (the interpreter pytest is running under,
    which is the venv python when invoked via ``uv run``) so the
    subprocess sees the installed SDK on its ``sys.path``. We do **not**
    pass ``-S``: that flag disables the venv's ``site.py`` shim and
    would render the SDK uninstalled for the subprocess.
    """
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(snippet)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return result.returncode, result.stdout, result.stderr


def test_root_import_does_not_load_https_libs() -> None:
    """``import youdotcom`` must leave httpx and urllib.request off sys.modules.

    Regression guard; failing this means ``youdotcom/__init__.py``
    has re-introduced an eager import path that drags transport modules in
    at ``import`` time.
    """
    snippet = """
        import sys

        import youdotcom

        # Transport-layer modules must NOT be present after a bare
        # ``import youdotcom``. ``urllib.request`` is enough of a marker
        # because the offending ``from .sdk import *`` pulls the full
        # ``urllib`` subtree transitively.
        httpx_loaded = "httpx" in sys.modules
        urllib_request_loaded = "urllib.request" in sys.modules
        if httpx_loaded or urllib_request_loaded:
            print("TRANSPORT_LEAK:", "httpx", httpx_loaded, "urllib.request", urllib_request_loaded)
            sys.exit(2)

        sys.exit(0)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, (
        "import youdotcom leaked transport-layer modules.\n"
        f"stdout: {stdout!r}\nstderr: {stderr!r}"
    )


def test_root_import_exposes_you_class() -> None:
    """``from youdotcom import You`` resolves to ``BaseSDK`` subclass.

    The root package's public surface contract is a single class export,
    ``You``, plus module-level constants and sub-package access. This
    is the import path every existing test in ``tests/`` uses.
    """
    snippet = """
        import sys
        from youdotcom import You
        from youdotcom.basesdk import BaseSDK
        if not (isinstance(You, type) and issubclass(You, BaseSDK)):
            print("PUBLIC_SURFACE_MISMATCH:", You)
            sys.exit(2)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, f"from youdotcom import You failed: {stdout!r} {stderr!r}"


def test_root_import_exposes_subpackages() -> None:
    """``youdotcom.models``, ``youdotcom.errors`` etc. resolve as sub-package attributes."""
    snippet = """
        import sys
        import youdotcom.models  # noqa: F401
        import youdotcom.errors  # noqa: F401
        import youdotcom.utils   # noqa: F401
        import youdotcom.types   # noqa: F401

        missing = [
            name
            for name in ("models", "errors", "utils", "types")
            # sub-package attribute access must not raise AttributeError
            if not hasattr(__import__("youdotcom"), name)
        ]
        if missing:
            print("MISSING_SUBPACKAGES:", missing)
            sys.exit(2)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, f"sub-package access failed: {stdout!r} {stderr!r}"

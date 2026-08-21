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

import os
import pathlib
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

    ``PYTHONPATH`` is set to the repo's ``src`` explicitly. A subprocess does
    not inherit pytest's ``pythonpath = ["src"]`` injection, so relying on the
    package being installed makes these tests fail confusingly (a
    ``ModuleNotFoundError`` for ``youdotcom``, reported as a transport leak)
    for anyone running the suite against a bare checkout.
    """
    src = pathlib.Path(__file__).resolve().parent.parent / "src"
    env = {**os.environ}
    env["PYTHONPATH"] = (
        f"{src}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(src)
    )
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(snippet)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=env,
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

        import youdotcom

        # Deliberately NO `import youdotcom.models` here: importing a submodule
        # binds it as an attribute on the parent package, which would satisfy
        # the hasattr below without ever reaching the PEP 562 __getattr__ this
        # test exists to exercise.
        missing = [
            name
            for name in ("models", "errors", "utils", "types")
            # sub-package attribute access must not raise AttributeError
            if not hasattr(youdotcom, name)
        ]
        if missing:
            print("MISSING_SUBPACKAGES:", missing)
            sys.exit(2)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, f"sub-package access failed: {stdout!r} {stderr!r}"


def test_star_import_binds_documented_surface() -> None:
    """``from youdotcom import *`` binds every name in ``__all__``.

    The sub-packages are the part worth guarding: ``import *`` binds
    exactly ``__all__``, so a sub-package reachable via attribute access
    (``youdotcom.models``) can still silently drop out of the star-import
    surface. Code doing ``from youdotcom import *`` followed by
    ``models.SearchRequestBody(...)`` worked through 3.1.1 and must keep
    working. ``test_root_import_exposes_subpackages`` covers attribute
    access and would pass even with the star-import surface broken.
    """
    snippet = """
        import sys

        import youdotcom

        namespace = {}
        exec("from youdotcom import *", namespace)

        missing = [name for name in youdotcom.__all__ if name not in namespace]
        if missing:
            print("MISSING_FROM_STAR_IMPORT:", missing)
            sys.exit(2)

        # Spot-check that a star-imported sub-package is actually usable,
        # not just bound to something truthy.
        models = namespace["models"]
        if models.SearchRequestBody(query="x").query != "x":
            print("SUBPACKAGE_UNUSABLE")
            sys.exit(3)

        for name in ("models", "errors", "utils", "types"):
            if name not in namespace:
                print("SUBPACKAGE_NOT_STAR_IMPORTED:", name)
                sys.exit(4)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, f"star-import surface regressed: {stdout!r} {stderr!r}"


def test_star_import_does_not_clobber_consumer_dunders() -> None:
    """``import *`` must not bind the version dunders.

    Without ``__all__`` CPython skips underscore names on a star import;
    naming them in ``__all__`` binds them. A consumer package that sets its
    own ``__version__`` in ``__init__.py`` and then star-imports the SDK would
    silently report the SDK's version as its own -- wrong output in a CLI
    ``--version``, a setuptools dynamic version, or an ``importlib.metadata``
    fallback. They must stay reachable as attributes either way.
    """
    snippet = """
        import sys

        namespace = {"__version__": "1.0.0-consumer", "__title__": "consumer-pkg"}
        exec("from youdotcom import *", namespace)

        clobbered = {
            name: namespace[name]
            for name, original in (
                ("__version__", "1.0.0-consumer"),
                ("__title__", "consumer-pkg"),
            )
            if namespace[name] != original
        }
        if clobbered:
            print("CONSUMER_DUNDERS_CLOBBERED:", clobbered)
            sys.exit(2)

        # ...but they must still be importable explicitly.
        from youdotcom import __title__, __version__  # noqa: F401

        if not __version__:
            print("DUNDER_NOT_REACHABLE")
            sys.exit(3)
    """
    rc, stdout, stderr = _run_in_subprocess(snippet)
    assert rc == 0, f"star-import clobbered consumer dunders: {stdout!r} {stderr!r}"

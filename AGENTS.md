# You.com Python SDK

Official Python SDK for the You.com API, published to PyPI as `youdotcom`. Since v3.0.0
(2026-08-06) it is **hand-maintained, not generated** — do not treat `src/openapi/_hooks/`
as authoritative.

## Stack

Python >=3.10, src-layout, uv. Deps: `httpx`, `httpcore`, `pydantic>=2.11`. Go 1.22 mock
server for tests (`tests/mockserver/`, port 18080).

## Commands

```shell
uv sync --dev
./scripts/run_tests.sh                   # starts mock server, pytest, cleanup
mypy src/youdotcom/
pylint src/youdotcom/ --rcfile=pylintrc
python scripts/check_drift.py            # OpenAPI drift: 0=clean, 1=drift, 2=specs down
./scripts/run_performance_tests.sh --quick
scripts/publish.sh                       # build + publish (needs $PYPI_TOKEN)
```

## Must-know

- **`timeout_ms` is doing real work** — without it httpx's 5s default raises
  `httpx.ReadTimeout` on most calls.
- Key resolution: `api_key_auth` arg -> `YDC_API_KEY` -> legacy `YOU_API_KEY_AUTH`. Never
  default to `""` — an empty string raises `ValueError`; use `os.getenv("YDC_API_KEY")`.
- `You` is a context manager and is **not reusable after `with` exits**; never close
  caller-supplied transports.
- `include_domains` cannot combine with `exclude_domains`/`boost_domains` (422).
- `server_url` only affects `api.you.com` endpoints; search/contents default to
  `ydc-index.io` and must be overridden per call.
- Research helpers bound waits: 10 min default, 4h for `frontier`.
- Never enable `YOU_DEBUG=1` in production; never commit debug logs.

## Verification

CI gate (`test.yml`): `pytest tests/` (excluding live/perf) + `mypy` + pylint errors-only
(tree is clean at 10.00/10). Test hygiene: leaked HTTP transports fail tests
(ResourceWarning-as-error). SemVer: breaking changes need `MIGRATION.md` + `CHANGELOG.md`.

## Adding a new parameter to search

1. **Add to method signatures** — `_search_impl` and `search_async` must both accept the
   new parameter (they share all logic via `_build_search_request`; never duplicate the
   body-construction block).
2. **Add to `SearchRequestBody`** — the model field (with docstring), the TypedDict field,
   and the `optional_fields` set in `serialize_model`. All three must be in sync.
3. **Normalize at the SDK layer** — if the API expects a specific casing, add a `_lower` or
   `_upper` call so callers can pass plain strings (the SDK normalizes to the casing the
   API expects).
4. **Add tests** — unit tests in `tests/test_search.py` (MockTransport), plus a live test
   in `tests/test_live.py` if the parameter affects actual API behavior.
5. **Update docs** — README.md examples, USAGE.md if it's a user-facing feature. The
   parameter table rows in `docs/sdks/{search,you}/README.md` and
   `docs/models/searchrequestbody.md` need a new row that matches the surrounding
   `Type` cell notation exactly.
6. **Run a surface sweep** — when the new parameter supersedes, renames, or deprecates
   anything already exposed, every surface that mentioned the previous name must also
   teach the new one. See "When the new parameter deprecates or replaces an existing one"
   below for the full checklist.

## Serialization pattern

`SearchRequestBody.serialize_model` uses a `model_serializer(mode="wrap")` that builds an
allowlist of optional fields. Fields with `None` values are dropped from the wire **if**
the field is in `optional_fields` (otherwise they serialize as JSON `null`). This means:

- Add new optional fields to the `optional_fields` set, or they'll serialize as `null` when `None`.
- To omit a field entirely by passing `None` (e.g. `language=None`), it must be in `optional_fields`.
- To intentionally send JSON `null`, do not add the field to `optional_fields`.
- Sub-models (`ExtractionHighlights`, `ExtractionFullPage`, `Extraction`) use their own
  `model_serializer(mode="wrap")` that drops `None` values so absent fields stay off the wire.

## TypedDict + Pydantic model pattern

When adding a new user-facing type:

1. Create the **TypedDict** first (in its own module if complex) — this is the type hint
   surface for callers who want to use dicts instead of models.
2. Create the **Pydantic model** with `extra="forbid"` on a strict base class — this catches
   unknown keys locally so callers fail-fast instead of routing to a 422.
3. Add type aliases (`Union[Enum, Literal[...]]`) on TypedDict enum fields so callers can
   pass plain strings (the SDK normalizes at the method layer).
4. Export both from `src/youdotcom/models/__init__.py` using the lazy-import pattern.

## The extraction model pattern (strict base + sub-models)

The `extraction` module demonstrates the recommended pattern for new typed API objects:

- **`_StrictExtractionBase`** — Pydantic model with `extra="forbid"`, `populate_by_name=True`,
  `protected_namespaces=()`, `arbitrary_types_allowed=True`. All sub-models inherit from this.
- **Sub-models** (`ExtractionHighlights`, `ExtractionFullPage`) — each has a
  `model_serializer(mode="wrap")` that drops `None` values.
- **Top-level model** (`Extraction`) — has a `model_validator(mode="after")` that enforces
  mutual-exclusion constraints (e.g. `highlights` only valid with `extraction_mode=HIGHLIGHTS`).
- **`model_validate()`** on the top-level model accepts both model instances and dicts —
  callers can pass `{"extraction_mode": "highlights"}` or `Extraction(extraction_mode=...)`.

## The shim pattern (backward compat)

When adding a new parameter that should also flow through backward-compat shims:

1. Add the parameter to `_shims.py` `SearchShim.__call__`, `unified`, and `unified_async`.
2. Forward the parameter to `self._you._search_impl(...)` or `search_async(...)`.
3. The shim's `__call__` emits `DeprecationWarning` with `stacklevel=3` so the warning
   reports the user frame, not the shim.
4. Add tests in `tests/test_shims.py` to verify the parameter is forwarded correctly.

## The lazy import pattern in models/__init__.py

New model exports go in three places in `__init__.py`:

1. **`TYPE_CHECKING` block** — import the class so type checkers see it.
2. **`__all__` list** — add the name so `from youdotcom.models import X` works.
3. **`_module_map` dict** — map the name to the source module path (e.g. `".extraction"`)
   so runtime imports are lazy and don't cause circular imports.

## When the new parameter deprecates or replaces an existing one

When introducing a parameter that supersedes, renames, or removes anything already
shipped in `SearchRequestBody`, every surface that mentioned the previous name must be
swept. Missing a surface is the most common agent bug on this codebase — even one
stray doc referencing the old name reads as evidence of a half-finished migration.

1. **`MIGRATION.md`** — on every minor bump that ships a deprecation, add a
   `## <old-version> → <new-version>` section even if the old form still works. The
   section needs: a mapping table (old → new), before/after Python code blocks for both
   dict and model forms, a "no code change required" snippet when both still work, and
   a removal-in note (e.g. "removal targeted for 4.0.0").
2. **`examples/api-example-calls.py`** — add or replace a runnable demo for the affected
   method matching the existing print/output pattern. Keep a paired "legacy" demo only
   when the deprecated form still works. Update the `FUNCTIONS` menu in lockstep.
3. **`tests/test_performance.py`** — if the parameter affects latency (network I/O,
   payload size, outgoing bytes per request), add a perf case mirroring the pattern of
   the analogous deprecated case. Use the same `create_timing_client("post_/v1/search")`
   + `measure_sdk_call(...)` + `ALL_METRICS.append(...)` recipe.
4. **New model pages** — if a new Pydantic model was added, create
   `docs/models/<modelname>.md` with a description, a runnable example (both dict and
   model forms), and a fields table. Match `docs/models/extraction.md`'s format
   exactly.
5. **Existing model pages** — fields added to existing models (`Contents.highlights`,
   etc.) get a row in `docs/models/<thatmodel>.md`'s field table; the model's prose
   description is rewritten so it reads "if `extraction` was enabled (formerly
   `livecrawl`)" rather than the old phrasing.
6. **Docstring carry-over** — narration on `Contents` / `WebResult.contents` /
   `NewsResult.contents` and similar fields is rewritten with `(formerly X)` when the
   behavior is identical between old and new parameters.
7. **CHANGELOG.md and README.md** — read together: every feature on the README usage
   section should match a CHANGELOG entry, and the CHANGELOG should mention the
   deprecation/removal note if any.
8. **`USAGE.md`** — if usage prose mentions the deprecated parameter, update the prose
   to teach the new parameter and demote the old one with a `(formerly X)` note.

Skip a step only when that surface legitimately does not apply (no MIGRATION section on
a non-deprecating change). Document any skip in the PR body.

## The plus-value rule pattern

When a parameter combination is invalid on the wire but you want default callers to work
without 422 errors:

1. Detect the conflict in `_build_search_request` (the shared helper).
2. Strip the conflicting parameter from the body (set to `None` so the serializer drops it).
3. Warn with `UserWarning` if the caller set a non-default value — default callers stay
   silent. Use `stacklevel=4` since the helper adds a frame.
4. Document the rule in the method docstring and the parameter docstring.
5. Add tests: one for the default case (silent strip), one for explicit non-default (warns
   + strips), and one for the non-conflicting case (keeps the value).

## Adding new tests

- **Unit tests** use `httpx.MockTransport` — no mock server needed. The `_capture()` context
  manager in `tests/test_extraction.py` is the standard pattern: yield `(you, captured)`
  where `captured["body"]` has the JSON that went over the wire.
- **Live tests** require `YDC_API_KEY` and run against the real API. Mark with
  `@requires_api_key` and keep them minimal — they verify the SDK doesn't crash, not the
  API behavior.
- **Mock server** (`tests/mockserver/`) is a Go app that serves static JSON responses.
  It's used by `run_tests.sh` but is not required for unit tests (which use MockTransport).
- Tests that depend on the mock server (port 18080) will fail with `Connection refused` if
  Go is not installed. State which checks were skipped and why.

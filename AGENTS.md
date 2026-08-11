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

## Surface sweep: pitfalls that survive the first pass

The 8-step surface sweep above catches most rename/deprecation oversights, but the
categories below still slipped through on PR #40. Codify them so they don't reopen
the same review threads on the next migration.

### Docstring sync between TypedDict and Pydantic

The same field has **two docstrings** in `SearchRequestBody`: one on the `TypedDict`
field and one on the Pydantic field. Editing only the Pydantic string leaves the IDE
surface (via the TypedDict) stale, and vice versa. Always edit both in lockstep after
any behavior or wording change.

### Module-level docstrings on model files

A model's module docstring at the top of `src/youdotcom/models/<x>.py` often describes
the SDK-layer behavior of a parameter (`models/extraction.py`'s `crawl_timeout`
stanza is an example). When that parameter's behavior changes, the module docstring
is also stale even if the field-level docstrings are not. Re-read the full module
docstring from top to bottom after any behavior edit.

### Result-class pages

`docs/models/webresult.md`, `docs/models/newsresult.md`, and similar `*result.md`
pages have `contents` rows that describe the **gating parameter** for livecrawl-family
behavior — phrased in terms of the deprecated name (e.g. "Contents of the page if
`livecrawl` was enabled"). When the gating parameter is renamed or deprecated, those
rows must read "if `extraction` was enabled (formerly `livecrawl`)" instead. Step 5
above lists "existing model pages" but does not call out `*result.md` files; grep
`docs/models/*result.md` for the deprecated name on every rename sweep.

### Cross-table identity

The same parameter appears in `docs/sdks/you/README.md`, `docs/sdks/search/README.md`,
`docs/models/searchrequestbody.md`, **and** the TypedDict + Pydantic field docstrings
in `src/youdotcom/models/`. The `Description` cells in those four locations must read
identically (the Search sub-SDK table may add a no-op note when the underlying
endpoint genuinely strips the field, but otherwise the wording is fixed). After
updating one, the others must also be updated; divergent wording is a near-guaranteed
review comment.

### Type cells in field tables come from the annotation

The `Type` column of `docs/models/<model>.md` is the caller-facing paraphrase of the
model's actual annotation. `Optional[List[str]]` becomes `Optional[List[*str*]]`, not
`List[*str*]`. Eyeball every row in the touched model page for the same
cell-vs-annotation drift; one botched cell sits there forever otherwise.

### Examples must be copy-paste runnable

A `## Example Usage` block in `docs/**/*.md` (or `README.md` / `USAGE.md`) is a
contract with the reader that copy-pasting the snippet will work on a fresh checkout.
Any snippet that calls `you.search(...)` without constructing a `You` instance — or
without showing the `import` lines that back the snippet — fails that contract with
`NameError: name 'you' is not defined`. Always include: (1) the `import` statements,
(2) client construction via `You(api_key_auth=os.getenv("YDC_API_KEY"))`, and (3) a
`with ... as you:` context for any method calls. Match the pattern used elsewhere in
`docs/sdks/*` before committing the snippet.

### Examples with network calls pass `timeout_ms`

Any snippet that triggers a network round-trip (`you.search`, `you.contents`,
`you.research`, anything with `crawl_timeout` or `extraction_mode="full_page"`)
must pass an explicit `timeout_ms` to `You(...)`. httpx's 5-second default raises
`ReadTimeout` on most real calls (the "must-know" line at the top of this file
already calls this out). A round-trip ready-to-run snippet without `timeout_ms`
is a copy-paste footgun. Use 60_000 ms (60 s) as the default for snippet
examples; live tests can vary by call shape.

### Deprecating an existing field on a model class

When renaming or deprecating a parameter that already lives on
`SearchRequestBody`, update **both** the TypedDict field docstring and the
Pydantic field docstring. They are not auto-synced — IDE/type-helper parity fails
otherwise. The opening of each docstring should start with *"Deprecated; use
`<new-name>` instead."* so callers browsing the IDE surface see it explicitly.
The same wording is used in the docs tables (`docs/sdks/you/README.md`,
`docs/sdks/search/README.md`, `docs/models/searchrequestbody.md`) — keep all
four surfaces in lockstep.

## Warn-then-raise vs raise-then-warn (Python gotcha)

When the helper that detects a conflict also has reason to warn (e.g. an `extraction`
vs. deprecated `livecrawl` conflict, plus a `DeprecationWarning` on `livecrawl`),
order the two reactions as **raise first, warn second**. Pytest and many lint runners
promote `DeprecationWarning` to an error via `-W error::DeprecationWarning`; a
warning-first ordering converts the warning into an exception that fires before the
conflict raise can run, masking the underlying 422 the caller is hitting. The
canonical ordering lives in `_build_search_request`; preserve it on future edits.

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

## Live tests are part of the contract

Live tests (`@requires_api_key`) are not homage. They are the only runtime check that
the SDK + API pair still match. Write them so a contract break fails loudly:

### Build the contract list, then assert non-empty

A live test whose body is `if result.contents: <loop with no failing assertion>`
silently passes when every result returns no contents. Instead accumulate the
observed matches into a list and assert the list is non-empty:

```python
content_seen = [
    (r.contents.html, r.contents.markdown)
    for r in res.results.web
    if r.contents and (r.contents.html is not None or r.contents.markdown is not None)
]
assert content_seen, "Expected at least one result with contents.html and/or contents.markdown"
```

The same `<x>_seen = [...filtered list...]; assert <x>_seen` pattern applies to
`contents.highlights`, `results.news[].contents`, and any "should be present"
assertion over a collection.

### `is not None`, not truthiness

The server returns empty strings for absent content, so
`assert item.contents.markdown or item.contents.html` fails even when both fields
are present but empty. Use `... is not None or ... is not None` when checking
API-returned string fields. Truthiness is not a presence check for server-returned
strings.

### Test names match assertion bodies

The function name should describe what the body asserts. A test named
`test_extraction_highlights_default_no_subkeys` that constructs
`Extraction(extraction_mode="full_page")` is a bug — rename it to
`test_extraction_full_page_default_no_subkeys`. Test-name vs body divergence is
the smoking-gun reviewer signal that the suite was written against an earlier
version of the code.

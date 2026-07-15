---
name: generate-sdk-and-open-pr
description: Generate the Speakeasy SDK for a new version and open a release PR
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
metadata:
  author: youdotcom-oss
  version: "1.0.0"
  category: release
  keywords: release, version, publish, pypi
---

# Release

Release a new version of the `youdotcom` Python SDK to PyPI and GitHub.

## Step 1: Verify OpenAPI specs

Speakeasy generates the SDK from OpenAPI specs defined in `.speakeasy/workflow.yaml`. The current source specs are:

- `https://you.com/specs/openapi_unified_agents.yaml`
- `https://you.com/specs/openapi_search_v1.yaml`
- `https://you.com/specs/openapi_contents.yaml`
- `https://you.com/specs/openapi_base.yaml`
- `https://you.com/specs/openapi_research.yaml`
- `https://you.com/specs/openapi_finance_research.yaml`

These are merged with the overlay at `overlays/python_overlay.yaml` and output to `.speakeasy/out.openapi.yaml`.

### 1a. Ask the user about spec sources

Use `AskUserQuestion` to ask:

```
The SDK is generated from these OpenAPI specs:

1. https://you.com/specs/openapi_unified_agents.yaml
2. https://you.com/specs/openapi_search_v1.yaml
3. https://you.com/specs/openapi_contents.yaml
4. https://you.com/specs/openapi_base.yaml
5. https://you.com/specs/openapi_research.yaml
6. https://you.com/specs/openapi_finance_research.yaml

Are the updates for this release already reflected in these specs, or do you have custom specs to use?
```

Options:
- **Use existing specs** (the remote URLs already have the changes)
- **Use custom specs** (user will provide spec content or file paths)

### 1b. If custom specs

If the user provides custom specs:

1. Ask which spec(s) they want to replace and get the new content or file path
2. Update the `inputs` locations in `.speakeasy/workflow.yaml` to point to the custom spec files (e.g. change the remote URL to a local path)
3. **IMPORTANT**: Do NOT commit changes to `.speakeasy/workflow.yaml`. These are temporary overrides for generation only. Remind the user that these changes should be reverted or excluded from the release commit.

If using existing specs, move on to step 2.

## Step 2: Check current versions and fetch latest changes

Before anything else, gather the current state of the world.

### 1a. Fetch all remote changes

```bash
git fetch --all --tags
```

### 1b. Check the latest GitHub release

```bash
gh release list --repo youdotcom-oss/youdotcom-python-sdk --limit 1
```

### 1c. Check the latest version on PyPI

```bash
curl -s https://pypi.org/pypi/youdotcom/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"
```

### 1d. Check the local version

Read the version from `pyproject.toml` (line 3) and `src/youdotcom/_version.py`.

### 1e. Report findings

Present a summary to the user:
- **GitHub release**: latest tag/release name
- **PyPI version**: latest published version
- **Local version**: version in pyproject.toml and _version.py
- **Unreleased commits**: `git log <latest-tag>..HEAD --oneline`

If any versions are out of sync, warn the user before proceeding.

## Step 3: Confirm the next version with the user

Analyze the unreleased commits from step 1e to determine the appropriate semver bump:
- **patch** (X.Y.Z+1): bug fixes, dependency updates, docs changes only
- **minor** (X.Y+1.0): new features, non-breaking additions
- **major** (X+1.0.0): breaking API changes, removed endpoints, changed response types

Use the highest version found across PyPI, GitHub, and local as the base for the bump.

Present the version summary and suggestion to the user using `AskUserQuestion`:

```
Latest PyPI version: X.Y.Z
Latest GitHub version: X.Y.Z
Local version: X.Y.Z

Suggested version: X.Y.Z based on [brief reasoning from commit analysis, e.g. "new endpoints added in 3 commits" or "bug fixes only"]

Proceed with update to version X.Y.Z?
```

Offer the suggested version as the recommended option, plus the other two semver bump levels as alternatives (e.g. if suggesting minor, also offer patch and major). Let the user pick or provide a custom version.

Do NOT proceed until the user confirms.

## Step 4: Generate the SDK and open a release PR

### 4a. Confirm SDK generation

Use `AskUserQuestion` to confirm:

```
Ready to run Speakeasy SDK generation for version X.Y.Z. This will regenerate the SDK source code from the OpenAPI specs.

Proceed with generation?
```

Options:
- **Yes, generate** (recommended)
- **No, cancel**

Do NOT proceed if the user cancels.

### 4b. Bump version via Speakeasy

Use `speakeasy bump` to set the version in `.speakeasy/gen.yaml`. This is the canonical way to update the Speakeasy target version.

```bash
speakeasy bump -v X.Y.Z -t you
```

This updates `python.version` in `.speakeasy/gen.yaml` to the confirmed version.

### 4c. Run Speakeasy generation

```bash
speakeasy run
```

This will:
- Fetch the OpenAPI specs (remote URLs or local overrides from step 1)
- Apply the overlay from `overlays/python_overlay.yaml`
- Regenerate all SDK source files under `src/`
- Regenerate `USAGE.md` and auto-generated sections in `README.md` (the `<!-- Start/End -->` blocks)
- Update `.speakeasy/out.openapi.yaml`

Wait for the command to complete and check for errors. If it fails, report the error to the user and stop.

### 4d. Revert temporary workflow changes

If custom specs were used in step 1, revert `.speakeasy/workflow.yaml` back to the original remote URLs:

```bash
git checkout -- .speakeasy/workflow.yaml
```

### 4e. Create a release branch

```bash
git checkout -b release/X.Y.Z
```

### 4f. Update version in all locations

Update the version string in these files (if not already updated by Speakeasy):
- `pyproject.toml` — `version = "X.Y.Z"`
- `src/youdotcom/_version.py` — `__version__: str = "X.Y.Z"` and the `__user_agent__` string

### 4g. Update markdown documentation

#### CHANGELOG.md
Add a new section at the top (below the header), following the existing Keep a Changelog format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Removed
- ...
```

Analyze the diff between the previous version and the newly generated code to determine what changed. Categorize changes into Added/Changed/Removed sections. Include code examples for significant API changes.

#### MIGRATION.md
Only update if there are breaking changes (major version bump). Add a new migration section at the top with before/after code examples, following the existing style.

#### USAGE.md
This file is auto-generated by Speakeasy (`<!-- Start/End SDK Example Usage -->` blocks). Verify it was updated by the generation step. If the examples are outdated or incorrect, update them.

#### README.md
The `<!-- Start/End -->` blocks are auto-generated by Speakeasy. Verify they were updated. Do NOT modify content outside these blocks unless necessary.

#### docs/ folder
The `docs/` folder contains auto-generated model and SDK documentation. These are updated by Speakeasy generation. Verify they look correct but do not manually edit them.

### 4h. Update and validate tests

After generation and doc updates, ensure the test suite is compatible with the new SDK code.

#### Test structure

- **Unit tests** (`tests/test_runs.py`, `tests/test_search.py`, `tests/test_contents.py`): Run against a Go mockserver in `tests/mockserver/`. These are auto-generated by Speakeasy. The mockserver is started via Docker or the compiled binary.
- **Integration tests** (`tests/test_live.py`): Run against the real You.com API. Require `YDC_API_KEY` env var.
- **Client tests** (`tests/test_client.py`): Test HTTP client setup helpers.

#### 4h-1. Update tests for new/changed APIs

Review the generated diff from step 4c. If Speakeasy added, removed, or changed any models, endpoints, or parameters:

1. Update unit tests to reflect the new request/response shapes
2. Update integration tests (`test_live.py`) if endpoints or model imports changed
3. Add new test cases for any new endpoints or features

#### 4h-2. Run unit tests

```bash
pytest tests/ --ignore=tests/test_live.py --ignore=tests/test_performance.py -v
```

If tests fail, fix the test code (or SDK issues if applicable) and re-run.

#### 4h-3. Run integration tests (if API key is available)

```bash
pytest tests/test_live.py -v
```

If `YDC_API_KEY` is not set, skip this step and note it in the PR description.

#### 4h-4. Validate tests line by line

After all tests pass, read through every changed test file line by line. Check for:
- Incorrect model imports that no longer exist
- Hardcoded values that should have been updated for the new version
- Missing assertions for new response fields
- Dead test cases for removed endpoints
- Inconsistencies between test expectations and the actual generated SDK code

If this review surfaces any changes needed, make the fixes and go back to step 4h-2. Repeat this loop until a full line-by-line review finds no additional changes needed.

### 4i. Post-generation manual fixes

Speakeasy generates the bulk of the SDK automatically, but several known disconnects require manual fixes every release. Go through each item below after generation succeeds.

#### 4i-1. Fix environment variable name (ALWAYS required)

Speakeasy generates `YOU_API_KEY_AUTH` as the env var name (derived from `envVarPrefix: YOU` + the security scheme field name `api_key_auth` in `gen.yaml`). The canonical name per `you.com/docs` is `YDC_API_KEY`.

**Fix**: Edit `src/youdotcom/utils/security.py` in the `get_security_from_env` function:

```python
# Replace this (generated):
if os.getenv("YOU_API_KEY_AUTH"):
    security_dict["api_key_auth"] = os.getenv("YOU_API_KEY_AUTH")

# With this:
api_key = os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY_AUTH")
if api_key:
    security_dict["api_key_auth"] = api_key
```

`YDC_API_KEY` is primary (canonical). `YOU_API_KEY_AUTH` is kept as fallback for users upgrading from 2.3.x without changing their environment.

Then bulk-replace `YOU_API_KEY_AUTH` with `YDC_API_KEY` across all non-source files:

```bash
# Tests, docs, README, USAGE — everywhere except security.py (which has the fallback)
sed -i '' 's/YOU_API_KEY_AUTH/YDC_API_KEY/g' \
  README.md USAGE.md tests/*.py tests/README.md \
  docs/sdks/*/README.md .agents/skills/generate-sdk-and-open-pr/SKILL.md
```

Verify only `security.py` retains `YOU_API_KEY_AUTH` (the fallback):

```bash
grep -rl "YOU_API_KEY_AUTH" --include="*.py" --include="*.md" . | grep -v __pycache__ | grep -v build/ | grep -v examples/ | grep -v tests/test_security_env.py
# Expected runtime-source hit: ./src/youdotcom/utils/security.py
# Docs and CHANGELOG/MIGRATION/USAGE may also mention YOU_API_KEY_AUTH by
# name (as the documented 2.3.x fallback being kept). tests/test_security_env.py
# is excluded because it intentionally references both env vars to lock
# in the fallback precedence.
```

#### 4i-2. Verify server URLs (do NOT change search/contents URLs)

The OpenAPI specs for search and contents use `https://ydc-index.io` as the server URL. This is correct and documented at `you.com/docs/api-reference/search/v1-search` (the page explicitly shows `GET https://ydc-index.io/v1/search`). The `api.you.com` host is a free MCP-only proxy (`/v1/agents/search`, 100 searches/day, IP-tracked) — the SDK should NOT use it for search or contents.

**Verify** (do not change) that these files still have `ydc-index.io`:

```bash
grep "ydc-index.io" src/youdotcom/models/searchop.py src/youdotcom/models/searchpostop.py src/youdotcom/models/contentsop.py
# All three should show "https://ydc-index.io"
```

The base `SERVERS` in `src/youdotcom/sdkconfiguration.py` should remain `https://api.you.com` (used by research, finance_research, agents).

#### 4i-3. Preserve and verify hand-maintained files

These files are NOT regenerated by Speakeasy and must survive across regens:

- `src/youdotcom/research_helpers.py` — background-mode helpers (`research_background`, `poll_research_task`, `research_and_wait`, `stream_research_events_raw`)
- `src/youdotcom/_hooks/registration.py` — `YDCUserAgentOverrideHook` (custom User-Agent support)

If `speakeasy run` overwrites or deletes these, restore them from git (`git checkout HEAD -- <file>`).

**Verify the User-Agent hook still works after regen**: The hook in `_hooks/registration.py` compares the configured `user_agent` against `__user_agent__` from `_version.py` (which Speakeasy regenerates) and checks the `speakeasy-sdk/` prefix to detect whether a custom UA has been set. If a future Speakeasy version changes that prefix, the hook's custom-UA detection would silently break.

```bash
# 1. Verify the hook file was not overwritten
git diff -- src/youdotcom/_hooks/registration.py
# Should show no changes (or only changes you intentionally made)

# 2. Verify __user_agent__ in _version.py still starts with the expected prefix
grep "__user_agent__" src/youdotcom/_version.py
# Should show: __user_agent__: str = "speakeasy-sdk/python ..."
# If the prefix changed from "speakeasy-sdk/", update _DEFAULT_UA_PREFIX in
# _hooks/registration.py to match

# 3. Verify the hook is still registered
grep "register_before_request_hook" src/youdotcom/_hooks/registration.py
# Should show: hooks.register_before_request_hook(YDCUserAgentOverrideHook())
```

#### 4i-4. Check for Speakeasy auto-version-bump

`speakeasy run` may auto-bump the version in `gen.yaml` and `pyproject.toml` beyond what was set in step 4b. If the version was already set correctly, manually revert:

```bash
# Check if speakeasy changed the version
git diff -- gen.yaml pyproject.toml src/youdotcom/_version.py | grep version
# If the version is wrong, revert to the intended version
```

#### 4i-5. Fix pyright/pylint issues in hand-maintained code

If `research_helpers.py` or other hand-maintained files have type-checker errors after a regen (new generated types may not match old annotations):

- **pyright**: Use `stream = await _open_raw_stream_async(...)` + `try/finally/stream.close()` instead of `async with _open_raw_stream_async(...)` (pyright treats raw coroutines as non-async-context-manager). Add return type annotations on internal helpers.
- **pylint**: Add `# pylint: disable=protected-access` on functions that access generated internals. Use `yield from stream` instead of `for evt in stream: yield evt`.

Run both checkers and fix until clean:

```bash
.venv/bin/pylint src/youdotcom/ --rcfile=pylintrc
.venv/bin/pyright src/youdotcom/research_helpers.py
```

#### 4i-6. Verify live test skip condition uses YDC_API_KEY

`tests/test_live.py` has a skip decorator that checks for the API key env var. Ensure it uses `YDC_API_KEY` (not `YOU_API_KEY_AUTH`):

```python
@pytest.mark.skipif(
    not os.getenv("YDC_API_KEY"),
    reason="YDC_API_KEY environment variable not set"
)
```

If `YDC_API_KEY` is set in the environment, live tests will run against the real API. To run only unit tests (mockserver-based), exclude live tests:

```bash
pytest tests/ --ignore=tests/test_live.py --ignore=tests/test_performance.py -v
```

#### 4i-7. Run full validation suite

After all post-generation fixes are applied, run the complete validation:

```bash
# 1. Start mockserver
cd tests/mockserver && go run . & sleep 3

# 2. Unit tests (exclude live + performance)
cd ../.. && .venv/bin/python -m pytest tests/ --ignore=tests/test_live.py --ignore=tests/test_performance.py -v
# Expected: all pass

# 3. Pylint
.venv/bin/pylint src/youdotcom/ --rcfile=pylintrc
# Expected: 10.00/10

# 4. Stop mockserver
kill $(lsof -ti:18080)
```

If any check fails, fix and re-run until all pass before committing.

#### 4i-8. Verify auto-generated Search examples are valid

Speakeasy assembles per-parameter `example` values into one combined request. For the Search API, three parameters have pairwise mutual-exclusion that the assembled example does not know about:

- `include_domains` **cannot** be combined with `exclude_domains` (returns `422`).
- `boost_domains` **cannot** be combined with `include_domains` (returns `422`).
- `exclude_domains` + `boost_domains` **is** valid.

After every regen, grep the lead Search examples in `USAGE.md` and `README.md` (specifically the `<!-- Start SDK Example Usage -->` blocks) to confirm no `search_post`/`search.unified` example combines all three of `include_domains`, `exclude_domains`, and `boost_domains`:

```bash
# Each occurrence with all three is a bug — drop include_domains (keep
# exclude_domains + boost_domains, which is the only valid pair).
grep -nE 'include_domains=\[' USAGE.md README.md
# Expected: no matches. If any are listed, hand-fix by deleting the
# "include_domains=[...]" block (and the comma before it) from each.
```

The long-term fix lives upstream: add a request-level `example` block on `SearchRequestBody` / `SearchRequest` in `overlays/python_overlay.yaml` (or the front-end OpenAPI specs) that uses a single valid pair, so Speakeasy prefers that example instead of concatenating per-field ones. Track that as a follow-up; the hand-fix above is what keeps 2.4.0 correct in the meantime.

Also scan for the `RetryConfig(...)` positional-after-kwargs regression that Speakeasy can produce when `search_post` is the lead example operation:

```bash
# If you see ", RetryConfig(...)" or similar after a keyword argument in a
# search_post example, the generated Python is a SyntaxError. Fix by
# passing `retries=RetryConfig(...)`.
grep -nE ', RetryConfig\(' README.md USAGE.md
```

If anything matches, fix by hand (overlay-up fix is the same follow-up above).

#### 4i-9. Audit empty-type / open-ended model schemas (`extra="ignore"` data-loss risk)

When the OpenAPI spec defines a schema with no `properties` (e.g. an empty typed envelope used as `output.content` for `output_schema` requests, or `task.result` for completed background research), Speakeasy emits a `BaseModel` subclass whose body is the literal `pass`:

```python
class Content(BaseModel):
    pass
```

Pydantic's default config is `extra="ignore"`, so unknown JSON keys returned by the server are silently dropped at unmarshal. The SDK cannot recover them: `res.output.content.model_dump()` returns `{}`, not the structured dict. Users of `output_schema=` and background-mode research loathe this and have hit it in 2.4.0.

**Detection** (after `speakeasy run`):

```bash
# Every BaseModel whose body is just `pass` — these are the silent-drop
# candidates. Read each one alongside the field it backs and decide whether
# the user can recover the data via a different path. If not, fix it.
python3 - <<'PY'
import re, pathlib
for p in pathlib.Path("src/youdotcom/models").glob("*.py"):
    for m in re.finditer(
        r"^class (\w+)\(BaseModel\):\n((?:[ \t]+.*?\n)+)",
        p.read_text(), re.MULTILINE,
    ):
        if m.group(2).strip() == "pass":
            print(f"{p.name}: {m.group(1)}")
PY
```

**Spec-side fix (regen-durable).** Add `additionalProperties: true` to the schema in the OpenAPI specification. Speakeasy then generates `extra="allow"` on the resulting model and unknown keys round-trip intact — see the [Speakeasy additionalProperties docs](https://www.speakeasy.com/docs/sdks/customize/data-model/additionalproperties).

Two ways to land it:

- **Upstream spec**: Edit the responsible `*.yaml` in `~/Workspace/youdotcom-frontend/public/specs/` and let the next regen pick it up.
- **OpenAPI overlay** (`overlays/python_overlay.yaml`): inject the keyword without touching upstream — survives regens and lives with this SDK. Use the [RFC 9535 JSONPath syntax](https://github.com/speakeasy-api/openapi-overlay) (`x-speakeasy-jsonpath: rfc9535`) to match the existing overlay in this repo:

  ```yaml
  overlay: 1.0.0
  x-speakeasy-jsonpath: rfc9535
  info:
    title: Allow extras on open-ended response schemas (output_schema content + background task result)
    version: 0.1.0
  actions:
    # ResearchResponse.output.content has shape oneOf: [string, object]
    # where the object branch is anonymous (no `properties`). Speakeasy
    # currently emits `class Content(BaseModel): pass` (extra="ignore") and
    # silently drops the structured payload returned by the server.
    - target: $["components"]["schemas"]["ResearchResponse"]["properties"]["output"]["properties"]["content"]["oneOf"][1]
      update:
        additionalProperties: true
    # TaskDetail.result is an anonymous object schema; same drop behaviour.
    - target: $["components"]["schemas"]["TaskDetail"]["properties"]["result"]
      update:
        additionalProperties: true
  ```

  After applying the overlay and regen, verify the generated model now allows extras:

  ```bash
  grep -nE "extra=\"allow\"|class Content\(BaseModel\):" \
      src/youdotcom/models/researchresponse.py
  # Expect: from typing import ... ConfigDict ... model_config = ConfigDict(extra="allow")
  # (or an equivalent annotation on the Content class)

  # If Content still has `pass` body and no extra="allow" config, the
  # overlay didn't apply. Double-check the JSONPath against
  # `.speakeasy/out.openapi.yaml`.
  ```

**Workaround until the fix lands.** When the typed model drops data:

- `research_helpers.py` docstring + CHANGELOG entry for `research_and_wait` MUST explicitly recommend the synchronous fallback (`client.research(..., background=False)` with the same `input`) and call out that `model_dump()` returns `{}`.
- `MIGRATION.md` `output_schema` example MUST show the same workaround rather than the misleading `output.content["..."]` syntax.
- `tests/test_research.py::TestResearchOutputSchema` MUST lock in `content_type.value == "object"` and the documented model_dump/emtpy-payload behaviour so a careless regen that re-introduces data loss fails loudly.
- Once the spec/overlay fix lands and regen produces `extra="allow"` models, simplify the workaround comments + drop the empty-payload lock-in assertion (replace with one that asserts the round-tripped dict).

**Long-term.** Treat *empty* typed schemas as a red flag in spec review. Any schema backing a user-facing response field should declare `additionalProperties: true` (or a real schema) — never `{}` / no `properties`. Add a check to the front-end repo's CI (e.g. `scripts/audit-empty-schemas.ts`) so an empty schema in `youdotcom-frontend/public/specs/*.yaml` fails the build with a message pointing to this skill step.

### 4j. Commit all changes

Stage and commit all generated and manually updated files to the release branch:

```bash
git add -A
git commit -m "feat: Python SDK X.Y.Z"
```

Do NOT commit `.speakeasy/workflow.yaml` if it still contains local spec overrides — it should have been reverted in step 4d.

### 4k. Push and open a PR

```bash
git push -u origin release/X.Y.Z
```

Open a PR against `main` using `gh`:

```bash
gh pr create --title "Python SDK X.Y.Z" --body "$(cat <<'EOF'
## Summary
- Release version X.Y.Z of the `youdotcom` Python SDK
- [Brief description of what changed based on changelog entries]

## Changes
[List key changes from the changelog]

## Checklist
- [ ] Speakeasy generation ran successfully
- [ ] Version updated in pyproject.toml, gen.yaml, and _version.py
- [ ] CHANGELOG.md updated
- [ ] MIGRATION.md updated (if breaking changes)
- [ ] README.md and USAGE.md verified
- [ ] Tests updated and passing
EOF
)"
```

Report the PR URL to the user when done.

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
- **Integration tests** (`tests/test_live.py`): Run against the real You.com API. Require `YOU_API_KEY_AUTH` env var.
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

If `YOU_API_KEY_AUTH` is not set, skip this step and note it in the PR description.

#### 4h-4. Validate tests line by line

After all tests pass, read through every changed test file line by line. Check for:
- Incorrect model imports that no longer exist
- Hardcoded values that should have been updated for the new version
- Missing assertions for new response fields
- Dead test cases for removed endpoints
- Inconsistencies between test expectations and the actual generated SDK code

If this review surfaces any changes needed, make the fixes and go back to step 4h-2. Repeat this loop until a full line-by-line review finds no additional changes needed.

### 4i. Commit all changes

Stage and commit all generated and manually updated files to the release branch:

```bash
git add -A
git commit -m "feat: Python SDK X.Y.Z"
```

Do NOT commit `.speakeasy/workflow.yaml` if it still contains local spec overrides — it should have been reverted in step 4d.

### 4j. Push and open a PR

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

---
name: sdk-review
description: Review rules for the You.com Python SDK. Use when reviewing changes to this repository.
---

# SDK Review Rules

Apply these rules to changed lines. Each rule is a short, checkable statement.

- Never default an API key to `""`. Resolve keys with `os.getenv("YDC_API_KEY")`; an empty string raises `ValueError`.
- `_search_impl` and `search_async` must accept the same parameters and build the body through `_build_search_request`; never duplicate the body-construction block.
- A new optional field on `SearchRequestBody` must be added to the model field, the TypedDict field, and the `optional_fields` set in `serialize_model`.
- New request models must set `extra="forbid"` so unknown keys fail locally instead of returning a 422.
- Never close a caller-supplied HTTP transport.
- Never enable `YOU_DEBUG=1` in production code or commit debug logs.
- Public surfaces (`CHANGELOG.md`, `README.md`, `USAGE.md`, `docs/`, docstrings) must not reference internal tickets, Linear IDs or links, or internal tooling.
- Breaking changes must update `MIGRATION.md` and `CHANGELOG.md`.
- Division or averaging helpers must raise on an empty or zero divisor instead of returning a silent default.

#!/usr/bin/env python3
"""
Drift check: compares the You.com Python SDK against the official OpenAPI specs.

Fetches OpenAPI specs from you.com/docs/openapi/ and compares:
  1. Endpoints — every path+method in the specs has a corresponding SDK method
  2. Server URLs — spec servers match SDK server constants
  3. Enums — spec enum values match SDK enum classes
  4. New APIs — specs the SDK doesn't cover yet (except known exceptions)
  5. Request parameters — spec request body properties match SDK method parameters
  6. Response schemas — spec response schema fields match SDK model fields

Usage:
    python scripts/check_drift.py            # Print warnings, exit 0 (CI, non-blocking)
    python scripts/check_drift.py --strict   # Exit 1 on drift (scheduled workflow)
    python scripts/check_drift.py --verbose  # Show all checks, even passing ones

Exit codes:
    0  no drift (or drift without --strict)
    1  drift detected (--strict only)
    2  specs could not be fetched — transient, not drift
    3  the check itself failed to run — a bug, not drift
"""

import argparse
import inspect
import re
import sys
import traceback
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAPI_INDEX = "https://you.com/docs/openapi.json"
OPENAPI_BASE = "https://you.com/docs/openapi/"

# APIs the SDK intentionally doesn't cover yet.
KNOWN_UNCOVERED = {"billing", "images"}

# Endpoints the SDK intentionally doesn't support (e.g. legacy GET search).
KNOWN_UNCOVERED_ENDPOINTS = {
    ("GET", "/v1/search"),
}

# Nested response fields the SDK models don't define yet. Keyed by (spec name,
# dotted field path from the response root). An entry that goes stale — the SDK
# catches up — is reported rather than silently ignored.
#
# Currently empty: the two gaps that recursion first surfaced
# (`AnswerSearchResult.description` / `.thumbnail_url` and
# `FinanceResearchSource.snippets`) were closed by adding the fields rather than
# suppressed. Prefer adding the field over suppressing it — the stale check can
# only see the SDK catching up, never the API starting to send a field the spec
# already promises, so a suppressed gap stays silent from that side forever.
KNOWN_RESPONSE_GAPS: dict[tuple[str, str], set[str]] = {}

# The mirror image: fields an SDK model declares that the spec schema at *this*
# path does not. The SDK shares one model across paths whose spec schemas differ
# in width, so the shared model is wider than some of them. Each entry is a field
# that is Optional and never populated at that path, so narrowing the model would
# be a breaking change with no behavioral gain. An entry that goes stale — the
# spec catches up — is reported rather than silently kept.
KNOWN_SHARED_MODEL_EXTRAS = {
    # `results.web[].contents` resolves to WebContentsPost, which defines
    # `highlights`; `results.news[].contents` resolves to the narrower Contents
    # schema (`html`, `markdown` only). The SDK uses one Contents model for both.
    # Verified against prod: with `extraction_mode="highlights"` news items carry
    # no `contents` at all, and with the deprecated `livecrawl="all"` they carry
    # `html` only — `highlights` never arrives on the news path.
    ("web-search", "results.news.contents"): {"highlights"},
}

# Map (method, path) -> SDK method name.
# {task_id} and {task_id}/stream are handled by helpers, not direct methods.
EXPECTED_ENDPOINTS = {
    ("POST", "/v1/search"): "you.search()",
    ("POST", "/v1/contents"): "you.contents()",
    ("POST", "/v1/answer"): "you.answer()",
    ("POST", "/v1/research"): "you.research()",
    ("GET", "/v1/research/{task_id}"): "you.get_research_task()",
    ("GET", "/v1/research/{task_id}/stream"): "stream_research() (helper)",
    ("POST", "/v1/finance_research"): "you.finance_research()",
}

# Map spec name -> SDK server URL constant.
EXPECTED_SERVERS = {
    "web-search": ("SEARCH_OP_SERVERS", "https://ydc-index.io"),
    "contents": ("CONTENTS_OP_SERVERS", "https://ydc-index.io"),
    "answer": ("SERVERS (default)", "https://api.you.com"),
    "research": ("SERVERS (default)", "https://api.you.com"),
    "finance-research": ("SERVERS (default)", "https://api.you.com"),
}

# Map (spec name, schema name fragment) -> SDK enum class import.
# We match schema names that contain the fragment.
ENUM_CHECKS = [
    ("research", "ResearchEffort", "youdotcom.models", "ResearchEffort"),
    ("finance-research", "ResearchEffort", "youdotcom.models", "FinanceResearchEffort"),
    ("web-search", "Freshness", "youdotcom.models", "Freshness"),
    ("answer", "Freshness", "youdotcom.models", "Freshness"),
    ("web-search", "Country", "youdotcom.models", "Country"),
    ("answer", "Country", "youdotcom.models", "Country"),
    ("research", "Country", "youdotcom.models", "Country"),
    ("web-search", "Knowledge", "youdotcom.models", "Knowledge"),
]

# SDK-internal parameters that aren't API params (excluded from drift comparison).
INTERNAL_PARAMS = {"retries", "server_url", "timeout_ms", "http_headers"}

# Map (spec_name, method, path) -> SDK method info for schema checks.
# sdk_method: attribute name on You (or "SearchShim"/"ContentsShim" for shims)
# sdk_response_models: pydantic model class names in youdotcom.models
SCHEMA_CHECKS = [
    {
        "spec": "web-search",
        "endpoint": ("POST", "/v1/search"),
        "sdk_method": "SearchShim.__call__",
        "sdk_response_models": ["SearchResponse"],
    },
    {
        "spec": "contents",
        "endpoint": ("POST", "/v1/contents"),
        "sdk_method": "ContentsShim.__call__",
        "sdk_response_models": ["ContentsResponse"],
    },
    {
        "spec": "answer",
        "endpoint": ("POST", "/v1/answer"),
        "sdk_method": "answer",
        "sdk_response_models": ["AnswerResponse"],
    },
    {
        "spec": "research",
        "endpoint": ("POST", "/v1/research"),
        "sdk_method": "research",
        "sdk_response_models": ["ResearchResponse", "TaskResponse"],
    },
    {
        "spec": "finance-research",
        "endpoint": ("POST", "/v1/finance_research"),
        "sdk_method": "finance_research",
        "sdk_response_models": ["FinanceResearchResponse"],
    },
]


# ---------------------------------------------------------------------------
# Spec fetching
# ---------------------------------------------------------------------------

def fetch_specs() -> dict[str, dict[str, Any]]:
    """Fetch all OpenAPI specs from the You.com docs index."""
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(OPENAPI_INDEX)
        r.raise_for_status()

        # The index page is HTML with relative links like:
        #   <a href="openapi/web-search.json">Web Search</a>
        matches = re.findall(r'href="openapi/([\w-]+)\.json"', r.text)
        if not matches:
            raise RuntimeError("Could not find any OpenAPI spec links in the index page")

        specs: dict[str, dict[str, Any]] = {}
        for name in matches:
            url = f"{OPENAPI_BASE}{name}.json"
            resp = client.get(url)
            resp.raise_for_status()
            specs[name] = resp.json()

        return specs


# ---------------------------------------------------------------------------
# Drift checks
# ---------------------------------------------------------------------------

def check_endpoints(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check that every path+method in specs has a corresponding SDK method."""
    warnings: list[str] = []

    for spec_name, spec in specs.items():
        if spec_name in KNOWN_UNCOVERED:
            continue

        for path, path_item in spec.get("paths", {}).items():
            for method in path_item:
                if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue
                key = (method.upper(), path)
                if key in KNOWN_UNCOVERED_ENDPOINTS:
                    continue
                if key not in EXPECTED_ENDPOINTS:
                    warnings.append(
                        f"[endpoint] {spec_name}: {method.upper()} {path} "
                        f"is in the OpenAPI spec but has no SDK method"
                    )

    # Also check for SDK endpoints that are no longer in any spec
    all_spec_endpoints: set[tuple[str, str]] = set()
    for spec_name, spec in specs.items():
        if spec_name in KNOWN_UNCOVERED:
            continue
        for path, path_item in spec.get("paths", {}).items():
            for method in path_item:
                if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    all_spec_endpoints.add((method.upper(), path))

    for endpoint, sdk_method in EXPECTED_ENDPOINTS.items():
        if endpoint not in all_spec_endpoints:
            warnings.append(
                f"[endpoint] SDK has {sdk_method} for {endpoint[0]} {endpoint[1]} "
                f"but it's not in any OpenAPI spec (may have been removed)"
            )

    return warnings


def check_server_urls(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check that spec server URLs match SDK server constants."""
    warnings: list[str] = []

    for spec_name, spec in specs.items():
        if spec_name in KNOWN_UNCOVERED:
            continue
        if spec_name not in EXPECTED_SERVERS:
            continue

        sdk_const, expected_url = EXPECTED_SERVERS[spec_name]
        spec_servers = [s["url"] for s in spec.get("servers", [])]

        if expected_url not in spec_servers:
            warnings.append(
                f"[server] {spec_name}: spec servers={spec_servers} "
                f"but SDK expects {expected_url} ({sdk_const})"
            )

    return warnings


def check_enums(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check that spec enum values match SDK enum classes."""
    warnings: list[str] = []

    # Import SDK enum classes
    import importlib
    sdk_enums: dict[str, Any] = {}
    for _, _, module_name, class_name in ENUM_CHECKS:
        if class_name not in sdk_enums:
            mod = importlib.import_module(module_name)
            sdk_enums[class_name] = getattr(mod, class_name)

    for spec_name, spec in specs.items():
        if spec_name in KNOWN_UNCOVERED:
            continue

        schemas = spec.get("components", {}).get("schemas", {})
        for schema_name, schema in schemas.items():
            # Only check string enums
            if schema.get("type") != "string" or "enum" not in schema:
                continue

            spec_values = set(schema["enum"])

            # Find matching SDK enum class
            for check_spec, name_fragment, _, sdk_class_name in ENUM_CHECKS:
                if check_spec != spec_name:
                    continue
                if name_fragment.lower() not in schema_name.lower():
                    continue

                sdk_class = sdk_enums.get(sdk_class_name)
                if sdk_class is None:
                    continue

                sdk_values = {e.value for e in sdk_class}

                if spec_values != sdk_values:
                    missing_in_sdk = spec_values - sdk_values
                    missing_in_spec = sdk_values - spec_values
                    if missing_in_sdk:
                        warnings.append(
                            f"[enum] {sdk_class_name}: spec has {missing_in_sdk} "
                            f"which SDK doesn't (schema: {schema_name})"
                        )
                    if missing_in_spec:
                        warnings.append(
                            f"[enum] {sdk_class_name}: SDK has {missing_in_spec} "
                            f"which spec doesn't (schema: {schema_name}) — possible fabricated value"
                        )

    return warnings


def check_new_apis(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check for API specs the SDK doesn't cover (excluding known exceptions)."""
    warnings: list[str] = []

    for spec_name in specs:
        if spec_name in KNOWN_UNCOVERED:
            continue
        if spec_name not in EXPECTED_SERVERS:
            warnings.append(
                f"[coverage] {spec_name}: OpenAPI spec exists but SDK doesn't cover this API"
            )

    return warnings


def _resolve_ref(ref: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve a $ref pointer within an OpenAPI spec."""
    # Format: "#/components/schemas/SchemaName"
    parts = ref.removeprefix("#/").split("/")
    obj: Any = spec
    for part in parts:
        obj = obj[part]
    return obj


def _get_schema_properties(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    """Extract top-level property names from a schema, resolving $ref, oneOf, and arrays."""
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], spec)

    if "oneOf" in schema:
        # Union type — collect properties from all branches
        props: set[str] = set()
        for branch in schema["oneOf"]:
            props |= _get_schema_properties(branch, spec)
        return props

    if schema.get("type") == "array" and "items" in schema:
        # Array type — look at the items schema
        return _get_schema_properties(schema["items"], spec)

    if "properties" in schema:
        return set(schema["properties"].keys())

    return set()


def _get_sdk_method_params(method_spec: str) -> set[str]:
    """Get SDK method parameter names, excluding internal params.

    A dotted ``method_spec`` names a shim class method (``SearchShim.__call__``);
    a bare one names a method on ``You`` (``answer``).
    """
    import importlib

    if "." in method_spec:
        cls_name, method_name = method_spec.split(".")
        mod = importlib.import_module("youdotcom._shims")
        cls = getattr(mod, cls_name)
        func = getattr(cls, method_name)
    else:
        mod = importlib.import_module("youdotcom")
        cls = getattr(mod, "You")
        func = getattr(cls, method_spec)

    sig = inspect.signature(func)
    params = {p for p in sig.parameters if p != "self"}
    return params - INTERNAL_PARAMS


def _get_sdk_model_fields(model_names: list[str]) -> set[str]:
    """Get pydantic model field names for one or more model classes."""
    import importlib
    mod = importlib.import_module("youdotcom.models")
    fields: set[str] = set()
    for name in model_names:
        cls = getattr(mod, name)
        fields |= set(cls.model_fields.keys())
    return fields


def check_request_params(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check that spec request body properties match SDK method parameters."""
    warnings: list[str] = []

    for check in SCHEMA_CHECKS:
        spec_name = check["spec"]
        method, path = check["endpoint"]
        if spec_name not in specs:
            continue

        spec = specs[spec_name]
        path_item = spec.get("paths", {}).get(path, {})
        operation = path_item.get(method.lower(), {})
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {}).get("application/json", {})
        schema = content.get("schema", {})

        if not schema:
            continue

        spec_params = _get_schema_properties(schema, spec)
        sdk_params = _get_sdk_method_params(check["sdk_method"])

        missing_in_sdk = spec_params - sdk_params
        missing_in_spec = sdk_params - spec_params

        if missing_in_sdk:
            warnings.append(
                f"[request] {spec_name} {method} {path}: spec has params {missing_in_sdk} "
                f"which SDK doesn't accept"
            )
        if missing_in_spec:
            warnings.append(
                f"[request] {spec_name} {method} {path}: SDK has params {missing_in_spec} "
                f"which spec doesn't define"
            )

    return warnings


def _resolve_schema(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Follow ``$ref`` and array ``items`` down to the underlying object schema."""
    seen: set[str] = set()
    while True:
        if "$ref" in schema:
            ref = schema["$ref"]
            if ref in seen:
                return {}
            seen.add(ref)
            schema = _resolve_ref(ref, spec)
            continue
        if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
            schema = schema["items"]
            continue
        return schema


def _nested_model(annotation: Any) -> Any:
    """Return the pydantic model a field annotation points at, or ``None``.

    Unwraps ``Optional[...]`` and ``List[...]`` so nested response objects
    more than one level down are still compared.
    """
    args = getattr(annotation, "__args__", None)
    if args is not None:
        for arg in args:
            found = _nested_model(arg)
            if found is not None:
                return found
        return None
    return annotation if hasattr(annotation, "model_fields") else None


def _compare_response_fields(
    schema: dict[str, Any],
    model: Any,
    path: str,
    spec: dict[str, Any],
    warnings: list[str],
    visited: set[Any],
    spec_name: str,
    field_path: str,
) -> None:
    """Compare a spec object schema against a model, recursing into nested objects.

    A top-level-only comparison misses drift inside nested response objects:
    a new ``results.knowledge`` array is invisible when ``results`` itself is
    unchanged.
    """
    if model in visited:
        return
    # ``visited`` is a recursion stack, not an "already compared" cache. The same
    # model can legitimately appear at several response paths backed by different
    # schemas, so it has to be compared at each one; discarding on exit keeps the
    # cycle breaker (a model already on the stack) without silently suppressing
    # sibling branches and missing real drift.
    visited.add(model)
    try:
        schema = _resolve_schema(schema, spec)
        props = schema.get("properties")
        if not props:
            # Nothing to compare against — a `oneOf` union or an unresolvable ref.
            # Bail rather than reporting every SDK field as absent from the spec.
            return
        model_fields = set(model.model_fields.keys())

        missing_in_sdk = set(props) - model_fields
        missing_in_spec = model_fields - set(props)

        known = KNOWN_RESPONSE_GAPS.get((spec_name, field_path), set())
        # Stale means the SDK model now defines the field, so the suppression no
        # longer does anything. Compare against the model, not against what's
        # missing: a field the spec dropped is neither missing nor defined, and
        # must not be reported as stale.
        stale = known & model_fields
        if stale:
            warnings.append(
                f"[response] {path}: KNOWN_RESPONSE_GAPS entry {stale} is stale — "
                f"the SDK model now defines it, so remove the entry"
            )
        missing_in_sdk -= known

        known_extra = KNOWN_SHARED_MODEL_EXTRAS.get((spec_name, field_path), set())
        # Stale here is the mirror image: the spec caught up and now defines the
        # field at this path, so the suppression no longer does anything.
        stale_extra = known_extra & set(props)
        if stale_extra:
            warnings.append(
                f"[response] {path}: KNOWN_SHARED_MODEL_EXTRAS entry {stale_extra} "
                f"is stale — the spec now defines it at this path, so remove the entry"
            )
        missing_in_spec -= known_extra

        if missing_in_sdk:
            warnings.append(
                f"[response] {path}: spec has fields {missing_in_sdk} "
                f"which SDK model doesn't have"
            )
        if missing_in_spec:
            warnings.append(
                f"[response] {path}: SDK model has fields {missing_in_spec} "
                f"which spec doesn't define"
            )

        for prop_name, prop_schema in props.items():
            if prop_name not in model_fields:
                continue
            child_model = _nested_model(model.model_fields[prop_name].annotation)
            if child_model is None:
                continue
            if "properties" in _resolve_schema(prop_schema, spec):
                _compare_response_fields(
                    prop_schema,
                    child_model,
                    f"{path}.{prop_name}",
                    spec,
                    warnings,
                    visited,
                    spec_name,
                    f"{field_path}.{prop_name}" if field_path else prop_name,
                )
    finally:
        visited.discard(model)


def check_response_schemas(specs: dict[str, dict[str, Any]]) -> list[str]:
    """Check that spec 200 response schema fields match SDK model fields.

    Endpoints with a single response model are compared recursively, so fields
    nested inside response objects are checked too. Endpoints whose response
    can be one of several models fall back to a flat union comparison.
    """
    warnings: list[str] = []

    for check in SCHEMA_CHECKS:
        spec_name = check["spec"]
        method, path = check["endpoint"]
        if spec_name not in specs:
            continue

        spec = specs[spec_name]
        path_item = spec.get("paths", {}).get(path, {})
        operation = path_item.get(method.lower(), {})
        responses = operation.get("responses", {})
        ok_response = responses.get("200", {})
        content = ok_response.get("content", {}).get("application/json", {})
        schema = content.get("schema", {})

        if not schema:
            continue

        model_names = check["sdk_response_models"]
        # Recurse only when the response resolves to a single object schema.
        # A `oneOf` union resolves to no properties, so it keeps the flat
        # comparison below rather than being mistaken for an empty schema.
        if len(model_names) == 1 and _resolve_schema(schema, spec).get("properties"):
            import importlib

            mod = importlib.import_module("youdotcom.models")
            model = getattr(mod, model_names[0])
            _compare_response_fields(
                schema,
                model,
                f"{spec_name} {method} {path} {model_names[0]}",
                spec,
                warnings,
                set(),
                spec_name,
                "",
            )
            continue

        spec_fields = _get_schema_properties(schema, spec)
        sdk_fields = _get_sdk_model_fields(check["sdk_response_models"])

        missing_in_sdk = spec_fields - sdk_fields
        missing_in_spec = sdk_fields - spec_fields

        if missing_in_sdk:
            warnings.append(
                f"[response] {spec_name} {method} {path}: spec has fields {missing_in_sdk} "
                f"which SDK model doesn't have"
            )
        if missing_in_spec:
            warnings.append(
                f"[response] {spec_name} {method} {path}: SDK model has fields {missing_in_spec} "
                f"which spec doesn't define"
            )

    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Every check, in run order. Named so --verbose can report each one individually.
CHECKS = [
    ("coverage", check_new_apis),
    ("endpoints", check_endpoints),
    ("servers", check_server_urls),
    ("enums", check_enums),
    ("request params", check_request_params),
    ("response schemas", check_response_schemas),
]


def run_checks(specs: dict[str, dict[str, Any]], verbose: bool) -> list[str]:
    """Run every check, optionally reporting the outcome of each one."""
    all_warnings: list[str] = []
    for name, check in CHECKS:
        warnings = check(specs)
        if verbose:
            status = f"{len(warnings)} warning(s)" if warnings else "ok"
            print(f"  [{name}] {status}")
        all_warnings += warnings
    if verbose:
        print()
    return all_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SDK drift against You.com OpenAPI specs")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when drift is found (for the scheduled workflow). "
             "Without it, drift is reported but the exit status stays 0.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show all checks, even passing ones")
    args = parser.parse_args()

    print("Fetching OpenAPI specs from you.com...")
    try:
        specs = fetch_specs()
    except Exception as e:
        # Transient: the docs site was unreachable or served something unexpected.
        print(f"ERROR: Could not fetch specs: {e}", file=sys.stderr)
        print("RESULT: fetch_error")
        return 2

    print(f"Found {len(specs)} specs: {', '.join(sorted(specs.keys()))}")
    print()

    try:
        all_warnings = run_checks(specs, args.verbose)
    except Exception as e:
        # A bug in the checker itself, or an SDK import failure. This must not
        # look like drift: the caller distinguishes it by exit code so the
        # scheduled workflow can flag a broken check instead of silently
        # reporting "no drift" (or filing an issue full of traceback).
        print(f"ERROR: Drift check failed to run: {e!r}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("RESULT: internal_error")
        return 3

    if all_warnings:
        print(f"DRIFT DETECTED ({len(all_warnings)} issue(s)):\n")
        for w in all_warnings:
            print(f"  ⚠️  {w}")
        print()
        print("Review the above and update the SDK if needed.")
        print("RESULT: drift")
        return 1 if args.strict else 0

    print("No drift detected. SDK matches OpenAPI specs.")
    print("RESULT: no_drift")
    if args.verbose:
        print(f"  Checked {len(specs)} specs, {len(EXPECTED_ENDPOINTS)} endpoints, "
              f"{len(ENUM_CHECKS)} enum mappings, {len(EXPECTED_SERVERS)} server URLs, "
              f"{len(SCHEMA_CHECKS)} schema/param mappings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

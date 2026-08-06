#!/usr/bin/env python3
"""
Drift check: compares the You.com Python SDK against the official OpenAPI specs.

Fetches OpenAPI specs from you.com/docs/openapi/ and compares:
  1. Endpoints — every path+method in the specs has a corresponding SDK method
  2. Server URLs — spec servers match SDK server constants
  3. Enums — spec enum values match SDK enum classes
  4. New APIs — specs the SDK doesn't cover yet (except known exceptions)

Usage:
    python scripts/check_drift.py            # Print warnings, exit 0 (CI, non-blocking)
    python scripts/check_drift.py --strict   # Exit 1 on drift (scheduled workflow)
    python scripts/check_drift.py --verbose  # Show all checks, even passing ones
"""

import argparse
import sys
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
        import re
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Check SDK drift against You.com OpenAPI specs")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on drift (for scheduled workflow)")
    parser.add_argument("--verbose", action="store_true", help="Show all checks, even passing ones")
    args = parser.parse_args()

    print("Fetching OpenAPI specs from you.com...")
    try:
        specs = fetch_specs()
    except Exception as e:
        print(f"ERROR: Could not fetch specs: {e}", file=sys.stderr)
        return 1 if args.strict else 0

    print(f"Found {len(specs)} specs: {', '.join(sorted(specs.keys()))}")
    print()

    all_warnings: list[str] = []
    all_warnings += check_new_apis(specs)
    all_warnings += check_endpoints(specs)
    all_warnings += check_server_urls(specs)
    all_warnings += check_enums(specs)

    if all_warnings:
        print(f"DRIFT DETECTED ({len(all_warnings)} issue(s)):\n")
        for w in all_warnings:
            print(f"  ⚠️  {w}")
        print()
        print("Review the above and update the SDK if needed.")
        return 1 if args.strict else 0
    else:
        print("No drift detected. SDK matches OpenAPI specs.")
        if args.verbose:
            print(f"  Checked {len(specs)} specs, {len(EXPECTED_ENDPOINTS)} endpoints, "
                  f"{len(ENUM_CHECKS)} enum mappings, {len(EXPECTED_SERVERS)} server URLs.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Wire audit: compares what the live API actually returns against what the SDK models keep.

`scripts/check_drift.py` compares the published OpenAPI specs against the SDK
models. That cannot see a field the API returns but no spec declares -- the model
drops it at parse time and every static check still agrees with itself. This
script closes that gap by walking the raw JSON from prod next to the parsed model
and reporting any key the model discarded.

It found three real drops that spec-vs-model comparison structurally could not:
`AnswerSearchResult.description` / `.thumbnail_url` (both since fixed) and
`WebResult.original_thumbnail_url` (still undeclared by any spec; see
KNOWN_WIRE_EXTRAS).

Requires a real API key, so it cannot gate pull requests. Run it before a release
or after any change to a response model:

    YDC_API_KEY=... python scripts/audit_wire.py
    YDC_API_KEY=... python scripts/audit_wire.py --fast     # skip research calls
    YDC_API_KEY=... python scripts/audit_wire.py --strict   # exit 1 on a drop

Exit codes:
    0  every wire key was kept by a model field (or is a known extra)
    1  an unexplained key was dropped (--strict only)
    2  no API key, or a call failed -- environment problem, not a finding
    3  the audit itself failed to run -- a bug, not a finding
"""

import argparse
import json
import os
import re
import sys
import traceback
from typing import Any, Optional

import httpx

from youdotcom import You

# Keys prod returns that no published spec declares, so no SDK model defines
# them. Deliberately not modeled: this repo grounds response models in the spec,
# and adding a field only observed on the wire would make the model authoritative
# for behavior the contract does not promise. Reported here rather than silently
# so the list stays a decision rather than an accident. Remove an entry once the
# spec declares the field and the model catches up.
#
# Keyed by (call label, dotted path with list indices normalized to []).
KNOWN_WIRE_EXTRAS = {
    # Observed on web results; absent from web-search.json and every other
    # published spec. Looks like a spec omission worth reporting upstream.
    ("search:extraction-highlights", "results.web[].original_thumbnail_url"),
    # Prod sends `warnings` at the top level of the finance-research response, and
    # the sibling research spec declares it (ResearchResponse models it), but
    # finance-research.json declares only `output`. Modeling it anyway would put
    # the SDK permanently ahead of that endpoint's published contract and leave a
    # standing drift warning, so it is recorded here instead. Observed as `[]`.
    # Add the field once finance-research.json declares it -- the sibling's
    # wording is the one to copy. Path is `root.` because this response is walked
    # from its top level rather than from a named section.
    ("finance-research", "root.warnings"),
}


class _Spy(httpx.BaseTransport):
    """Wrap a transport and keep the last decoded JSON response body.

    ``BaseTransport.close()`` is a no-op and ``Client.close()`` only calls the
    outer transport, so the wrapped transport has to be closed explicitly or
    every call in a run leaks its connection pool.
    """

    def __init__(self, inner: httpx.BaseTransport):
        self.inner = inner
        self.last: Any = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self.inner.handle_request(request)
        try:
            body = response.read()
            self.last = json.loads(body)
            response._content = body
        except Exception:  # non-JSON or unreadable; nothing to audit
            self.last = None
        return response

    def close(self) -> None:
        self.inner.close()


def _json_keys(model: Any) -> dict[str, str]:
    """Map the JSON key a model field reads to its attribute name."""
    return {(f.alias or name): name for name, f in type(model).model_fields.items()}


def _normalize(path: str) -> str:
    return re.sub(r"\[\d+\]", "[]", path)


def _walk(raw: Any, parsed: Any, path: str, dropped: list, kept: list) -> None:
    """Compare a raw JSON node against the model it parsed into, recursively."""
    if isinstance(raw, dict):
        if parsed is None or not hasattr(type(parsed), "model_fields"):
            return
        keys = _json_keys(parsed)
        for key, value in raw.items():
            if key not in keys:
                dropped.append((path, key, sorted(keys)))
                continue
            kept.append(f"{path}.{key}")
            _walk(value, getattr(parsed, keys[key], None), f"{path}.{key}", dropped, kept)
    elif isinstance(raw, list) and isinstance(parsed, list):
        for index, (raw_item, parsed_item) in enumerate(zip(raw, parsed)):
            _walk(raw_item, parsed_item, f"{path}[{index}]", dropped, kept)


def _audit(label: str, call, root: Optional[str], api_key: str) -> tuple[list, list]:
    spy = _Spy(httpx.HTTPTransport())
    client = httpx.Client(transport=spy)
    dropped: list = []
    kept: list = []
    try:
        with You(api_key_auth=api_key, timeout_ms=300_000, client=client) as you:
            parsed = call(you)
        if spy.last is None:
            raise RuntimeError(f"{label}: no JSON response captured")
        raw = spy.last[root] if root else spy.last
        model = getattr(parsed, root, None) if root else parsed
        _walk(raw, model, root or "root", dropped, kept)
    finally:
        client.close()
    return dropped, kept


SEARCH = "what is the capital of France"
RESEARCH_INPUT = "What drove NVIDIA data center revenue in fiscal 2025?"


def _calls(fast: bool) -> list:
    out = [
        ("search:plain", lambda y: y.search(query=SEARCH, count=3), "results"),
        ("search:knowledge-core", lambda y: y.search(query=SEARCH, count=3, knowledge="core"), "results"),
        ("search:extraction-highlights", lambda y: y.search(
            query="latest advances in fusion energy research", count=3,
            extraction={"extraction_mode": "highlights"}), "results"),
        ("answer", lambda y: y.answer(query="What caused the 2008 financial crisis?"), None),
        ("contents", lambda y: y.contents(
            urls=["https://example.com"], formats=["html", "markdown"]), None),
    ]
    if not fast:
        # research endpoints take tens of seconds to minutes each
        out += [
            ("research", lambda y: y.research(input=RESEARCH_INPUT, research_effort="standard"), None),
            ("finance-research", lambda y: y.finance_research(input=RESEARCH_INPUT), None),
        ]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--strict", action="store_true", help="exit 1 on an unexplained drop")
    parser.add_argument("--fast", action="store_true", help="skip the slow research endpoints")
    parser.add_argument("--verbose", action="store_true", help="list kept keys too")
    args = parser.parse_args()

    api_key = os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY_AUTH")
    if not api_key:
        print("YDC_API_KEY is not set; this audit calls the live API.")
        return 2

    try:
        unexplained: list = []
        total_kept = 0
        for label, call, root in _calls(args.fast):
            try:
                dropped, kept = _audit(label, call, root, api_key)
            except Exception as exc:
                print(f"  {label}: call failed ({type(exc).__name__}: {exc})")
                return 2
            total_kept += len(kept)
            known = [(p, k) for p, k, _ in dropped if (label, _normalize(f"{p}.{k}")) in KNOWN_WIRE_EXTRAS]
            new = [d for d in dropped if (label, _normalize(f"{d[0]}.{d[1]}")) not in KNOWN_WIRE_EXTRAS]
            status = "ok" if not new else f"{len(new)} DROPPED"
            print(f"  [{status:>10}] {label}: kept {len(kept)} wire keys"
                  + (f", {len(known)} known-undeclared" if known else ""))
            if args.verbose:
                for path, key, fields in new:
                    print(f"               {path}.{key}  (model has: {fields})")
            else:
                for path, key, fields in new:
                    print(f"             ! {_normalize(path)}.{key} not modeled; model has {fields}")
            unexplained += [(label, path, key) for path, key, _ in new]

        print(f"\nAudited {len(_calls(args.fast))} live calls, {total_kept} wire keys walked.")
        if unexplained:
            print(f"DROPPED: {len(unexplained)} key(s) the API returned and no model kept:")
            for label, path, key in unexplained:
                print(f"  {label}: {_normalize(path)}.{key}")
            print("\nEither the model is missing a field, or the key is undeclared by every")
            print("spec and belongs in KNOWN_WIRE_EXTRAS with a reason.")
            return 1 if args.strict else 0
        print("RESULT: no_unexplained_drops")
        return 0
    except Exception:
        traceback.print_exc()
        print("RESULT: audit_failed")
        return 3


if __name__ == "__main__":
    sys.exit(main())

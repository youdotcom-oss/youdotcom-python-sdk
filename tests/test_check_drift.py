"""Regression tests for ``scripts/check_drift.py``.

The script is not an importable package module, so it is loaded by path. These
tests pin the response-recursion and suppression rules that two separate review
rounds found bugs in:

- ``_compare_response_fields`` treated ``visited`` as a global "already compared
  this model" cache rather than a recursion stack, so a model reused at two
  schema paths was compared only at the first and drift on later branches went
  unreported.
- ``stale = known & model_fields`` reported a field the *spec* dropped as a stale
  suppression, contradicting the comment directly above it.

Neither was caught by a failing test, because the script had no test coverage at
all. Every case below was first reproduced by hand while fixing the bug.
"""

import importlib.util
from pathlib import Path
from typing import List, Optional

import pytest

from youdotcom.types import BaseModel

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_drift.py"


@pytest.fixture(scope="module")
def cd():
    """The drift checker, loaded by path (it is a script, not a package module)."""
    spec = importlib.util.spec_from_file_location("check_drift_under_test", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _restore_suppression_tables(cd):
    """Tests mutate the suppression tables; put them back afterwards."""
    gaps = dict(cd.KNOWN_RESPONSE_GAPS)
    extras = dict(cd.KNOWN_SHARED_MODEL_EXTRAS)
    yield
    cd.KNOWN_RESPONSE_GAPS.clear()
    cd.KNOWN_RESPONSE_GAPS.update(gaps)
    cd.KNOWN_SHARED_MODEL_EXTRAS.clear()
    cd.KNOWN_SHARED_MODEL_EXTRAS.update(extras)


# ---------------------------------------------------------------------------
# Models and spec builders
# ---------------------------------------------------------------------------


class Item(BaseModel):
    title: Optional[str] = None


class Nested(BaseModel):
    web: Optional[List[Item]] = None


class Root(BaseModel):
    results: Optional[Nested] = None


class Node(BaseModel):
    name: Optional[str] = None
    child: Optional["Node"] = None


class Branch(BaseModel):
    a: Optional["Trunk"] = None


class Trunk(BaseModel):
    b: Optional[Branch] = None


Node.model_rebuild()
Branch.model_rebuild()
Trunk.model_rebuild()


def _spec(schemas: dict) -> dict:
    return {"components": {"schemas": schemas}}


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props}


def _ref(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def _array(items: dict) -> dict:
    return {"type": "array", "items": items}


def _run(cd, schema, model, spec, *, spec_name="demo", field_path="", path="resp"):
    warnings: list = []
    cd._compare_response_fields(
        schema, model, path, spec, warnings, set(), spec_name, field_path
    )
    return warnings


# ---------------------------------------------------------------------------
# Recursion
# ---------------------------------------------------------------------------


class TestRecursion:
    def test_drift_nested_inside_an_array_is_caught(self, cd):
        """The case that motivated the recursion: a new field two levels down,
        inside an array, where the top-level object is unchanged."""
        spec = _spec({
            "Item": _obj({"title": {"type": "string"}, "brand_new": {"type": "string"}}),
            "Nested": _obj({"web": _array(_ref("Item"))}),
            "Root": _obj({"results": _ref("Nested")}),
        })
        w = _run(cd, _ref("Root"), Root, spec)
        assert any("brand_new" in x for x in w), w

    def test_top_level_only_comparison_would_miss_it(self, cd):
        """Guard the premise: with only top-level props compared, nothing inside
        `results` is visible. Keeps the recursion honest about what it adds."""
        spec = _spec({
            "Item": _obj({"title": {"type": "string"}, "brand_new": {"type": "string"}}),
            "Nested": _obj({"web": _array(_ref("Item"))}),
            "Root": _obj({"results": _ref("Nested")}),
        })
        top_level = set(spec["components"]["schemas"]["Root"]["properties"])
        assert top_level == {"results"}
        assert "brand_new" not in top_level

    def test_oneof_union_bails_instead_of_reporting_everything_missing(self, cd):
        """A union response has no `properties` of its own. Bailing is correct;
        reporting every SDK field as absent from the spec would be noise."""
        spec = _spec({"Root": {"oneOf": [_ref("A"), _ref("B")]}})
        w = _run(cd, _ref("Root"), Root, spec)
        assert w == []


class TestSiblingBranches:
    """Regression: `visited` used to be a global cache, not a recursion stack."""

    def test_same_model_at_two_paths_is_compared_at_both(self, cd):
        class TwoPaths(BaseModel):
            left: Optional[Item] = None
            right: Optional[Item] = None

        TwoPaths.model_rebuild()
        spec = _spec({
            "Left": _obj({"title": {"type": "string"}}),
            # `right` gains a field the SDK model does not have.
            "Right": _obj({"title": {"type": "string"}, "only_on_right": {"type": "string"}}),
            "TwoPaths": _obj({"left": _ref("Left"), "right": _ref("Right")}),
        })
        w = _run(cd, _ref("TwoPaths"), TwoPaths, spec)
        assert any("only_on_right" in x for x in w), (
            "drift on the second branch was skipped — `visited` is behaving as a "
            "global cache again"
        )

    def test_self_referential_schema_terminates(self, cd):
        """Cycle safety must survive dropping the global cache."""
        spec = _spec({
            "Node": _obj({
                "name": {"type": "string"},
                "child": _ref("Node"),
                "node_only": {"type": "string"},
            }),
        })
        w = _run(cd, _ref("Node"), Node, spec)
        assert any("node_only" in x for x in w), w

    def test_mutual_cycle_terminates_and_still_reports(self, cd):
        spec = _spec({
            "Trunk": _obj({"b": _ref("Branch")}),
            "Branch": _obj({"a": _ref("Trunk"), "branch_only": {"type": "string"}}),
        })
        w = _run(cd, _ref("Trunk"), Trunk, spec)
        assert any("branch_only" in x for x in w), w


# ---------------------------------------------------------------------------
# Schema resolution helpers
# ---------------------------------------------------------------------------


class TestResolveSchema:
    def test_follows_ref_then_array_items(self, cd):
        spec = _spec({"Inner": _obj({"x": {"type": "string"}})})
        resolved = cd._resolve_schema(_array(_ref("Inner")), spec)
        assert "x" in resolved.get("properties", {})

    def test_breaks_a_ref_cycle(self, cd):
        spec = _spec({"A": _obj({"b": _ref("B")}), "B": _obj({"a": _ref("A")})})
        # Must return rather than recurse forever; the exact result is a bail-out.
        assert isinstance(cd._resolve_schema(_ref("A"), spec), dict)

    def test_self_ref_cycle_returns_empty(self, cd):
        spec = _spec({"Loop": _ref("Loop")})
        assert cd._resolve_schema(_ref("Loop"), spec) == {}


class TestNestedModel:
    def test_unwraps_optional_and_list(self, cd):
        assert cd._nested_model(Optional[List[Item]]) is Item

    def test_bare_model(self, cd):
        assert cd._nested_model(Item) is Item

    def test_scalar_has_no_nested_model(self, cd):
        assert cd._nested_model(Optional[str]) is None


# ---------------------------------------------------------------------------
# Suppression tables
# ---------------------------------------------------------------------------


class TestKnownResponseGaps:
    """`KNOWN_RESPONSE_GAPS` excuses a field the spec defines and the SDK lacks."""

    def _spec_with(self, props):
        return _spec({"Item": _obj({p: {"type": "string"} for p in props})})

    def test_suppresses_a_known_gap(self, cd):
        cd.KNOWN_RESPONSE_GAPS[("demo", "")] = {"ghost"}
        w = _run(cd, _ref("Item"), Item, self._spec_with(["title", "ghost"]))
        assert not any("ghost" in x for x in w), w

    def test_gap_still_open_is_not_stale(self, cd):
        """Case 1: spec defines it, SDK does not — a live suppression."""
        cd.KNOWN_RESPONSE_GAPS[("demo", "")] = {"ghost"}
        w = _run(cd, _ref("Item"), Item, self._spec_with(["title", "ghost"]))
        assert not any("is stale" in x for x in w), w

    def test_stale_once_the_sdk_catches_up(self, cd):
        """Case 2: both sides define it, so the entry no longer does anything."""
        cd.KNOWN_RESPONSE_GAPS[("demo", "")] = {"title"}
        w = _run(cd, _ref("Item"), Item, self._spec_with(["title"]))
        assert any("is stale" in x for x in w), w

    def test_not_stale_when_the_spec_drops_the_field(self, cd):
        """Case 3 — regression. The spec no longer defines the field, so the
        entry is not excusing anything and must not be reported stale."""
        cd.KNOWN_RESPONSE_GAPS[("demo", "")] = {"title"}
        w = _run(cd, _ref("Item"), Item, self._spec_with(["other"]))
        assert not any("is stale" in x for x in w), w

    def test_unsuppressed_gap_is_still_reported(self, cd):
        w = _run(cd, _ref("Item"), Item, self._spec_with(["title", "ghost"]))
        assert any("ghost" in x for x in w), w


class TestKnownSharedModelExtras:
    """The mirror table: a field the SDK declares that the spec at *this* path
    does not, because one model serves paths with differently-shaped schemas."""

    def _spec_with(self, props):
        return _spec({"Item": _obj({p: {"type": "string"} for p in props})})

    def test_suppresses_the_extra_field(self, cd):
        class Wide(BaseModel):
            title: Optional[str] = None
            extra: Optional[str] = None

        Wide.model_rebuild()
        cd.KNOWN_SHARED_MODEL_EXTRAS[("demo", "")] = {"extra"}
        w = _run(cd, _ref("Item"), Wide, self._spec_with(["title"]))
        assert not any("extra" in x for x in w), w

    def test_stale_once_the_spec_defines_it(self, cd):
        class Wide(BaseModel):
            title: Optional[str] = None
            extra: Optional[str] = None

        Wide.model_rebuild()
        cd.KNOWN_SHARED_MODEL_EXTRAS[("demo", "")] = {"extra"}
        w = _run(cd, _ref("Item"), Wide, self._spec_with(["title", "extra"]))
        assert any("is stale" in x for x in w), w

    def test_unsuppressed_extra_is_still_reported(self, cd):
        class Wide(BaseModel):
            title: Optional[str] = None
            extra: Optional[str] = None

        Wide.model_rebuild()
        w = _run(cd, _ref("Item"), Wide, self._spec_with(["title"]))
        assert any("extra" in x for x in w), w


# ---------------------------------------------------------------------------
# The real tables shipped with the SDK
# ---------------------------------------------------------------------------


class TestShippedTables:
    def test_known_response_gaps_is_empty(self, cd):
        """Both gaps this table once held were closed by adding the fields, so
        nothing should be suppressed any more. If this fails, a new gap was
        suppressed instead of fixed — say so in the PR rather than hiding it."""
        assert cd.KNOWN_RESPONSE_GAPS == {}

    def test_shared_model_extras_entries_are_current(self, cd):
        """Each entry must still describe a real asymmetry: the SDK model defines
        the field and the spec schema at that path does not."""
        assert cd.KNOWN_SHARED_MODEL_EXTRAS == {
            ("web-search", "results.news.contents"): {"highlights"},
        }

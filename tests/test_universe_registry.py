"""Tests for the NS-4A universe seed registry (PRD-308)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from cuttingboard.universe_registry import (
    KNOWN_FUNCTIONS,
    PRIMARY_GROUPS,
    UNIVERSE_REGISTRY,
    UniverseInstrument,
)

_APPROVED = (
    "SPY", "QQQ", "GDX", "GLD", "SLV", "XLE", "UCO",
    "NVDA", "TSLA", "META", "AMZN", "GOOG",
)

_APPROVED_GROUPS = {
    "SPY": "INDEX", "QQQ": "INDEX",
    "GDX": "METALS", "GLD": "METALS", "SLV": "METALS",
    "XLE": "ENERGY", "UCO": "ENERGY",
    "NVDA": "TECH", "TSLA": "HIGH_BETA", "META": "TECH",
    "AMZN": "TECH", "GOOG": "TECH",
}


def _by_symbol() -> dict[str, UniverseInstrument]:
    return {i.symbol: i for i in UNIVERSE_REGISTRY}


# (A) exactly 12 symbols, each exactly once
def test_exactly_twelve_symbols_each_once() -> None:
    symbols = [i.symbol for i in UNIVERSE_REGISTRY]
    assert len(symbols) == 12
    assert len(set(symbols)) == 12
    assert set(symbols) == set(_APPROVED)


# (B) AAPL absent
def test_aapl_absent() -> None:
    assert "AAPL" not in {i.symbol for i in UNIVERSE_REGISTRY}


# (C) GOOG present exactly once
def test_goog_present_exactly_once() -> None:
    assert [i.symbol for i in UNIVERSE_REGISTRY].count("GOOG") == 1


# (D) UCO present exactly once
def test_uco_present_exactly_once() -> None:
    assert [i.symbol for i in UNIVERSE_REGISTRY].count("UCO") == 1


# (E) primary groups exactly the owner assignment, all within the allowed set
def test_primary_groups_exact() -> None:
    by = _by_symbol()
    for sym, grp in _APPROVED_GROUPS.items():
        assert by[sym].primary_group == grp
    assert all(i.primary_group in PRIMARY_GROUPS for i in UNIVERSE_REGISTRY)


# (R1) frozen dataclass with exactly the six fields
def test_frozen_dataclass_six_fields() -> None:
    assert isinstance(UNIVERSE_REGISTRY, tuple)
    field_names = {f.name for f in dataclasses.fields(UniverseInstrument)}
    assert field_names == {
        "symbol", "trade_eligible", "functions",
        "primary_group", "enabled", "rationale",
    }
    for inst in UNIVERSE_REGISTRY:
        assert isinstance(inst, UniverseInstrument)
        with pytest.raises(dataclasses.FrozenInstanceError):
            inst.symbol = "X"  # immutable


# (R4) trade_eligible is an independent bool; all True in v1
def test_trade_eligible_all_true() -> None:
    for inst in UNIVERSE_REGISTRY:
        assert inst.trade_eligible is True


# (R4) functions is a bounded tuple; UCO carries crude_proxy, XLE does not;
# the two ENERGY names are not collapsed
def test_functions_bounded_uco_crude_proxy_xle_distinct() -> None:
    by = _by_symbol()
    assert by["UCO"].functions == ("crude_proxy",)
    assert by["XLE"].functions == ()
    assert by["UCO"].functions != by["XLE"].functions
    for inst in UNIVERSE_REGISTRY:
        assert set(inst.functions) <= KNOWN_FUNCTIONS
    # only UCO carries any function in v1
    assert {i.symbol for i in UNIVERSE_REGISTRY if i.functions} == {"UCO"}


# (R5) all enabled; rationale is a non-empty membership string; no disabled reason
def test_all_enabled_rationale_nonempty() -> None:
    for inst in UNIVERSE_REGISTRY:
        assert inst.enabled is True
        assert isinstance(inst.rationale, str) and inst.rationale


# (R5) owner-approved rationale wording for the two new symbols; GOOG carries no
# forecast/directional claim (asserted via the exact approved string)
def test_goog_uco_rationale_wording() -> None:
    by = _by_symbol()
    assert by["GOOG"].rationale == "large-cap tech"
    assert by["UCO"].rationale == "crude-oil energy proxy"


# (J) one-reader boundary: exactly one production module imports the registry,
# and it is watchlist_sidecar -- no runtime/market_map/regime/qualification/
# execution/trend/macro/heatmap/news/leadership/decoupling/GEX importer.
def test_registry_has_exactly_one_production_importer() -> None:
    root = Path(__file__).resolve().parent.parent / "cuttingboard"
    importers: list[str] = []
    for py in root.rglob("*.py"):
        if py.name == "universe_registry.py":
            continue
        for line in py.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith(("import ", "from ")) and "universe_registry" in s:
                importers.append(py.name)
                break
    assert importers == ["watchlist_sidecar.py"], importers


# (K) the registry touches no GEX surface
def test_registry_references_no_gex() -> None:
    root = Path(__file__).resolve().parent.parent / "cuttingboard"
    text = (root / "universe_registry.py").read_text(encoding="utf-8").lower()
    assert "gex" not in text

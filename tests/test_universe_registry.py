"""Tests for the Market Structure Universe registry (NS-4A v2; PRD-337 precursor).

Pins the ratified 22-symbol measurement projection, the 11-symbol personal
projection, the exact benchmark map, and the import-time validation rules. Each
validation rule ships a red test that constructs a bad registry tuple and asserts
the raise (F8). ``trade_eligible`` is proven independent of observation membership
and unread by any production module (F9).
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from cuttingboard.universe_registry import (
    KNOWN_FUNCTIONS,
    PRIMARY_GROUPS,
    UNIVERSE_REGISTRY,
    UniverseInstrument,
)
from cuttingboard.watchlist_sidecar import validate_registry

# --- Ratified literals (section 3.2 / 3.3 / 3.4) ----------------------------

_MARKET_STRUCTURE_22 = (
    "SPY", "QQQ",
    "XLK", "XLF", "XLE", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC",
    "GLD", "SLV", "GDX",
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOG",
)
_PERSONAL_11 = (
    "SPY", "QQQ", "XLE", "GLD", "SLV", "GDX", "NVDA", "META", "AMZN", "GOOG", "UCO",
)
_ELEVEN_SECTORS = (
    "XLK", "XLF", "XLE", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC",
)
_GROUP_BY_SYMBOL = {
    "SPY": "MARKET", "QQQ": "MARKET",
    **{s: "SECTORS" for s in _ELEVEN_SECTORS},
    "GLD": "METALS", "SLV": "METALS", "GDX": "METALS",
    "AAPL": "MEGACAPS", "MSFT": "MEGACAPS", "NVDA": "MEGACAPS",
    "META": "MEGACAPS", "AMZN": "MEGACAPS", "GOOG": "MEGACAPS",
}
_BENCHMARK = {
    "SPY": None, "QQQ": "SPY",
    **{s: "SPY" for s in _ELEVEN_SECTORS},
    "GLD": None, "SLV": "GLD", "GDX": "GLD",
    "AAPL": "QQQ", "MSFT": "QQQ", "NVDA": "QQQ",
    "META": "QQQ", "AMZN": "QQQ", "GOOG": "QQQ",
}
# New measurement rows carry trade_eligible=False; legacy rows keep True (F9/3.2).
_TRADE_ELIGIBLE_FALSE = {
    "XLK", "XLF", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC", "AAPL", "MSFT",
}


def _by_symbol() -> dict[str, UniverseInstrument]:
    return {i.symbol: i for i in UNIVERSE_REGISTRY}


def _measurement() -> tuple[str, ...]:
    return tuple(i.symbol for i in UNIVERSE_REGISTRY if i.market_structure)


def _personal() -> tuple[str, ...]:
    return tuple(i.symbol for i in UNIVERSE_REGISTRY if i.enabled and i.personal)


# --- Shape ------------------------------------------------------------------
def test_frozen_dataclass_nine_fields() -> None:
    assert isinstance(UNIVERSE_REGISTRY, tuple)
    field_names = {f.name for f in dataclasses.fields(UniverseInstrument)}
    assert field_names == {
        "symbol", "trade_eligible", "functions", "primary_group", "enabled",
        "rationale", "personal", "market_structure", "benchmark_symbol",
    }
    for inst in UNIVERSE_REGISTRY:
        assert isinstance(inst, UniverseInstrument)
        with pytest.raises(dataclasses.FrozenInstanceError):
            inst.symbol = "X"  # immutable


# --- Measurement projection (22, exact, in order) ---------------------------
def test_measurement_projection_is_exact_22_in_order() -> None:  # M3
    assert _measurement() == _MARKET_STRUCTURE_22
    assert len(_MARKET_STRUCTURE_22) == 22
    assert len(set(_MARKET_STRUCTURE_22)) == 22


def test_all_eleven_sector_spdrs_present() -> None:  # M3
    measurement = set(_measurement())
    for sector in _ELEVEN_SECTORS:
        assert sector in measurement, sector
    assert len(_ELEVEN_SECTORS) == 11


def test_measurement_primary_groups_exact_and_closed() -> None:
    by = _by_symbol()
    for sym, grp in _GROUP_BY_SYMBOL.items():
        assert by[sym].primary_group == grp
    for inst in UNIVERSE_REGISTRY:
        if inst.market_structure:
            assert inst.primary_group in PRIMARY_GROUPS
        else:
            assert inst.primary_group is None


# --- Personal projection (11, exact, pinned literal) ------------------------
def test_personal_projection_is_exact_11() -> None:
    assert _personal() == _PERSONAL_11


def test_uco_personal_not_measurement() -> None:  # M7
    uco = _by_symbol()["UCO"]
    assert uco.personal is True
    assert uco.market_structure is False
    assert uco.enabled is True
    assert uco.primary_group is None
    assert "UCO" not in _measurement()
    assert "UCO" in _personal()


def test_aapl_msft_measurement_not_personal() -> None:
    by = _by_symbol()
    for sym in ("AAPL", "MSFT"):
        assert by[sym].market_structure is True
        assert by[sym].personal is False
        assert sym in _measurement()
        assert sym not in _personal()


# --- TSLA tombstone ---------------------------------------------------------
def test_tsla_disabled_and_absent_from_active_projections() -> None:  # M8
    tsla = _by_symbol()["TSLA"]
    assert tsla.enabled is False
    assert tsla.market_structure is False
    assert tsla.personal is False
    assert tsla.primary_group is None
    assert "TSLA" not in _measurement()
    assert "TSLA" not in _personal()


# --- Benchmark map ----------------------------------------------------------
def test_benchmark_relationships_exact() -> None:  # M9
    by = _by_symbol()
    for sym, target in _BENCHMARK.items():
        assert by[sym].benchmark_symbol == target, (sym, by[sym].benchmark_symbol, target)


def test_benchmark_targets_exist_and_are_measurement() -> None:
    measurement = set(_measurement())
    for inst in UNIVERSE_REGISTRY:
        if inst.benchmark_symbol is not None:
            assert inst.benchmark_symbol in measurement
            assert inst.benchmark_symbol != inst.symbol


def test_non_measurement_rows_have_null_benchmark() -> None:
    by = _by_symbol()
    assert by["UCO"].benchmark_symbol is None
    assert by["TSLA"].benchmark_symbol is None


# --- trade_eligible independence (F9) ---------------------------------------
def test_trade_eligible_legacy_true_new_rows_false() -> None:
    for inst in UNIVERSE_REGISTRY:
        expected = inst.symbol not in _TRADE_ELIGIBLE_FALSE
        assert inst.trade_eligible is expected, (inst.symbol, inst.trade_eligible)


def test_trade_eligible_does_not_imply_personal_or_measurement() -> None:
    by = _by_symbol()
    # AAPL: trade_eligible False yet market_structure True -> field is independent
    assert by["AAPL"].trade_eligible is False and by["AAPL"].market_structure is True
    # TSLA: trade_eligible True yet neither personal nor market_structure nor enabled
    assert by["TSLA"].trade_eligible is True
    assert not (by["TSLA"].personal or by["TSLA"].market_structure or by["TSLA"].enabled)


# --- Structural no-reader guard for trade_eligible (F9; Astra R3) -----------
# The legacy text guard (`".trade_eligible" in text`, skipping universe_registry.py)
# had concrete bypasses: `getattr(inst, "trade_eligible")` carries no
# `.trade_eligible` substring, and an executable reader added inside the skipped
# registry stayed GREEN. Replace it with a small, inspectable, repo-local AST scan
# that detects EXECUTABLE reads of the field across ALL production modules
# (including the registry itself), while permitting the dataclass field
# declaration, construction kwargs, attribute stores, and documentary text.
def _source_reads_trade_eligible(source: str) -> bool:
    """True iff `source` contains an executable READ of the ``trade_eligible``
    field: an attribute load (``x.trade_eligible`` -- any object, so aliasing the
    instance does not evade it), ``getattr(x, "trade_eligible"[, default])``, or a
    literal mapping/subscript access (``x["trade_eligible"]``).

    NOT reads (allowed): the dataclass field DECLARATION (``trade_eligible: bool``,
    an annotated Store target), construction keyword arguments
    (``U(trade_eligible=...)``), attribute STORES (``obj.trade_eligible = ...``),
    and docstring/comment mentions. Bound: a fully indirect read whose attribute
    name is only known at runtime (``getattr(x, some_var)``) is out of scope for a
    small structural guard; the four Astra-named variants -- direct, aliased-object,
    helper/getattr, and registry-local -- are all covered."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "trade_eligible"
            and isinstance(node.ctx, ast.Load)
        ):
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "trade_eligible"
        ):
            return True
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "trade_eligible":
                return True
    return False


def test_no_production_module_reads_trade_eligible() -> None:
    # Scan EVERY production module, including universe_registry.py itself -- a
    # registry-local reader is exactly the bypass R3 flagged. The AST guard permits
    # the field declaration and construction there, so only an executable READ
    # reddens. Scoped to production Python (cuttingboard/), not audit/history files.
    root = Path(__file__).resolve().parent.parent / "cuttingboard"
    offenders = [
        py.name
        for py in sorted(root.rglob("*.py"))
        if _source_reads_trade_eligible(py.read_text(encoding="utf-8"))
    ]
    assert offenders == [], offenders


def test_trade_eligible_guard_reddens_on_direct_attribute_read() -> None:
    # `if inst.trade_eligible:` -- the branching-on-authority case R3 requires.
    assert _source_reads_trade_eligible("if inst.trade_eligible:\n    pass\n")
    # Aliasing the object does not evade the attribute-name match.
    assert _source_reads_trade_eligible("alias = inst\nx = alias.trade_eligible\n")


def test_trade_eligible_guard_reddens_on_getattr_read() -> None:
    # `getattr(inst, "trade_eligible")` -- the exact string the old guard missed.
    assert _source_reads_trade_eligible('permission = getattr(inst, "trade_eligible")\n')
    assert _source_reads_trade_eligible('permission = getattr(inst, "trade_eligible", False)\n')


def test_trade_eligible_guard_reddens_on_mapping_read() -> None:
    assert _source_reads_trade_eligible('flag = row["trade_eligible"]\n')


def test_trade_eligible_guard_reddens_on_registry_local_read() -> None:
    # An executable reader added INSIDE universe_registry.py must redden too (the
    # old skip-by-basename bypass).
    assert _source_reads_trade_eligible(
        "eligible = [i for i in UNIVERSE_REGISTRY if i.trade_eligible]\n"
    )


def test_trade_eligible_guard_allows_declaration_construction_and_docs() -> None:
    # Dataclass field declaration is metadata, not a read.
    assert not _source_reads_trade_eligible(
        "from dataclasses import dataclass\n@dataclass\nclass U:\n    trade_eligible: bool\n"
    )
    # Construction keyword argument is not a read.
    assert not _source_reads_trade_eligible('U(symbol="AAA", trade_eligible=False)\n')
    # An attribute STORE (assignment) is not a read.
    assert not _source_reads_trade_eligible("obj.trade_eligible = False\n")
    # Docstring / comment mentions are not executable reads.
    assert not _source_reads_trade_eligible(
        '"""trade_eligible is legacy metadata."""\n# trade_eligible: do not read\nx = 1\n'
    )


# --- functions vocabulary ---------------------------------------------------
def test_functions_bounded_uco_crude_proxy() -> None:
    by = _by_symbol()
    assert by["UCO"].functions == ("crude_proxy",)
    assert by["XLE"].functions == ()
    for inst in UNIVERSE_REGISTRY:
        assert set(inst.functions) <= KNOWN_FUNCTIONS
    assert {i.symbol for i in UNIVERSE_REGISTRY if i.functions} == {"UCO"}


# --- One-reader / no-GEX boundary -------------------------------------------
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


def test_registry_references_no_gex() -> None:
    root = Path(__file__).resolve().parent.parent / "cuttingboard"
    text = (root / "universe_registry.py").read_text(encoding="utf-8").lower()
    assert "gex" not in text


def test_canonical_registry_passes_validation() -> None:
    validate_registry(UNIVERSE_REGISTRY)  # must not raise


# --- Validation rules: each rule reddens on a constructed bad tuple (F8) -----
def _inst(**over) -> UniverseInstrument:
    """A valid MARKET anchor row; override one field to violate a rule."""
    base = dict(
        symbol="AAA", trade_eligible=False, functions=(), primary_group="MARKET",
        enabled=True, rationale="ok", personal=False, market_structure=True,
        benchmark_symbol=None,
    )
    base.update(over)
    return UniverseInstrument(**base)


def test_rule1_duplicate_symbol_rejected() -> None:
    reg = (_inst(symbol="AAA"), _inst(symbol="AAA"))
    with pytest.raises(ValueError):
        validate_registry(reg)


def test_rule1_empty_symbol_rejected() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(symbol=""),))


def test_rule1_lowercase_symbol_rejected() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(symbol="aaa"),))


def test_rule2_enabled_needs_personal_or_measurement() -> None:
    bad = _inst(enabled=True, personal=False, market_structure=False, primary_group=None)
    with pytest.raises(ValueError):
        validate_registry((bad,))


def test_rule3_measurement_requires_valid_group() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(market_structure=True, primary_group="NOPE"),))
    with pytest.raises(ValueError):
        validate_registry((_inst(market_structure=True, primary_group=None),))


def test_rule3_non_measurement_requires_null_group() -> None:
    bad = _inst(market_structure=False, personal=True, primary_group="MARKET",
                benchmark_symbol=None)
    with pytest.raises(ValueError):
        validate_registry((bad,))


def test_rule4_benchmark_target_must_exist() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(symbol="AAA", benchmark_symbol="ZZZ"),))


def test_rule4_benchmark_no_self_reference() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(symbol="AAA", benchmark_symbol="AAA"),))


def test_rule4_benchmark_requires_measurement_row() -> None:
    anchor = _inst(symbol="AAA", market_structure=True, primary_group="MARKET")
    bad = _inst(symbol="BBB", market_structure=False, personal=True,
                primary_group=None, benchmark_symbol="AAA")
    with pytest.raises(ValueError):
        validate_registry((anchor, bad))


def test_rule4_benchmark_cycle_rejected() -> None:
    a = _inst(symbol="AAA", market_structure=True, primary_group="MARKET", benchmark_symbol="BBB")
    b = _inst(symbol="BBB", market_structure=True, primary_group="MARKET", benchmark_symbol="AAA")
    with pytest.raises(ValueError):
        validate_registry((a, b))


def test_rule5_unknown_function_rejected() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(functions=("mystery",)),))


def test_rule5_enabled_needs_rationale() -> None:
    with pytest.raises(ValueError):
        validate_registry((_inst(enabled=True, rationale=""),))

"""Tests for market_map_lifecycle.inject_lifecycle and GRADE_ORDER."""

import copy


from cuttingboard.market_map_lifecycle import GRADE_ORDER, inject_lifecycle


# ---------------------------------------------------------------------------
# Minimal fixture helpers
# ---------------------------------------------------------------------------

def _sym(grade: str = "B", setup_state: str = "DEVELOPING") -> dict:
    return {"grade": grade, "setup_state": setup_state, "bias": "BULLISH"}


def _map(*symbols: tuple[str, dict]) -> dict:
    return {"symbols": dict(symbols), "schema_version": "market_map.v1"}


# ---------------------------------------------------------------------------
# GRADE_ORDER
# ---------------------------------------------------------------------------

def test_grade_order_constant_correct() -> None:
    assert GRADE_ORDER == {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}


# ---------------------------------------------------------------------------
# No previous snapshot
# ---------------------------------------------------------------------------

def test_no_previous_snapshot_all_unknown() -> None:
    current = _map(("SPY", _sym("A", "ACTIONABLE")), ("QQQ", _sym("B", "DEVELOPING")))
    result = inject_lifecycle(current, None)
    for sym_data in result["symbols"].values():
        lc = sym_data["lifecycle"]
        assert lc["grade_transition"] == "UNKNOWN"
        assert lc["setup_state_transition"] == "UNKNOWN"


def test_is_new_false_when_no_previous_snapshot() -> None:
    current = _map(("SPY", _sym()))
    result = inject_lifecycle(current, None)
    assert result["symbols"]["SPY"]["lifecycle"]["is_new"] is False


def test_previous_grade_none_when_no_snapshot() -> None:
    current = _map(("SPY", _sym("A")))
    result = inject_lifecycle(current, None)
    lc = result["symbols"]["SPY"]["lifecycle"]
    assert lc["previous_grade"] is None
    assert lc["previous_setup_state"] is None


# ---------------------------------------------------------------------------
# New symbol (absent from previous)
# ---------------------------------------------------------------------------

def test_new_symbol_in_current_not_in_previous() -> None:
    previous = _map(("QQQ", _sym("A")))
    current = _map(("QQQ", _sym("A")), ("SPY", _sym("B")))
    result = inject_lifecycle(current, previous)
    lc = result["symbols"]["SPY"]["lifecycle"]
    assert lc["grade_transition"] == "NEW"
    assert lc["setup_state_transition"] == "NEW"
    assert lc["is_new"] is True
    assert lc["previous_grade"] is None


# ---------------------------------------------------------------------------
# Grade transitions
# ---------------------------------------------------------------------------

def test_grade_unchanged() -> None:
    previous = _map(("SPY", _sym("B")))
    current = _map(("SPY", _sym("B")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "UNCHANGED"


def test_grade_upgraded() -> None:
    previous = _map(("SPY", _sym("B")))
    current = _map(("SPY", _sym("A")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "UPGRADED"


def test_grade_downgraded() -> None:
    previous = _map(("SPY", _sym("A")))
    current = _map(("SPY", _sym("C")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "DOWNGRADED"


def test_grade_unrecognized() -> None:
    previous = _map(("SPY", _sym("X")))
    current = _map(("SPY", _sym("B")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "UNKNOWN"


def test_all_grade_order_values() -> None:
    grades = list(GRADE_ORDER.keys())
    for i, better in enumerate(grades):
        for worse in grades[i + 1:]:
            prev = _map(("SPY", _sym(worse)))
            curr = _map(("SPY", _sym(better)))
            r = inject_lifecycle(curr, prev)
            assert r["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "UPGRADED", \
                f"{worse}→{better} should be UPGRADED"

            prev2 = _map(("SPY", _sym(better)))
            curr2 = _map(("SPY", _sym(worse)))
            r2 = inject_lifecycle(curr2, prev2)
            assert r2["symbols"]["SPY"]["lifecycle"]["grade_transition"] == "DOWNGRADED", \
                f"{better}→{worse} should be DOWNGRADED"


# ---------------------------------------------------------------------------
# Setup state transitions
# ---------------------------------------------------------------------------

def test_setup_state_unchanged() -> None:
    previous = _map(("SPY", _sym(setup_state="ACTIONABLE")))
    current = _map(("SPY", _sym(setup_state="ACTIONABLE")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["setup_state_transition"] == "UNCHANGED"


def test_setup_state_changed() -> None:
    previous = _map(("SPY", _sym(setup_state="DEVELOPING")))
    current = _map(("SPY", _sym(setup_state="ACTIONABLE")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["setup_state_transition"] == "CHANGED"


def test_setup_state_unknown_when_no_previous() -> None:
    current = _map(("SPY", _sym(setup_state="ACTIONABLE")))
    result = inject_lifecycle(current, None)
    assert result["symbols"]["SPY"]["lifecycle"]["setup_state_transition"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# is_removed always False in symbols
# ---------------------------------------------------------------------------

def test_is_removed_always_false_in_symbols() -> None:
    previous = _map(("SPY", _sym("A")))
    current = _map(("SPY", _sym("B")))
    result = inject_lifecycle(current, previous)
    assert result["symbols"]["SPY"]["lifecycle"]["is_removed"] is False


# ---------------------------------------------------------------------------
# removed_symbols
# ---------------------------------------------------------------------------

def test_removed_symbols_empty_when_no_removals() -> None:
    previous = _map(("SPY", _sym()), ("QQQ", _sym()))
    current = _map(("SPY", _sym()), ("QQQ", _sym()))
    result = inject_lifecycle(current, previous)
    assert result["removed_symbols"] == []


def test_removed_symbols_populated() -> None:
    previous = _map(("SPY", _sym("A")), ("GLD", _sym("B")))
    current = _map(("SPY", _sym("A")))
    result = inject_lifecycle(current, previous)
    removed = result["removed_symbols"]
    assert len(removed) == 1
    entry = removed[0]
    assert entry["symbol"] == "GLD"
    assert entry["previous_grade"] == "B"
    assert entry["grade_transition"] == "REMOVED"
    assert entry["is_removed"] is True


def test_removed_symbols_key_always_present() -> None:
    current = _map(("SPY", _sym()))
    result = inject_lifecycle(current, None)
    assert "removed_symbols" in result
    assert result["removed_symbols"] == []


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------

def test_does_not_mutate_current_map() -> None:
    current = _map(("SPY", _sym("A", "ACTIONABLE")))
    original = copy.deepcopy(current)
    inject_lifecycle(current, None)
    assert current == original


def test_does_not_mutate_previous_map() -> None:
    previous = _map(("SPY", _sym("B")))
    original = copy.deepcopy(previous)
    current = _map(("SPY", _sym("A")))
    inject_lifecycle(current, previous)
    assert previous == original


# ---------------------------------------------------------------------------
# current_grade / current_setup_state populated correctly
# ---------------------------------------------------------------------------

def test_current_grade_and_setup_state_set() -> None:
    current = _map(("SPY", _sym("A+", "ACTIONABLE")))
    result = inject_lifecycle(current, None)
    lc = result["symbols"]["SPY"]["lifecycle"]
    assert lc["current_grade"] == "A+"
    assert lc["current_setup_state"] == "ACTIONABLE"


def test_previous_grade_set_when_snapshot_exists() -> None:
    previous = _map(("SPY", _sym("C", "DEVELOPING")))
    current = _map(("SPY", _sym("A", "ACTIONABLE")))
    result = inject_lifecycle(current, previous)
    lc = result["symbols"]["SPY"]["lifecycle"]
    assert lc["previous_grade"] == "C"
    assert lc["previous_setup_state"] == "DEVELOPING"


# ---------------------------------------------------------------------------
# PRD-085: current_price preservation
# ---------------------------------------------------------------------------

def test_inject_lifecycle_preserves_current_price() -> None:
    # T1: inject_lifecycle must not drop current_price added by PRD-084
    symbols = {
        sym: {**_sym("B", "DEVELOPING"), "current_price": 100.0 + i}
        for i, sym in enumerate(("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE"))
    }
    current = {"symbols": symbols, "schema_version": "market_map.v1"}
    result = inject_lifecycle(current, previous_map=None)
    for i, sym in enumerate(("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")):
        assert "current_price" in result["symbols"][sym], f"{sym} missing current_price"
        assert result["symbols"][sym]["current_price"] == 100.0 + i


def test_inject_lifecycle_preserves_current_price_none() -> None:
    # inject_lifecycle must preserve current_price: None when quote was unavailable
    current = {"symbols": {"SPY": {**_sym(), "current_price": None}}, "schema_version": "market_map.v1"}
    result = inject_lifecycle(current, previous_map=None)
    assert "current_price" in result["symbols"]["SPY"]
    assert result["symbols"]["SPY"]["current_price"] is None

"""
Deterministic lifecycle transition computation for market_map candidates.

Compares current market_map["symbols"] against a previous snapshot and injects
a "lifecycle" block into each symbol. Adds "removed_symbols" at the top level.

Pure functions only — no file I/O.
"""

from __future__ import annotations

import copy
import math
from typing import Any

GRADE_ORDER: dict[str, int] = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}


def _grade_transition(prev_grade: str | None, curr_grade: str | None) -> str:
    if prev_grade is None or curr_grade is None:
        return "UNKNOWN"
    if prev_grade not in GRADE_ORDER or curr_grade not in GRADE_ORDER:
        return "UNKNOWN"
    if prev_grade == curr_grade:
        return "UNCHANGED"
    if GRADE_ORDER[curr_grade] < GRADE_ORDER[prev_grade]:
        return "UPGRADED"
    return "DOWNGRADED"


def _setup_state_transition(prev_state: str | None, curr_state: str | None) -> str:
    if prev_state is None or curr_state is None:
        return "UNKNOWN"
    if prev_state == curr_state:
        return "UNCHANGED"
    return "CHANGED"


def inject_lifecycle(
    current_map: dict[str, Any],
    previous_map: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a new market_map dict with lifecycle blocks injected.

    Does not mutate current_map or previous_map.
    """
    result = copy.deepcopy(current_map)
    prev_symbols: dict[str, Any] = (previous_map or {}).get("symbols", {})
    curr_symbols: dict[str, Any] = result.get("symbols", {})

    for symbol, sym in curr_symbols.items():
        prev_sym: dict[str, Any] | None = prev_symbols.get(symbol)
        is_new = (previous_map is not None) and (prev_sym is None)

        if is_new:
            grade_tr = "NEW"
            setup_tr = "NEW"
        elif previous_map is None:
            grade_tr = "UNKNOWN"
            setup_tr = "UNKNOWN"
        else:
            grade_tr = _grade_transition(
                prev_sym.get("grade") if prev_sym else None,
                sym.get("grade"),
            )
            setup_tr = _setup_state_transition(
                prev_sym.get("setup_state") if prev_sym else None,
                sym.get("setup_state"),
            )

        sym["lifecycle"] = {
            "previous_grade": prev_sym.get("grade") if prev_sym else None,
            "current_grade": sym.get("grade"),
            "grade_transition": grade_tr,
            "previous_setup_state": prev_sym.get("setup_state") if prev_sym else None,
            "current_setup_state": sym.get("setup_state"),
            "setup_state_transition": setup_tr,
            "is_new": is_new,
            "is_removed": False,
        }

        if sym.get("current_price") is None and prev_sym is not None:
            prev_price = prev_sym.get("current_price")
            if isinstance(prev_price, (int, float)) and math.isfinite(prev_price):
                sym["current_price"] = float(prev_price)

    removed: list[dict[str, Any]] = []
    if previous_map is not None:
        for symbol, prev_sym in prev_symbols.items():
            if symbol not in curr_symbols:
                removed.append({
                    "symbol": symbol,
                    "previous_grade": prev_sym.get("grade"),
                    "grade_transition": "REMOVED",
                    "is_removed": True,
                })

    result["removed_symbols"] = removed
    return result

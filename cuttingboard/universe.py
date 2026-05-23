"""Symbol tradability helpers."""

from __future__ import annotations

from cuttingboard import config


def is_tradable_symbol(symbol: str) -> bool:
    if symbol.startswith("^"):
        return False
    return symbol not in config.NON_TRADABLE_SYMBOLS

from __future__ import annotations

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _macro_tape_block, _macro_tape_value_slots, _market_map, _payload, _run


def _drivers() -> dict:
    return {
        "gold": {"symbol": "GC=F", "level": 4705.2, "change_pct": 0.5},
        "silver": {"symbol": "SI=F", "level": 87.32, "change_pct": -0.3},
        "bitcoin": {"symbol": "BTC-USD", "level": 81300.0, "change_pct": 1.1},
        "volatility": {"symbol": "^VIX", "level": 18.1, "change_pct": -1.5},
        "dollar": {"symbol": "DX-Y.NYB", "level": 98.5, "change_pct": -0.2},
        "rates": {"symbol": "^TNX", "level": 4.42, "change_pct": -0.7},
        "oil": {"symbol": "CL=F", "level": 78.5, "change_pct": 1.2},
    }


def test_prd138_dashboard_macro_tape_row_order() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    assert [symbol for symbol, _value in _macro_tape_value_slots(html)] == [
        "XAU", "XAG", "BTC",
        "VIX", "DXY", "10Y", "OIL",
        "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE",
    ]


def test_prd138_dashboard_xau_xag_directional_css() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    tape = _macro_tape_block(html)
    # PRD-211: visible label is the honest CME futures ticker (GC/SI); the slot
    # id / data-symbol stays XAU/XAG (asserted elsewhere). PRD-224: 2-char
    # labels pad to the 3-char column with &nbsp; so arrow glyphs align.
    assert 'class="macro-tape-slot tape-slot up"><span class="macro-tape-label">GC&nbsp; ↑</span>' in tape
    assert 'class="macro-tape-slot tape-slot down"><span class="macro-tape-label">SI&nbsp; ↓</span>' in tape


def test_prd224_three_char_labels_are_not_padded() -> None:
    # PRD-224 R1: only sub-3-char labels pad; 3-char slots emit unchanged, and
    # the pad never leaks into data-symbol ids. Red test: padding a 3-char
    # label (or dropping the metals pad) fails one of these literals.
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    tape = _macro_tape_block(html)
    assert '<span class="macro-tape-label">BTC ↑</span>' in tape
    assert '<span class="macro-tape-label">VIX ↓</span>' in tape
    assert 'BTC&nbsp;' not in tape
    assert 'data-symbol="XAU"' in tape and 'data-symbol="XAU&nbsp;"' not in tape

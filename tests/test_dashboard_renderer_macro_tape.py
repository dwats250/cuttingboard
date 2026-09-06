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
    # PRD-336 R1: four families four-across in DOM order — VOL / CRYPTO
    # (VIX/BTC/ETH), RATES (2Y/5Y/10Y/30Y), FX (DXY/EURUSD/USDJPY/USDCAD), FUTURES
    # (OIL/NG/XAU/XAG) — then the unchanged tradables row. Cells render even when
    # this fixture supplies no block (value "--"); order is fixed by the families.
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    assert [symbol for symbol, _value in _macro_tape_value_slots(html)] == [
        "VIX", "BTC", "ETH",
        "2Y", "5Y", "10Y", "30Y",
        "DXY", "EURUSD", "USDJPY", "USDCAD",
        "OIL", "NG", "XAU", "XAG",
        "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE",
    ]


def test_prd138_dashboard_xau_xag_directional_css() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    tape = _macro_tape_block(html)
    # PRD-211: visible label is the honest CME futures ticker (GC/SI); data-symbol
    # stays XAU/XAG. PRD-336 R1: STACKED cell — label alone, then the direction
    # arrow on the value line inside .macro-tape-quote; the up/down slot class
    # colours the whole cell. No label padding (each cell is its own grid column).
    assert ('class="macro-tape-slot tape-slot up"><span class="macro-tape-label">GC</span>'
            '<span class="macro-tape-quote">↑&nbsp;') in tape
    assert ('class="macro-tape-slot tape-slot down"><span class="macro-tape-label">SI</span>'
            '<span class="macro-tape-quote">↓&nbsp;') in tape


def test_prd336_stacked_labels_are_not_padded() -> None:
    # PRD-336 R1: the stacked cell drops the PRD-224 &nbsp; column padding (each
    # cell is its own grid column). Labels are the bare display text; the pad never
    # leaks into data-symbol ids. Red test: re-introducing padding fails a literal.
    html = render_dashboard_html(_payload(macro_drivers=_drivers()), _run(), market_map=_market_map())
    tape = _macro_tape_block(html)
    assert '<span class="macro-tape-label">BTC</span>' in tape
    assert '<span class="macro-tape-label">VIX</span>' in tape
    assert '<span class="macro-tape-label">GC</span>' in tape   # metals no longer padded
    assert 'BTC&nbsp;' not in tape and 'GC&nbsp;' not in tape
    assert 'data-symbol="XAU"' in tape and 'data-symbol="XAU&nbsp;"' not in tape

"""Shared semantic layout for the dashboard and notification macro tape."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
import types as _types


@_dataclass(frozen=True)
class TapeSlot:
    label: str
    payload_key: str | None
    quote_symbol: str
    display_label: str | None = None

    @property
    def display(self) -> str:
        """Human-facing tape text. Defaults to ``label`` -- which is also the
        historic ``data-symbol`` key and the value-format dispatch key -- and is
        overridden only where ``label`` would misstate what the data IS. PRD-211:
        the metals slots carry the CME front-month *futures* (GC=F/SI=F), so the
        visible text reads GC/SI, not the spot codes XAU/XAG. ``label`` /
        ``data-symbol`` stay XAU/XAG for slot-id shape stability (PRD-136/137/138
        contract + the publish-refresh marker)."""
        return self.display_label or self.label


@_dataclass(frozen=True)
class TapeRow:
    name: str
    slots: tuple[TapeSlot, ...]


MACRO_ROW_1 = TapeRow(
    name="macro_row_1",
    slots=(
        TapeSlot(label="XAU", payload_key="gold", quote_symbol="GC=F", display_label="GC"),
        TapeSlot(label="XAG", payload_key="silver", quote_symbol="SI=F", display_label="SI"),
        TapeSlot(label="BTC", payload_key="bitcoin", quote_symbol="BTC-USD"),
    ),
)

MACRO_ROW_2 = TapeRow(
    name="macro_row_2",
    slots=(
        TapeSlot(label="VIX", payload_key="volatility", quote_symbol="^VIX"),
        TapeSlot(label="DXY", payload_key="dollar", quote_symbol="DX-Y.NYB"),
        # PRD-335 (R1/R2): display-only rate/FX context. USDJPY sits beside DXY
        # (FX); the actual 2Y (FRED DGS2) sits before 10Y and 30Y (rates). None of
        # these carry a macro-pressure vote — see MACRO_BIAS_DRIVERS below.
        TapeSlot(label="USDJPY", payload_key="usdjpy", quote_symbol="JPY=X"),
        TapeSlot(label="2Y", payload_key="rates_2y", quote_symbol="DGS2"),
        TapeSlot(label="10Y", payload_key="rates", quote_symbol="^TNX"),
        TapeSlot(label="30Y", payload_key="rates_30y", quote_symbol="^TYX"),
        # PRD-336 R5: the oil future is shown as "CL" in the cockpit FUTURES
        # family, but that relabel is COCKPIT-LOCAL (applied in the renderer, not
        # here) so the notification tape stays byte-unchanged (Helm ruling 1). The
        # shared slot keeps display "OIL"; only the dashboard cell substitutes CL.
        TapeSlot(label="OIL", payload_key="oil", quote_symbol="CL=F"),
    ),
)

# PRD-336 (Helm ruling 1): DASHBOARD-ONLY macro slots. They render on the cockpit
# macro tape (added to the renderer's display iterations and _slot_by_label) but
# are DELIBERATELY kept OUT of the notification/alert tape, which iterates only
# (MACRO_ROW_1, MACRO_ROW_2). Do NOT add MACRO_ROW_3 to the notification
# projection. All five are display-only and fenced from every vote site.
MACRO_ROW_3 = TapeRow(
    name="macro_row_3",
    slots=(
        TapeSlot(label="5Y", payload_key="rates_5y", quote_symbol="DGS5"),
        TapeSlot(label="EURUSD", payload_key="eurusd", quote_symbol="EURUSD=X"),
        TapeSlot(label="USDCAD", payload_key="usdcad", quote_symbol="USDCAD=X"),
        TapeSlot(label="NG", payload_key="natgas", quote_symbol="NG=F"),
        TapeSlot(label="ETH", payload_key="ethereum", quote_symbol="ETH-USD"),
    ),
)

TRADABLES_ROW = TapeRow(
    name="tradables_row",
    slots=(
        TapeSlot(label="SPY", payload_key=None, quote_symbol="SPY"),
        TapeSlot(label="QQQ", payload_key=None, quote_symbol="QQQ"),
        TapeSlot(label="GLD", payload_key=None, quote_symbol="GLD"),
        TapeSlot(label="GDX", payload_key=None, quote_symbol="GDX"),
        TapeSlot(label="SLV", payload_key=None, quote_symbol="SLV"),
        TapeSlot(label="XLE", payload_key=None, quote_symbol="XLE"),
    ),
)

MACRO_LABEL_TO_PAYLOAD_KEY = _types.MappingProxyType(
    {
        slot.label: slot.payload_key
        for row in (MACRO_ROW_1, MACRO_ROW_2, MACRO_ROW_3)
        for slot in row.slots
        if slot.payload_key is not None
    }
)

MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL = _types.MappingProxyType(
    {
        slot.payload_key: slot.quote_symbol
        for row in (MACRO_ROW_1, MACRO_ROW_2, MACRO_ROW_3)
        for slot in row.slots
        if slot.payload_key is not None
    }
)

# PRD-160: per-driver cyclicality for the macro_bias tally, keyed by
# payload_key. Contra-cyclical drivers move inversely to risk appetite — a
# falling VIX/DXY/10Y is risk-ON (long), a rising one is risk-OFF (short).
# Pro-cyclical drivers move with risk appetite — a rising BTC is risk-ON.
# OIL and the metals (XAU/XAG slots; GC/SI front-month futures) are
# visibility-only and deliberately excluded from the bias arithmetic. Keep this
# list here (not in the bias function) so adding a driver to the tally is a data
# edit, not a logic edit.
MACRO_BIAS_CONTRA_CYCLICAL = frozenset({"volatility", "dollar", "rates"})
MACRO_BIAS_PRO_CYCLICAL = frozenset({"bitcoin"})
MACRO_BIAS_DRIVERS = MACRO_BIAS_CONTRA_CYCLICAL | MACRO_BIAS_PRO_CYCLICAL

# PRD-214 retired the per-driver macro-evidence rows in favour of a single
# risk-vote tally, orphaning the PRD-177/PRD-191 interpretation strings
# (MACRO_BIAS_INTERPRETATION / _MACRO_BIAS_NEUTRAL_INTERP). They had no remaining
# consumer and were removed here as the dead-branch completion of that
# supersession. The cyclicality data above (CONTRA/PRO/DRIVERS) still feeds the
# tally and stays.

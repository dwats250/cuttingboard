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
        TapeSlot(label="10Y", payload_key="rates", quote_symbol="^TNX"),
        TapeSlot(label="OIL", payload_key="oil", quote_symbol="CL=F"),
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
        for row in (MACRO_ROW_1, MACRO_ROW_2)
        for slot in row.slots
        if slot.payload_key is not None
    }
)

MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL = _types.MappingProxyType(
    {
        slot.payload_key: slot.quote_symbol
        for row in (MACRO_ROW_1, MACRO_ROW_2)
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

# PRD-177 / PRD-191: presentation-only interpretation strings for the per-driver
# macro-evidence rows, keyed by payload_key and then by the driver's reading
# direction. PRD-191 made these direction-aware so the rationale subtitle agrees
# with the cyclicality-aware vote rendered alongside it: each form bakes in the
# driver's cyclicality (a rising contra-cyclical driver -- vol/dollar/yields --
# favors caution, a falling one favors risk; a rising pro-cyclical driver -- BTC
# -- favors risk). The renderer selects the form by the SAME arrow it computes
# for the vote, so prose and vote can never disagree. Strings only -- keep them
# here so wording stays a data edit, not a logic edit.
MACRO_BIAS_INTERPRETATION = _types.MappingProxyType(
    {
        "volatility": {"rising": "rising vol favors caution", "falling": "falling vol favors risk"},
        "dollar": {"rising": "firm dollar favors caution", "falling": "soft dollar favors risk"},
        "rates": {"rising": "rising yields favor caution", "falling": "easing yields favor risk"},
        "bitcoin": {"rising": "crypto bid favors risk", "falling": "crypto offered favors caution"},
    }
)

# PRD-191: the single shared neutral rationale for the flat / no-vote case (the
# driver's arrow is neither up nor down). Private (`_`-prefixed) so it stays off
# the module's public export surface (tests/test_macro_tape_layout.py allowlist).
_MACRO_BIAS_NEUTRAL_INTERP = "flat reading, no directional bias"

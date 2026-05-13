"""Shared semantic layout for the dashboard and notification macro tape."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
import types as _types


@_dataclass(frozen=True)
class TapeSlot:
    label: str
    payload_key: str | None
    quote_symbol: str


@_dataclass(frozen=True)
class TapeRow:
    name: str
    slots: tuple[TapeSlot, ...]


MACRO_ROW_1 = TapeRow(
    name="macro_row_1",
    slots=(
        TapeSlot(label="XAU", payload_key="gold", quote_symbol="GC=F"),
        TapeSlot(label="XAG", payload_key="silver", quote_symbol="SI=F"),
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

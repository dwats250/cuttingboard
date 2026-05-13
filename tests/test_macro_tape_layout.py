from __future__ import annotations

import dataclasses
import inspect
from types import MappingProxyType

from cuttingboard.delivery import macro_tape_layout as layout


def _labels(row: layout.TapeRow) -> tuple[str, ...]:
    return tuple(slot.label for slot in row.slots)


def test_macro_tape_layout_rows_are_frozen_dataclasses() -> None:
    assert dataclasses.is_dataclass(layout.TapeSlot)
    assert dataclasses.is_dataclass(layout.TapeRow)
    assert layout.TapeSlot.__dataclass_params__.frozen is True
    assert layout.TapeRow.__dataclass_params__.frozen is True


def test_macro_tape_layout_ordering_is_canonical() -> None:
    assert _labels(layout.MACRO_ROW_1) == ("XAU", "XAG", "BTC")
    assert _labels(layout.MACRO_ROW_2) == ("VIX", "DXY", "10Y", "OIL")
    assert _labels(layout.TRADABLES_ROW) == ("SPY", "QQQ", "GLD", "GDX", "SLV", "XLE")


def test_macro_tape_layout_macro_mappings_are_exhaustive() -> None:
    macro_slots = (*layout.MACRO_ROW_1.slots, *layout.MACRO_ROW_2.slots)

    assert set(layout.MACRO_LABEL_TO_PAYLOAD_KEY) == {slot.label for slot in macro_slots}
    assert set(layout.MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL) == {
        slot.payload_key for slot in macro_slots
    }
    for slot in macro_slots:
        assert slot.payload_key is not None
        assert layout.MACRO_LABEL_TO_PAYLOAD_KEY[slot.label] == slot.payload_key
        assert layout.MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL[slot.payload_key] == slot.quote_symbol


def test_macro_tape_layout_has_only_pure_semantic_exports() -> None:
    allowed_instances = (
        layout.MACRO_ROW_1,
        layout.MACRO_ROW_2,
        layout.TRADABLES_ROW,
        layout.MACRO_LABEL_TO_PAYLOAD_KEY,
        layout.MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL,
    )
    for name, member in inspect.getmembers(layout):
        if name.startswith("_") or name == "annotations":
            continue
        if member in (layout.TapeSlot, layout.TapeRow):
            continue
        if member in allowed_instances:
            continue
        raise AssertionError(f"unexpected public macro_tape_layout export: {name}")

    assert isinstance(layout.MACRO_LABEL_TO_PAYLOAD_KEY, MappingProxyType)
    assert isinstance(layout.MACRO_PAYLOAD_KEY_TO_QUOTE_SYMBOL, MappingProxyType)
    assert [
        name for name, _member in inspect.getmembers(layout, inspect.isfunction)
        if not name.startswith("_")
    ] == []

"""PRD-292: `_OPTIONAL_MACRO_DRIVERS` is single-sourced in `contract_types`
(the leaf); both consumers reference the same authority, with no duplicate
declaration and no `payload -> contract` import."""
from cuttingboard.contract import _OPTIONAL_MACRO_DRIVERS as contract_ref
from cuttingboard.contract_types import _OPTIONAL_MACRO_DRIVERS as leaf_ref
from cuttingboard.delivery.payload import _OPTIONAL_MACRO_DRIVERS as payload_ref


def test_single_authority_identity() -> None:
    # Both consumers must resolve to the exact same object from the leaf.
    assert contract_ref is leaf_ref
    assert payload_ref is leaf_ref


def test_vocabulary_preserved() -> None:
    # PRD-335: the display-only rate/FX drivers join the visibility fence.
    # PRD-336: five further display-only cockpit drivers join the same fence.
    assert leaf_ref == frozenset(
        {
            "oil", "gold", "silver", "rates_2y", "rates_30y", "usdjpy",
            "rates_5y", "eurusd", "usdcad", "natgas", "ethereum",
        }
    )


def test_no_duplicate_literal_declaration() -> None:
    # Neither consumer re-declares the frozenset literal (dedup invariant).
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "cuttingboard"
    for rel in ("contract.py", "delivery/payload.py"):
        src = (root / rel).read_text(encoding="utf-8")
        assert '_OPTIONAL_MACRO_DRIVERS = frozenset(' not in src and \
               '_OPTIONAL_MACRO_DRIVERS: frozenset[str] = frozenset(' not in src, \
               f"{rel} still declares the frozenset literal"

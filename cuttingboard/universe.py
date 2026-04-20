"""Minimal compatibility helpers for runtime execution filtering."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from logging import Logger
from typing import TypeVar

T = TypeVar("T")


def filter_execution_dict(items: Mapping[str, T], *, log: Logger | None = None) -> dict[str, T]:
    del log
    return dict(items)


def filter_execution_items(
    items: Iterable[T],
    *,
    symbol_getter: Callable[[T], str],
    log: Logger | None = None,
) -> list[T]:
    del symbol_getter, log
    return list(items)


def log_universe_configuration(log: Logger | None = None) -> None:
    if log is not None:
        log.debug("Universe filter compatibility layer active")

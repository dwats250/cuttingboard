"""Pure signal detectors for the stateless scanning layer."""

from cuttingboard.signals.models import MarketData

Signal = tuple[str, str]


def crossed_above(prev_price: float, price: float, threshold: float) -> bool:
    return prev_price <= threshold and price > threshold


def crossed_below(prev_price: float, price: float, threshold: float) -> bool:
    return prev_price >= threshold and price < threshold


def detect_signals(data: MarketData) -> list[Signal]:
    signals: list[Signal] = []

    if (
        data.price > data.ema9 > data.ema21 > data.ema50
        and crossed_above(data.prev_price, data.price, data.ema9)
    ):
        signals.append(("long", "breakout"))

    if (
        data.price < data.ema9 < data.ema21 < data.ema50
        and crossed_below(data.prev_price, data.price, data.ema9)
    ):
        signals.append(("short", "breakout"))

    if data.ema9 > data.ema21 > data.ema50 and data.ema21 <= data.price <= data.ema9:
        signals.append(("long", "pullback"))

    if data.ema9 < data.ema21 < data.ema50 and data.ema9 <= data.price <= data.ema21:
        signals.append(("short", "pullback"))

    if crossed_above(data.prev_price, data.price, data.ema50):
        signals.append(("long", "reversal"))

    if crossed_below(data.prev_price, data.price, data.ema50):
        signals.append(("short", "reversal"))

    return signals

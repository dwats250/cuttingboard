"""
Cuttingboard configuration.

All secrets come from .env (gitignored). Constants are safe to commit.
Never hardcode API keys, tokens, or credentials here.
"""

import os
import tomllib
from datetime import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_TOML = _PROJECT_ROOT / "config.toml"


def get_flow_data_path(_config_path: Optional[Path] = None) -> Optional[str]:
    """Return flow data_path from config.toml [flow] section, or None if absent/empty.

    Accepts an optional _config_path for test isolation (overrides default location).
    Never reads from environment variables.
    """
    path = _config_path if _config_path is not None else _CONFIG_TOML
    if not path.exists():
        return None
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    value = data.get("flow", {}).get("data_path", "")
    return str(value) if value else None


def get_engine_doctor_runtime_gate(_config_path: Optional[Path] = None) -> bool:
    """Return runtime_gate_enabled from config.toml [engine_doctor] section.

    Defaults to False when the section or key is absent.
    Accepts an optional _config_path for test isolation.
    """
    path = _config_path if _config_path is not None else _CONFIG_TOML
    if not path.exists():
        return False
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return bool(data.get("engine_doctor", {}).get("runtime_gate_enabled", False))

# ---------------------------------------------------------------------------
# Secrets — loaded from .env only, never hardcoded
# ---------------------------------------------------------------------------

POLYGON_API_KEY: str | None = os.getenv("POLYGON_API_KEY")
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")

# ---------------------------------------------------------------------------
# Pipeline constants
# ---------------------------------------------------------------------------

MIN_RR_RATIO            = 2.0
MIN_REGIME_CONFIDENCE   = 0.50
TARGET_DOLLAR_RISK      = 150
MAX_DOLLAR_RISK         = 200
FRESHNESS_SECONDS       = 300        # 5 minutes — max quote age for valid data
MAX_CLOCK_SKEW_SECONDS  = 5          # max tolerated quote timestamp skew into the future
HALT_SYMBOLS            = ["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]
OHLCV_MIN_BARS          = 21
OHLCV_FETCH_MONTHS      = 6
EMA_FAST                = 9
EMA_SLOW                = 21
EMA_TREND               = 50
ATR_PERIOD              = 14
VIX_CHAOTIC_SPIKE       = 0.15
VIX_HIGH                = 28
VIX_ELEVATED            = 20
VIX_LOW                 = 15
INTRADAY_ALERT_COOLDOWN = 90         # minutes

EXTENSION_ATR_MULTIPLIER            = 1.5   # reject if |price − ema21| > multiplier × ATR14
NEUTRAL_RR_RATIO                    = 3.0   # minimum R:R for NEUTRAL regime trades
EXPANSION_RR_RATIO                  = 1.5   # reduced R:R for EXPANSION continuation entries
FVG_DISPLACEMENT_K                  = 1.2   # displacement candle body vs ATR14
FVG_GAP_K                           = 0.3   # minimum gap size vs ATR14
FVG_PROXIMITY_K                     = 1.5   # max distance from current price to zone midpoint vs ATR14
FVG_LOOKBACK_CANDLES                = 6     # scan window in completed daily bars
REGIME_RISK_MULTIPLIER: dict[str, float] = {
    "RISK_ON":   1.0,
    "RISK_OFF":  1.0,
    "NEUTRAL":   0.6,
    "CHAOTIC":   0.0,
    "EXPANSION": 1.0,
}

# ---------------------------------------------------------------------------
# EXPANSION regime detection
# ---------------------------------------------------------------------------

EXPANSION_LEADERSHIP_SYMBOLS  = ["NVDA", "COIN", "MSTR", "SMCI", "TSLA"]
EXPANSION_MIN_BREADTH         = 0.70   # advancing / total watchlist symbols
EXPANSION_VIX_PCT_THRESHOLD   = -0.01  # VIX must be <= -1% to confirm falling volatility
EXPANSION_LEADERSHIP_MIN_PCT  = 0.015  # leadership symbol must gain >= +1.5%
EXPANSION_LEADERSHIP_MIN_COUNT = 2     # at least N leaders required

# Continuation entry parameters
CONTINUATION_BREAKOUT_BARS    = 5      # look back N candles for breakout level
CONTINUATION_HOLD_CANDLES     = 1      # completed candles that must hold above breakout
CONTINUATION_MOMENTUM_K       = 0.75   # last candle range >= K * ATR14
CONTINUATION_VIX_SPIKE_BLOCK  = 0.01   # block continuation if VIX pct > +1%
CONTINUATION_MAX_EXTENSION_ATR = 2.5   # reject if continuation entry is too far from EMA21
ENTRY_CUTOFF_ET                     = time(15, 30)  # no new entries at or after 3:30 PM ET

# ---------------------------------------------------------------------------
# Flow alignment gate (PRD-013)
# ---------------------------------------------------------------------------

FLOW_MIN_PREMIUM    = 250_000   # minimum print premium to qualify
FLOW_MIN_SPEC_SHARE = 0.60      # OTM ask premium must be >= 60% of total to classify SPECULATIVE
FLOW_RATIO_THRESHOLD = 1.50     # dominant direction premium must exceed opposite by 1.5×

# ---------------------------------------------------------------------------
# Data fetch settings
# ---------------------------------------------------------------------------

OHLCV_STALE_HOURS       = 12
OHLCV_CACHE_DIR         = "data/cache"
FETCH_RETRIES           = 3
FETCH_BACKOFF_SECONDS   = 2
FETCH_TIMEOUT_SECONDS   = 10

# ---------------------------------------------------------------------------
# Instrument universe
# ---------------------------------------------------------------------------

MACRO_DRIVERS = ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD"]
NON_TRADABLE_SYMBOLS: frozenset[str] = frozenset(MACRO_DRIVERS)
INDICES       = ["SPY", "QQQ", "IWM"]
COMMODITIES   = ["GLD", "SLV", "GDX", "PAAS", "USO", "XLE"]
HIGH_BETA     = ["NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR"]

ALL_SYMBOLS      = MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA
REQUIRED_SYMBOLS = ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "SPY", "QQQ"]

# ---------------------------------------------------------------------------
# Source priority per symbol
# ---------------------------------------------------------------------------

SYMBOL_SOURCE_PRIORITY: dict[str, list[str]] = {
    "^VIX":     ["yfinance"],
    "DX-Y.NYB": ["yfinance"],
    "^TNX":     ["yfinance"],
    "BTC-USD":  ["yfinance"],
    "default":  ["yfinance", "polygon"],
}

# ---------------------------------------------------------------------------
# Price sanity bounds (current market levels — update periodically)
# ---------------------------------------------------------------------------

PRICE_BOUNDS: dict[str, tuple[float, float]] = {
    "SPY":      (300,   900),
    "QQQ":      (200,   900),
    "IWM":      (100,   350),
    "GLD":      (100,   600),
    "SLV":      (10,    120),
    "GDX":      (15,    200),
    "PAAS":     (5,     120),
    "USO":      (40,    250),
    "XLE":      (50,    120),
    "NVDA":     (50,    2000),
    "TSLA":     (100,   600),
    "AAPL":     (120,   400),
    "META":     (200,   1000),
    "AMZN":     (100,   400),
    "COIN":     (50,    600),
    "MSTR":     (100,   2000),
    "^VIX":     (9,     90),
    "^TNX":     (1.0,   8.0),
    "DX-Y.NYB": (85,    125),
    "BTC-USD":  (10000, 200000),
}

# ---------------------------------------------------------------------------
# Units by symbol — used in NormalizedQuote.units
# ---------------------------------------------------------------------------

SYMBOL_UNITS: dict[str, str] = {
    "^VIX":     "index_level",
    "DX-Y.NYB": "index_level",
    "^TNX":     "yield_pct",
}
DEFAULT_UNITS = "usd_price"

# ---------------------------------------------------------------------------
# Polygon
# ---------------------------------------------------------------------------

POLYGON_PREV_URL = "https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"

# ---------------------------------------------------------------------------
# Correlation policy layer (PRD-023)
# ---------------------------------------------------------------------------

CORRELATION_ENABLED                 = True
CORRELATION_GOLD_SYMBOL             = "GLD"
CORRELATION_DOLLAR_SYMBOL           = "DX-Y.NYB"
CORRELATION_RISK_MODIFIER_ALIGNED   = 1.0
CORRELATION_RISK_MODIFIER_NEUTRAL   = 0.7
CORRELATION_RISK_MODIFIER_CONFLICT  = 0.4

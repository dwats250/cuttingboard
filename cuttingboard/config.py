"""
Cuttingboard configuration.

All secrets come from .env (gitignored). Constants are safe to commit.
Never hardcode API keys, tokens, or credentials here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Secrets — loaded from .env only, never hardcoded
# ---------------------------------------------------------------------------

POLYGON_API_KEY: str | None = os.getenv("POLYGON_API_KEY")
NTFY_TOPIC: str | None = os.getenv("NTFY_TOPIC")
NTFY_URL: str | None = os.getenv("NTFY_URL")

# ---------------------------------------------------------------------------
# Pipeline constants
# ---------------------------------------------------------------------------

MIN_RR_RATIO            = 2.0
MIN_REGIME_CONFIDENCE   = 0.50
TARGET_DOLLAR_RISK      = 150
MAX_DOLLAR_RISK         = 200
FRESHNESS_SECONDS       = 300        # 5 minutes — max quote age for valid data
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
REGIME_RISK_MULTIPLIER: dict[str, float] = {
    "RISK_ON":  1.0,
    "RISK_OFF": 1.0,
    "NEUTRAL":  0.6,
    "CHAOTIC":  0.0,
}
LATE_SESSION_CUTOFF                 = (15, 30)  # (hour, minute) ET — no entries after 3:30 PM

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

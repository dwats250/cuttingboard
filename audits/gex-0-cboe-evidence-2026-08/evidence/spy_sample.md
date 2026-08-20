# CBOE delayed_quotes evidence excerpt - SPY

Truncated schema + partial rows (no full chain). Machine-read by
`test_gex0_cboe_evidence.py` (extracts the single fenced json block).

```json
{
  "source": "CBOE delayed_quotes public JSON",
  "provider_label": "Cboe Global Markets, Inc. (delayed_quotes CDN feed)",
  "symbol": "SPY",
  "endpoint": "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json",
  "fetched_at_utc": "2026-08-17T18:43:25.118488+00:00",
  "http_status": 200,
  "response_top_level_keys": [
    "data",
    "symbol",
    "timestamp"
  ],
  "response_timestamp_field": "2026-08-17 18:42:26",
  "observed_full_contract_count": 14546,
  "settlement_roots_present": {
    "SPY": 14546
  },
  "expiration_yymmdd_min": "260817",
  "expiration_yymmdd_max": "281215",
  "distinct_expirations": 34,
  "excerpt_row_count": 2,
  "underlying": {
    "current_price": 773.5099,
    "close": 773.5099,
    "prev_day_close": 776.34,
    "bid": 773.51,
    "ask": 773.53,
    "tick": "down",
    "volume": 16160558,
    "last_trade_time": "2026-08-17T14:27:23",
    "price": 773.5099
  },
  "field_schema": {
    "option": "str",
    "bid": "float",
    "bid_size": "float",
    "ask": "float",
    "ask_size": "float",
    "iv": "float",
    "open_interest": "float",
    "volume": "float",
    "delta": "float",
    "gamma": "float",
    "vega": "float",
    "theta": "float",
    "rho": "float",
    "theo": "float",
    "change": "float",
    "open": "float",
    "high": "float",
    "low": "float",
    "tick": "str",
    "last_trade_price": "float",
    "last_trade_time": "str",
    "percent_change": "float",
    "prev_day_close": "float"
  },
  "sample_contracts": [
    {
      "option": "SPY260817C00500000",
      "bid": 273.38,
      "bid_size": 1.0,
      "ask": 273.81,
      "ask_size": 2.0,
      "iv": 0.0,
      "open_interest": 0.0,
      "volume": 372.0,
      "delta": 0.9998,
      "gamma": 0.0,
      "vega": 0.0001,
      "theta": -0.0039,
      "rho": 0.0,
      "theo": 273.4989,
      "change": -2.4,
      "open": 275.58,
      "high": 275.81,
      "low": 272.65,
      "tick": "down",
      "last_trade_price": 273.81,
      "last_trade_time": "2026-08-17T14:27:08",
      "percent_change": -0.868901,
      "prev_day_close": 276.209991455078
    },
    {
      "option": "SPY260817P00500000",
      "bid": 0.0,
      "bid_size": 0.0,
      "ask": 0.01,
      "ask_size": 2114.0,
      "iv": 8.2778,
      "open_interest": 12.0,
      "volume": 0.0,
      "delta": -0.0002,
      "gamma": 0.0,
      "vega": 0.0001,
      "theta": -0.0039,
      "rho": 0.0,
      "theo": 0.0039,
      "change": 0.0,
      "open": 0.0,
      "high": 0.0,
      "low": 0.0,
      "tick": "no_change",
      "last_trade_price": 0.01,
      "last_trade_time": "2026-08-13T14:48:29",
      "percent_change": 0.0,
      "prev_day_close": 0.00499999988824129
    }
  ],
  "observed_response_headers": {
    "Date": "Mon, 17 Aug 2026 18:43:24 GMT",
    "Content-Type": "application/json",
    "last-modified": "Mon, 17 Aug 2026 18:42:34 GMT",
    "Cache-Control": "max-age=0, s-maxage=5",
    "x-cache": "Miss from cloudfront",
    "x-amz-cf-pop": "SEA900-P6",
    "cf-cache-status": "DYNAMIC"
  }
}
```

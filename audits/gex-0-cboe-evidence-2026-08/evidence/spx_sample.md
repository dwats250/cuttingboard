# CBOE delayed_quotes evidence excerpt - _SPX

Truncated schema + partial rows (no full chain). Machine-read by
`test_gex0_cboe_evidence.py` (extracts the single fenced json block).

```json
{
  "source": "CBOE delayed_quotes public JSON",
  "provider_label": "Cboe Global Markets, Inc. (delayed_quotes CDN feed)",
  "symbol": "_SPX",
  "endpoint": "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json",
  "fetched_at_utc": "2026-08-17T18:43:25.963651+00:00",
  "http_status": 200,
  "response_top_level_keys": [
    "data",
    "symbol",
    "timestamp"
  ],
  "response_timestamp_field": "2026-08-17 18:42:35",
  "observed_full_contract_count": 30558,
  "settlement_roots_present": {
    "SPX": 10208,
    "SPXW": 20350
  },
  "expiration_yymmdd_min": "260817",
  "expiration_yymmdd_max": "311219",
  "distinct_expirations": 57,
  "excerpt_row_count": 2,
  "underlying": {
    "current_price": 7755.5098,
    "close": 7755.5098,
    "prev_day_close": 7785.7598,
    "bid": 7754.1602,
    "ask": 7756.9102,
    "tick": "down",
    "volume": 0,
    "last_trade_time": "2026-08-17T14:27:32",
    "price": 7755.5098
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
      "option": "SPX260821C00200000",
      "bid": 7543.8,
      "bid_size": 2.0,
      "ask": 7564.3,
      "ask_size": 1.0,
      "iv": 0.0,
      "open_interest": 2960.0,
      "volume": 0.0,
      "delta": 0.9999,
      "gamma": 0.0,
      "vega": 0.0001,
      "theta": 0.0,
      "rho": 0.0331,
      "theo": 7553.8584,
      "change": 0.0,
      "open": 0.0,
      "high": 0.0,
      "low": 0.0,
      "tick": "no_change",
      "last_trade_price": 7553.37,
      "last_trade_time": "2026-08-11T10:31:50",
      "percent_change": 0.0,
      "prev_day_close": 7581.40014648438
    },
    {
      "option": "SPX260821P00200000",
      "bid": 0.0,
      "bid_size": 0.0,
      "ask": 0.05,
      "ask_size": 967.0,
      "iv": 0.0,
      "open_interest": 10649.0,
      "volume": 0.0,
      "delta": 0.0,
      "gamma": 0.0,
      "vega": 0.0001,
      "theta": -0.005,
      "rho": 0.0,
      "theo": 0.005,
      "change": 0.0,
      "open": 0.0,
      "high": 0.0,
      "low": 0.0,
      "tick": "no_change",
      "last_trade_price": 0.05,
      "last_trade_time": "2026-04-13T09:30:02",
      "percent_change": 0.0,
      "prev_day_close": 0.025000000372529
    }
  ],
  "observed_response_headers": {
    "Date": "Mon, 17 Aug 2026 18:43:25 GMT",
    "Content-Type": "application/json",
    "last-modified": "Mon, 17 Aug 2026 18:42:38 GMT",
    "Cache-Control": "max-age=0, s-maxage=5",
    "x-cache": "RefreshHit from cloudfront",
    "x-amz-cf-pop": "SEA900-P6",
    "cf-cache-status": "DYNAMIC"
  }
}
```

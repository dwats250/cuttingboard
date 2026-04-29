---
name: cuttingboard
description: "Skill for the Cuttingboard area of cuttingboard. 81 symbols across 12 files."
---

# Cuttingboard

81 symbols | 12 files | Cohesion: 72%

## When to Use

- Working with code in `cuttingboard/`
- Understanding how test_error_contract_macro_drivers_empty_dict, build_pipeline_output_contract, build_error_contract work
- Modifying cuttingboard-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `cuttingboard/contract.py` | build_pipeline_output_contract, build_error_contract, _build_market_context, _build_audit_summary, _iso_str (+11) |
| `cuttingboard/watch.py` | _classify_symbol, _structure_score, _compression_score, _momentum_score, _compression_state (+8) |
| `cuttingboard/ingestion.py` | fetch_ohlcv, _is_fresh_ohlcv_cache, _ohlcv_cache_path, _write_ohlcv_cache, fetch_all_quotes (+7) |
| `cuttingboard/evaluation.py` | run_post_trade_evaluation, load_most_recent_prior_run, extract_allow_trade_candidates, build_evaluation_records, assert_evaluation_valid (+6) |
| `cuttingboard/intraday_state_engine.py` | _evaluate_break_state, _select_orb_level, _to_et, _et_time, _orb_bars (+3) |
| `cuttingboard/normalization.py` | normalize_quotes, normalize_quote, _to_decimal, _ensure_utc, _validated_float |
| `cuttingboard/confirmation.py` | _normalize_allowed_directions, _crosses_level, _reclaims_level, _build_confirmation, evaluate_level_confirmation |
| `tests/test_phase1.py` | test_pct_change_large_value_corrected, test_naive_datetime_gets_utc, test_age_seconds_is_positive, test_normalize_quotes_filters_failures |
| `cuttingboard/derived.py` | _compute, _wilder_atr, _momentum_5d, _volume_ratio |
| `tests/test_contract_macro_drivers.py` | test_error_contract_macro_drivers_empty_dict |

## Entry Points

Start here when exploring this area:

- **`test_error_contract_macro_drivers_empty_dict`** (Function) — `tests/test_contract_macro_drivers.py:140`
- **`build_pipeline_output_contract`** (Function) — `cuttingboard/contract.py:47`
- **`build_error_contract`** (Function) — `cuttingboard/contract.py:105`
- **`test_pct_change_large_value_corrected`** (Function) — `tests/test_phase1.py:151`
- **`test_naive_datetime_gets_utc`** (Function) — `tests/test_phase1.py:162`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_error_contract_macro_drivers_empty_dict` | Function | `tests/test_contract_macro_drivers.py` | 140 |
| `build_pipeline_output_contract` | Function | `cuttingboard/contract.py` | 47 |
| `build_error_contract` | Function | `cuttingboard/contract.py` | 105 |
| `test_pct_change_large_value_corrected` | Function | `tests/test_phase1.py` | 151 |
| `test_naive_datetime_gets_utc` | Function | `tests/test_phase1.py` | 162 |
| `test_age_seconds_is_positive` | Function | `tests/test_phase1.py` | 172 |
| `test_normalize_quotes_filters_failures` | Function | `tests/test_phase1.py` | 177 |
| `normalize_quotes` | Function | `cuttingboard/normalization.py` | 40 |
| `normalize_quote` | Function | `cuttingboard/normalization.py` | 60 |
| `evaluate_level_confirmation` | Function | `cuttingboard/confirmation.py` | 105 |
| `run_post_trade_evaluation` | Function | `cuttingboard/evaluation.py` | 36 |
| `load_most_recent_prior_run` | Function | `cuttingboard/evaluation.py` | 73 |
| `extract_allow_trade_candidates` | Function | `cuttingboard/evaluation.py` | 108 |
| `build_evaluation_records` | Function | `cuttingboard/evaluation.py` | 134 |
| `assert_evaluation_valid` | Function | `cuttingboard/evaluation.py` | 231 |
| `append_evaluation_records` | Function | `cuttingboard/evaluation.py` | 250 |
| `test_stale_ohlcv_cache_rejected_after_fetch_failure` | Function | `tests/test_derived.py` | 249 |
| `fetch_ohlcv` | Function | `cuttingboard/ingestion.py` | 120 |
| `test_get_session_phase_boundaries` | Function | `tests/test_watch.py` | 96 |
| `get_session_phase` | Function | `cuttingboard/watch.py` | 102 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _ohlcv_cache_path` | cross_community | 5 |
| `Main → _is_fresh_ohlcv_cache` | cross_community | 5 |
| `Main → _write_ohlcv_cache` | cross_community | 5 |
| `Main → _wilder_atr` | cross_community | 5 |
| `Main → _momentum_5d` | cross_community | 5 |
| `Compute_intraday_state → _to_et` | cross_community | 5 |
| `Deliver_html → Get_session_phase` | cross_community | 5 |
| `Compute_all_derived → _run_with_timeout` | cross_community | 5 |
| `Run_post_trade_evaluation → _assert_candidate_shape` | cross_community | 4 |
| `Run_post_trade_evaluation → _filter_forward_bars` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 6 calls |

## How to Explore

1. `gitnexus_context({name: "test_error_contract_macro_drivers_empty_dict"})` — see callers and callees
2. `gitnexus_query({query: "cuttingboard"})` — find related execution flows
3. Read key files listed above for implementation details

---
name: tests
description: "Skill for the Tests area of cuttingboard. 1331 symbols across 78 files."
---

# Tests

1331 symbols | 78 files | Cohesion: 82%

## When to Use

- Working with code in `tests/`
- Understanding how test_chaotic_regime_short_circuits, test_risk_on_passes_regime_gate, test_low_confidence_short_circuits work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_phase5.py` | _regime, _structure, _quote, _dm, _qual_result (+82) |
| `tests/test_qualification.py` | _regime, _structure, _candidate, _dm, _valid_long_fvg_df (+70) |
| `tests/test_chain_validation.py` | _quote, _setup, _mock_ticker, test_validated_on_clean_chain, test_manual_check_when_chain_unavailable (+68) |
| `tests/test_levels.py` | test_every_scenario_has_level_token, test_risk_on_scenarios_have_tokens, test_risk_off_scenarios_have_tokens, test_neutral_scenarios_have_tokens, test_chaotic_scenarios_have_tokens (+51) |
| `tests/test_prd018_notification_suppression.py` | test_first_run_sends_when_no_state_file, _make_contract, test_error_status_is_critical, test_stale_data_is_critical, test_tradable_true_is_high (+45) |
| `tests/test_payload.py` | _minimal_contract, _trade_candidate, _rejection, test_valid_contract_produces_valid_payload, test_schema_version_is_correct (+44) |
| `tests/test_delivery.py` | _contract, _payload, test_ok_status_renders_without_halt, test_stay_flat_renders_no_trade, test_adapter_does_not_render_summary_block (+44) |
| `tests/test_flow.py` | test_gate_noop_when_snapshot_none, _pass_result, _watchlist_result, _reject_result, _otm_ask_call (+43) |
| `tests/test_structure.py` | _dm, _quote, _insufficient, test_none_dm_is_chop, test_insufficient_history_is_chop (+41) |
| `tests/test_scenario_engine.py` | test_required_keys_exact, test_preferred_direction_enum, test_id_and_condition_are_nonempty_strings, test_identical_inputs_produce_identical_scenarios, test_two_scenarios (+39) |

## Entry Points

Start here when exploring this area:

- **`test_chaotic_regime_short_circuits`** (Function) — `tests/test_qualification.py:314`
- **`test_risk_on_passes_regime_gate`** (Function) — `tests/test_qualification.py:319`
- **`test_low_confidence_short_circuits`** (Function) — `tests/test_qualification.py:325`
- **`test_chop_symbol_excluded`** (Function) — `tests/test_qualification.py:339`
- **`test_chop_not_in_qualified_or_watchlist`** (Function) — `tests/test_qualification.py:346`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TestBuildNotificationMessage` | Class | `tests/test_prd017_notification_stabilization.py` | 67 |
| `test_chaotic_regime_short_circuits` | Function | `tests/test_qualification.py` | 314 |
| `test_risk_on_passes_regime_gate` | Function | `tests/test_qualification.py` | 319 |
| `test_low_confidence_short_circuits` | Function | `tests/test_qualification.py` | 325 |
| `test_chop_symbol_excluded` | Function | `tests/test_qualification.py` | 339 |
| `test_chop_not_in_qualified_or_watchlist` | Function | `tests/test_qualification.py` | 346 |
| `test_short_candidate_in_risk_on_regime_excluded` | Function | `tests/test_qualification.py` | 360 |
| `test_long_candidate_in_risk_off_regime_excluded` | Function | `tests/test_qualification.py` | 368 |
| `test_no_candidates_no_per_symbol_qualification` | Function | `tests/test_qualification.py` | 381 |
| `test_stay_flat_gate1_reject` | Function | `tests/test_qualification.py` | 394 |
| `test_low_confidence_gate2_reject` | Function | `tests/test_qualification.py` | 403 |
| `test_direction_mismatch_gate3_reject` | Function | `tests/test_qualification.py` | 412 |
| `test_chop_structure_gate4_reject` | Function | `tests/test_qualification.py` | 419 |
| `test_hard_failure_no_watchlist` | Function | `tests/test_qualification.py` | 426 |
| `test_hard_failure_gates_passed_accumulated` | Function | `tests/test_qualification.py` | 431 |
| `test_fully_qualified_result` | Function | `tests/test_qualification.py` | 455 |
| `test_all_9_gates_passed` | Function | `tests/test_qualification.py` | 462 |
| `test_position_sizing` | Function | `tests/test_qualification.py` | 476 |
| `test_direction_field_set` | Function | `tests/test_qualification.py` | 487 |
| `test_zero_stop_fails_gate5` | Function | `tests/test_qualification.py` | 502 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _normalize_frame` | cross_community | 6 |
| `Main → _ohlcv_cache_path` | cross_community | 5 |
| `Main → _is_fresh_ohlcv_cache` | cross_community | 5 |
| `Main → _write_ohlcv_cache` | cross_community | 5 |
| `Main → _wilder_atr` | cross_community | 5 |
| `Main → _momentum_5d` | cross_community | 5 |
| `Main → _iso` | cross_community | 5 |
| `Compute_intraday_state → _to_et` | cross_community | 5 |
| `Deliver_html → _require_keys` | cross_community | 5 |
| `Deliver_html → _require_eq` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cuttingboard | 19 calls |
| Algos | 7 calls |
| Notifications | 4 calls |
| Delivery | 4 calls |

## How to Explore

1. `gitnexus_context({name: "test_chaotic_regime_short_circuits"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details

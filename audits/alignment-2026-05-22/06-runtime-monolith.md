# 06 — runtime.py Monolith (Informational)

`cuttingboard/runtime.py` is acknowledged technical debt per
`docs/PROJECT_STATE.md § Known technical debt`. Refactor deferred until a
forcing function (next runtime PRD spanning ≥3 independent branches).
This file flags observations only; no prescription.

## Shape

- ~2100 LOC (formal count in PROJECT_STATE.md / PRD-135 milestone).
- Hit by every notify mode: hourly, daily live, sunday, intraday, fixture.
- ~50+ top-level functions; module structure surveyed via grep on
  `^def `, `^class ` in this audit.

## Functional groupings observed

A future refactor PRD will likely cut along these lines. Listed as
*natural* not *prescribed*:

1. **CLI / orchestration entry**: `build_parser`, `cli_main`,
   `execute_prefetch`, `execute_run` (lines ~245–321).
2. **Notify-mode dispatch + hourly path**: `_hourly_rr`,
   `_build_hourly_candidate_lines`, `_load_flow`, `_execute_notify_run`,
   `_build_hourly_contract`, `_build_hourly_run_summary`,
   `_write_hourly_artifacts` (lines ~399–1870).
3. **Main pipeline**: `_run_pipeline` at line 698 — the core function.
4. **Intraday wiring**: `_apply_intraday_short_permission` (1205) and
   helpers `_compute_overall_pressure`,
   `_load_execution_policy_session_state`,
   `_build_execution_policy_orb_states`, `_intraday_state_bars_from_df`,
   `_reconstruct_previous_close`, `_downside_permission_from_state`.
5. **Verification / IO helpers**: `verify_run_summary`, `_load_inputs`,
   `_load_fixture_quotes`, `_fixture_*`, `_write_markdown_report`,
   `safe_write_latest`, `_write_summary_files`, `_write_contract_file`.
6. **Sidecar wiring + write**: `_load_previous_market_map`,
   `_write_market_map_file`, `_tradable_symbols`,
   `_write_trend_structure_snapshot`, `_refresh_trend_structure_sidecar`,
   `_write_watchlist_snapshot`, `_write_macro_snapshot`,
   `_write_payload_artifacts`.
7. **Small utilities**: `_data_status`, `_kill_switch`,
   `_min_rr_for_regime`, `_summary_regime_fields`, `_chain_warning_lines`,
   `_validated_chain_result`, `_resolve_*`, `_deterministic_run_at`,
   `_run_id`, `_generation_id`, `_attach_generation_id_to_payload`.

The 7 groups above are independent enough that a refactor PRD could
extract any subset without dragging the others. Most natural first cut:
**group 6 (sidecar wiring + write)** — it has minimal coupling to the
core pipeline logic and is the most consumer-facing.

## VISION-alignment observations within runtime.py

- **Description, not prediction**: clean. `_kill_switch`,
  `_min_rr_for_regime`, etc. operate on observed regime state.
- **Read-only sidecars**: runtime is the wiring layer that *invokes*
  sidecar builders and *writes* their output. The sidecars themselves
  remain read-only; runtime is the legitimate place for that wiring.
- **Cuts before additions**: TENSION. The size itself is the issue. Every
  new notify-mode PRD widens the monolith. The cleanup pass left
  `_tradable_symbols` as an intentionally deferred vulture candidate per
  PROJECT_STATE.md — this is consistent with "don't refactor runtime
  outside a scoped PRD" but means dead-symbol drift accumulates here
  preferentially.
- **Matches documentation**: runtime is now well-described via PRD-135
  milestone (`docs/milestones/ENGINE_MILESTONE_2026-05-12.md`) and
  `docs/PRD_PROCESS.md`. No silent drift detected.

## Dead-code suspects already flagged

- `_tradable_symbols` (1904) — explicitly deferred vulture candidate per
  PROJECT_STATE.md known-debt entry. Do not re-run vulture here outside a
  scoped PRD.
- No new candidates surfaced by this read. Per audit brief: do not re-run
  vulture; reference the cleanup output.

## Possible naturally-extracting responsibilities

Listed as observations, not recommendations:

- **`runtime/hourly.py`** — the hourly-mode path
  (`_execute_notify_run` for `notify_mode == NOTIFY_HOURLY`, hourly
  contract/summary/artifact builders).
- **`runtime/sidecars.py`** — the sidecar wiring + write layer.
- **`runtime/io.py`** — `safe_write_latest` and the JSON write helpers.
- **`runtime/fixture.py`** — `_fixture_*` helpers; fully isolatable.

None of the above are prescriptions. They surface as natural extraction
seams in case the user wants to scope the refactor PRD later.

## Headline

runtime.py size remains the dominant TENSION against
*cuts-before-additions* but per VISION operating principles this is
acknowledged debt awaiting its forcing function. No VIOLATIONS detected
inside the file. Pipeline grouping is intact and extractable when the
refactor PRD is scoped.

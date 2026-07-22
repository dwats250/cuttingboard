# Verification — Track B: stage0-02-evaluation-v0.1.md (Q13-15)

**MEMORY PROVENANCE CORROBORATED; SESSION ID SELF-REPORT INVALID** — see
`verify-00-disposition-index.md`'s capability header: this session's
self-reported session id was a template placeholder, invalid on its own
terms, but its memory provenance is independently corroborated from the
real subagent transcript (agentId `ae66653afaad4b245`): zero memory-file
reads. Isolation stands as verified on the memory dimension. The findings
below were independently derived via each check's own methodology as a
further, separable claim. Verified against
this worktree's HEAD, source-tree-identical to the pinned SHA
`771f730839b00b0537327f9696210275f36cd790`.

## Per-question disposition

- **Q13 (minimal cohort evaluation schema) — CONFIRMED.**
  - `evaluation.py::extract_allow_trade_candidates` (lines 114-137): reads
    `raw.get("decision_status") == "ALLOW_TRADE"` as the sole selector —
    confirmed verbatim; no watchlist/excluded cohort is referenced anywhere
    in the function.
  - `evaluation.py:45-71` (`run_post_trade_evaluation`): loads the prior audit
    record, calls `extract_allow_trade_candidates`, returns `[]` if empty —
    confirmed.
  - `evaluation.py:167-176`: the persisted record shape is
    `evaluated_at_utc/decision_run_at_utc/symbol/direction/entry/stop/target/evaluation`
    — confirmed, no cohort-source field.
  - `qualification.py:124-142` (`QualificationSummary`) — confirmed
    `watchlist: list[QualificationResult]` and `excluded: dict[str, str]` both
    exist as distinct fields on the dataclass.
  - `audit.py:154-166` writes `qual.watchlist` into the audit record's
    `near_a_plus` key; `audit.py:190-197` separately writes
    `watch_summary.watchlist` (a different object, `WatchSummary.watchlist`)
    into the record's own `watchlist` key; `audit.py:230-234` confirms both
    keys (`near_a_plus` and `watchlist`) coexist in the final record dict —
    confirmed exactly. This substantiates the "bare `watchlist` label is
    ambiguous" claim: the audit record's `watchlist` key is the intraday
    `WatchSummary` one, not the qualification watchlist (which is
    `near_a_plus`) — a real naming trap for anyone reading the audit schema
    casually.

- **Q14 (`stay_flat_reason` persistence gap) — CONFIRMED.**
  - `contract.py:226-263` (`_build_system_state`) derives `stay_flat_reason`
    from `halt_reason` / `regime_failure_reason` / `"STAY_FLAT posture"` in
    that priority order — confirmed exactly.
  - `runtime/__init__.py:799` sets
    `contract["system_state"]["reason"] = contract["system_state"].get("stay_flat_reason")`;
    `runtime/__init__.py:806-808` (the `MODE_SUNDAY` branch) overrides
    `stay_flat_reason = "PREMARKET_CONTEXT"` immediately after — confirmed the
    exact sequencing the artifact describes ("sets the alias before the
    Sunday... override").
  - `runtime/__init__.py:1124-1147` (`write_audit_record` call site) passes
    only `halt_reason=validation_summary.halt_reason` — no `stay_flat_reason`
    parameter exists on `write_audit_record`'s signature
    (`audit.py:35-83`), and the built record dict (`audit.py:199-241`)
    contains a `halt_reason` key but no `stay_flat_reason` key — confirmed by
    reading the full record-construction dict; the field is genuinely absent
    from the append-only audit schema.
  - `runtime/__init__.py:248-275` calls `_write_contract_file(pipeline.contract)`
    which persists the full finalized contract (including `stay_flat_reason`)
    to `logs/latest_contract.json` — confirmed, contrasting with the audit
    gap.
  - `delivery/payload.py:98-101` reads `ss.get("stay_flat_reason")` into
    `validation_halt_detail` — confirmed the field does reach the payload.
  - Net: the claim that the contract/payload path already carries
    `stay_flat_reason` while the append-only audit path does not is
    precisely correct, verified by reading every cited function's actual
    field list rather than trusting the artifact's paraphrase.

- **Q15 (session-clustered aggregation, min-sample=5) — CONFIRMED.**
  - `performance_engine.py:23` — `_MIN_SAMPLE = 5` confirmed literally.
  - `performance_engine.py:85-105` (`_aggregate`) groups exclusively by
    `record["symbol"]` — confirmed, no session/date/run grouping key anywhere
    in the function.
  - `performance_engine.py:111-136` — `if total < _MIN_SAMPLE:` branch sets
    `insufficient_data: True` and omits `win_rate`/`expectancy`; the `else`
    branch computes them and sets `insufficient_data: False` — confirmed
    exactly.
  - `evaluation.py:167-176` retains `decision_run_at_utc` per-record but this
    field is never consumed for grouping anywhere in `performance_engine.py`
    (confirmed by reading the whole `_aggregate` function) — substantiates
    "no session_id/session_cluster grouping exists."
  - `runtime/__init__.py:1143-1147` invokes evaluation then
    `run_performance_engine` in sequence — confirmed the reachability claim.

## Assessment

All three questions' load-bearing STATIC claims were checked directly against
function bodies (not just line-range existence) and match exactly, including
subtle details like the `near_a_plus` vs. `watchlist` key-naming trap in
`audit.py` and the precise ordering of the Sunday `stay_flat_reason` override
relative to the `reason` alias assignment. No RUNTIME trace in this track
required independent re-execution beyond what STATIC code reading already
settles (the traced functions — `extract_allow_trade_candidates`,
`_aggregate`, `_build_record` — are pure, small, and their behavior is fully
determined by the code paths already confirmed above).

**Disposition: CONFIRMED across Q13, Q14, Q15. Nothing falsified or narrowed.**

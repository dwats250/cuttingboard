> Orchestrator note: Codex self-reported it could not detect its own
> CLI banner/session id (a known blind spot -- the banner is printed
> by the CLI wrapper, outside the model's own context). The actual
> session id, extracted from stdout by the orchestrator, is
> `019f8315-7c04-7582-8ce2-9fdcb0136890`. Rollout: `rollout-2026-07-20T22-10-51-019f8315-7c04-7582-8ce2-9fdcb0136890.jsonl`.
> Verification disposition: CORROBORATED -- every tool call in the
> rollout is a local `exec` (git/rg/sed/python3/pytest); no MCP,
> plugin, browser, or network tool call appears anywhere; the
> self-reported memory-file reads (MEMORY.md, memory_summary.md,
> and any skill files) match the rollout's actual reads exactly.
>
---

## Header

- Repository and inspected SHA: dwats250/cuttingboard @ 771f730839b00b0537327f9696210275f36cd790
- Session/model: Could not detect a CLI banner; best identification: Codex, an agent based on GPT-5; session id unavailable in visible context.
- Repository access: READ
- Test/trace capability: YES — `python -B -m pytest --collect-only -q -p no:cacheprovider` could not start because `python` is absent; `python3 -B -m pytest --collect-only -q -p no:cacheprovider` failed before collection because the read-only sandbox has no usable temporary directory; pure `python3 -B -c` traces of `extract_allow_trade_candidates`, `_aggregate`, and `audit._build_record` worked.
- Prior findings visible before first pass: YES — `docs/DECISIONS.md:135-139`, stating that `_check_regime_gates` appends a human-readable coverage note into `stay_flat_reason`. No `audits/*` or `docs/PROJECT_STATE.md` conclusion was read.
- Evidence classes used: STATIC@771f730839b00b0537327f9696210275f36cd790, RUNTIME@771f730839b00b0537327f9696210275f36cd790, HYPOTHESIS
- Questions owned by this artifact: Q13-15
- Explicit out-of-scope tracks: stage0-01-decision-surface-v0.1.md, stage0-03-scheduler-v0.1.md, stage0-04-gex-v0.1.md, stage0-05-governance-debt-v0.1.md

## Memory provenance (mandatory -- per docs/DECISIONS.md 2026-07-19: a leg that cannot produce this is not a fresh-context leg)

- Memory surface loaded, enumerated: `/home/dustin/.codex/memories/memory_summary.md` was supplied at session start; `/home/dustin/.codex/memories/MEMORY.md` was queried. No rollout summary or skill file was opened.
- Checked against this dispatch's excluded-content list: N/A for a producing/recon leg -- no snapshot-exclusion set was prepared for this dispatch (that mechanism applies only to the separate verification session isolating itself from producer conclusions). The "prior findings visible" line above is this artifact's applicable substitute disclosure.
- Persisted anything back to memory this run: NO
- Session id: Could not determine it from visible CLI banner/session metadata.

## MCP / tool-call audit

- none.

## Q13 — Minimal cohort evaluation schema

- **Claim.** The current evaluator selects only `ALLOW_TRADE` decisions; it does not represent qualification watchlist or excluded cohorts.

  - **Path/symbol:** `cuttingboard/evaluation.py::extract_allow_trade_candidates`, `::run_post_trade_evaluation`.
  - **Bounded source:** lines 45-71 load a prior audit record, select candidates, and return `[]` when none exist; lines 114-137 select only `raw["decision_status"] == "ALLOW_TRADE"`; lines 167-176 persist the resulting evaluation record.
  - **Classification:** STATIC@771f730839b00b0537327f9696210275f36cd790; RUNTIME@771f730839b00b0537327f9696210275f36cd790 pure trace with one `ALLOW_TRADE` and one `BLOCK_TRADE` returned only the allow candidate.
  - **Consumer/path reachability:** `cuttingboard/runtime/__init__.py:1124-1147` writes the audit record, then invokes `run_post_trade_evaluation`; the evaluator reads `audit.jsonl` and appends `evaluation.jsonl`.
  - **Current unavailable/failure behavior:** `near_a_plus`, `watchlist`, and `excluded_symbols` are not inputs to the evaluator; a prior run with no allow decision produces no evaluation record.
  - **Falsifier:** a reachable current evaluator path that passes qualification watchlist or excluded entries to the selector, or a selector condition admitting a non-`ALLOW_TRADE` cohort.
  - **PRD consequence:** HYPOTHESIS — use a reference-only evaluation manifest keyed by existing `decision_run_at_utc`, explicit cohort source, and symbol, with an evaluation payload only where an evaluation definition exists. Do not copy audit reasons, gates, geometry, traces, or full audit context.

- **Claim.** A bare `watchlist` cohort is ambiguous at this SHA.

  - **Path/symbol:** `cuttingboard/qualification.py::QualificationSummary`; `cuttingboard/watch.py::WatchSummary`; `cuttingboard/audit.py::_build_record`.
  - **Bounded source:** `QualificationSummary.watchlist` and `.excluded` are defined at lines 124-142; `_build_record` writes that qualification watchlist as `near_a_plus` at lines 154-166, while separately writing `WatchSummary.watchlist` as `watchlist` at lines 190-197 and both keys at lines 230-234.
  - **Classification:** STATIC@771f730839b00b0537327f9696210275f36cd790.
  - **Consumer/path reachability:** the audit record is the evaluator’s prior-run source via `evaluation.py:74-111`; today its candidate selector reaches only `trade_decisions`.
  - **Current unavailable/failure behavior:** no persisted evaluation field identifies which of the two source meanings a future bare `watchlist` label denotes.
  - **Falsifier:** a single authoritative current mapping that merges those collections or declares one canonical evaluation cohort.
  - **PRD consequence:** HYPOTHESIS — the minimal manifest must distinguish `qualification_watchlist` from the intraday `WatchSummary.watchlist`; it must not retrospectively assign outcomes to either watchlist or excluded entries in this recon.

## Q14 — Remaining `stay_flat_reason` persistence change

- **Claim.** The final `system_state.stay_flat_reason` already reaches persisted contract/payload artifacts, but the append-only audit record used by evaluation omits it. The exact remaining audit/evaluation-path change is to persist the final contract field as a distinct audit field.

  - **Path/symbol:** `cuttingboard/contract.py::_build_system_state`; `cuttingboard/runtime/__init__.py::_build_and_finalize_contract`; `cuttingboard/audit.py::write_audit_record` and `::_build_record`.
  - **Bounded source:** `contract.py:226-263` derives `stay_flat_reason` from halt, qualification short-circuit, or `STAY_FLAT`; `runtime/__init__.py:799,806-808` sets the alias before the Sunday `PREMARKET_CONTEXT` override; `runtime/__init__.py:1124-1142` passes only `validation_summary.halt_reason` to audit; `audit.py:35-83,199-241` accepts and stores `halt_reason` but has no `stay_flat_reason` field. By contrast, `runtime/__init__.py:248-275,1842-1844` persists the contract to `logs/latest_contract.json`, and `delivery/payload.py:98-101` carries the field into payload detail.
  - **Classification:** STATIC@771f730839b00b0537327f9696210275f36cd790; RUNTIME@771f730839b00b0537327f9696210275f36cd790 pure `_build_record` trace returned an audit dict without `stay_flat_reason`.
  - **Consumer/path reachability:** final contract construction precedes the audit call; the audit JSONL is then read by `evaluation.py::load_most_recent_prior_run` at lines 74-111.
  - **Current unavailable/failure behavior:** audit history can retain a validation halt reason but cannot retain the final non-halt reason, such as qualification short-circuit, `STAY_FLAT posture`, or the Sunday override.
  - **Falsifier:** a current audit record schema containing `stay_flat_reason`, or a runtime call that passes the final contract field into `write_audit_record`.
  - **PRD consequence:** HYPOTHESIS — thread `contract["system_state"]["stay_flat_reason"]` after finalization into the append-only audit record as its own field; do not substitute `halt_reason` or the pre-Sunday `reason` alias. No additional contract/payload persistence change is indicated by this evidence.

## Q15 — Session-clustered aggregation and minimum-sample disclosure

- **Claim.** Current aggregation is per-symbol and per-evaluation-record, not session-clustered; its minimum sample is five individual records.

  - **Path/symbol:** `cuttingboard/evaluation.py::build_evaluation_records`; `cuttingboard/performance_engine.py::_aggregate`.
  - **Bounded source:** evaluation records retain `decision_run_at_utc` at `evaluation.py:167-176`; `_aggregate` groups only on `record["symbol"]` at `performance_engine.py:85-105`; `_MIN_SAMPLE = 5` is at line 23 and lines 111-136 suppress metrics below that record count.
  - **Classification:** STATIC@771f730839b00b0537327f9696210275f36cd790; RUNTIME@771f730839b00b0537327f9696210275f36cd790 pure trace of five records sharing one `decision_run_at_utc` produced `total_trades: 5` and `insufficient_data: False`.
  - **Consumer/path reachability:** `runtime/__init__.py:1143-1147` invokes evaluation, then performance aggregation; its summary is written by `performance_engine.py:26-37`.
  - **Current unavailable/failure behavior:** multiple candidate rows from one run count as independent observations; no `session_id`, `session_cluster`, or clustering logic exists in `evaluation.py`, `performance_engine.py`, or `audit.py`.
  - **Falsifier:** a current grouping key beyond symbol in `_aggregate`, or a persisted session identifier consumed by the aggregation path.
  - **PRD consequence:** HYPOTHESIS — no final session reducer or numerical threshold can be specified from this snapshot. If an authority defines a session identity, the summary should disclose both session-cluster count and evaluation-record count, the cohort basis, the applicable minimum-sample policy, and `insufficient_data`. The current value of five is reported only as existing record-level behavior; it is not proposed, changed, or tuned here.

## NO CLAIM

- stage0-01-decision-surface-v0.1.md — I make no claim about this track.
- stage0-03-scheduler-v0.1.md — I make no claim about this track.
- stage0-04-gex-v0.1.md — I make no claim about this track.
- stage0-05-governance-debt-v0.1.md — I make no claim about this track.


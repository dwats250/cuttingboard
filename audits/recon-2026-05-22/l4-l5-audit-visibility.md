# Recon - L4 to L5 Audit Visibility

## 1. Document identification

Examined files:

- `cuttingboard/runtime.py`
  - Candidate-generation to qualification windows: `runtime.py:482-508`, `runtime.py:511-538`, `runtime.py:803-825`.
  - Audit write call: `runtime.py:1023-1041`.
  - Run summary count handling: `runtime.py:1127-1202`.
  - Gap-down helper: `runtime.py:1205-1248`.
  - Downside permission adapter: `runtime.py:1352-1363`.
  - Notify-mode artifact path: `runtime.py:437-645`.
- `cuttingboard/audit.py`
  - `write_audit_record(...)`: `audit.py:29-77`.
  - `_build_record(...)`: `audit.py:84-235`.
- `cuttingboard/intraday_state_engine.py`
  - `downside_short_permission(...)`: `intraday_state_engine.py:242-260`.
  - `compute_intraday_state(...)` permission derivation: `intraday_state_engine.py:430-476`.
- `docs/architecture.md`
  - Layer flow and L7 qualification contract: `architecture.md:102-149`.
  - data-contract table: `architecture.md:216-223`.
  - candidate-generation trust rules: `architecture.md:234-238`.
- `docs/prd_history/PRD-151.md`
  - as-built scope and runtime behavior: `PRD-151.md:34-123`.
  - invalidation conditions: `PRD-151.md:218-254`.
- `logs/audit.jsonl`
  - recent pipeline run records found at lines 638-640; most recent sampled run record is line 640, `run_at_utc=2026-05-13T11:25:25.137997+00:00`.
  - last physical lines 684-686 are notification-event records, not pipeline run records.
- Additional relevant files:
  - `cuttingboard/options.py:112-157` for `generate_candidates(...)`.
  - `cuttingboard/qualification.py:74-88`, `qualification.py:114-141`, `qualification.py:175-199`, `qualification.py:216-279`, `qualification.py:595-605` for `TradeCandidate`, `QualificationSummary`, `qualify_all(...)`, and continuation behavior.
  - `cuttingboard/sector_router.py:21-50` because `runtime.py` passes `suppressed_candidates` from `apply_sector_router(...)` into the audit writer.

All requested input files were located.

## 2. L4 output and L5 input boundary

In current code, the practical L4-to-L5 candidate boundary is `generate_candidates(...) -> qualify_all(...)`, even though `docs/architecture.md` labels derived metrics as L4, regime as L5, and qualification as L7 (`architecture.md:102-149`). `generate_candidates(structure_results, derived_metrics, valid_quotes, regime) -> dict[str, TradeCandidate]` returns one `TradeCandidate` per generated non-CHOP symbol, keyed by symbol (`options.py:112-157`). Each `TradeCandidate` carries `symbol`, `direction`, `entry_price`, `stop_price`, `target_price`, `spread_width`, and optional earnings state (`qualification.py:74-88`). `qualify_all(regime, structure_results, candidates, derived_metrics, ohlcv, now_et, flow_snapshot) -> QualificationSummary` consumes that candidate dict or `None` and emits qualified, watchlist, and excluded outputs (`qualification.py:114-141`, `qualification.py:267-279`).

## 3. Inventory of L4->L5 filters and transformations

### `_apply_intraday_short_permission`

- **Location:** `cuttingboard/runtime.py:489`, `runtime.py:518`, `runtime.py:805`; helper body at `runtime.py:1205-1248`.
- **Trigger condition:** Runs after `generate_candidates(...)` and before `qualify_all(...)` in three production paths:
  - notify qualify-only modes at `runtime.py:482-508`;
  - hourly notify modes when posture is not `STAY_FLAT` at `runtime.py:511-538`;
  - main daily/live path at `runtime.py:803-825`, except fixture mode (`if mode != MODE_FIXTURE` at `runtime.py:804`).
- **Effect on candidates:** Copies the candidate dict, inspects only candidates whose `candidate.direction == "SHORT"`, and pops the symbol from the filtered dict when downside permission is false (`runtime.py:1209-1245`). Long candidates are not affected (`runtime.py:1212-1214`). Missing intraday state is fail-open: missing bars, empty bars, no converted bars, or state-computation exceptions preserve the candidate (`runtime.py:1216-1236`).
- **Reason recorded:** The helper returns a per-symbol `context` dict with `intraday_state_available`, and when available, `downside_permission` plus `intraday_state` (`runtime.py:1238-1243`). It also writes a logger line when a symbol is suppressed (`runtime.py:1244-1246`). The daily/live call site preserves that context in `intraday_state_context` (`runtime.py:805`, `runtime.py:1040`), but the notify-mode call sites discard it with `_` (`runtime.py:489`, `runtime.py:518`).

### `candidates or None` at `qualify_all(...)`

- **Location:** `cuttingboard/runtime.py:498`, `runtime.py:527`, `runtime.py:815`.
- **Trigger condition:** Always present at the call boundary; it changes behavior only when the post-filter candidate dict is empty.
- **Effect on candidates:** Converts an empty dict into `None` before L5/qualification receives it. In `qualify_all`, `candidates is None` means the primary candidate-dependent gate block does not run (`qualification.py:182-199`). CHOP exclusions still run (`qualification.py:175-180`). In EXPANSION regime, continuation logic still iterates `structure_results` rather than the candidate dict (`qualification.py:216-228`), so an empty candidate dict does not stop continuation checks.
- **Reason recorded:** No direct reason is emitted for the conversion. If candidate generation was empty because `direction_for_regime(regime)` returned `None`, the reason is only a logger message from `generate_candidates(...)` (`options.py:127-135`). The audit record has no raw candidate-list field and no explicit "empty candidates converted to None" field.

### `ohlcv` construction keyed by filtered candidates

- **Location:** `cuttingboard/runtime.py:490-494`, `runtime.py:519-523`, `runtime.py:807-811`.
- **Trigger condition:** Runs after `_apply_intraday_short_permission` and before `qualify_all(...)`.
- **Effect on candidates:** Does not mutate the candidate dict. It builds an `ohlcv` side input only for symbols still present in `candidates`. Because continuation qualification later uses `df = (ohlcv or {}).get(symbol)` (`qualification.py:226-228`) and rejects `df is None` as `DATA_INCOMPLETE` (`qualification.py:595-605`), this can affect continuation evaluation inputs, but it is not itself a candidate-list filter.
- **Reason recorded:** No candidate-removal reason, because no candidate is removed by this operation.

### `apply_sector_router(...)`

- **Location:** `cuttingboard/runtime.py:504-508`, `runtime.py:533-537`, `runtime.py:821-825`; implementation at `sector_router.py:45-50`.
- **Trigger condition:** Runs after `qualify_all(...)`, not between candidate generation and L5 input.
- **Effect on candidates:** Current implementation returns the `QualificationSummary` unchanged and an empty suppressed-candidate list (`sector_router.py:45-50`).
- **Reason recorded:** Not an L4->L5 operation. It is listed here only because its `suppressed_candidates` output is written to the audit record and could otherwise be confused with gap-down suppression.

No additional production operation was found that mutates, filters, or suppresses the generated candidate dict between `generate_candidates(...)` and `qualify_all(...)`.

## 4. Audit record schema

`write_audit_record(...)` writes the pipeline run record to `logs/audit.jsonl` by calling `_build_record(...)` and `_append_record(...)` (`audit.py:29-77`). The writer accepts `suppressed_candidates` and `intraday_state_context` parameters (`audit.py:45-46`, `audit.py:100-101`). The emitted record fields are defined at `audit.py:193-233`:

- `run_at_utc`, `date`, `outcome`: run identity and top-level result (`audit.py:193-197`).
- `regime`, `posture`, `confidence`, `net_score`, `vix_level`, `router_mode`, `energy_score`, `index_score`: regime and router metadata (`audit.py:198-206`).
- `symbols_validated`, `symbols_total`, `symbols_failed`: validation counts (`audit.py:208-211`).
- `symbols_qualified`, `symbols_near_a_plus`, `symbols_watchlist`, `symbols_excluded`, `regime_short_circuited`, `regime_failure_reason`: post-qualification counts and regime short-circuit metadata (`audit.py:213-219`).
- `qualified_trades`: list built from `qual.qualified_trades`, with symbol, direction, setup fields, sizing fields, optional trade-decision fields, and optional intraday context only for surviving qualified symbols (`audit.py:117-146`, `audit.py:222`).
- `trade_decisions`: list built from `trade_decisions`, with execution decision fields and decision trace (`audit.py:162-182`, `audit.py:223`).
- `watchlist`: broader watch-summary entries from `watch_summary.watchlist`, not the qualification watchlist (`audit.py:184-191`, `audit.py:224`).
- `near_a_plus`: list built from `qual.watchlist`, with optional intraday context only for surviving watchlist symbols (`audit.py:148-158`, `audit.py:225`).
- `excluded_symbols`: `dict(qual.excluded)`, so it captures only qualification exclusions (`audit.py:160`, `audit.py:226`).
- `suppressed_candidates`: `list(suppressed_candidates or [])`, populated from the sector-router output passed by `runtime.py:1036`, not from `_apply_intraday_short_permission` (`audit.py:227`, `runtime.py:821-825`, `runtime.py:1036`).
- `halt_reason`, `alert_sent`, `report_path`: run metadata (`audit.py:229-232`).

The sampled latest pipeline run record at `logs/audit.jsonl:640` contains the writer fields above, including `qualified_trades`, `trade_decisions`, `watchlist`, `near_a_plus`, `excluded_symbols`, and `suppressed_candidates`. It does not contain a raw pre-L5 candidate list, raw L4 candidate count, gap-down suppression count, gap-down suppressed symbol list, or a top-level `intraday_state_context` field. Intraday state fields can appear only inside `qualified_trades` or `near_a_plus` entries for candidates that survived into those lists (`audit.py:141-145`, `audit.py:153-157`).

## 5. Visibility classification

### `_apply_intraday_short_permission`: INVISIBLE for removed candidates

The audit record does not capture the helper's input candidate dict, output candidate dict, removed symbol identities, or removal reasons. The `context` returned by `_apply_intraday_short_permission` is not written as a top-level audit field; `audit.py` only copies matching context onto `qualified_trades` and `near_a_plus` entries (`audit.py:141-145`, `audit.py:153-157`). A suppressed candidate is absent from both lists because it was popped before `qualify_all(...)`, so its context has no audit destination. The `suppressed_candidates` audit field is insufficient because it is populated from `apply_sector_router(...)` after qualification (`runtime.py:821-825`, `runtime.py:1036`), while current `apply_sector_router(...)` returns `[]` (`sector_router.py:45-50`).

### `candidates or None`: INVISIBLE when it changes the call shape

The audit record does not record whether `qualify_all(...)` received an empty dict or `None`; it only records post-qualification counts and lists (`audit.py:213-227`). A reader can sometimes infer a no-candidate run from all-empty post-qualification fields, but cannot distinguish "no generated candidates", "all candidates removed before qualification", "qualification short-circuited", and "candidate dict converted to None" without external runtime context. There is no audit field for raw candidate count before this conversion or for post-filter candidate count after `_apply_intraday_short_permission`.

### `ohlcv` construction keyed by filtered candidates: NOT A CANDIDATE-FILTER VISIBILITY ITEM

This operation does not remove or mutate candidates. Its side-effect is that only surviving candidate symbols get OHLCV frames before `qualify_all(...)` (`runtime.py:807-811`). For this recon's candidate-suppression question, it is not classified as visible/partial/invisible because no candidate-list action occurs.

### `apply_sector_router(...)`: OUTSIDE L4->L5

This runs after `qualify_all(...)`, so it is outside the L4->L5 boundary. Its output is visible in the audit schema through `suppressed_candidates` (`audit.py:227`), but current implementation returns an empty list (`sector_router.py:45-50`).

## 6. Verdict - scope of the visibility gap

**BOUNDED-TO-GAP-DOWN.**

`_apply_intraday_short_permission` is the only production operation found that removes generated candidates before `qualify_all(...)`. Its removals are invisible in `logs/audit.jsonl`: no pre-filter candidate list, post-filter candidate list, removed symbol list, or gap-down reason field is written. The only other boundary transformation found is `candidates or None`, which can change the L5 call shape for an already-empty candidate dict but does not remove a candidate itself.

## 7. Implications for Phase 2 scoping

Phase 2's Moomoo statement join against `logs/audit.jsonl` would need to acknowledge gap-down pre-qualification suppression as a known blind spot. A suppressed SHORT candidate can be absent from `qualified_trades`, `trade_decisions`, `near_a_plus`, `excluded_symbols`, and `suppressed_candidates`, so the audit join cannot count it as a decision surface from the current record alone. This recon found no wider pre-L5 suppression channel that Phase 2 also needs to name.

## 8. Honest limits

- I did not read all of `cuttingboard/runtime.py`. I read the windows around all `generate_candidates(...)`, `_apply_intraday_short_permission(...)`, and `qualify_all(...)` call sites reported by `rg`, plus the audit write path and helper definitions listed in section 1. The rest of `runtime.py` remains unread for this recon.
- The audit sample is a single most-recent pipeline run record at `logs/audit.jsonl:640`, with two preceding run records at lines 638-639. It confirms the emitted field set for that mode, but a single run may not surface optional nested fields such as `decision_trace` or intraday fields inside surviving `qualified_trades` / `near_a_plus` entries.
- The most recent physical lines in `logs/audit.jsonl` are notification audit events, not pipeline run records. I treated records with `outcome` and `run_at_utc` as pipeline run records, matching `_load_run_history(...)` in `runtime.py:1690-1700`.
- The architecture document's layer numbering does not match the brief's L4/L5 terminology exactly: `docs/architecture.md` labels derived metrics as L4, regime as L5, and qualification as L7 (`architecture.md:102-149`). I interpreted the brief's "L4 output and L5 input" as the code boundary from `generate_candidates(...)` to `qualify_all(...)`, because that is the boundary described by the requested files and PRD-151.
- The EXPANSION continuation path in `qualify_all(...)` iterates `structure_results` rather than the candidate dict (`qualification.py:216-228`). A gap-down-suppressed symbol can therefore still be considered by continuation logic, but because `ohlcv` is built only for the filtered candidate dict, a removed symbol has no `df` and continuation rejects it as `DATA_INCOMPLETE` (`qualification.py:595-605`). Continuation rejection counts may appear in `continuation_audit` in run summaries, but `logs/audit.jsonl` does not write `continuation_audit`.
- A visible fix is out of scope. The recon stops at classification of the current visibility gap and does not propose a PRD, schema change, or runtime change.

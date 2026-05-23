# Audit Doctrine — cuttingboard

This document defines what `logs/audit.jsonl` records and what it does
not. The two binding rules below are load-bearing — adding a new
pipeline-audit write site, or changing the one-record-per-invocation
shape, requires a PRD that cites this doctrine and identifies a named
consumer of the change.

This is a peer document to `docs/sidecar_doctrine.md`. The sidecar
doctrine governs how observation artifacts are added; this doctrine
governs how the canonical run log is written and read.

---

## What logs/audit.jsonl is

`logs/audit.jsonl` is an append-only JSONL file written by
`cuttingboard/audit.py`. It holds two distinct record families that
share the file by historical accident, not by design:

- **Pipeline records.** Written by `write_audit_record(...)`. One
  record per `cuttingboard/runtime.py:_run_pipeline` invocation.
  Carries `run_at_utc`, `outcome`, `regime`, `posture`,
  `qualified_trades`, `trade_decisions`, `near_a_plus`, `watchlist`,
  `excluded_symbols`, `suppressed_candidates`, `intraday_state_context`
  when present, `halt_reason`, `alert_sent`, `report_path`, and the
  router / validation / qualification summary fields built by
  `audit._build_record`. These are the records every "audit log
  consumer" in the codebase reads.

- **Notification-event records.** Written by
  `write_notification_audit(...)` on every Telegram send attempt
  (success, failure, retry, suppression, skip). Carries `event ==
  "notification"` plus transport / status / state-key fields. These
  records exist for delivery debugging; they are not part of the
  pipeline state log.

Both families are appended in chronological order of writer call.
There is no schema versioning, no record-family tag at file level, and
no separation by directory or file name — the two streams interleave.

---

## Rule 1 — Pipeline writes only from `_run_pipeline`

Pipeline-shaped audit records (those carrying `run_at_utc` +
`outcome` + the full state at decision time) may be written **only**
from `cuttingboard/runtime.py:_run_pipeline`. The one canonical write
site is at `runtime.py:1004` via `write_audit_record(...)`.

`_execute_notify_run` (the path used by `hourly`, `post_orb`,
`orb_trajectory`, `midmorning`, `power_hour`, and `market_close`
notify modes) intentionally **does not** write pipeline records. This
is design, not omission. Notify-mode firings are lightweight alert
paths; they are observed through their notification-event records and
through their own ad-hoc artifacts (e.g., `logs/latest_hourly_run.json`),
not through `logs/audit.jsonl`'s pipeline stream.

Adding a new pipeline-audit write site requires a PRD whose
`REQUIREMENTS` identify a named consumer of the new records. "Future
analysis might want this" is not a named consumer; "module X reads
field Y under condition Z" is.

---

## Rule 2 — One record per invocation; notifications are a separate stream

Each `_run_pipeline` invocation appends exactly **one** pipeline
record. Not one per symbol, not one per decision event, not one per
mode, not one per evaluated candidate. A pipeline record is a
snapshot of the full run state — all qualified trades, all trade
decisions, all watchlist entries, all exclusions — flattened into a
single JSON object.

Notification-event records (`event == "notification"`) share the file
but are an independent record family with its own shape and its own
producers. **Any consumer reading `logs/audit.jsonl` as a pipeline log
MUST filter out records where `event == "notification"`.** The
canonical filter is `record.get("event") != "notification"`; consumers
that look for affirmative pipeline-record fields (e.g.,
`"run_at_utc" in r and "outcome" in r`) are also acceptable and
slightly more defensive.

---

## Consumer guidance

Three consumers in the codebase read `logs/audit.jsonl` as a pipeline
log. Each has a structural constraint that follows from the two rules
above.

| Consumer | What it does | What to expect |
|---|---|---|
| `cuttingboard/moomoo_join.py:load_audit_records` | Loads pipeline records for trade-to-audit join (PRD-153). | ~1 record per trading day. Intraday trades will frequently have no same-day audit record. This is the doctrine working as designed. |
| `cuttingboard/evaluation.py:load_most_recent_prior_run` | Loads the most recent same-day prior pipeline run for post-trade evaluation. | On a typical trading day the only same-day prior run is the premarket `live`-mode run; "most recent prior" effectively means "the premarket run." |
| `cuttingboard/runtime.py:_load_run_history` | Returns up to N most-recent pipeline records for postmarket-report context. | Spans across trading days; ~1 record per trading day. Notification-event records are filtered out. |

A consumer that needs denser coverage than ~1 record per trading day
must either change the doctrine (a PRD that justifies a new
pipeline-audit write site per Rule 1) or read a different artifact
entirely.

---

## What this doctrine does NOT bind

The doctrine declares as little as possible. The following are
explicitly **not** claimed:

- **Not a schema lock.** Field additions, removals, or renames in the
  pipeline-record shape do not require a CONTRACT-class PRD under
  this doctrine. Schema discipline is governed by
  `docs/PRD_PROCESS.md § CLASS Matrix` (CONTRACT row) on its own
  merits, not by audit-log doctrine.
- **Not a density guarantee.** Sparseness is permitted, expected, and
  not a defect. A trading day with zero pipeline records (CI
  failure, missed cron, holiday) is consistent with the doctrine.
- **Not a position on intraday coverage.** Whether
  `_execute_notify_run` modes should ever start writing pipeline
  records is an open question — this doctrine neither permits nor
  forbids it. A future PRD may propose intraday coverage; that PRD
  must justify the addition under Rule 1.
- **Not a write-ordering guarantee.** Pipeline records and
  notification-event records may interleave in any order consistent
  with their writer calls. Consumers must not assume relative
  ordering between the two families.

---

## Cross-references

- `docs/sidecar_doctrine.md` — peer doctrine governing observation
  artifacts written downstream of finalize.
- `docs/PRD_PROCESS.md § CLASS Matrix` — defines CONTRACT and
  GOVERNANCE classes referenced above.
- `CLAUDE.md § operational rules` — the project-wide rules under
  which this doctrine sits.
- `docs/DECISIONS.md` (2026-05-23 entry) — the recon trail that
  surfaced the need for this doctrine.

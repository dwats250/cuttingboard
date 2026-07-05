# Session resume — 2026-07-05 (qualification tuning audit → PRD-240 shipped)

Session scratch per the PRD-230 sediment rule: delete once the next session
confirms nothing here was lost. Durable content already lives in DECISIONS
2026-07-05 (×2 entries), PRD-240/241, and PROJECT_STATE.

## 1. LANDED THIS SESSION (on `main`)

- `fd4250d` (PR #110) — PRD-240 + PRD-241 filed as PROPOSED from the
  qualification tuning audit; DECISIONS entry dispositions all ten audit
  findings; registry/index rows added.
- `07415a8` (PR #111) — PRD-240 implemented (R1–R6) + same-PR closeout
  (COMPLETE @ #111). EXPANSION_RR_RATIO 1.5→2.0; Gate-6 stop floor
  0.5→1.0×ATR14 (`STOP_ATR_FLOOR_K`); shared `MIN_STOP_PCT`;
  `CONTINUATION_REWARD_ATR_MULTIPLE=3.0`; `_min_rr_for_regime()` shared by
  Gate 7 + `_resolve_entry_mode`; continuation close-location ≥ 0.75 filter;
  R6 asymmetry comment. +4 mutation-verified red tests; suite 2888+1 xfailed.
  HIGH-RISK gate: fresh-context Claude review ACCEPT
  (`docs/prd_history/PRD-240.review.claude.md` @ `da214f7`); Codex leg =
  Dustin's manual merge recorded the waiver (no codex CLI in container).
  Post-merge CI on `main` @ `07415a8`: green (verified).

## 2. LIVE BRANCHES

- `claude/qualification-system-audit-sp0wat` @ `098f572` — the read-only
  audit findings artifact (`audits/qualification-tuning-2026-07-05/findings.md`).
  NEXT GATE: Dustin's delete-or-merge decision. Disposition is fully recorded
  in DECISIONS 2026-07-05, so deletion is legitimate under the PRD-230
  sediment rule; nothing on the branch is load-bearing anymore.
- `claude/qualification-audit-prd-6sefn9` (remote) — carries only history
  already squash-merged via #110/#111 plus this resume note's PR. NEXT GATE:
  none; delete after this note's PR merges.
- All other `origin/claude/*` branches predate this session — unchanged here;
  tracked by PROJECT_STATE and earlier resume notes (recon-2026-06-24 latest).

## 3. DURABLE FINDINGS NOT IN ANY PRD

- **Continuation band arithmetic (generalized lesson):** the continuation R:R
  gate is a stop-width ceiling — risk ≤ CONTINUATION_REWARD_ATR_MULTIPLE /
  EXPANSION_RR_RATIO × ATR14 (now 1.5×). Retuning EITHER constant, or adding
  any continuation stop floor, moves/narrows that band multiplicatively.
  Check the band before any future retune (in-code comment at the R6 block
  carries the math; this is the cross-PRD warning).
- **Stale-`__pycache__` after in-place mutation checks:** a sed revert+restore
  that lands same-size/same-second can leave a stale bytecode cache and produce
  a phantom test result. Clear caches / use fresh caches before trusting a
  post-restore run. (Bit the PRD-240 reviewer; disclosed in the review
  artifact; → DECISIONS 2026-07-05.)
- **Token grep sweeps miss fixture-geometry breakage:** PRD-240's FILES sweep
  grepped every constant token, yet `tests/test_account_equity_sizing.py`
  broke anyway — its fixture's stop/ATR geometry failed the new Gate-6 floor
  before reaching sizing asserts. For threshold-tightening PRDs, run the full
  suite at FILES-scoping time. (→ DECISIONS 2026-07-05.)
- **Environment quirks (this remote container):** no `codex` CLI (Codex gate =
  Dustin-merge waiver, Fable-window pattern); the github MCP server flaps and
  intermittently demands re-auth — `send_later` re-arms failed twice with
  "permission stream closed" (retry next turn works), and when MCP is down,
  git ancestry checks + WebFetch of public GitHub pages are the fallback;
  `actions_list` returns oversized results — parse the saved tool-results file
  with python/jq; test runner is `.venv/bin/pytest` (no system pytest,
  `pytest-timeout` not installed).
- **SSRN citations in the audit are search-snippet confidence only** (SSRN
  bot-blocks direct fetches) — verify full text before leaning on them again.

## 4. QUEUED / FUTURE SCOPE

- **PRD-241 (PROPOSED, MICRO, doc truth) — now unblocked:** PRD-240 values are
  final; document Gate 7's three R:R tiers + CONTINUATION + PULLBACK_IMBALANCE
  entry modes in `docs/trade_qualification.md`, fix `system_logic_map.md`
  "9–11 gates" line. File: `docs/prd_history/PRD-241.md`.
- **Deferred review recommendations (PROJECT_STATE):** (1)
  `runtime/__init__.py` third min-RR tier duplicate feeding `min_rr_applied` —
  needs its own PRD (runtime refactor rule); (2) name the 0.75 close-location
  literal — next polish batch.
- **WATCHLIST `gates_skipped` render gap** (PRD-235 review RECOMMENDED-1) —
  still consciously deferred; separate CONSUMER PRD if picked up.
- **Min-votes confidence guard** (audit §2: few macro votes cast → thin ±1
  margin looks confident) — flagged-not-actioned, degraded-data edge case.
- Master-plan post-window queue (D/E/F, K/L/M) — unchanged; owner PROJECT_STATE.

## 5. DECISIONS.md CANDIDATES

Two §3 findings are "from now on" rules, added to DECISIONS 2026-07-05
(same commit as this note): full-suite-at-scoping for threshold-tightening
PRDs, and the stale-`__pycache__` mutation-check rule. The rest are dated
observations — note-only.

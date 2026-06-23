# Session resume note — 2026-06-22 (PRD-204 arc)

Stand-up doc for a fresh session. Contract context that is not re-derivable from
the diff. Scannable, not narrative.

## Landed this session (on `main`)
- **PRD-204 — COMPLETE (`9c1fb37`):** non-destructive `regime_history.aggregate()`.
  Preserve-prior + always-present `spy_close_change_pct_stale` marker instead of
  nulling a populated `spy_close_change_pct` when the SPY parquet is absent. Closed
  PRD-198 invariant #1 (docstring/code drift). Amendments: 1 = restore
  `logs/regime_history.jsonl` before aggregate in both publish workflows
  (env-parity-guarded); 2 = warn loudly on a wholly-absent series; 3 = warn on a
  partial/truncated mid-series gap. **Stale-tail P2 DECLINED** — not distinguishable
  from legitimate pending inside `aggregate()` (no calendar/clock), and already
  covered by the PRD-190 `OHLCV_STALE_HOURS` TTL self-heal. Home if it resurfaces:
  PRD-193, not a heuristic in aggregate().
- **PRD-203 — COMPLETE (`35e0641`):** closed out alongside (combined closeout PR #53).
  Test baseline now canonical/CI-sourced: `2830 passing, 1 xfailed @ 9c1fb37`.
- Index: `latest_complete=204`, `next_prd=205`.

## Live branches — exact next gate for each
- **`claude/codex-review-router-prd205`** — PRD-205 Stage-0 scaffold, reviewed
  (R3 broadened; CLAUDE.md:55 is do-not-touch; Path-B noted in OUT OF SCOPE).
  **NEXT: host implementation, THEN PR.** Host-side wrapper — builds on Dustin's
  machine (needs `~/.codex` creds + egress).
- **`claude/narrow-regime-glob-prd206`** — PRD-206 PROPOSED, **GOVERNANCE /
  manual-merge** (excluded from auto-merge). Narrows `docs/AGENT_WORKFLOW.md:36`
  `*regime*.py` → `regime.py`. **NEXT: protected-set-diff review** — enumerate
  every file the OLD glob matched vs the NEW glob; ACCEPT only if the ONLY dropped
  file is the test-verified PRD-175 read-only sidecar `regime_history.py`. THEN
  host impl + manual-merge PR.

## Durable findings NOT captured in any PRD (do not re-derive)
- **CI Codex (PRD-197 workflow) = a FIXED consistency pass.** It cannot carry a
  custom review focus. An adversarial LOGIC review requires host `codex exec` with
  a real prompt — only.
- **Codex invocation is environment-dependent.** `codex exec` is host-only (needs
  `~/.codex` creds + network egress); containers route via the PRD-197 GitHub
  Actions workflow. Do NOT prompt for local `codex exec` from a container — the
  egress wall is by design. (Recorded canonically in `docs/DECISIONS.md`,
  2026-06-23.)
- **OPEN HIGH DEBT — PRD-198 invariant #2 (`extract_model` provenance).** Metadata
  reports `gpt-5-codex` while the prose self-report varies. Every Codex APPROVE
  rests on this. Needs a human spot-check: does `extract_model` read the SERVED
  model or a request echo?

## Queued / Path-B
- **Path-B** (seeded in PRD-205 OUT OF SCOPE): a flexible Codex wrapper =
  arbitrary target AND arbitrary prompt, not target alone.
- **Dashboard audit remaining leads** (`audits/recon-2026-06-22/`, lower priority):
  PRD-191 direction-blind captions; absolute timestamp; LIVE STATE staleness flag
  (Lead 5 — reads the new `spy_close_change_pct_stale` marker); mobile overflow;
  collapse the Sunday pre-market banner into the macro card.

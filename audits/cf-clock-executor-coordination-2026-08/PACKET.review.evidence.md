# CF Clock/Executor Coordination packet — INDEPENDENT ADVERSARIAL REVIEW (EVIDENCE, NON-GATING)

## Provenance and status — READ FIRST

**THIS IS NOT THE GOV-2 §2/§7 INDEPENDENT CODEX PACKET-REVIEW GATE.** It does not
satisfy it and must not be recorded as satisfying it.

- **Classification:** author-side EVIDENCE (GOV-2 §3 — "may contribute evidence
  but cannot satisfy the independent-review requirement").
- **Why non-gating:** GOV-2 §2/§7 require an independent **Codex** review for the
  MATERIAL packet cycle; the Codex instrument is not present in this cloud
  session. GOV-2 §3 additionally bars the authoring agent AND any subagent it
  spawns from satisfying independent review. The reviewer here is a fresh-context
  subagent spawned by the authoring session — genuinely free of authoring memory
  (useful for surfacing defects), but by §3 it is evidence, not the gate.
- **Owner decision authorizing this artifact:** Dustin, this session — "fresh
  reviewer, recorded as non-gating evidence"; the formal GOV-2 §2 Codex gate
  stays OPEN (see the packet's §17, still PENDING).
- **Reviewed content:** packet v0.1 at exact head
  `982615442e7e3ebcfb60b440feb04436a010ae13`.
- **Reviewer:** fresh-context general-purpose subagent, no authoring context,
  read the packet + `scripts/check_run_revision.py`,
  `scripts/resolve_run_mode.py`, `.github/workflows/cuttingboard.yml`,
  `.github/workflows/hourly_alert.yml`, `tools/ci_push_artifacts.sh`,
  `docs/prd_history/PRD-298.md`, `docs/governance/GOV-2_*.md`, and the CF entry
  in `docs/DECISIONS.md`.
- **Charge:** Dustin's verbatim 10-target falsification charge (this session).

The GOV-2 §2 durable-record fields in the packet's §17 remain PENDING; nothing
in this artifact fills them.

---

## VERDICT (evidence): REQUIRED CHANGES

One load-bearing defect (timezone basis of the OPEN window vs. UTC cron clocks),
one factual mischaracterization that drove the D2 recommendation the wrong way,
and one authority-boundary gap (conflict with ratified CF-D4). No redesign; the
coordination architecture is sound and fails safe. Consolidated correction set
below; author dispositions recorded against v0.1 → v0.2.

---

## Findings (as returned) and AUTHOR DISPOSITION

### F1 / Target 2 & 4 — OPEN window is PT-anchored but the clocks are UTC — **CONFIRMED (load-bearing)**
Both GitHub Actions schedule crons and Cloudflare Worker cron triggers are
UTC-only. The existing live cron `0 13 * * 1-5` is labeled "06:00 PT / 13:00 UTC"
(`cuttingboard.yml:8`) — true in PDT, but 05:00 PST in winter. The packet's §5.2
PT window `[05:55, 06:20)` therefore EXCLUDES the real slot runs (~13:00/13:05
UTC) every winter → coordination reads `UNSATISFIED` for ~4–5 months/year →
systematic double-execution whenever CF + fallback both fire. Fails safe (no
missing board) but defeats dedup half the calendar.
**Independent re-verification (author):** `cuttingboard.yml:8` label confirmed;
Cloudflare cron triggers UTC-only confirmed (external, well-established); PST
offset arithmetic confirmed.
**DISPOSITION: ACTIONED (C1).** Re-anchor clause 5 to UTC (see D1). Delete the
false "Both … fall inside it" claim. Add a PST/winter test.

### F2 / Target 3 — D2 mischaracterizes PRD-194; steers to the wrong option — **CONFIRMED**
`hourly_alert.yml` uses concurrency group `hourly-alert` (`:27`), distinct from
`cuttingboard-pipeline` (`:35`), and already publishes to the same `publish`
branch concurrently. Publish-race safety is provided by
`tools/ci_push_artifacts.sh` delta-append + bounded push-retry (`:13–16, 59–61,
88–170`), NOT by the shared concurrency group (`cuttingboard.yml:31–33` says
exactly this). So a dedicated OPEN group does NOT introduce a new publication
race; the packet's D2 sentence ("permits concurrent artifact/git-write/publish
races") is FALSE. The only cross-slot mutable seams in `cuttingboard.yml` are
(i) the `publish` branch (delta-append-safe) and (ii) the OHLCV `actions/cache`,
whose sole writer is `prefetch` (`Save OHLCV cache` gated on `job_mode=='prefetch'`).
**Independent re-verification (author):** all four facts re-grepped and confirmed
(hourly group, concurrent publish, ci_push_artifacts delta-append/retry,
cache-save prefetch-gated).
**DISPOSITION: ACTIONED (C2).** Change D2 recommendation to a dedicated OPEN
group; correct the PRD-194 characterization; state the two benign seams.

### F3 / Target 9 & 10 — §7.5 cron replacement conflicts with ratified CF-D4 — **CONFIRMED**
`docs/DECISIONS.md:73` — "CF-D4 — APPROVED. Retain the existing GitHub cron
heartbeats in slice 1." §7.5 replaces/retimes the 06:00 live cron, modifying a
ratified owner decision. That is not inside §16's auto-ruling boundary, so the
design-direction ruling is NOT automatic for this element. Also, §7.5's framing
of the replacement as "a correctness fix, not an optimization" over-states: the
true correctness requirement is only that the existing cron must not run un-gated
(it must carry the `CB-SLOT:OPEN` token + §7.4 pre-check, else double-exec);
*retiming* it to ~06:05 is an elective design choice that produces the rollout
gap.
**Independent re-verification (author):** CF-D4 wording confirmed at
`DECISIONS.md:73`; §16 auto-ruling list contains no CF-D4 modification.
**DISPOSITION: ACTIONED (C3) + HELD FOR OWNER RULING.** Surface the CF-D4 conflict
as an explicit item Dustin must rule on (it also engages the charter's
"~5-min-delayed fallback" vs CF-D4's "retain heartbeats"; reconciling them is a
GOV-2 §10 canonical-ruling-propagation act only Dustin can make). Separate the
true correctness requirement (token + pre-check) from the elective retiming in
§7.5. The author does NOT unilaterally resolve this.

### Recommended (non-blocking) / Target 6 — rerun-conclusion-mutation edge — **CONFIRMED, minor**
The list endpoint returns the latest attempt's conclusion. If the original
published-success run is re-run and the re-run fails, its conclusion flips to
`failure`, dropping it from the success set and leaving a no-op success as the
sole matcher — so the prose invariant "∃ qualifying OPEN success ⟺ real publish"
is technically falsifiable. Safety holds (the board persisted on `publish`; a
failed re-run does not unpublish). 
**DISPOSITION: ACTIONED (C4).** Add an explicit test (T23) pinning this edge and
the safety argument, replacing T22's "unreachable" assertion.

### HOLDS (independently verified by the reviewer — no change)
- Target 1 SLOT IDENTITY: run-name feasibility; token substring-safety; source
  spoof-inertness; the manual-`slot=OPEN`-in-window override is coherent (the
  only manual participation path), not a contradiction.
- Target 5 FIRST-SUCCESS PROOF: full SATISFIED predicate; typed PROOF_ERROR
  separated from UNSATISFIED; PROOF_ERROR→execute explicit and logged.
- Target 6 no-op recursion (operational core): no queried filter drops the real
  publish while keeping the no-op; pagination/retention non-issues intra-day.
- Target 7 PUBLISH TRUTH: `check_readiness` inside Commit under `set -euo
  pipefail` before commit; Push gated on `success()` + PUBLISH_READY + main;
  publish failure → job failure → non-satisfying.
- Target 8 WORKER SECURITY: Actions-write-only sufficient; no
  contents-write/admin/secrets-read/merge/market authority; dispatch failure
  logged as dispatch failure only.
- Target 10 SCOPE: no hidden coupling to CF-D1b/CF-E2/latest_run/notification-
  reliability/PRD-293/general-scheduler.

---

## REVIEW DECISIONS (as recommended; folded into v0.2)

- **D1 — window basis:** anchor clause-5 membership in **UTC** (matching the UTC
  cron clocks), bracketing the actual trigger instants (~13:00 UTC CF + ~13:05
  UTC fallback) with margin — candidate `[12:50, 13:25) UTC`, exact bounds set at
  Stage-0 from CF-E1/E2 run-time evidence. Contains the real runs in BOTH DST
  regimes; resolves D3 simultaneously. (A fixed *PT* board time year-round would
  instead need a seasonal cron pair — larger, called out, not chosen here.)
- **D2 — concurrency:** dedicated group for coordination-participating OPEN runs
  (keyed on the trading date). Does not reintroduce a publish race (F2). Closes
  the pending-eviction/missing-board hazard that the shared group leaves.
- **D3 — fallback clock:** a single fixed-UTC fallback cron, paired with the
  UTC-anchored D1 window; documented as tracking a fixed UTC instant that drifts
  ±1h in PT across DST (matching the existing accepted convention), NOT labeled
  "~06:05 PT" as if PT-stable.

---

END OF EVIDENCE REVIEW — NON-GATING. The GOV-2 §2 independent Codex packet-review
gate remains OPEN (packet §17 PENDING).

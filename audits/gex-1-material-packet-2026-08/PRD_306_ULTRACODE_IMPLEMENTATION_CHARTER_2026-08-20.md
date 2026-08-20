# PRD-306 Ultracode Implementation Charter (POST-GATE-A ONLY)

Status: PREPARED, NOT YET DISPATCHABLE. Prepared 2026-08-20.

## DO NOT DISPATCH UNTIL BOTH ARE TRUE

1. Fresh-context independent PRD review of PRD-306 is CLEAN
   (ACCEPT or ACCEPT-WITH-NITS with nits addressed), artifact committed at
   `docs/prd_history/PRD-306.review.claude.md` (or a commissioned
   second-model slot).
2. Dustin has issued explicit Gate A on the reviewed PRD-306 revision.

Implementation authority comes SOLELY from the reviewed PRD-306 + Dustin's
Gate A. This charter carries none on its own. If either is missing: STOP.

## Authority and non-deviation

- Build EXACTLY the reviewed PRD-306. No redesign, no re-reconnaissance, no
  re-discovery of the provider, no re-litigation of settled P0 semantics.
  The design is review-clean at packet head `33f753f`; treat it as frozen.
- The single source of build truth is `docs/prd_history/PRD-306.md`
  (BUILD-BINDING CONTRACTS 1-8 and REQUIREMENTS R1-R37). The packet is
  reference for rationale only.
- Charge envelope: honor `docs/plans/agent-work-charge-template-v0.1.md`
  (non-deviation) and GOV-0 (decision-support expansion draft hold).

## Hard build boundaries (STOP immediately on any breach)

- FILES cone (production): create ONLY `tools/gex_snapshot.py` and
  `tests/test_gex_snapshot.py`. Modify ONLY `docs/artifact_flow_map.md`
  (one writer row) and `docs/plans/decision-support-workplan-v0.1.md`
  (GEX-1 state flip) plus ordinary PRD lifecycle bookkeeping. Do NOT touch
  dashboard, payload, contract, or any `cuttingboard/` decision module.
- Ceiling: `<= 400` net production LOC in the ONE file
  `tools/gex_snapshot.py`. Exceeding 400, a second production file, a new
  dependency, a workflow, or any consumer/machine-reader surface -> STOP and
  escalate for HELM / the GOV-2 amended-authority path. Never silently widen.
- Zero new dependencies: stdlib only (including `zoneinfo`; if the OS IANA tz
  database is absent, FAIL LOUD, do NOT add a `tzdata` pip dep).
- Isolation: `tools/gex_snapshot.py` imports no `cuttingboard` module and is
  imported by none.
- Baseline-neutral: the artifact is observe-only; it creates/alters no
  decision authority.

## How to work (orchestration guidance)

- Use lightweight subagents aggressively for mechanical repository reads,
  test-precedent lookup (how existing `tests/` inject fetchers / freeze
  clocks / assert artifacts), and cross-reference checks. Do NOT use a
  premium model or Codex for simple greps, git ops, or mechanical edits.
- Concentrate all production code in `tools/gex_snapshot.py`.
- Implement tests FIRST, or in tight red/green slices, following the PRD's
  IMPLEMENTATION ORDER (fetch/fail-loud -> top-level admissibility ->
  OCC parse + exclusion counting -> GEX + per-strike aggregation ->
  structural selection + tie-break -> 0DTE -> provenance + coverage ->
  artifact assembly + atomic write -> isolation/non-redistribution guards).
- Demonstrate the required mutation-red behavior (PRD-198 invariant 4): for
  each load-bearing guard, show the test RED when the guard is removed/
  inverted, then GREEN. At minimum the MUTATION OBLIGATIONS list in the PRD:
  R3, R15, R17, R18, R23, R28, R7/R8/R33/R34, R10, R36, R37, R11, R12.

## Testing rules

- NO network in tests: inject the fetcher or override the URL; synthetic
  fixtures only; commit NO Cboe chain fixture.
- Cover the full R1-R37 matrix (families A-H in the PRD).
- Determinism: a fixed fixture + fixed clock must yield a byte-identical
  artifact (R13).
- Run focused tests throughout (`pytest tests/test_gex_snapshot.py -q`).
- Run the FULL required suite once before handoff, in CI-parity conditions
  (PRD-198 invariant 5): local/sandbox green is unverified until reproduced
  where the gate decides.

## Verification before handoff (all must pass)

- `rg -n "import cuttingboard|from cuttingboard" tools/gex_snapshot.py` -> empty.
- `rg -n "gex_snapshot" cuttingboard/` -> no import of the producer.
- `rg -n "^import |^from " tools/gex_snapshot.py` -> stdlib only.
- Net production LOC of `tools/gex_snapshot.py` <= 400.
- `git diff --stat -- requirements*.txt pyproject.toml` -> untouched.
- Full required suite GREEN in CI parity.
- No generated LIVE artifacts staged (leave `logs/*.json`, `logs/audit.jsonl`,
  `ui/dashboard.html` and equivalent scheduled outputs untouched/unstaged).

## Landing

- Open the implementation PR as a DRAFT (GOV-0 decision-support expansion
  hold; GOV-1 manual merge). Name it as an expansion-plan PR in the body.
- Lane-required fresh-context IMPLEMENTATION review before merge (distinct
  from and additional to the pre-Gate-A PRD review).
- Closeout rides the implementation PR via the `prd-closeout-verified` skill
  (same-PR mode `#NNN`), never a hand-rolled `prd_close.sh`.
- Dustin merges (GOV-1). Agents never merge and never queue auto-merge.
- No Claude Code attribution in any commit, PR body, or repo artifact.

## Stop conditions (halt and report; do not route around)

- Ceiling breach, second production file, new dependency, workflow, or
  consumer surface becomes necessary.
- Repo truth forces a production file outside the two-file cone.
- Any authority or scope expansion beyond the reviewed PRD-306 + Gate A.
- A denied git operation is needed (worktree/checkout/reset/rebase are
  hard-denied; ask Dustin, never route around with plumbing).

# CuttingBoard — Ultra Pilot Evaluation (2026-08-09)

Owner-commissioned Ultra pilot: run ONE multi-agent Ultra task against ordinary
single-agent Codex on the identical work, then rule whether Ultra becomes a
standing campaign tool.

## Pilot task
Repo-wide consumer / dead-code / collision audit, 5 independent subproblems
(config symbol-list consumers; single-owner-seam readers; SMCI degradation;
`_OPTIONAL_MACRO_DRIVERS` duplication; cross-lane file collisions). Chosen
because it satisfied all six owner criteria: bounded finish line; substantial
enough that parallel investigation helps; several independent subproblems; no
owner semantics; mechanically reconcilable (every claim is a grep); observable
failure (a claim is right or wrong). READ-ONLY both arms.

## Two arms, identical task

| Arm | Model / mode | Agents | Wall-clock | Tokens | Tool calls |
|---|---|---|---|---|---|
| Ordinary Codex | `gpt-5.6-terra`, single-agent, read-only, medium | 1 | **136s** | **83,735** | single-agent |
| Ultra Workflow | Claude general-purpose, multi-agent pipeline (5 investigate -> 5 adversarial-verify), read-only | **10** | **471s** | **503,140** | 124 |

Ultra cost ~**3.5x wall-clock** and ~**6x tokens**.

## Findings comparison
**Core findings IDENTICAL across both arms:** `REQUIRED_SYMBOLS` is dead;
`INDICES`/`COMMODITIES`/`HIGH_BETA` have zero DIRECT consumers (only compose
`ALL_SYMBOLS`); SMCI leadership gate silently degraded; `_OPTIONAL_MACRO_DRIVERS`
is an unguarded duplicate; three real cross-lane collisions.

**What Ultra added (all from the adversarial-verify stage — its differentiator):**
- *seam-readers:* refined the single-owner-seam premise — owning `payload.py` +
  `dashboard_renderer.py` does NOT own their production callers (`transport.py`,
  `output.py`, `runtime/__init__.py`, `html_renderer.py` are separate files);
  and the two seams DO couple at runtime via
  `transport.deliver_html -> html_renderer -> dashboard_renderer` public API, not
  just the JSON data boundary. (Codex noted "does not establish single owner" but
  did not trace the coupling path.)
- *seam-readers:* caught a false-positive "importer" — `test_trend_structure.py:551`
  is a source-text allowlist entry (`_PRD112_AUTHORIZED_CONSUMERS`), not an import.
- *cross-lane:* corrected a PROJECT_STATE overstatement — `PROJECT_STATE.md` is NOT
  in the PRD-159 Stage-0 mandated triple; the QW-4/Alignment collision on it occurs
  at CLOSEOUT, not Stage-0.
- *cross-lane:* flagged QW-4's "NS ledger" target as genuinely AMBIGUOUS (two
  candidate files: `CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` vs
  `NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`) — must be resolved before QW-4.
- *config:* cross-corroborated `REQUIRED_SYMBOLS`-is-dead with three independent
  sources (`vulture-output.md`, `PRD-262.md`, the Registry packet).

**Duplicated / noisy work:** on 3 of 5 subproblems (config, smci, macro-dup) the
adversarial verify only CONFIRMED — all claims survived, zero corrections: pure
confirmation, no new value. Roughly 70% of Ultra's output duplicated the Codex
baseline verbatim in substance.

**Did Ultra find anything single Codex missed? YES, narrowly.** The verify layer
caught real overstatements / false-positives on 2 of 5 subproblems. But the
single Codex baseline was already ~85% as complete at ~1/6 the cost.

## RULING: Ultra becomes a STANDING tool — used SELECTIVELY
- **NOT the default for bounded, well-specified audits.** For a surface this size,
  single-agent Codex wins decisively on ROI (6x cheaper, 3.5x faster, ~85% of the
  value). Default such tasks to single Codex + a targeted adversarial re-check on
  the 1-2 highest-stakes claims, not a 10-agent fan-out.
- **Ultra's proven differentiator is the ADVERSARIAL-VERIFY layer** catching a
  strong single agent's overstatements and false-positives. Deploy Ultra where
  that specifically pays: high-stakes findings that gate a decision (adversarial
  pre-merge validation of a MAJOR feature), or surfaces large enough that a single
  agent loses coverage (repo-wide migrations, multi-proof-surface implementations,
  multi-angle failure analysis after two normal passes fail) — exactly the owner's
  stated Ultra categories.
- Verdict for the campaign: keep Ultra in the toolbox for its named categories;
  do not spend it on bounded audits, quick wins, or PRD-specified work.

## Useful campaign findings the pilot produced (feed real work)
1. `REQUIRED_SYMBOLS` fully dead (cross-corroborated) -> Registry R3 cut candidate.
2. SMCI: EXPANSION leadership gate degraded — never fetched (absent from
   ALL_SYMBOLS/PRICE_BOUNDS/SYMBOL_UNITS), its `s in valid_quotes` test permanently
   false, no injection path -> feeds TD-4 owner ruling + the REG-D1 membership
   question.
3. `_OPTIONAL_MACRO_DRIVERS`: confirmed unguarded duplicate (`contract.py` +
   `delivery/payload.py`) -> QW-2.
4. Single-owner-seam refinement: CF's "owns payload.py + dashboard_renderer.py"
   serialization holds, but owning the seam FILES does not own their CALLERS, and
   the two seams couple at runtime via `html_renderer` — note when CF touches the
   render path.
5. Cross-lane collisions confirmed (`resolve_run_mode.py`, `payload.py`,
   `PROJECT_STATE.md`); the PROJECT_STATE collision is at closeout; QW-4's NS-ledger
   target must be disambiguated first.

---
Read-only pilot. Authorizes nothing; every merge/ruling remains Dustin's.

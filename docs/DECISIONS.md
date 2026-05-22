# Decisions log

Meaningful decisions and rationale. Date-ordered, newest first.
Short notes, not ceremony.

---

## 2026-05-22 — Gap-Down Permission Gating governance gap closed (PRD-151 retrospective)

The PRD-150 coupling recon at
`audits/recon-2026-05-22/gap-down-prd150-coupling.md` surfaced that
Gap-Down Permission Gating — listed as "in flight, needs
implementation" in VISION.md and PROJECT_STATE.md — was already
implemented in production: `cuttingboard/intraday_state_engine.py`
defines `classify_gap`, `downside_short_permission`, and supporting
state types; `cuttingboard/runtime.py:1205 _apply_intraday_short_permission`
filters SHORT candidates pre-qualification at three call sites
(`runtime.py:489, 518, 805`); test coverage exists at
`tests/test_gap_down_permission_integration.py` (4 integration tests)
and `tests/test_intraday_state.py` (8 gap-down unit tests). The
feature predates VISION.md being written; the governance docs were
never updated to reflect what shipped.

Resolution:

- Wrote PRD-151 at `docs/prd_history/PRD-151.md` documenting the
  as-built behavior with STATUS = COMPLETE on first write, full
  R1–R9 requirements derived from the existing code, an
  invalidation-conditions section describing what would make the
  feature wrong or unneeded, and an explicit NOTES section flagging
  this as the first instance of the retrospective-documentation
  pattern.
- Updated `docs/PRD_REGISTRY.md` and `docs/prd_index.json` to
  include PRD-151 as COMPLETE; `latest_complete` advanced to 151
  and `next_prd` to 152.
- Updated `VISION.md`: Gap-Down Permission Gating moved from
  "in flight" to "built and in use"; Phase 1 step 3 marked as
  already complete with a note that the realignment discovered it
  was implemented prior to VISION.md being written. PRD-150's
  PROPOSED entry in "in flight" was already gone from the cleanup;
  the section is now "none."
- Updated `docs/PROJECT_STATE.md`: `Last completed PRD` advanced to
  PRD-151; `Next step` advanced to Phase 1 step 4 (architectural
  alignment audit). Steps 1–3 of Phase 1 are complete.

### Precedent for future drift

This is the first instance of a feature shipping ahead of (or
without) its PRD in cuttingboard's recorded history. The
resolution pattern is:

1. **Retrospective documentation, not silent acknowledgment.** When
   code and governance docs diverge and the code is correct, the
   resolution is to write the PRD that should have existed — not
   to quietly delete the "in flight" line from VISION.md.
2. **STATUS = COMPLETE on first write.** Retrospective PRDs do not
   pass through PROPOSED / IN PROGRESS. The work is already
   committed across many prior commits; the PRD is documenting it,
   not authorizing it.
3. **Explicit NOTES section flagging the retrospective nature.** So
   future readers don't mistake the file for prospective work and
   try to "implement" it.
4. **No COMMIT PLAN section.** The work is already committed.
5. **Invalidation conditions are mandatory.** Because the
   retrospective PRD is the first written record of the feature's
   intent, it must include the conditions under which the feature
   becomes wrong or unneeded — these would normally be implicit in
   the prospective PRD's GOAL / OUT OF SCOPE language but here
   they're explicit because there's no prospective record.

Future drift of this shape (feature implemented without a PRD,
discovered later) should follow this pattern. Silent acknowledgment
("just delete the in-flight line") is forbidden because it loses
the institutional memory that comes with a PRD record.

If the drift is in the other direction (PRD exists, code doesn't
match it), the PATCH PRD path applies (`CLAUDE.md § PRD documentation
rule`) — that's already a documented pattern.

---

## 2026-05-22 — PRD-150 killed

PRD-150 (Five-Tier Symbol Classification System) flipped from
`PROPOSED` to `DEPRECATED` in `docs/PRD_REGISTRY.md`. The proposal
file at `docs/prd_history/PRD-150.md` is retained intact as historical
record.

Rationale: vision review at
`audits/recon-2026-05-22/prd-150-vision-review.md` found the PRD's
realizable behavior insufficient to justify its surface area. Across
four Codex cross-review passes the realizable output of the main
visibility channel (the new CLASSIFICATION rejections stage) shrank
from "five tiers, every evaluated symbol" to one tier in practice —
post-R5 PRIME→QUALIFIED demotions via concentration cap or
flow-gate. The other four tiers route through pre-existing channels
and are dedupe-guarded out of the new emission. Two new modules,
contract value-space expansion, a new sidecar artifact, a
notification path split, and a postmarket counter refactor —
in service of one new realizable emission case — fails VISION.md's
"cuts before additions" standard and the behavioral test
("does this change what Dustin actually does, or just help him feel
more informed?").

Salvageable elements captured in the same commit:
`docs/architecture.md` records the `block_reason == decision_trace["reason"]`
contract invariant surfaced in Codex Pass 2. `CLAUDE.md` workflow
patterns gain three PRD-author disciplines surfaced across the
review arc: dead-branch enumeration, downstream-consumer audit, and
realizability check.

If a narrower follow-up captures the PRIME-only notification gating
(the one substantive behavior nudge in PRD-150, implementable as
~10 LOC standalone), it should be drafted as a new PRD against
VISION.md from scratch — not a revision of PRD-150.

---

## 2026-05-22 — Phase 1 realignment

Executed VISION.md-anchored cleanup. See `audits/inventory-2026-05-22/`
for the audit that surfaced the cleanup scope and
`audits/cleanup-2026-05-22/` for verification findings.

Key decisions:

- Polygon integration removed (never used in production).
- ntfy references removed from docs (PRD-006 already removed the code).
- Legacy intraday entrypoint `run_intraday.py` deleted (the live engine
  is `intraday_state_engine.py` consumed by `runtime.py`).
- LLM-driven macro sidecar `tools/macro_collector.py` deleted (no
  consumer; latent risk of crossing description/prediction line).
- Backtesting harness deleted (contradicts VISION non-goal).
- ORB Pine script and reference module deleted; rebuild intent
  documented at `pinescripts/README.md`.
- PRD-053 / PRD-053-PATCH reconciled to `COMPLETE` (landed alongside
  PRD-054; registry's `READY` status was stale recordkeeping —
  verified by comparing `cuttingboard/market_map.py` against the
  PRD-053 spec; full enum + schema + read-only-sidecar match).
- PRD-142 deprecated; workflow change never landed and VISION schedules
  it for kill.
- AGENTS.md deleted as redundant with CLAUDE.md. The file is
  auto-generated by GitNexus; the existing
  `scripts/gitnexus-analyze.sh` wrapper passes `--skip-agents-md` so
  re-generation is suppressed when that wrapper is used. AGENTS.md is
  already in `.gitignore` (line 65), so accidental regeneration via
  `npx gitnexus analyze` direct invocation won't re-enter the repo.
- CLAUDE.md and CODEX.md rewritten as lean skeletons that point at
  canonical source-of-truth documents instead of duplicating them.
- PROJECT_STATE.md elevated as canonical current-state source.

### Polygon key exposure — accepted post-rotation

Gitleaks found 109 historical exposures of `POLYGON_API_KEY` across
`.env`, `logs/intraday.log` (commit `27b2a35a`), two
`logs/run_*.json` artifacts, and one daily report. All from the same
single value, captured by Python logging of the Polygon URL's
`?apiKey=` query string before `logs/` was gitignored at PRD-096
(commit `4e9e34b`).

Repo is public (`https://github.com/dwats250/cuttingboard`). Decision:
**rotate the key out-of-band and accept the leak as historical**.
No git history rewrite. Rationale: post-rotation the leaked value is
worthless; rewriting 714 commits would invalidate any existing clone
and force collaborators (current or future) to re-clone, while the
secret already exists in any prior clone, fork, or archive. The
Polygon code path that produced the leak is removed in this same
cleanup, so the leak cannot reoccur.

### Inventory audit corrections

Two specific inventory-audit assumptions were wrong and were
corrected in verifications:

- `numpy` *is* directly imported by `tests/test_derived.py:11` —
  retained in `pyproject.toml`. The inventory audit speculated
  otherwise.
- `AGENTS.md` is auto-generated by GitNexus; the audit treated it
  as a hand-authored file. Approach above accounts for this.

# 04 — PRD-to-Code Reconciliation

Scope: registry rows in `docs/PRD_REGISTRY.md` + files under `docs/prd_history/`. 150 unique PRD numbers used (1–150 minus skipped PRD-015 and PRD-047). Registry has 158 rows; filesystem holds 177 PRD-prefixed files (registry rows include patches and `.review.*.md` etc. live alongside).

This audit does not re-verify each PRD's implementation against code. The "drift" assessment below is **structural** — does the registry tell a coherent story, are status values consistent, do files exist where rows claim, is there code matching a PRD with no file, etc. Behavioral correctness verification per PRD is out of scope.

## Method

- Registry parsed by line.
- For each row, status is one of: `COMPLETE`, `IN PROGRESS`, `PATCH`, `DEPRECATED`, `PROPOSED`, `READY`, `—`.
- `READY` is non-canonical per `CLAUDE.md § lifecycle states` (only PROPOSED / IN PROGRESS / COMPLETE / PATCH / DEPRECATED permitted) — see flags.

## Status counts (registry rows)

| Status | Count |
|---|---|
| COMPLETE | 142 |
| PATCH | 4 |
| DEPRECATED | 1 |
| IN PROGRESS | 1 |
| PROPOSED | 1 |
| READY | 2 |
| — (sentinel / unassigned) | 1 |

## Per-status classification

### `APPEARS-ABANDONED` / `STALLED` — needs decision

| PRD | Title | Status in registry | Note |
|---|---|---|---|
| **PRD-032** | Catastrophic output and validation contract repair | DEPRECATED | File exists. No commit. Properly recorded as DEPRECATED — no further action needed. |
| **PRD-053** | Graded market map sidecar | READY | Non-canonical status. No commit hash. File exists. Implementation status unclear vs. PRD-054's "Add trade framing to market map sidecar" which is COMPLETE. Suggests PRD-053 may have been *de facto* implemented and registry was never updated. **Drift.** |
| **PRD-053 PATCH** | Market map input plumbing + usefulness calibration | READY | Same issue. |
| **PRD-142** | PATCH PRD-141 — persist hourly slot state | IN PROGRESS | Per VISION.md: stalled, scheduled for kill. `hourly_alert.yml` does not contain the `git add -f logs/last_hourly_slot.json` change the PRD specifies. `[SCHEDULED-FOR-KILL]`. |

### `PROPOSED`

| PRD | Title | Note |
|---|---|---|
| **PRD-150** | Five-Tier Symbol Classification System | Draft PRD added 2026-05-19/20; companion Codex review file present. No implementation commit. Untracked in working tree. Active draft, not abandoned. |

### Registry status anomalies

- `READY` status appears twice (PRD-053, PRD-053 PATCH). Not in the canonical lifecycle set. **Drift.**
- `COMPLETE (unregistered — no PRD file)` status text on PRD-054 row. Non-canonical wording; the row also lacks a file link. Either resolve (write a stub file or formally fold into PRD-055) or document the exception.
- PRD-049 row has commit "—" in column 2 but is marked COMPLETE. Verify commit reference.
- PRDs **with COMPLETE status but no commit hash and no file link**: PRD-050, PRD-051, PRD-101, PRD-106 (no file link, but commit hashes exist). Inconsistent with PRD-001..PRD-049 rows that always link.

### Numbering gaps

- **PRD-015** — registry shows it bundled with PRD-014 (`30ce0adc`). File not present (folded into PRD-014.md). Treated as continuity-preserving merge.
- **PRD-047** — registry explicitly: "*(intentionally skipped — number not assigned)*". Documented.

No silent gaps in registry numbering, but the filesystem holds 177 PRD-prefixed files vs 158 registry rows; the surplus comes from per-PRD review/patch/audit artifacts:

- `AUDIT_PRD016.md`
- `*.review.claude.md`, `*.review.codex.md`
- `*.adjudication.md`
- `PRD-012-cleanup.md`, `PRD-012A.md`, `PRD-003.{2,3,4}.md`, `PRD-053-PATCH.md`, `PRD-073-PATCH.md`, `PRD-089-PATCH.md`, `PRD-100-PATCH.md`, `PRD-122-PATCH.md`, `PRD-137.md` (PATCH for PRD-136)

### Reverse drift — code without a corresponding PRD

No high-confidence findings during this pass. Spot checks:

- `algos/orb_reference.py`, `backtesting/run_orb_backtest.py`, `pinescripts/0dte Momentum Setup` — pre-date the PRD-numbered era; no PRD claims these. They are reference/historical assets, not pipeline code.
- `tools/macro_collector.py` — owned by PRD-139. Match.
- `cuttingboard/notify_test.py` — no PRD claims this ad-hoc script. Predates PRD-006. Reverse-drift candidate (orphan; recommend delete in cleanup).
- `cuttingboard/run_intraday.py` — predates pipeline canonicalization (PRD-016); explicitly called legacy in CODEX.md. Reverse-drift candidate.

A full reverse-drift sweep would require reading each PRD's `FILES:` section and diffing against the live tree. Out of scope for this inventory; recommend it as a cleanup-pass deliverable.

## Documentation drift inside PRDs

Spot-check findings (not exhaustive):

- `CODEX.md` § PIPELINE LAYERS labels `notifications/` as "ntfy alert formatting" — outdated post-PRD-006.
- `CODEX.md` `## SYSTEM STATE (2026-04-27)` claims "830 tests passing". Actual baseline per `PROJECT_STATE.md`: **2524 passing** (~3× drift). PRD-149 last updated.
- `README.md:45, 97` and `docs/architecture.md` retain ntfy language despite PRD-006 removing it. See `03-dead-code.md § A.ntfy`.
- `docs/engine_doctor.md:93` — `.env` doc lists ntfy + Polygon. Will need updating with `SCHEDULED-FOR-DELETION` cleanup.

## Summary table

| Bucket | PRDs |
|---|---|
| `COMPLETE-AND-MATCHES` (presumed; not individually verified) | 142 rows minus the four cleaned-up below — ~138 |
| `COMPLETE-BUT-DRIFTED` (documentation drift, see above) | At minimum: PRD-001, PRD-006 (doc references), PRD-016/021 (architecture.md drift). Behavioral conformance unverified. |
| `IN-FLIGHT` | PRD-150 (PROPOSED, draft) |
| `STALLED` | PRD-053 (READY, no commit), PRD-053 PATCH (READY, no commit) |
| `APPEARS-ABANDONED` / `SCHEDULED-FOR-KILL` | PRD-142 (IN PROGRESS, scheduled for kill per VISION.md) |
| `DEPRECATED` (clean) | PRD-032 |

## Open questions for Dustin

1. **PRD-053 / 053 PATCH** — `READY` status with no commit but PRD-054 (trade framing on market map sidecar) is COMPLETE. Did PRD-053 actually land as part of PRD-054, or is it still pending?
2. **PRD-142** — VISION.md says kill. Should the registry row flip to `DEPRECATED` as part of this cleanup batch?
3. **PRD-054** — registry status text is non-canonical (`COMPLETE (unregistered — no PRD file; see PRD-055 continuity note)`). Write a stub file or formalize the exception?
4. **CODEX.md `830 tests`** — should the milestone snapshot be updated (or removed in favor of always reading PROJECT_STATE.md)?

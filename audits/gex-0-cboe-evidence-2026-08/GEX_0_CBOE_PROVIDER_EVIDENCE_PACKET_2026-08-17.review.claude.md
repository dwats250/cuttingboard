# Fresh-context independent review - GEX-0 Cboe provider-evidence pass

**Gate:** GOV-1 routine gate (one fresh-context review). Lane: STANDARD/NON-MATERIAL
(GEX-0 evidence; no PRD).
**Reviewed commit (SHA-pinned):** `cd1ac72` (evidence pass: packet + evidence
excerpts + guards + one workplan row).
**Reviewer context:** fresh-context independent agent; did NOT author the change.
**Connector (PRD-228, advisory only):** `chatgpt-codex-connector[bot]` posted a
single issue comment reporting Codex code-review usage limits reached - it did not
perform a review. Four channels checked (submitted reviews / inline threads / issue
comments / PR reactions): no substantive findings to disposition. The connector is
advisory and never gate-satisfying; this fresh-context review is the routine gate.

---

## VERDICT: ACCEPT-WITH-NITS

The `PROVIDER VIABLE` verdict is sound and honestly reasoned; the three integrity
guards work and turn named tests red when violated; the committed evidence contains
no full chain; the diff is scope-clean (5 files, workplan +1/-1). No required edits.

## REQUIRED EDITS
(none)

## RECOMMENDED EDITS and disposition

1. **§1 wording** - "directly established live" slightly overstated two legs (terms =
   owner-ruled; ~15-min figure = REPORTED). **ACTIONED** in this correction cycle:
   §1 now reads "established this pass - directly observed live, or owner-ruled/
   REPORTED where noted (the terms leg and the exact delay figure; §6, §8)."
2. **`docs/PROJECT_STATE.md` staleness (lines ~24, ~209)** - still describes GEX-0 as
   `EVIDENCE INCOMPLETE`; goes stale when this workplan flip merges. **DEFERRED -
   out of scope.** This packet's FILES are locked to the audits dir + one workplan
   row; editing PROJECT_STATE here would be a scope violation. Flagged for the
   post-merge drift sweep (PRD-186 drift audit is post-merge by design).
3. **§6 row 12 wording** - the cited _SPX 08-11 row's own `gamma`/`iv` are 0.0;
   "live Greeks" was loose. **ACTIONED** in this correction cycle: row 12 now reads
   "with populated `theo`/OI/model fields (that row's own `gamma`/`iv` read 0.0,
   deep-ITM)."

## DRIFT CHECK
- **VISION conflict?** No. Packet states GEX would be "computed **descriptively**
  in-repo," labels model gamma "a derived-of-derived quantity," repeatedly states it
  "creates no trade permission" (G1/G2/§4.1), builds no sidecar, and adds no
  product/consumer/cron/pipeline code. Consistent with description-not-prediction,
  read-only-sidecars, cuts-before-additions.
- **PROJECT_STATE staleness?** Yes (recommended #2) - post-merge remediation, not a
  pre-merge blocker, and out of this packet's locked scope.

## Verification performed (by the reviewer)
- All 13 doctrine §4.3 legs present and mapped 1:1 to §6 rows 1-13; the two
  REPORTED/owner-ruled legs (delay figure; terms) honestly labeled and re-listed in
  §8, not promoted to VERIFIED by inference. `PROVIDER VIABLE` tracks the doctrine
  bar ("unknowable meaning -> EVIDENCE INCOMPLETE"); no leg's core meaning is wholly
  unknowable.
- `pytest audits/gex-0-cboe-evidence-2026-08/ -q` -> 4 passed. Independently confirmed
  the excerpt guard flags a simulated 14,546-row dump (offender at `$.sample_contracts`)
  and the claim guard catches a field absent from the excerpt key-set;
  `test_fetch_shape_flags_missing_field` is a genuine self-contained red test.
- Both `evidence/*_sample.md` carry exactly 2 rows; only large numbers are scalar
  counts, not arrays. No full chain committed. `*.json` gitignore rationale verified
  (`.gitignore:54`).
- §10 claim/evidence consistency verified against SPY/SPX row keys and `underlying`.
- Scope: commit `cd1ac72` touches exactly the packet, two evidence excerpts, the
  test, and one workplan row. No product code/schema/consumer/cron/pipeline/gitignore
  edit. `logs/*.json` in `git status` are pre-existing working-tree dirt, not in the
  commit.
- Internal consistency: SPX 10,208 + SPXW 20,350 = 30,558; SPY last-trade lag ~16 min;
  spot bases match excerpts; 23-field schema; SPX AM / SPXW PM settlement noted;
  delayed data stated honestly; GEX kept context-only.

## Correction-cycle note (GOV-1)
This is the single bounded correction cycle: recommended nits #1 and #3 applied to
the packet; nit #2 deferred as out-of-scope. The substantive reviewed payload -
evidence excerpts, guards, and the `PROVIDER VIABLE` verdict - is UNCHANGED from
`cd1ac72`; only two wording clauses in the packet were sharpened. No second review is
triggered. Merge remains Dustin's under GOV-1.

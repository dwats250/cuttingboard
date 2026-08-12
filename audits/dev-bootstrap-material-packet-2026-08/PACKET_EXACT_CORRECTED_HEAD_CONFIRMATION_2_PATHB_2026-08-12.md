# PRD-301 MATERIAL packet — GOV-2 exact-corrected-head confirmation #2 (PATH-B)

- Confirmation subject: corrected packet head **e537b61** (branch
  worktree-prd-301-bootstrap-lock), after the PATH-B bounded correction (owner
  event #4) + §6 accuracy fix.
- Instrument: Codex `gpt-5.6-terra`, `-s read-only`, reasoning xhigh, fresh
  independent context (did not author the packet). GOV-2 confirmation confined to
  ACCEPT or a new material boundary omission.
- Covers (owner directive): all five original packet-review findings + REC1, the
  PATH-B post-move fail-loud correction and its Finding-2 residual closure, the
  deterministic proof + mutation, R6 completeness (`ls -A`), authority wording,
  and exact LOC. The confirmer independently applied the pinned diff to 07dce51
  and recounted LOC.

## Verdict (Codex, verbatim)

CONFIRMATION: ACCEPT (all findings addressed, no unresolved material omission)

PER-ITEM:
1. ADDRESSED — EXIT trap removes RECLAIM_LOCK only after reading this process's PID
   from it, eliminating the held-flag handoff and acquire-to-flag signal wedges.
2. ADDRESSED — both historical `.stale.PID` forms accounted for; the legacy-dir
   form is fail-closed after the authoritative post-move `rmdir` check, never
   silently discarded.
3. ADDRESSED — embedded unified diff applies cleanly to the unchanged 07dce51
   script; auditable canonical-metric count within the provisional ceiling.
4. ADDRESSED — POSIX `link()` distinguished from platform `link(1)`; macOS-runner
   exact-pathname check required pre-Gate-A.
5. ADDRESSED — each material guard has a controlled event ordering, a named
   real-process test, and an independently killing mutation.
REC1. ADDRESSED — minimum pre-amendment race stated as three processes (A, B, C).
P1. ADDRESSED — a live mover's PID-tagged grave name is exclusive among concurrent
   movers; post-move `rmdir` failure retains and names the grave, returns 4,
   propagates to `_lock` exit 2, and prevents this run from reaching acquisition or
   bootstrap work. §6 accurately describes the retained non-empty grave as visible,
   manual-removal-only, and inert to ordinary later acquisition.
P2. ADDRESSED — the shimmed-`mv` proof injects after the snapshot and before
   rename; the model retains the child and exits 2, while restoring
   `rmdir ... || true` removes the failure signal and permits acquisition — the
   named test is validly mutation-sensitive.
P3. ADDRESSED — R6 AMENDMENT explicitly permits `ls -A` (Linux + macOS/BSD) and
   extends the pre-Gate-A macOS check to empty / one-`pid` / stray-child dirs.
P4. ADDRESSED — §0 expressly says 07dce51 does not preserve every safety invariant
   and identifies the two RED-held safety violations.
P5. ADDRESSED — confirmer applied the pinned diff to 07dce51 and counted 257
   net-production lines, within the 260 provisional ceiling.

NEW MATERIAL BOUNDARY OMISSION: none
EXACT LOC MEASURED: 257 (metric: non-blank non-comment lines)

RATIONALE: At exact head e537b61 the production carrier remains unchanged from
RED-held 07dce51; the correction is confined to the governed packet/PRD artifacts.
The PATH-B post-move check closes the specified snapshot-to-`mv` lifecycle gap by
making any residual grave terminal and inspectable rather than swallowed.

## Disposition

The packet is REVIEW-CLEAN at head e537b61: independent packet review ->
one consolidated correction cycle -> exact-corrected-head confirmation (DESIGN
INCOMPLETE) -> owner PATH-B -> one bounded PATH-B correction -> this fresh
independent exact-corrected-head confirmation = ACCEPT, no unresolved material
omission. Per the owner directive, HELM returns for the owner DESIGN-DIRECTION
RULING. Still prohibited before the corresponding owner decisions: updating the
amended PRD against final direction, amended Gate A, production implementation,
closeout, merge. Head 07dce51 stays RED-held.

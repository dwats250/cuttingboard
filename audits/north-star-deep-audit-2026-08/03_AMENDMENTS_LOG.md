# Amendments Log — North Star Deep Audit

Append-only. Any Luna, Fable, or Sol discovery that would expand scope (new
domain, new source, reversal of an excluded-by-default item, a capability
gap) is logged here and NOT investigated further until Dustin rules on it.

Entry format:

```
## AMENDMENT-<NNN> — <date>
- Discovered by: <domain / phase>
- Description: <what was found outside current scope>
- Proposed scope change: <exact addition requested>
- Blocking: yes/no
- Status: PROPOSED
```

---

## AMENDMENT-001 — 2026-08-02

- Discovered by: Phase 0 scaffold (Charter §5, mechanical PR #187
  provenance attestation)
- Description: PR #187 has 28 inline review comments from
  `chatgpt-codex-connector[bot]` (1 P1, 27 P2), fully enumerated via the
  GitHub REST API (`gh api repos/dwats250/cuttingboard/pulls/187/comments`).
  Full per-thread ACTIONED/DISMISSED disposition per the PRD-228 taxonomy
  requires each thread's resolved/unresolved state, which GitHub exposes
  only via GraphQL (`reviewThreads { isResolved }`). This session's `gh api
  graphql` calls were initially denied by repository permission settings.
- Resolution: GitHub GraphQL review-thread metadata has since been
  independently obtained: 28 threads exist, all 28 are unresolved, some are
  marked outdated and some are not. Resolved/unresolved and
  outdated/current are GitHub workflow metadata — they describe a thread's
  relationship to the current diff, not whether the underlying comment was
  substantively actioned or dismissed. GitHub's `isResolved` state cannot
  by itself establish a PRD-228 disposition, and neither can `isOutdated`.
  The full governed taxonomy is exactly three values (CLAUDE.md's PRD-228
  clause: ACTIONED/DISMISSED; GOV-2 §7 extends it for MATERIAL packets):
  ACTIONED requires an in-thread reply citing the fixing commit SHA or PRD
  number; DISMISSED requires an in-thread one-line reason; BLOCKED/PARKED
  applies when the finding is valid, the packet is not review-clean, and
  no downstream authority may proceed until Dustin resumes, narrows, or
  retires it. An unresolved thread is not automatically BLOCKED/PARKED,
  and a resolved thread is not automatically ACTIONED or DISMISSED.
  Inspecting replies/fixes/reasons for all 28 threads is Phase 1 work, not
  completed here. No comment is treated as ACTIONED, DISMISSED,
  BLOCKED/PARKED, correct, or incorrect in Phase 0.
  Substantive adjudication of all 28 comments is routed to Phase 1,
  principally Domain A (owns the PRD-228 bot-thread convention per the
  Source Authority Manifest), and to whichever other domain owns a given
  comment's specific subject matter.
- Proposed scope change: none — closed without adding a source, domain,
  finding, or investigative pass.
- Blocking: no — the raw enumeration and the resolution-state layer are
  both now complete and independently verified. What remains (substantive
  disposition of each comment) is Phase 1 work, not a Phase 0 gap.
- Status: CLOSED — NON-BLOCKING (2026-08-02)

---

## AMENDMENT-002 — 2026-08-02

- Discovered by: Domain A dispatch, attempt 1 (Phase 1)
- Description: several North Star lifecycle/evidence-blocked assertions
  Domain A owns (via Master Ledger / Program) reference GOV-0 and
  expansion-doctrine mechanics whose primary text is `docs/plans/decision-support-workplan-v0.1.md`
  and `docs/plans/decision-support-expansion-doctrine-v0.1.md` — both owned
  by Domain G, not cited by Domain A. Domain A produced a row for each such
  assertion using only its authorized OWNED/CITED sources (appropriately
  hedged confidence/result) and did not investigate the G-owned material.
- Proposed scope change: add `docs/plans/decision-support-workplan-v0.1.md`
  and the relevant sections of `docs/plans/decision-support-expansion-doctrine-v0.1.md`
  to Domain A's CITED sources for governance-boundary assertions.
- Blocking: no — Domain A reached COMPLETE without this citation; the gap
  affects confidence/completeness of specific rows (see A_GOVERNANCE_AUTHORITY.md
  evidence table), not overall coverage.
- Status: PROPOSED

## AMENDMENT-003 — 2026-08-02

- Discovered by: Domain B dispatch, attempt 1 (Phase 1)
- Description: several Program §3 (source map) and §4 (dependency graph)
  rows Domain B owns reference PR #184/#185 packet artifacts, additional
  stage-0 recon files, and PRD-history files beyond Domain B's authorized
  CITED set. Domain B produced rows for the owning assertions with
  appropriately hedged confidence and did not investigate the unlisted
  artifacts.
- Proposed scope change: add the specific referenced artifacts (not a
  blanket grant) needed to verify those particular portfolio assertions —
  exact list to be drawn from B_PORTFOLIO_LIFECYCLE.md's evidence table.
- Blocking: no — Domain B reached COMPLETE without these citations.
- Status: PROPOSED

## AMENDMENT-004 — 2026-08-02

- Discovered by: Domain D1 dispatch, attempt 1 (Phase 1)
- Description: verifying specific stage0-01-owned assertions in full
  requires five additional pinned implementation files not on D1's
  9-file seam list: `cuttingboard/config.py` (universe-substrate agreement
  check), `cuttingboard/delivery/payload.py` and `cuttingboard/trade_visibility.py`
  (producer/consumer ownership verification), `cuttingboard/trend_structure.py`
  and `docs/artifact_flow_map.md` (artifact-flow verification). D1
  explicitly confirmed no broader `cuttingboard/` traversal was performed
  or needed beyond these five named files.
- Proposed scope change: add these five specific paths to Domain D1's
  implementation-seam list. Not an open-ended `cuttingboard/` sweep.
- Blocking: no — Domain D1 reached COMPLETE without them.
- Status: PROPOSED

## AMENDMENT-005 — 2026-08-02

- Discovered by: Domain F dispatch, attempt 1 (Phase 1)
- Description: (a) Program §12's NS-8 references to CB-11 and CB-20…CB-25
  are outside Domain F's cited `FINDING_STATUS_MATRIX.md` rows (CB-06/CB-18
  only); (b) the Program §4 dependency graph describes NS-9C as sharing
  substrate with the NS-2A observation artifact, which Domain F does not
  own or cite.
- Proposed scope change: (a) add the relevant matrix rows only if a
  complete NS-8 dependency-chain verification is required; (b) add the
  NS-2A artifact source only if a cross-domain substrate audit is
  required. Neither is needed for F's current scope.
- Blocking: no.
- Status: PROPOSED

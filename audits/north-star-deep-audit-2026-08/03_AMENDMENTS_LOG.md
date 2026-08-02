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
  evidence table), not overall coverage. (Reconciled 2026-08-02: the
  domain file's own "blocking: yes" on this amendment is scoped to fully
  resolving A-GOV-017's confidence, not to Domain A's COMPLETE status —
  both now say the same thing explicitly.)
- Status: PROPOSED

## AMENDMENT-003 — 2026-08-02

- Discovered by: Domain B dispatch, attempt 1 (Phase 1)
- Description: several Program §3 (source map) and §4 (dependency graph)
  rows Domain B owns reference PR #184/#185 packet artifacts, additional
  stage-0 recon files, and PRD-history files beyond Domain B's authorized
  CITED set. Domain B produced rows for the owning assertions with
  appropriately hedged confidence and did not investigate the unlisted
  artifacts.
- Proposed scope change (made exact 2026-08-02 per adjudicated Stage 0
  finding, derived only from B-017's and B-018's own recorded evidence,
  citations, and assumptions — no broad repository search performed): add
  the following specific artifacts to Domain B's CITED set, needed to fully
  resolve B-017's and B-018's confidence:
  1. `docs/plans/decision-support-workplan-v0.1.md` — the workplan Program's
     dependency graph (lines 99-136, B-017's own citation) references for
     ODATA-0/OPT-1 sequencing ("unlocks ODATA-0 backlog recon (workplan:
     'after OPT-1')").
  2. `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md` —
     the seeded packet for NS-2A/B/C MATERIAL intake, named directly in the
     same dependency graph range.
  3. `audits/stage0-recon-2026-07-20/stage0-03-scheduler-v0.1.md` and
     `audits/stage0-recon-2026-07-20/verify-03-scheduler.md` — the NS-9
     evidence base named directly in the same dependency graph range
     ("NS-9 scheduling/freshness (evidence: stage0-03...)").
  4. GitHub PR #184 and PR #185 content (not a committed repository path —
     an external GitHub artifact) — named in the same dependency graph
     range and directly in B-018's own assumption ("PR and packet
     artifacts were not in Domain B's dispatch"). If granted, this requires
     authorizing `gh pr view`/`gh pr diff` access, not a file-path CITED
     grant.
  5. Unresolved, not enumerable from B-017/B-018's own recorded evidence: the
     OPT-0 upstream MATERIAL packet's "findings artifacts" referenced by
     Master Ledger sec5's Options/reconciliation chain (cited in B-018's
     evidence range, `Master Ledger:257-266`, as "findings artifacts
     committed, all 13 connector threads actioned"). Neither B-017 nor
     B-018's recorded text states an exact repository path for these
     artifacts. This item is named as a precise open gap, not resolved with
     an invented path; a future amendment or Dustin's direct pointer would
     be needed before it could be added to CITED.
- Blocking: no — Domain B reached COMPLETE without these citations.
  (Reconciled 2026-08-02: the domain file's own "blocking: yes" on this
  amendment is scoped to fully resolving B-017/B-018's confidence, not to
  Domain B's COMPLETE status — both now say the same thing explicitly.)
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
- Blocking: no — Domain D1 reached COMPLETE without them. (Reconciled
  2026-08-02: the domain file's own "blocking: yes" on each of these
  amendments is scoped to fully resolving the affected rows' confidence,
  not to Domain D1's COMPLETE status — both now say the same thing
  explicitly.)
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

## AMENDMENT-006 — 2026-08-02

- Discovered by: Fable adjudication (bounded adjudicator pass against head
  `3d3ededc78e6b32ac3af7cfa6e9b99c9b83b1d97`), Rule 1 closing question
- Description: the two North Star documents' own preamble/title blocks —
  `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:1-12` and
  `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:1-15` (the text
  before either document's own `## 1.` heading) — are assigned to no
  domain in `01_SOURCE_AUTHORITY_MANIFEST.md`, yet are cited by A-GOV-005,
  A-GOV-009, A-GOV-012, A-GOV-024, B-001, and D2-NS2-08. This is a genuine
  manifest gap, not a violation of an existing grant: no domain's citation
  of these exact preamble lines re-derives another domain's owned
  territory, because no domain owned them at all.
- Proposed scope change: assign exactly
  `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:1-12` and
  `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:1-15` to Domain
  A, consistent with Domain A's existing ownership of both documents' §1
  (Ledger §1 = lines 13-46; Program §1 = lines 16-32) immediately
  following. No later line is included in this grant. No domain other than
  A receives citation access to these ranges. This ruling creates no
  general "foundational" or "shared-source" doctrine — it is an exact,
  narrow ownership assignment for exactly these two line ranges, closing
  the specific gap Fable identified, and does not authorize treating any
  other document's preamble, or any other section of either North Star
  document, as implicitly shared.
- Blocking: no — this closes a manifest gap retroactively; no domain's
  COMPLETE status depended on these lines being unowned.
- Status: RULED — ACCEPTED (2026-08-02). Dustin ruled directly: assign both
  ranges to Domain A, exact grant, no implicit shared-source access
  created. Applied in `01_SOURCE_AUTHORITY_MANIFEST.md`'s owning/citing
  table and Domain A's dispatch block in the same commit as this entry.

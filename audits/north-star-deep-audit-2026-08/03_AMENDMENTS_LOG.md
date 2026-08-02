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

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
  graphql` calls were denied by repository permission settings — not
  routed around, flagged here instead.
- Proposed scope change: either (a) Dustin grants GraphQL read access for a
  future session so this layer can be completed mechanically, (b) Dustin
  supplies the resolved/unresolved state directly, or (c) per-thread
  disposition is explicitly deferred to Domain A's governance pass in
  Phase 1 (Domain A owns the PRD-228 bot-thread convention per the
  Source Authority Manifest) rather than blocking Phase 0.
- Blocking: no — the raw enumeration (count, authors, files, severities,
  representative topics) is complete and independently verified; only the
  resolved/unresolved layer is gapped. Phase 0 scaffold proceeds without
  it.
- Status: PROPOSED

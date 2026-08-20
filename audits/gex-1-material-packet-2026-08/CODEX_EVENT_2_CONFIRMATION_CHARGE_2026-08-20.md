# GOV-2 Event 2 — exact-corrected-head confirmation charge: GEX-1 MATERIAL design packet

Run from the repo root of dwats250/cuttingboard with the packet's branch
checked out **at the exact corrected head named below**, sandboxed
read-only:

    codex exec -s read-only - < audits/gex-1-material-packet-2026-08/CODEX_EVENT_2_CONFIRMATION_CHARGE_2026-08-20.md

Capture stdout verbatim into
`audits/gex-1-material-packet-2026-08/GEX_1_EVENT_2_CONFIRMATION_2026-08-20.md`
with a header pinning the confirmed commit SHA. Codex writes nothing into
the tree.

---

You are performing a GOV-2 §7 **exact-corrected-head confirmation**, from
fresh context, with read-only repository access. You are not the packet's
author.

**THIS IS A CONFIRMATION, NOT A REVIEW.** You are checking the corrected
head against the Event-1 findings list — nothing else. It is NOT another
broad GEX review: do not re-litigate design choices the Event-1 review
accepted, do not open new scope, do not produce findings outside the
checklist below. The only new-material question you answer is the narrow
one in step 4. Disagreement is Dustin's to adjudicate; there is no second
author correction cycle — if a check fails, the packet returns to DESIGN
INCOMPLETE.

## Pinned head

- **CORRECTED HEAD TO CONFIRM:** `<CORRECTED_HEAD_SHA>`
  (placeholder — the orchestrator fills the real SHA after the final
  correction commit; refuse to proceed if it is still a placeholder)
- Verify `git rev-parse HEAD` equals that SHA exactly. A confirmation of
  any other commit does not count.

## Prior-cycle record (your checklist source)

- Event-1 review (reviewed SHA `70475f2bdd0bd7dd51525ba08a304b0f5add87a5`,
  verdict DESIGN INCOMPLETE):
  `audits/gex-1-material-packet-2026-08/GEX_1_EVENT_1_CODEX_REVIEW_2026-08-20.md`
- Corrected packet:
  `audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.md`
  (its `## CORRECTION CYCLE` section records the disposition of every
  finding)

## What to confirm (the whole scope)

1. **SHA:** HEAD is exactly `<CORRECTED_HEAD_SHA>`.

2. **Every Event-1 finding resolved at that exact head.** Check each
   against the packet text as it stands at HEAD:

   REQUIRED:
   - F1 — consumer-enumeration leg recorded as firing; human consumer
     (Dustin, manual local inspection) named in §0/§5; artifact_flow_map
     row spec no longer `Consumers: (none)`
   - F2 — evidence-ancestry language truthful (no stale "PR #256
     open/pending" claim anywhere in the packet)
   - F3 — eligible-input domain frozen (D6: top-level and per-contract
     admissibility, six exclusion reason keys, bool-first and finite
     checks, fail-loud rules)
   - F4 — timestamp contract matches the observed provider shape
     (naive `YYYY-MM-DD HH:MM:SS` interpreted UTC; tz-aware ISO-8601
     `feed_timestamp_utc`; malformed → fail loud; no `2026-08-18T01:00Z`
     form surviving; R23 crosses the UTC/ET date boundary)
   - F5 — unavailable output shapes always-present with `reason` tokens;
     unified `gex_1pct_usd` metric name; frozen `zero_dte` shape
   - F6 — provenance exhaustive in five classes
     (CONFIGURED/OBSERVED/REPORTED/DERIVED/INFERRED); coverage under
     DERIVED; `fetched_at_utc` identified as locally observed
   - F7 — proxy tests eliminated (R7 three surfaces; R14 triple-distinct
     fixture; R17 negative-magnitude winner; R19 mixed calls/puts; R23
     real timestamp shape; R12 exhaustive forbidden-key guard; R24–R37
     mutation-red rows for every new F3–F6 rule)

   RECOMMENDED:
   - R1 — `rg -ni 'gex|gamma' cuttingboard/` form in the Event-1 charge
     and the packet's citations
   - R2 — `roots` has its own D5 schema row
   - R3 — `python3` used consistently (§11)
   - R4 — `dominant_gamma` renamed `dominant_net_gamma` everywhere
     (historical §12 mentions may remain if explicitly marked superseded)

3. **Evidence ancestry:** `git merge-base --is-ancestor ed87913 HEAD`
   succeeds (the canonical PR #256 merge is an ancestor), and
   `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md`
   is present in-tree at HEAD.

4. **No NEW material boundary introduced by the correction:** the
   corrected packet still describes the same bounded design — `_SPX` only,
   one fetch, standalone `tools/gex_snapshot.py`, stdlib only,
   `logs/gex_snapshot.json`, no workflow/cadence, no machine consumer, no
   payload/contract/dashboard path, no second provider, no SPY — and the
   `top_strikes` removal plus the frozen validation rules added no new
   consumer, seam, schema surface beyond the sidecar artifact, dependency,
   or authority claim.

5. **FILES cone and LOC ceiling remain honest:** §7 still names one
   production file + one test file + the mandated doc rows; §8's
   re-estimated ceiling (≤ 400, arithmetic shown) is consistent with the
   corrected design and was not silently raised.

## Output format (stdout only)

- `CONFIRMED COMMIT:` the SHA (must equal `<CORRECTED_HEAD_SHA>`)
- `CONFIRMATION:` one of CONFIRMED / NOT CONFIRMED
- Per-item checklist: F1–F7, R1–R4, ancestry, no-new-boundary,
  cone/ceiling — each `PASS` or `FAIL` with a one-line citation (packet
  section or command output)
- `NOTES:` at most brief; no new findings, no fresh-scope review prose

Bounds: one confirmation pass against the prior findings list; no
review-of-review; no scope beyond the checks named here. A FAIL on any
item returns the packet to DESIGN INCOMPLETE for Dustin's disposition — it
does not open a second correction cycle.

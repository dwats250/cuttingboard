# GEX-1 MATERIAL Packet — Event 2 Exact-Corrected-Head Confirmation, ATTEMPT 1 (durable record)

- **Event:** EXACT-CORRECTED-HEAD CONFIRMATION — ATTEMPT 1
- **Reviewer:** Codex, fresh-context independent
- **Confirmed candidate SHA:** `4dd0a0b18683f41b3cba7084747c4e43c00ca156`
- **Verdict:** NOT CONFIRMED
- **Date:** 2026-08-20
- **Context:** fresh, read-only, independent (GOV-2 §7 exact-corrected-head confirmation, not a fresh-scope review)
- **stdout:** verbatim Codex output supplied by Dustin, reproduced below without paraphrase

This file is the durable ATTEMPT-1 record for the GOV-2 §7 exact-corrected-head
confirmation of the packet's Event-1 corrected head. The confirmation returned
NOT CONFIRMED on exactly three checks — F4, F6, R4 — which Dustin/HELM
classified as NON-MATERIAL confirmation defects (stale literals in
correction-history prose for F4/R4; a local provenance-manifest self-classification
omission for F6). One owner-authorized confirmation repair for those three
defects only was applied; the ATTEMPT-2 confirmation record is a separate file.
This is not a second author correction cycle.

---

## Verbatim Codex stdout (ATTEMPT 1)

```
codex
CONFIRMED COMMIT: 4dd0a0b18683f41b3cba7084747c4e43c00ca156
CONFIRMATION: NOT CONFIRMED

F1: PASS — Packet §§0/5 record the consumer-enumeration leg as firing, name Dustin/manual local inspection, distinguish no machine readers, and prohibit `Consumers: (none)` (§0 lines 35–46; §5 lines 484–500).
F2: PASS — Packet §1 records PR #256 as merged and its evidence as ancestral/in-tree; §3 likewise records merge commit `ed87913` (lines 72–87, 121–125). The old open/ready claim appears only as explicitly identified stale history in the correction disposition.
F3: PASS — D6 freezes all three top-level checks, per-contract admissibility, bool-first and finite validation, SPX/SPXW allowlisting, six exclusion keys, deterministic counting, and fail-loud behavior (lines 387–440).
F4: FAIL — Although D5/D6 and R23 contain the corrected provider-shape contract, the forbidden literal `2026-08-18T01:00Z` still survives in the packet’s correction-cycle text (line 812).
F5: PASS — D4a/D5 freeze always-present wall/dominant/zero-DTE objects, explicit reason tokens, and the unified `gex_1pct_usd` metric (lines 223–316, 323–345).
F6: FAIL — D5 claims every emitted top-level field appears in exactly one provenance class (lines 347–350), but the emitted top-level `provenance` field itself is absent from all five classification lists (lines 352–380).
F7: PASS — §6 contains the required strengthened R7/R12/R14/R17/R19/R23 fixtures and mutation-red rows R24–R37 (lines 531–561).
R1: PASS — The Event-1 charge and packet citations use `rg -ni 'gex|gamma' cuttingboard/` (charge line 40; packet lines 43 and 509).
R2: PASS — `roots` has its own D5 schema row (line 331).
R3: PASS — §11 uses `python3 tools/validate_prd_registry.py --skip-commit-resolvability` (lines 680–683).
R4: FAIL — `dominant_gamma` remains in current D4a prose outside the expressly allowed superseded §12 history (line 263); therefore it was not renamed everywhere under the stated check.
ancestry: PASS — `git merge-base --is-ancestor ed87913 HEAD` exited 0, and `git cat-file -e HEAD:audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md` exited 0.
no-new-boundary: PASS — D1–D3, D8, §5, and §§7–8 retain `_SPX` only, one fetch, standalone stdlib CLI, one sidecar artifact, human-only consumption, and no workflow, payload, second provider, SPY, dependency, or widened authority surface.
cone/ceiling: PASS — §7 retains one production file, one test file, and mandated documentation/bookkeeping rows (lines 579–587); §8 retains ≤400 production LOC with arithmetic totaling ≈380 plus ≈20 margin and no widened cone (lines 593–625).

NOTES: F4, F6, and R4 fail the supplied confirmation checklist. Per the charge, the packet returns to DESIGN INCOMPLETE for Dustin’s disposition; this does not open another correction cycle.
```

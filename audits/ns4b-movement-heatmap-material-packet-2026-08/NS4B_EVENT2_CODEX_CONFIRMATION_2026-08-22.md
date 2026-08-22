# NS-4B — GOV-2 Event-2 EXACT-CORRECTED-HEAD CONFIRMATION — durable record

**Event type:** `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §2 step 5;
owner-commissioned by Dustin, 2026-08-22).
**Scope:** confirm Event-1 F1-F6 resolved at the corrected head; detect any NEW
blocking (P1/BOUNDARY) inconsistency introduced by the correction. A
confirmation, not a fresh-scope review.
**Reviewer identity / capability role:** independent Codex (`codex-cli 0.147.0`,
`gpt-5.6-sol`), fresh context, read-only (`codex exec -s read-only`, high
effort).
**Reviewed commit SHA / packet revision:**
`5d21923b36c475ebe272252897721a9228019e52` — packet v0.3. Code baseline / merge
base `80ac6eb2618eb419afff6764292dec5c838204ce` (intervening commits are
audit-packet records only, confirmed by the reviewer).
**Review date:** 2026-08-22.
**Fresh-context / independence / run-isolation:** separate Codex session, no
access to the Claude authoring context; sandbox `read-only`, no repo write
access; record transcribed by Claude Code from captured stdout.

## Verdict: NOT CLEAN — F1-F6 all RESOLVED; ONE new blocking finding (G1, P1)

### Per-finding confirmation (Codex)

- **F1 RESOLVED** — §6 traces the correct production seam (renderer default ->
  hourly `ui/dashboard.html` -> `ui/index.html` -> readiness -> `publish` branch
  -> Pages). Cite: packet §6; `dashboard_renderer.py:53-58`;
  `hourly_alert.yml:152-216`; `pages.yml:30-38`.
- **F2 RESOLVED** — producer iterates every enabled registry instrument; per-row
  `registry_index` survives `sort_keys=True`; sort by (group order, index)
  reconstructs R2 without a renderer registry import. Cite:
  `universe_registry.py:50-65`; `watchlist_sidecar.py:43-83`;
  `runtime/__init__.py:2513-2519`.
- **F3 RESOLVED** — §3.5 accurately distinguishes full `normalized_quotes`
  sidecar inputs from `valid_quotes` consumers, selects existing-sidecar display
  parity, and defers any admission / last-trade-age change as a runtime scope
  expansion + owner ruling. Carrier already MATERIAL for its first reader, so
  materiality is unchanged. Cite: `runtime/__init__.py:549-599,778-787`;
  `validation.py:93-102,177-200`; `ingestion.py:293-343`.
- **F4 RESOLVED** — §5.1 gives one fail-closed identity/version contract; v1
  lacks all three newly reader-required row fields, supporting the v2 bump.
- **F5 RESOLVED** — M6-M9, M11-M13 each specify a single discriminating outcome
  (whole-output equality, serialized-order recovery, unknown-group suppression,
  exact hourly-only call-site assertion).
- **F6 RESOLVED** — hygiene-test surface included, precedent exists, production
  estimate raised to ~120-160 (ceiling <=190), helper clarity/testability
  separated from size.

### NEW BLOCKING FINDING

- **[G1] P1 — M11 "future generated_at" is undetectable under the packet's own
  clock boundary.** The F5 correction changed M11 to a mandatory exact outcome
  for a "future `generated_at`", but detecting "future" requires a reference
  clock and an authorized comparison source, while §12 #6 forbids any
  `datetime.now()` dependence in the block. The rule cannot be derived from the
  artifact alone and conflicts with the packet's clock boundary (§5.2 lists only
  "malformed/naive", not "future"). Evidence: packet §10 M11 (v0.3:402), §5.2
  (:276-278), §12 #6 (:435). Introduced by the consolidated correction, hence
  NEW.

## Governance consequence (GOV-2 §2 / §6 terminal rule)

A NEW P1 at the confirmation head means the packet is **NOT review-clean** and
returns to **DESIGN INCOMPLETE**. Per GOV-1 the single correction cycle is spent;
no further author correction may be made without Dustin's explicit authorization.
The packet is held for Dustin's decision (see the OWNER HANDOFF): authorize a
bounded second correction of G1 (drop "future" from M11 — leave only
clock-free malformed/naive detection; align §5.2/§10/§12), then a narrow Event-2
re-confirmation of G1 only; OR rule G1 non-blocking; OR otherwise direct.

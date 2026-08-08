# CUTTINGBOARD — GEX Remainder / Viability Closure: Planning Packet

PLANNING ONLY. No implementation, no PRD allocated, no Gate A, no PR beyond
the planning commit, no fresh evidence pass executed. Third and final lane
packet of the 2026-08-08 planning session; fills the GEX placeholder row in
`NORMALIZATION_REPORT_2026-08-08.md`. Recon basis: the merged GEX-0 packet
(`audits/gex-0-polygon-provider-evidence-2026-08/`, PR #223 squash
`5fb05a1`, doc corrections PR #224 `26c2afe`), doctrine §3.1/§4, workplan
Wave 5, North Star NS-5, and this session's prior surveys — no new broad
recon was run.

**PLANNING DISPOSITION (2026-08-08): DRAFT COMPLETE — HELD FOR OWNER
REVIEW. Not implementation-ready; the lane itself is BLOCKED on owner
action (§13).**

**READINESS: BLOCKED** (on GEX-D1/GEX-D2 owner actions). Upon grant +
commission the specified continuation pass is immediately runnable with no
further agent planning.

---

## 1. PURPOSE / USER VALUE

If — and only if — the provider proves viable, GEX gives Dustin one
narrow thing: deterministic, provenance-rich context about options-market
gamma structure (net dealer-gamma posture, flip region, wall levels
computed in-repo from raw chain data), serving VISION questions 1 and 4 —
what environment are we in, and where might hedging flows pin or
accelerate a move. It is descriptive, optional, display-only-when-built,
and independently unavailable: absent, stale, or failed GEX leaves every
existing surface byte-identical. It is never a score, gate, override,
prediction, runtime dependency, or hidden input to the Market Control
Card. (North Star NS-5: "GEX is context, not a magic signal.")

## 2. CURRENT TRUTH

**Authority (binding):**
- The GEX-0 Polygon provider-evidence packet exists in-tree
  (`GEX_0_POLYGON_PROVIDER_EVIDENCE_PACKET_2026-08-06.md`), merged via PR
  #223 (`5fb05a1`), corrected via PR #224 (`26c2afe`).
- **Final verdict, §1: `EVIDENCE INCOMPLETE`, scoped to Polygon.io's
  options-chain offering ONLY.** Doctrine §4.3: this verdict "ends the
  track until Dustin explicitly commissions a fresh pass."
- All 16 provider-side honesty rows (§6) are unresolved — the 2026-08-07
  egress probe returned HTTP 000 / proxy 403 for all 8 candidate hosts, so
  the pass was desk research with zero primary evidence. Row 13 (a
  captured, hashed sample response) alone caps the verdict.
- What PR #224 corrected: overclaims were demoted to unverified
  provider-description characteristics (raw-data-not-derived-feed;
  provider-computed greeks expectation) and the prospective
  `logs/gex_snapshot.json` shape was rephrased as conditional would-be —
  the correction class was truthfulness of claims, not new evidence.
- The packet self-classified **NON-MATERIAL** under GOV-2 §1 (read-only
  evidence, no consumers, no seam, no schema).
- §13e leaves one owner ambiguity open: whether the egress-blocked
  INCOMPLETE counts as track-ended (fresh commission) or the same pass
  paused (egress grant) — either way, doctrine requires Dustin's explicit
  act before any continuation.
- Repo-side constraints already established: Polygon was previously
  removed as dead code (never used in production); banned-import guards
  (`tests/test_scenario_engine.py:319`, `tests/test_levels.py:163`) keep
  provider imports out of pure modules; the historical POLYGON_API_KEY
  query-string leak (109 exposures, key rotated) mandates header auth.

**Docs drift (named, not fixed here):** `docs/PROJECT_STATE.md` and the
workplan GEX-0 row still say "stopped without a verdict … waits on an
egress grant" — pre-packet framing that contradicts the packet's explicit
§1 VERDICT; the North Star ledger says "never attempted," also
pre-packet; `docs/system_logic_map.md:21` still claims a Polygon fallback
(tracked CB-27). All should be reconciled in the closeout of whatever
lands next in this lane — not silently.

**Planning commentary (non-authority):** everything below this line.

## 3. UNRESOLVED LOOP

> Can Polygon.io demonstrably provide the required raw chain evidence —
> fields, semantics, coverage, freshness, auth, rate limits, and
> licensing/redistribution terms acceptable for a publicly published
> dashboard — strongly enough to reach a terminal PROVIDER VIABLE /
> PROVIDER NOT VIABLE ruling and, only if VIABLE, permit a bounded GEX-1
> producer slice?

## 4. SMALLEST NEXT SLICE — the GEX-0 continuation pass

One network-enabled, read-only evidence pass against `api.polygon.io`
ONLY, reusing the existing packet's §6 16-row checklist verbatim as the
evidence contract (no new checklist is invented). It MUST end in exactly
one terminal verdict — PROVIDER VIABLE / PROVIDER NOT VIABLE / EVIDENCE
INCOMPLETE — with no "proceed cautiously" middle state.

**Evidence classes to collect (the unresolved §6 rows, grouped):**
- *Primary capture:* ≥1 real response per candidate endpoint (options
  snapshot, contracts reference, quotes/trades, aggs, underlying spot),
  each captured verbatim, SHA-256-hashed, with request (sans credentials),
  UTC timestamp, and account tier recorded — this is row 13, the
  load-bearing gap.
- *Field semantics:* exact field enumeration; whether `greeks.gamma` is
  provider-model-computed vs exchange-sourced (row 3 — material to G1);
  timestamp units/source/TZ; spot-price basis incl. SPX index handling.
- *Coverage/entitlement:* SPY (and SPX if entitled) chain coverage,
  strike/expiry ranges, real-time vs 15-min-delayed status per tier
  (row 8), update cadence.
- *Operational contract:* auth mechanism (MUST support header auth — a
  query-string-only key scheme is a stop condition), rate limits and
  observed 429 behavior, staleness/missing-contract behavior observed
  live (null vs omitted vs stale timestamp — feeds the honest-absence
  contract).
- *Licensing (row 11 — able to flip the verdict alone):* the concrete
  question is not abstract OPRA policy but whether Polygon's agreement
  permits (a) in-repo caching/persistence of raw and computed values and
  (b) display of computed GEX levels on CuttingBoard's publicly published
  GitHub Pages dashboard. Documented from Polygon's actual terms, quoted
  and dated.
- *Pricing:* tier cost facts (row 10) recorded as documentation for
  GEX-D4.

**Network required:** egress allowlist for `api.polygon.io` (and
`polygon.io` docs pages) only — no other host, per doctrine §4.2's
no-comparison rule.

**Verdict discipline:** VIABLE requires all 16 rows resolved with none
disqualifying (licensing affirmatively permitting the public-display
surface); NOT VIABLE on any disqualifying row (licensing prohibits;
required fields/coverage absent; auth contract unacceptable); INCOMPLETE
only if access fails again — and a second INCOMPLETE ends the track
pending a fresh owner ruling, it does not authorize retries.

**Deliverable:** an addendum/v2 evidence artifact in the existing packet
folder (continuation of existing authority, §11) — docs + captured
hashed samples only; zero production code.

## 5. OWNER DECISIONS REQUIRED (minimized)

1. **GEX-D1 — Egress grant:** allow `api.polygon.io` (+docs host) through
   the agent proxy for the pass.
2. **GEX-D2 — Fresh commission + §13e interpretation in one act:**
   commission the continuation pass, stating whether it resumes the
   paused pass or supersedes an ended track (either framing works; the
   act itself is what doctrine §4.3 requires).
3. **GEX-D3 — Confirm Polygon remains the sole provider under review**
   (doctrine §4.2 forbids comparison; substitution is OUT OF SCOPE
   without this ruling changing).
4. **GEX-D4 — Tier decision:** authorize free-tier evidence first with
   paid-tier facts gathered as documentation (recommended), or
   pre-authorize a paid tier for the pass.

No other rulings are needed before the pass. (Whether licensing must be
terminally resolved before VIABLE can be granted is NOT a separate
decision — row 11 is one of the 16 rows, so a VIABLE verdict already
requires it resolved; stated here so it is not re-litigated.)

## 6. DEPENDENCIES

- **True blockers:** GEX-D1 + GEX-D2 (owner actions). Nothing else blocks
  the pass.
- **Sequencing dependencies (conditional path):** GEX-1 requires a
  PROVIDER VIABLE verdict + Dustin's go (owner hold: "GEX go/stop after
  evidence"); GEX-2 requires inspected/accepted GEX-1 artifacts (G3);
  cadence requires GEX-3's own ruling (G4). Non-collapsible (G8).
- **Morning Brief / Cloudflare: NO dependency either direction.** GEX-1
  would be manual/workflow-dispatch initially per the workplan; it does
  not need the Cloudflare clock, and the clock must not gain a second
  scheduled consumer without its own ruling (that packet's scope wall).
- **Context Registry / NEWS-0: NO dependency.** GEX-1's universe is
  SPY-primary per the workplan; if a later GEX slice wants registry
  symbols it consumes a ratified version then. No file or schema overlap.
- **Nice-to-have context only:** real-use Market Control Card observation
  (informs whether GEX-2 display is ever worth building; irrelevant to
  GEX-0/GEX-1).

## 7. PARALLEL-SAFE WORK

Everything currently in flight is parallel-safe with this lane: Morning
Brief CF-E1/CF-E2 evidence + packet work; Registry MATERIAL packet
drafting; card real-use observation. The GEX-0 continuation touches only
the audit folder (docs) — zero file coupling with any lane. A future
GEX-1 would touch new files (producer module, workflow, tests) plus
`docs/artifact_flow_map.md` registration; the only foreseeable collision
class is `.github/workflows/` additions, resolved by Dustin's serialized
merges.

## 8. SCOPE WALLS (this lane does NOT include)

GEX-2 detailed UI/design (only its existence as the conditional third
step is acknowledged); alternative providers or provider comparison
(OUT OF SCOPE — not authorized; doctrine §4.2); automatic provider
fallback; Morning Brief integration or any Cloudflare-clock scheduling of
GEX; registry/news integration; heatmap; macro; decision-engine changes;
trade permissions or sizing effects; composite scoring; predictive use;
any GEX import into `cuttingboard/` pure modules guarded by banned-import
tests; any cron/notification; any Market Control Card coupling; query-
string credentials anywhere.

## 9. FILE / SURFACE ESTIMATE

**A. GEX-0 evidence continuation:** docs only — addendum/v2 artifact +
captured hashed samples in the existing audit folder; any capture helper
script stays in the audit folder (non-production). **0 production LOC.**
Egress allowlist change is owner/infra config, not repo code.

**B. Conditional GEX-1 producer** (planned only if VIABLE + owner go;
ranges honest per the PRD-288 195→308→amended 325 / PRD-289
300→499→amended 525 estimation lesson — validation, typed-unavailable
carriers, and provenance dominate):

| Surface | Est. LOC |
|---|---|
| Provider adapter + response parsing (header auth, retries, rate-limit handling) | 100–180 |
| Provenance carrier + typed unavailable states (source/model-label/expiry-scope/as-of/observation-time/spot-basis per NS-5's required honesty; fail-loud) | 80–150 |
| In-repo GEX computation (per-strike aggregation, net gamma, flip/wall identification) | 80–160 |
| Cache/artifact writer (`logs/gex_snapshot.json`-shaped, versioned, one writer) + schema validation | 60–110 |
| Workflow (dispatch-only) + config/env (secret via env, never query string) | 30–60 |
| **Production total** | **350–660** |
| Tests (incl. mutation scaffolding, fixture captures) | 450–800 |
| Docs (artifact_flow_map registration, PRD doc, DECISIONS) | n/a |

The wide production range is honest: this slice is larger than the
Market Control Card and its Gate-A ceiling should be set near the top of
the range plus margin, not the middle.

## 10. TEST / FALSIFICATION PLAN (conditional GEX-1; mutation targets M)

- Valid provider response fixture → exact artifact contents pinned
  (deterministic parsing; M: perturb a parse → red).
- Missing required field / malformed field → typed unavailable, never a
  substituted zero/default (PRD-198 #1; M per field class).
- Auth failure / network failure / 429 → fail-loud typed unavailable;
  exit non-zero on the producer path; no partial artifact (M: swallow →
  red).
- Stale provider timestamp / absent timestamp → explicit stale/
  unavailable state per the honest-absence contract observed in GEX-0
  evidence (M: treat stale as fresh → red).
- Cache write failure → loud failure, no silent success.
- Unavailable artifact is still truthful: schema-valid, states its
  reason, carries provenance of the attempt.
- Exact provenance: source, model label, expiry scope, as-of time,
  observation time, spot basis all present (M: drop any → red).
- Run idempotence: re-run overwrites its own versioned artifact
  deterministically; no accumulation semantics unless specified.
- No secret leakage: no credential in URLs, logs, artifacts, or error
  messages (M: move key to query string → red test via URL assertion).
- Isolation invariants: no runtime hard failure when GEX absent
  (baseline pipeline byte-identical); no decision-contract change; no
  Market Control Card dependency; no Morning Brief dependency; no import
  from guarded pure modules (import-guard tests, M each).

## 11. MATERIALITY / GOVERNANCE PATH

- **GEX-0 continuation: NON-MATERIAL, continuation of existing
  authority.** The merged packet self-classified NON-MATERIAL and
  doctrine §4.3's own mechanism (Dustin commissions a fresh pass) is the
  governing act — a correction/continuation addendum in the existing
  packet folder suffices. NO new MATERIAL packet, NO new
  provider-evidence packet from scratch, NO Codex packet cycle is
  triggered by the continuation itself. Do not over-ceremonialize.
- **GEX-1 producer: classify at GOV-2 §1 intake when (and only when)
  VIABLE + owner go exist.** Expect MATERIAL (new versioned artifact
  contract, new external runtime dependency + secret, future display
  consumer) → MATERIAL packet → Codex review + exact-head confirmation →
  design-direction ruling → Stage-0 PRD → review → Gate A. Lane:
  STANDARD / SIDECAR expected (no HIGH-RISK file in the producer slice —
  renderer untouched until GEX-2).

## 12. STOP CONDITIONS

**Terminal lane stops:** licensing/redistribution terms prohibit caching
or public-dashboard display (NOT VIABLE — row 11 alone suffices);
required fields/coverage cannot be obtained (no per-contract OI or
greeks/IV path, no usable spot basis); field semantics cannot be
established well enough for honest labeling (row 3 unresolvable);
provenance cannot be established (no trustworthy as-of/observation
times); auth contract unacceptable (query-string-only credentials);
egress remains unavailable after GEX-D1 (second INCOMPLETE ends the track
pending fresh owner ruling); rate limits make even manual snapshots
impractical.

**Boundary resets (stop and re-classify/escalate):** scope drifting
toward provider substitution or comparison without authority; GEX
beginning to influence the decision contract, permissions, or sizing in
any proposed form; required freshness that cannot be truthfully
represented (would force fabricated freshness — G6 violation); any
proposal to couple GEX to the Cloudflare clock, Morning Brief, registry,
or Market Control Card.

## 13. IMPLEMENTATION READINESS

**BLOCKED** — on GEX-D1 (egress grant) and GEX-D2 (fresh commission +
§13e framing), both owner actions. Nothing in this lane can move on agent
effort alone. Upon those two acts the continuation pass is immediately
runnable as specified in §4 (no further planning needed); its terminal
verdict then either ends the lane (NOT VIABLE), re-blocks it (second
INCOMPLETE), or unlocks GEX-1's MATERIAL intake (VIABLE + Dustin's go).
GEX-1 is deliberately NOT promoted toward readiness here despite its
implementation being well-understood — readiness is not promoted on ease.

Sequential (hard order): GEX-D1+D2(+D3/D4) → continuation pass → terminal
verdict → owner go/stop → GEX-1 MATERIAL intake → packet → PRD → Gate A →
producer → inspection → GEX-2 consideration. Intentionally deferred:
GEX-2 design; cadence (GEX-3); registry-symbol expansion.

## 14. RECOMMENDED NEXT COMMISSION

**Exactly one:** present Dustin the bundled GEX-D1–GEX-D4 decision (one
short owner ruling covering egress grant, fresh-pass commission with §13e
framing, sole-provider confirmation, and tier posture). Nothing else in
this lane is actionable before that ruling, and everything after it is
already specified. Not executed here.

---

## CLOUDFLARE-FIRST CHALLENGE TEST

**Did this recon uncover a compelling reason to change the
owner-preferred Cloudflare-first order? NO.**

Nothing in the GEX evidence is time-sensitive: the provider evidence is
repeatable at any time, no entitlement or offer is expiring, the
EVIDENCE INCOMPLETE verdict is stable authority, and no GEX dependency
touches or invalidates any part of the Morning Brief or registry plans
(no shared files, no shared schema, no shared clock). There is no
correctness or safety exposure in deferral — GEX has zero production
footprint today. The only cost of Cloudflare-first is calendar delay on a
lane that is BLOCKED on owner action anyway; since the GEX-D1–D4 ruling
and the continuation pass are small and fully parallel-safe, the owner
can even issue the ruling during the Cloudflare arc without reordering
anything. Cloudflare-first stands.

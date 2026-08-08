# CUTTINGBOARD — Planning-Packet Normalization Report (2026-08-08)

Planning-quality correction pass only. No implementation, no PRD, no Gate
A, no product-direction change. Inputs: the outsider memo and the two lane
packets in this folder. Checks: one fresh-context cross-consistency
checker + one rulings-compliance checker (lightweight agents), plus direct
verification of every applied correction.

## A. Corrections made

**Both lane packets — structure.** Rewritten to the common 14-section
structure (PURPOSE / CURRENT TRUTH / UNRESOLVED LOOP / SMALLEST NEXT
SLICE / OWNER DECISIONS / DEPENDENCIES / PARALLEL-SAFE WORK / SCOPE WALLS
/ FILE-SURFACE ESTIMATE / TEST-FALSIFICATION / MATERIALITY-GOVERNANCE /
STOP CONDITIONS / IMPLEMENTATION READINESS / RECOMMENDED NEXT
COMMISSION). STOP CONDITIONS and UNRESOLVED LOOP are new sections in
both; readiness labels added. All prior content preserved; no product
direction changed.

**Decision-ID namespacing (cross-consistency finding).** The two packets'
colliding D-numbers are now document-scoped: `CF-D1a…CF-D6` / `CF-E1,
CF-E2` (Morning Brief) and `REG-D1…REG-D7` (Registry). The memo's "D-4
SPLIT" is a PRD-289-packet ruling ID from a different namespace and is
untouched.

**Memo ↔ packet contradiction (cross-consistency finding, CONTRADICTION).**
The memo's "probably cut scheduler/freshness" verdict and the Morning
Brief packet stood in silent conflict. Fixed both directions: a
SUPERSESSION NOTE at the top of the memo (verdict superseded by the
owner's product reframing; §6's next-moves list predates the packets;
merged sequencing deferred to the holistic review) and a matching
supersession note in the Morning Brief packet header.

**LOC-history inconsistency (cross-consistency finding).** The packets'
two-number ceiling chains now match the memo's fuller account:
PRD-288 195→308→amended 325; PRD-289 300→499→amended 525.

**Registry packet — two RULING_VIOLATIONs corrected (rulings checker +
independent verification):**
1. *Benchmark v1 inclusion was pre-decided.* §3 had `benchmark` as a
   settled v1 field and D3 asked only semantics. Now: REG-D3a (whether
   benchmark belongs in v1 at all) + REG-D3b (semantics/assignments if
   included); the schema lists benchmark as conditional on REG-D3a; §6
   states the timing trade instead of arguing inclusion.
2. *Theme-axis outcome was stated as settled.* "Axis-separated per D2 —
   kept distinct from roles" presented REG-D2's outcome as resolved. Now
   explicitly "PROPOSED … pending REG-D2; REG-D2 may rule otherwise," and
   REG-D2 also carries the Holdings/Spec-Learning canonical-context
   question per ruling B.

**Registry packet — additional corrections:** REG-D7 added (final
canonical file/schema shape — path/format were stated flatly in §7 while
hedged in §5; now hedged consistently everywhere); SMCI and the
`_OPTIONAL_MACRO_DRIVERS` duplicate explicitly labeled NAMED DEBT
graduated out of the lane (ruling B: never silently fixed in-lane), with
SMCI reduced to a membership question inside REG-D1; §10's validation
plan now carries per-invariant (M: …→ red) mutation annotations matching
the sibling packet's rigor; loader fail-loud invariant added.

**Morning Brief packet — additional corrections:** banner string format
flagged under CF-D1a (the ruling's literal wording vs the packet's signed
minus for GAP DOWN — confirmed at packet stage, not silently assumed);
disposition line retained as ACCEPT WITH MINOR REFINEMENTS because that
was an actual owner review outcome (the 2026-08-08 surgical-edit pass) —
the vocabulary difference vs the registry packet's DRAFT COMPLETE — HELD
FOR OWNER REVIEW is a true state difference, not drift: one packet has
been owner-reviewed, the other has not.

**Estimation check (ruling C):** both packets use ranges; validation,
closed vocabularies, DST/time handling, typed-unavailable carriers, and
mutation/test scaffolding are counted as first-class items; no tightened
ceilings were introduced. No correction needed beyond the LOC-history
chains above.

**Not changed:** the memo's body (temporary synthesis, annotated only);
any canonical doc; any code; any product ruling.

## B. Cross-packet readiness matrix

| Lane | Readiness | Gates to next state | Parallel-safe with | Hard-sequential | Stops entirely if |
|---|---|---|---|---|---|
| Morning Brief / Cloudflare Clock | **PLANNING-READY** | CF-E1 (trigger-path evidence; needs CF-D5 owner PAT/deploy) + CF-E2 (premarket-quote & first-bar evidence) + rulings CF-D1a–CF-D6 → then MATERIAL-packet draft | Registry lane; GEX owner decision; card observation (this arc amplifies it) | CF-D5 → CF-E1; CF-E2 → CF-D1b; evidence+rulings → packet → Codex cycle → ruling → PRD → Gate A | CF-E1 unworkable under least-privilege auth; CF-D5 declined; CF-E2 fails on BOTH premarket semantics AND bar latency |
| Context Registry / NEWS-0 | **MATERIAL-PACKET-READY** | Commission the packet draft now (REG-D2 ideally first); no evidence phase needed | Morning Brief lane; GEX owner decision; card observation | REG-D2 → packet → Codex cycle → REG-D1–D7 rulings + design direction → PRD → Gate A → (later) R2 → R3 | Owner declines to ratify any universe/theme content; or a ruling breaks the context-only doctrine boundary |
| GEX (placeholder — third packet not yet drafted) | **BLOCKED** (owner action) | Egress grant + fresh GEX-0 commission + packet §13e interpretation (track-ended vs paused) — all Dustin's; then a fresh evidence pass | Everything (no files) | Owner decision → fresh GEX-0 pass → verdict → (if VIABLE + go) GEX-1 → GEX-2 | GEX-0 returns PROVIDER NOT VIABLE (OPRA licensing named as able to flip it alone) and no new provider is commissioned |

Deliberately deferred across the set: GH-cron retirement
(observed-replacement-gated); holiday calendar; premarket bar ingestion;
pairwise relationship content; roles/horizons/questions; all registry
consumer migration (R2) and deletions (R3); Market Map narrowing (after
the card observation window); the merged three-lane action ranking
(explicitly left to the final holistic sequencing review).

## C. Residual open items for the holistic sequencing review

1. One merged, single ranked action list across the three lanes (the memo's
   §6 list predates both packets and is annotated as superseded-in-part).
2. The GEX planning packet (third packet — not begun in this pass, per the
   charge).
3. Owner rulings queues: CF-D1a–CF-D6 + CF-E1/CF-E2 commissioning;
   REG-D1–REG-D7; the GEX decision trio.

Disposition of this pass: **NORMALIZATION COMPLETE — no readiness
promoted, no direction changed; both lane packets internally consistent
with each other, the memo, and the A/B/C corrective rulings.**

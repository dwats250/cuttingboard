# GOV-2 Event 1 -- independent packet review charge: GEX-2 FREE board card MATERIAL design packet

Run from the repo root of dwats250/cuttingboard with the packet's branch
checked out, sandboxed read-only:

    codex exec -s read-only - < audits/gex-2-free-board-card-2026-08/CODEX_REVIEW_PROMPT_2026-08-21.md

Capture stdout verbatim into
`audits/gex-2-free-board-card-2026-08/GEX_2_EVENT_1_CODEX_REVIEW_2026-08-21.md`
with a header pinning the reviewed commit SHA. Codex writes nothing into the
tree.

---

You are performing an independent GOV-2 material-packet review, from fresh
context, with read-only repository access. You are NOT the packet's author and
have no access to the authoring session.

SUBJECT:
`audits/gex-2-free-board-card-2026-08/GEX_2_FREE_BOARD_CARD_MATERIAL_PACKET_2026-08-21.md`
-- the upstream MATERIAL design packet for GEX-2, a FREE-path, display-only,
fully-removable GEX context card added to the existing Cuttingboard dashboard
renderer, reading the existing `logs/gex_snapshot.json` sidecar (GEX-1 /
PRD-306). Review the packet AND the underlying repository surfaces it claims
about (GOV-2 sec2 step 3). State at the top the exact commit SHA you reviewed
(`git rev-parse HEAD`).

GOVERNING INPUTS (read before judging):
- `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` sec1-2, sec5-8
- `docs/plans/decision-support-expansion-doctrine-v0.1.md` (G1-G10; sec4.4)
- `docs/plans/decision-support-workplan-v0.1.md` sec8 (GEX rows)
- `docs/sidecar_doctrine.md` (observation sidecar; dashboard as consumer;
  no renderer computation; contract isolation)
- `docs/artifact_flow_map.md` (the `logs/gex_snapshot.json` row)
- `tools/gex_snapshot.py` (the producer + the exact artifact schema) and
  `logs/gex_snapshot.json` (the live sample, in the working tree)
- `cuttingboard/delivery/dashboard_renderer.py` (the renderer seam)
- The frozen PR #261 packet is historical evidence only; do NOT require this
  fresh packet to match it.

REVIEW QUESTION: is this the smallest honest FREE-path, display-only GEX card
design that satisfies doctrine sec4.4 (display/audit only; no permission or
sizing effect; no renderer computation of new analytics; missing/stale/invalid
yields baseline-identical output), the sidecar doctrine, and the owner's
free-first direction -- and is any MATERIAL boundary omitted? Specifically
verify, re-running decisive checks yourself:

1. INTAKE (sec0): are the GOV-2 sec1 legs argued correctly? Is any leg
   mis-stated or missing? Is the STANDARD-vs-HIGH-RISK question (sec9 Q1)
   framed honestly (materiality does not force HIGH-RISK)?

2. SEAM TRACE / DECISIVE NEGATIVES (sec3, sec5): re-run yourself --
   `rg -ni 'gex|gamma' cuttingboard/` (expect exit 1);
   `git ls-files --error-unmatch logs/gex_snapshot.json` (expect not tracked);
   `git check-ignore -v logs/gex_snapshot.json` (expect ignored by
   `.gitignore` `logs/`); confirm no `cuttingboard` module imports
   `tools.gex_snapshot`. Is the consumer enumeration in sec5 complete? Is the
   decision-path non-coupling claim (G2; contract/payload/qualification/
   regime/grade/size/contract-selection/notification/readiness) true against
   the current tree?

3. CARRIER REALIZABILITY (D10, the headline): verify the claim that
   `logs/gex_snapshot.json` is gitignored, untracked, absent from `main`, and
   invoked/force-added by NO workflow -- so on the CI-published board the card
   ALWAYS suppresses and the packet designs no carrier. Is the "capability-now
   / public-later" framing stated honestly (G6), or does it overclaim that the
   card will appear on the live public board in v1? Is deferring the carrier to
   GEX-3 consistent with doctrine G3/G4/G8 and the workplan GEX-2/GEX-3 gates?

4. FRESHNESS CLOCK (D4/D5): the packet binds recency on `fetched_at_utc` (our
   capture clock), shows an absolute ET capture time, and REJECTS
   `feed_timestamp_utc` as a freshness clock and `observation_trading_date` /
   `is_market_open` as a session gate (frozen E1-002 / H-1). Is the staleness
   check (capture-age vs injected render `now`, provisional STALE_MAX=24h)
   genuinely non-circular and honest? Any residual liveness overclaim?

5. SUPPRESSION / DOMAIN (D5): are the hard-suppression and row-level
   typed-unavailable rules representable against the ACTUAL artifact shapes
   (`{strike, gex_1pct_usd, reason}` objects; `zero_dte.share` null-with-reason
   vs honest 0.0; `schema_version`; `spot.value` domain)? Any invalid/edge
   class left ambiguous (NaN/Inf cannot occur -- producer writes
   `allow_nan=False`; confirm)? Is honest-zero vs null handled correctly (G6)?

6. RENDERER PURITY (D1/D7, sec6 R18): does isolating all GEX arithmetic in
   `cuttingboard/delivery/gex_card.py` and keeping `dashboard_renderer.py` to
   load-and-emit satisfy "no renderer computation"? Is the `if frag:`-no-else
   true-omission suppression correct against the renderer's actual assembly
   (does any existing block truly omit, or only degrade in place)?

7. BASELINE-NEUTRALITY (D6, sec6 R1/R17): is the INDEPENDENT pre-feature
   golden oracle correct, and is "None vs default None" correctly rejected as
   insufficient? Are R1 and R17 sufficient to prove byte-identity on
   suppression AND decision-output invariance?

8. TEST/MUTATION MATRIX (sec6): does every requirement map to a discriminating
   test whose named mutation genuinely turns it red (PRD-198 invariant 4)? Any
   proxy assertion, or any guard that cannot fail? Is the forbidden-vocabulary
   guard (R13) and the no-decision-import guard (R15) sound?

9. PRODUCER TRUTH-CORRECTION (D11, sec9 Q4): the producer docstring
   `tools/gex_snapshot.py:8` asserts "no machine consumer", which this design
   falsifies. Is the one-line, non-functional docstring correction the minimal
   honest fix, and is putting the producer file in FILES (flagged
   docstring-only) handled correctly under the owner's "avoid touching the
   producer" boundary?

10. FILES / LOC (sec7-8): is the FILES cone complete for the change described
    (including `docs/CALL_SITE_MAP.md`, `docs/artifact_flow_map.md`,
    `docs/SCHEMA_MAP.md`, the workplan flip, and the test golden asset)? Is any
    consumer, renderer, or test surface omitted? Is the `<=200` net-LOC
    estimate credible?

OUTPUT (exact shape):

```
REVIEWED COMMIT: <sha>
VERDICT: REVIEW-CLEAN | DESIGN INCOMPLETE
NEW MATERIAL BOUNDARY OMITTED: YES | NO

REQUIRED FINDINGS:
1. <finding, with the exact packet section / repo path / line it concerns and
   the concrete correction required>
...

RECOMMENDED (non-blocking):
- <...>

INDEPENDENCE / PROVENANCE:
- fresh context, read-only, not the packet author; <memory-provenance or
  run-isolation note>
```

Rules: review the packet and the repository surfaces, NOT any other review's
prose. A finding must be a real, corrigible design or truthfulness defect --
not a request to re-add the frozen PR #261 carrier/cadence machinery the owner
deliberately deferred (that direction is Dustin's, not a defect). If you find a
previously omitted consumer class, renderer, schema surface, or end-to-end
seam, say so explicitly (GOV-2 sec6 boundary-reset). Disagreement about
design direction is Dustin's to adjudicate; report it as a question, not a
required finding.

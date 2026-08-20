# GOV-2 Event 1 — independent packet review charge: GEX-1 MATERIAL design packet

Run from the repo root of dwats250/cuttingboard with the packet's branch
checked out, sandboxed read-only:

    codex exec -s read-only - < audits/gex-1-material-packet-2026-08/CODEX_REVIEW_PROMPT_2026-08-20.md

Capture stdout verbatim into
`audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.review.<model>.md`
with a header pinning the reviewed commit SHA. Codex writes nothing into the
tree.

---

You are performing an independent GOV-2 material-packet review, from fresh
context, with read-only repository access. You are not the packet's author.

SUBJECT: `audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.md`
— the upstream MATERIAL design packet for GEX-1, a manual cached GEX
producer for the Cboe `_SPX` delayed_quotes feed. Review the packet AND the
underlying repository surfaces it makes claims about (GOV-2 §2 step 3).
State at the top the exact commit SHA you reviewed (`git rev-parse HEAD`).

GOVERNING INPUTS (read before judging):
- `docs/plans/decision-support-expansion-doctrine-v0.1.md` §4 and G1–G10
- `docs/plans/decision-support-workplan-v0.1.md` §8 (GEX rows)
- `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §§1–2
- `docs/sidecar_doctrine.md`
- `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md`
  (the provider evidence the design rests on)
- `docs/DECISIONS.md` 2026-08-20 entry (the operator ruling)

REVIEW QUESTION: is this the smallest honest GEX-1 design that satisfies
doctrine §4.4, the sidecar doctrine, and the operator ruling — and is any
material boundary omitted? Specifically verify:

1. INTAKE (§0): is the GOV-2 §1 classification argued correctly? Any leg
   mis-stated?
2. SEAM TRACE (§5): re-run the decisive negatives yourself
   (`rg -niE "gex|gamma" cuttingboard/`; import edges around `tools/`;
   readers of `logs/gex_snapshot.json`). Is any consumer, reader, or
   coupled surface omitted? Is any "CONFIRMED" disposition wrong?
3. DESIGN (§4): does any element violate G1 (prediction), G2 (permission),
   G5 (additive versioning), G6 (honest absence), doctrine §4.2 (single
   provider, no abstraction/fallback), or the non-redistribution posture?
   Is the computation spec (sign, units, multiplier, spot basis, OCC parse)
   internally consistent with the evidence packet's observed fields?
4. REQUIREMENTS (§6): is any requirement untestable as specified, any test
   a proxy rather than the resolved behavior, any guard missing its red
   mutation?
5. CEILING (§7–§8): is the FILES cone complete for the stated design (would
   implementing it force a file outside the cone?), and is the LOC ceiling
   plausible?
6. OPEN QUESTIONS (§9): is any presented "open question" actually settled
   by an authority the packet missed, or any settled choice actually open?

OUTPUT FORMAT (stdout only):
- `REVIEWED COMMIT:` the SHA
- `VERDICT:` one of ACCEPT / ACCEPT-WITH-NITS / REQUIRED-CHANGES /
  DESIGN INCOMPLETE (material boundary omission)
- `REQUIRED FINDINGS:` numbered, each with the packet section, the defect,
  and the repository evidence
- `RECOMMENDED:` numbered nits
- `RATIONALE:` brief

Bounds: one review, no review-of-review, no scope beyond the packet and the
surfaces it names. Findings feed exactly ONE consolidated correction cycle
(GOV-1); disagreement is Dustin's to adjudicate.

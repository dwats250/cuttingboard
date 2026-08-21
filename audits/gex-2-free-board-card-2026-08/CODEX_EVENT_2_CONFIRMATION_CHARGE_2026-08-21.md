# GOV-2 Event 2 -- exact-corrected-head confirmation charge: GEX-2 FREE board card MATERIAL packet

Run from the repo root of dwats250/cuttingboard with the packet branch checked
out at the exact corrected head named below, sandboxed read-only:

    codex exec -s read-only - < audits/gex-2-free-board-card-2026-08/CODEX_EVENT_2_CONFIRMATION_CHARGE_2026-08-21.md

Capture stdout verbatim into
`audits/gex-2-free-board-card-2026-08/GEX_2_EVENT_2_CONFIRMATION_2026-08-21.md`
with a header pinning the confirmed SHA. Codex writes nothing into the tree.

---

You are performing a GOV-2 sec7 EXACT-CORRECTED-HEAD CONFIRMATION, from fresh
context, read-only, not the packet author.

**THIS IS A CONFIRMATION, NOT A REVIEW.** You check the corrected head against
the Event-1 findings list only. It is NOT another broad GEX review: do not
re-litigate design choices Event-1 accepted, do not open new scope, do not
produce findings outside the checklist -- EXCEPT the single narrow new-material
question in step F8. Disagreement about design direction is Dustin's to
adjudicate; there is no second author correction cycle -- if a check fails, the
packet returns to DESIGN INCOMPLETE.

## Pinned head (ATTEMPT 2 -- after the bounded F4/F7 confirmation repair)

- **CORRECTED HEAD TO CONFIRM:** `bed44ab699be57ce7e213c5e493b46a2636d62b7`
- Verify `git rev-parse HEAD` equals that SHA exactly. A confirmation of any
  other commit does not count. (Untracked charge/record files in the working
  tree do not alter the packet content at this SHA.)
- ATTEMPT 1 (against `e9b4cce`) returned NOT CONFIRMED on F4 and F7 only
  (non-material); a bounded repair of those two defects was applied. F1, F2,
  F3, F5, F6, F8 were already PASS -- re-confirm all F1-F8 at this head, with
  particular attention to F4 (exact `data_delay` identity + the 0DTE
  contradictory-pair rule in D5a) and F7 (R18 pinned to
  `tests/test_dashboard_renderer.py`; the producer-docstring conditional
  labeled Q5, the sole remaining conditional).

## Subject

`audits/gex-2-free-board-card-2026-08/GEX_2_FREE_BOARD_CARD_MATERIAL_PACKET_2026-08-21.md`
at the pinned head, with its ## CORRECTION CYCLE section. The Event-1 durable
record is
`audits/gex-2-free-board-card-2026-08/GEX_2_EVENT_1_CODEX_REVIEW_2026-08-21.md`.

## Checklist source -- Event-1 required findings (reviewed `0920c24`, DESIGN INCOMPLETE)

Confirm each is resolved at the pinned head. Re-run the decisive checks
yourself where noted.

- **F1 -- lane must be CONSUMER / HIGH-RISK.** Confirm sec0 states HIGH-RISK is
  FORCED by PRD-121 R11 (renderer is a HIGH-RISK-for-CONSUMER file touched as
  payload), STANDARD is withdrawn, sec9 Q1 is marked resolved, and sec10
  carries the HIGH-RISK Second-Model-Disposition obligation. Verify the matrix
  claim against `docs/PRD_PROCESS.md`.

- **F2 -- byte-identity vs unconditional `_CSS`.** Confirm D7 step 5 adds ZERO
  new rules to `_CSS` (reuse existing classes; any unavoidable rule inside the
  conditional fragment) and that sec6 R1's mutation set includes "add a card
  rule to the unconditional `_CSS`". Verify `_CSS` is emitted unconditionally
  at `cuttingboard/delivery/dashboard_renderer.py:2264`.

- **F3 -- false "no force-add" claim; omitted publish-staging seam.** Confirm
  sec3 and D10 now state the truthful inventory: a `git add -f logs/`
  force-add mechanism EXISTS (`.github/workflows/cuttingboard.yml:527`;
  `tools/ci_push_artifacts.sh:156`), and the card is absent on the published
  board because no workflow invokes `tools/gex_snapshot.py` and it is not
  restored -- not because no force-add exists. Verify both force-add sites and
  the no-producer-invocation fact yourself
  (`rg -n 'gex_snapshot' .github/ tools/ci_push_artifacts.sh`). Confirm GEX-3
  is reframed as "invoke producer in CI" and kept optional. Confirm this was
  the SOLE newly discovered class (so a boundary refresh, not a second reset).

- **F4 -- invalid domain.** Confirm D5a freezes the consumer admissibility
  domain: bool-first schema identity (`True==1` excluded), non-bool finite
  numerics, `spot>0`, `share` in [0,1], reason/value-pair coherence with the
  exact producer reason tokens, unknown-token rejection, tz-aware/future-clock
  timestamp rule, and source identity -- with honest-zero preserved. Confirm
  sec6 R3/R5/R15/R16 give each a red mutation.

- **F5 -- freshness clock threading.** Confirm D7 step 3 states
  `render_dashboard_html` has NO `now` param today and the PRD ADDS a single
  tz-aware `now = _utcnow()` threaded main -> write_dashboard ->
  render_dashboard_html -> gex_card, with naive/future behavior in D5a, and no
  `feed_timestamp_utc`/session-gate freshness survives. Verify the current
  signature at `dashboard_renderer.py:2049-2071` and `_utcnow` at `:486`.

- **F6 -- R15/R17 discrimination.** Confirm sec6 R17 is an AST + path-literal
  isolation guard (no `cuttingboard` module except the renderer imports
  `gex_card`; no reverse import; no other module opens the artifact path) and
  R18 is a controlled decision-output construction run (only difference
  absent-vs-valid artifact; byte-compare contract/payload/decision/
  qualification/regime/grade/sizing/selection/notification/audit/readiness).

- **F7 -- exact FILES ceiling.** Confirm the golden asset is named
  (`tests/data/dashboard_pre_gex_golden.html`), `docs/SCHEMA_MAP.md` is
  REQUIRED not conditional, the R18 test location is named, and the ceiling is
  re-estimated (`<=230` net production LOC). One remaining conditional (the
  producer docstring, Q5) is acceptable as a pre-ruling estimate under GOV-2
  sec5.

- **F8 -- new-material question (the only new judgment).** Does the corrected
  head reveal ANY previously omitted consumer class, renderer, audit carrier,
  schema surface, or end-to-end seam beyond F3's publish-staging seam? If yes,
  name it -> the packet returns to DESIGN INCOMPLETE (GOV-2 sec6). If no, say
  so.

## Output (exact shape)

```
CONFIRMED COMMIT: <sha>
CONFIRMATION: CONFIRMED | NOT CONFIRMED

F1: PASS|FAIL -- <one line>
F2: PASS|FAIL -- <one line>
F3: PASS|FAIL -- <one line>
F4: PASS|FAIL -- <one line>
F5: PASS|FAIL -- <one line>
F6: PASS|FAIL -- <one line>
F7: PASS|FAIL -- <one line>
F8: PASS(no new class)|FAIL(names it) -- <one line>

INDEPENDENCE / PROVENANCE: <fresh context, read-only, not author; note>
```

CONFIRMATION is CONFIRMED only if F1-F8 are all PASS at the pinned head.

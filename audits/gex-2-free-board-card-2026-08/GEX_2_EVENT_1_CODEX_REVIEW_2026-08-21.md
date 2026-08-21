# GEX-2 FREE Board Card MATERIAL Packet -- Event 1 Codex Review (durable record)

- **Event type:** INITIAL PACKET REVIEW (GOV-2 sec2)
- **Reviewer:** Codex (`gpt-5.6-sol`, reasoning effort high), fresh-context independent reviewer
- **Reviewed commit:** `0920c241d2b4235d435c69b98a8ddd1d3340042b`
- **Date:** 2026-08-21
- **Verdict:** DESIGN INCOMPLETE (new material boundary omitted: YES -- Finding 3 publish-staging seam)
- **Invocation:** `codex exec -s read-only - < audits/gex-2-free-board-card-2026-08/CODEX_REVIEW_PROMPT_2026-08-21.md`; sandbox read-only; approval never; no repo write.
- **Context:** fresh, read-only, independent of the authoring session (separate process; no access to the authoring conversation).

This is the durable Event-1 evidence artifact required by GOV-2 sec2. The
single consolidated author correction answering these findings is recorded in
the CORRECTION CYCLE section of
`audits/gex-2-free-board-card-2026-08/GEX_2_FREE_BOARD_CARD_MATERIAL_PACKET_2026-08-21.md`.
Event 2 (independent confirmation of the exact corrected head) is a separate
GOV-2 sec7 step recorded in its own file.

---

## Verbatim Codex stdout

```
REVIEWED COMMIT: 0920c241d2b4235d435c69b98a8ddd1d3340042b
VERDICT: DESIGN INCOMPLETE
NEW MATERIAL BOUNDARY OMITTED: YES

REQUIRED FINDINGS:
1. The STANDARD recommendation is contrary to the binding lane matrix. Packet sec0 lines 73-77 and sec9 Q1 lines 553-559 say HIGH-RISK fires only if an R11 trigger exists, but the proposed CLASS is CONSUMER and the FILES cone modifies `cuttingboard/delivery/dashboard_renderer.py` (sec7 lines 497-500). That file is explicitly HIGH-RISK for CONSUMER work in `docs/PRD_PROCESS.md:456-460`; lines 478-503 require HIGH-RISK whenever such a file is payload. Correct the packet to `CONSUMER / HIGH-RISK`, remove STANDARD as an available recommendation, and carry the corresponding review/closeout requirements. MATERIAL itself does not force HIGH-RISK, but this independent R11 trigger does.

2. D6 and D7 cannot both hold as designed. D6 lines 315-324 requires byte-identical pre-feature output on suppression, including no surviving CSS diff, while D7 lines 345-347 directs adding card rules to module-level `_CSS`. The renderer emits `_CSS` unconditionally at `cuttingboard/delivery/dashboard_renderer.py:2257-2265`; therefore even `frag == ""` changes every suppressed document. The existing `if alert_candidates:` precedent at `dashboard_renderer.py:2592-2604` proves true block omission, but it does not solve unconditional CSS. Specify either that the card uses existing styles with zero new CSS, or conditionally include card CSS only when a valid fragment is present. R1 must compare the result against a parent-commit golden and must go red for the proposed unconditional `_CSS` mutation.

3. The load-bearing “no workflow force-adds it” carrier claim is false, revealing an omitted publish-staging seam. Packet sec3 lines 149-152 and D10 lines 380-384 categorically deny any force-add, but `.github/workflows/cuttingboard.yml:511-532` runs `git add -f logs/`, and `tools/ci_push_artifacts.sh:148-156` force-adds the entire `logs` directory in the publish worktree. Current clean-checkout suppression still follows because no workflow invokes `tools/gex_snapshot.py` and the restore lists do not restore this artifact, but that is the truthful reason—not absence of a force-add mechanism. Refresh the complete producer-to-render-to-stage-to-publish inventory per GOV-2 sec6, distinguish “not produced/restored in CI” from “cannot be force-added,” and make GEX-3 language conditional: public visibility could follow only if that optional slice is later authorized and implemented. This is the newly omitted end-to-end carrier boundary.

4. D5 does not fully define the invalid domain it promises to suppress. Packet lines 287-313 and R3-R11 leave unresolved: `True == 1` passing a bare schema equality check; bool/non-finite values for net, strikes, and 0DTE share; `zero_dte.share` outside `[0,1]`; contradictory null/reason/value triples; unknown reason tokens; non-null strikes paired with unavailable reasons; malformed or future `fetched_at_utc`; and the identity fields used to print “Cboe delayed” (`source` and `data_delay`). The actual producer emits wall objects shaped exactly `{strike, gex_1pct_usd, reason}` at `tools/gex_snapshot.py:222-255`, emits the 0DTE pair at lines 275-286, and writes with `allow_nan=False` at lines 367-370, so NaN/Inf cannot be persisted by the sole valid producer; nevertheless the consumer’s written invalid contract must say which domain checks it performs. Pin exact non-boolean numeric, finiteness/range, timestamp-awareness/future-clock, source identity, and reason/value-pair rules, then parameterize R3-R11 so removing any individual guard turns a named test red. Preserve the correct honest-zero rule: `share == 0.0` with `reason is None` renders, while the exact null-with-`zero_abs_gex_denominator` pair omits only that row.

5. The freshness clock is conceptually non-circular but its threading is inaccurately described. D7 lines 336-339 says the renderer “already resolves” a render `now` and cites `_utcnow` at line 488. In the current tree, `render_dashboard_html` has no `now` parameter (`dashboard_renderer.py:2049-2071`), `_utcnow()` is used by publish validation rather than as a threaded render clock, and `main()` separately calls `datetime.now()` for red-folder data at line 3397. Specify a single timezone-aware `now` resolution and its exact threading through `main` → `write_dashboard` → `render_dashboard_html` → `gex_card`, including the behavior for naive and future timestamps. Retain `fetched_at_utc` capture age, absolute ET display, no session gate, and no relative/liveness claim.

6. R15 and R17 are not yet discriminating enough for the non-coupling claim. R15 at packet line 484 proposes an import grep while simultaneously claiming there is no machine reader other than the renderer; an import-only grep will miss a decision/notifier/runtime module that directly opens `logs/gex_snapshot.json`, and it does not guard reverse imports from `gex_card.py`. R17 line 486 does not identify the authoritative construction seam; a renderer input-before/input-after comparison, like the existing test at `tests/test_dashboard_renderer.py:391-440`, proves only non-mutation of passed dictionaries and can remain green if a runtime path begins reading the sidecar. Define R15 as an AST/path-literal guard covering all `cuttingboard` modules except the single renderer-to-card import and forbidding decision imports from the card. Define R17 as a controlled production decision-output construction run with the only environmental difference being absent versus valid GEX artifact, comparing contract, payload, decision, qualification, regime, grade, sizing, contract selection, notification, audit/readiness-relevant outputs byte-for-byte.

7. The FILES cone is not yet an exact ceiling. Sec7 lines 507-511 counts a committed golden asset but does not name its path, although that asset is a file and GOV-2 requires an exact FILES boundary. Lines 518-519 also leave `docs/SCHEMA_MAP.md` conditional, and the producer file remains conditional pending Q4. Name the golden asset explicitly, resolve every conditional file after Dustin’s ruling, identify where the authoritative R17 end-to-end test lives, and then re-estimate the `<=200` production-LOC ceiling after the domain validation, explicit clock threading, and conditional-CSS correction are included. The current estimate is plausible only for the underspecified implementation.

RECOMMENDED (non-blocking):
- Add the omitted GOV-2 sec1 cross-surface leg: the proposed read crosses persistence, delivery, and dashboard, independently satisfying the “two or more” criterion. The packet’s MATERIAL conclusion is already correct.
- Accept D11’s one-line `tools/gex_snapshot.py:8` docstring correction plus the `docs/artifact_flow_map.md` reader update. Once the machine reader exists, leaving “no machine consumer” in the producer is knowingly false; the proposed docstring-only edit is the smallest honest correction and does not alter producer behavior or schema.
- Dustin should expressly adjudicate whether distance-from-spot is permitted presentation geometry or a “new metric” under `docs/sidecar_doctrine.md:118-132`. The existing renderer already computes analogous level distance at `dashboard_renderer.py:1722-1728`, so this is a design-direction question rather than a required defect.
- Capability-now/public-later, the dominant-anchor suppression choice, and a provisional 24-hour capture-age threshold are doctrine-compatible if recorded as owner rulings and if GEX-3 remains optional rather than presumed.

INDEPENDENCE / PROVENANCE:
- fresh context, read-only, not the packet author; no other review prose was consulted. A memory-registry quick pass produced no task-specific GEX-2 review evidence and supplied no substantive finding. GitNexus had no available index, so no index was rebuilt under the read-only constraint; all findings come from direct inspection and re-executed repository checks at the pinned SHA. The working tree remained clean.

```

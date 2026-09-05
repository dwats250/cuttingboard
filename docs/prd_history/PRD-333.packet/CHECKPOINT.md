# D5 / GEX integration checkpoint

Design only, 2026-09-05. No implementation authority. Repository untouched.
Runtime exposed: GPT-6. OWNER-ATTESTED UI SEAT: GPT-6 Astra / High; runtime detail not exposed. Parent context inherited. Three mechanical recon packets completed using GPT-5.6 Luna.

Canonical remote main, verified by git ls-remote: 9b46802ab9935162c5c16df1d1f96606be1ead1c. Read-only source snapshot: canonical.git in this directory. Local branch claude/prd-234-manual-check-prominence, HEAD d58f3364047392a6b6261aa7ea05d77f0e38157c; cached origin/main 45910ffda55ecab940b07504a0283c317801af23. No local refs refreshed, branch switched, dirty file altered, or stash inspected.

## Essential facts

1. PRD-332 is COMPLETE on canonical main; D5 is A-upper / C-WATCHING.
2. Daily workflow checks out main; cuttingboard.yml:570 runs `python3 -m cuttingboard.delivery.dashboard_renderer --output ui/dashboard.html`.
3. cuttingboard.yml:571 copies dashboard.html to index.html; approved artifacts are pushed to publish, not main.
4. hourly_alert.yml:205-210 runs the same renderer with hourly inputs and mirrors index.html.
5. pages.yml checks out publish and deploys ui after completed producer workflows.
6. Live pipeline run 33954319542 at canonical D5 SHA succeeded on 2026-09-05, with live execution, verification, artifact commit and push successful.
7. Pages run 33954366607 succeeded immediately afterward. Publish commit: 3338049e18c6d167323410031edd5a8942b36930.
8. Served https://dwats250.github.io/cuttingboard/ equals BOTH publish HTML files byte-for-byte: SHA256 c4899677132af26c0ca9d0706727c6d54044b10b34507294849ccd75c99569c3. D5 is already published. No new commissioning code is needed.
9. Hierarchy: VERDICT, TAPE, optional SPY SESSION, NEXT EVENT, WATCHING, DETAILS / HISTORY. WATCHING closes at dashboard_renderer.py:3559; DETAILS begins :3563.
10. TAPE GEX reports unavailable when no admitted card (:3150-3162). The current detail card is suppressed inside DETAILS (:3567-3575).
11. gex_card.build_gex_card (:334-383) checks schema/source/delay, numeric domain, timestamps, 24h maximum age and 5m future skew. Preserve it.
12. Missing/malformed profile may omit only the profile; internally contradictory valid carrier suppresses the entire card. Do not flatten this distinction.
13. GEX profile is SPX/SPXW, not SPY: 31 half-open 25-point bins, own spot, outside mass, grayscale ladder, accessible table.
14. Pure shared profile/geometry already exists in gex_card.py. Current wrapper hardcodes gex-context, Cboe and as-of labels; it cannot be used unchanged for reference.
15. No sanctioned production reference/demo GEX seam exists. tests/test_gex_card.py::_rich (:493-517) is a synthetic teaching-quality geometry fixture; _base claims sample lineage and must not be used as provenance.
16. Acquisition is unwired and adapter dormant. No provider work is needed or authorized.
17. Existing tests cover live admission/suppression, profile math, ladder geometry/accessibility, dashboard decision isolation and goldens. setup_chart_legacy_oracle.json pins existing DETAILS/upper regions and must remain untouched.
18. Cloudflare dispatch is not execution/publish proof; no Tuesday-specific acceptance contract was found. A1-C is COMPLETE in PRD-324. Tuesday operational proof remains separate and uncaptured here.

## Core decision / remaining questions

Choose ONE frozen synthetic SPX teaching example, structurally separate from current snapshots, in a collapsed native disclosure immediately AFTER WATCHING and BEFORE unchanged DETAILS / HISTORY. Keep TAPE and the current card path unchanged. Reuse validated numeric/profile and geometry helpers; never pass a fake time/source through live admission. Never overlay current SPY or current macro values onto the example. Full brief follows in INTEGRATION_BRIEF.md.

Remaining implementation detail: exact small shared helper factoring while preserving current output bytes; prove typed carrier separation and production-to-reference rejection with tests. No product menu remains open.

## Preliminary scope killers

- Any live freshness bypass, stale-to-reference fallback, synthetic live metadata, provider/adapter activation, or upstream semantic change.
- Any need to edit D5 upper/WATCHING markup, existing DETAILS region, or legacy chart oracle rather than add the independent disclosure.
- Proposed production FILES ceiling is MATERIAL under GOV-2; dashboard protected file forces HIGH-RISK. Brief is provisional, not Gate A; PRD-332-only review exception cannot transfer.
- Injected registry gap PRD-332.impl-review.claude.md must be resolved by the authorized documentation owner before any new PRD is saved. This turn saves no PRD and changes no registry.

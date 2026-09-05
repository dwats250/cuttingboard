# Codex INITIAL PACKET REVIEW prompt — Dashboard D5 MATERIAL packet (GOV-2 sec2 step 3)

You are the commissioned fresh-context, independent Codex/Sol reviewer for a
MATERIAL packet under Cuttingboard's GOV-2 review order. Operate read-only,
fresh-context, independent of the authoring session. Your job is to FALSIFY the
packet's material-surface claims, not to praise the design (the visual direction
is frozen by owner ruling and is NOT under review).

Repository: /home/dustin/Projects/cuttingboard (branch head is the reviewed
revision; run `git rev-parse HEAD` and pin it in your output). The change is NOT
implemented — only the packet, the frozen design brief, and the PRD scaffold
exist. Review the packet against the actual repository surface.

Read:
- audits/dashboard-d5-material-packet-2026-09/DASHBOARD_D5_MATERIAL_PACKET_2026-09-04.md
- audits/dashboard-d5-material-packet-2026-09/INTEGRATION_BRIEF.md (the frozen design; sections 1-10)
- docs/prd_history/PRD-332.md
- cuttingboard/delivery/dashboard_renderer.py (the _CSS constant ~937-1217; the WATCHING emission ~3163-3436; _render_candidate_card ~2248; _render_spy_session ~2512; _render_setup_chart_block ~2232)
- the tests named in the packet's section 5 (oracle impact)

Attempt to falsify each of these claims and report where each holds or breaks,
with file:line evidence:

1. PRESENTATION-ONLY. Does the described C selector (radio group + inline
   per-symbol CSS wrapping the unchanged _render_candidate_card, default =
   select_primary_card_symbol) actually require zero change to any upstream
   compute module (market_map.py, chain_validation.py, trade_decision.py,
   execution_policy.py, contract.py, delivery/primary_selection.py,
   delivery/payload.py, delivery/setup_chart.py)? Name any module the design
   silently forces to change.

2. NO JAVASCRIPT feasibility. Given the current WATCHING DOM (tier-groups, some
   as <details>, candidate cards, the existing PRD-330 `.chart-toggle` /
   `#spy-levels:checked~` pattern), can a pure CSS `:checked ~` radio group
   deliver the selector WITHOUT a <script> and without breaking the existing
   nested <details> (chart-detail, level-detail, tier-group) or the LEVELS
   toggle? Identify any interaction where CSS-only cannot achieve the behavior.

3. CHART-SLOT SEMANTICS. The packet claims `chart_slot_available = (sym ==
   primary)` is byte-unchanged and that the default tab = primary shows the
   inline chart while other tabs keep `CHART >`. Verify against
   _render_candidate_card / the candidate-board loop. Does making each panel
   selectable change which card takes the single chart slot, or the setup-chart
   count the tests assert?

4. MANUAL CHECK GUARDRAIL. Relocating #alert-watchlist ABOVE #candidate-board:
   is the alert-watchlist ALWAYS a sibling outside every setup panel (so
   selection can never hide it)? Can a NEEDS_MANUAL_CHECK candidate ever render
   inside the selectable setup tiers (#candidate-board tier-groups) rather than
   #alert-watchlist — which would let selection hide it? Trace how
   alert_candidates vs the tier candidates are populated.

5. ORACLE COMPLETENESS. Is the packet's list of breaking byte-oracles complete?
   grep tests/ for assertions on #watching-zone / #candidate-board /
   #alert-watchlist / tier-group / setup order / the below-seam hash / the
   whole-document goldens. Name any test that the WATCHING recomposition or the
   _CSS tail-append would break that the packet did NOT list, and any it listed
   that would NOT actually break.

6. FILES / LOC ESTIMATE. Is the ESTIMATED SURFACE (production confined to
   dashboard_renderer.py; ~200-250 prod LOC; the listed test files + 2 goldens)
   credible and complete, or does the design imply an unlisted file (a fixture,
   a preview helper, a CALL_SITE/SCHEMA map, another asserting test)?

7. PRD-331 PRESERVATION. Does the design keep every PRD-331 assertion green
   except the candidate-board->alert-watchlist adjacency direction (the "MANUAL
   CHECK" literal count, "flag only in #alert-watchlist", color-independence)?
   Does the tab "CHECK" token (deliberately not the literal "MANUAL CHECK")
   avoid tripping the PRD-331 literal-count / location tests?

Output format: VERDICT (ACCEPT | ACCEPT WITH CHANGES | REJECT) with counts, then
REQUIRED findings (each: claim falsified, file:line evidence, why it matters),
then RECOMMENDED findings, then a short note confirming you operated fresh-context
and read-only. Pin the reviewed HEAD SHA.

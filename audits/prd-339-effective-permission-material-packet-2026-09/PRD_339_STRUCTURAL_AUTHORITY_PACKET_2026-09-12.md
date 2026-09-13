# PRD-339 EFFECTIVE-PERMISSION -- COMPLETENESS-BY-CONSTRUCTION Packet (2026-09-12)

STATUS: PROVISIONAL (GOV-2 s6 rebuild under Dustin's METHOD RULING of 2026-09-12:
"REBUILD -- COMPLETENESS BY CONSTRUCTION"). Not review-clean until the GOV-2 cycle
(initial Codex review -> one consolidated correction -> exact-corrected-head confirmation)
records it. Grants no downstream authority: no PRD drafting/review, no Gate A, no
implementation.

SUPERSEDES the enumeration framing of PRD_339_DECISION_AUTHORITY_REBUILD_PACKET_2026-09-12.md
(GOV-2 s10). That packet's boundary-COMPLETENESS CLAIM is SUPERSEDED (three boundary resets
proved hand-enumeration is not a reliable completeness proof here). Its exhaustive inventory
(seams, sinks, carriers, duplicate origins) REMAINS VALID and is reused below as the
MIGRATION / SINK LIST -- not as the completeness proof. The completeness proof is now
STRUCTURAL (s5).

OWNER METHOD RULING (binding, current; earlier "enumerate consumers" framing marked
SUPERSEDED): Cuttingboard shall have ONE canonical authority for resolved effective
permission; only it may answer whether Dustin may act. Other components may produce evidence
/ observations / candidates / rankings / qualification / posture / market framing / setup
strength / contextual recommendations, but may NOT independently originate, restore, override
a restriction, or present themselves as authoritative permission. Every surface communicating
authoritative actionability must consume the canonical resolved EffectivePermission through an
approved interface. Completeness proof must be STRUCTURAL (a sink cannot validly emit
authoritative action state without consuming canonical EffectivePermission); a lexical
action-vocabulary scanner is defense-in-depth only. NOTE: the ruling text as received cut off
at "...defense-in-depth to catch"; this packet treats the lexical scanner as secondary per the
visible text and will fold in any additional constraint from the tail if provided.

Repository base: main @ 1e91f897 (unchanged, nothing pushed). Branch
claude/prd-339-effective-permission-design @ d3604cb3. PRD-339 design (0348cee1) PROVISIONAL,
not modified; it must be reconciled to this architecture before it can be authoritative.
Docs-only CI boundary (GOV-2 s8): CI here only confirms the branch preserves the green
baseline; it does not execute or validate the proposed design.

---

## 1. Why MATERIAL (GOV-2 s1)

Selects a carrier/seam shared across pipeline layers; adds a persisted + typed schema surface
(EffectivePermission) with many readers; establishes a governance guardrail (the structural
CI guard); resolves High findings; crosses runtime/contract/qualification/market_map/
market_control_card/notification/delivery/dashboard/reporting/persistence. MATERIAL;
ineligible for LANE: MICRO. CLASS (CONTRACT vs EXECUTION) and lane (HIGH-RISK) are owner
rulings (Q7).

---

## 2. The invariant this architecture enforces

Only an admitted, valid, fully-evaluated daily decision, resolved through the ONE canonical
EffectivePermission authority, may answer "may Dustin act." Restrictions (HALT / operator-
lock / integrity) constrain it monotonically within a session; recovery only by a new daily
decision. Every authoritative-actionability sink consumes the resolved EffectivePermission via
the approved interface. No other component originates, restores, overrides, or presents
authoritative permission; they may only feed evidence into the resolver or render clearly
NON-authoritative analytical context.

---

## 3. The canonical authority (design)

NEW module `cuttingboard/effective_permission.py` (frozen-dataclass convention: 54/56 existing
dataclasses are frozen; SystemState already declares outcome/permission fields):

- `EffectivePermission` -- a frozen dataclass, the ONE resolved authority. Carries the
  authoritative action state (verdict: PERMITTED / NO_TRADE / OBSERVE_ONLY / HALT /
  UNAVAILABLE), the directional permission, the grade-actionability / if_now decision, the
  operator-lock + HALT restriction, and decision/session identity (reusing the PRD-339
  design-v6 carrier fields: decision_uid, session_date, restriction_rank, authority_version,
  run_uid, valid_until, recovery_basis).
- `resolve_effective_permission(...)` -- the ONLY constructor of EffectivePermission, called
  ONCE at the producer boundary (runtime/__init__.py:1051-1055, right where
  decision_is_actionable already computes the canonical outcome). It consumes the decision +
  operator snapshot + safety state + market_map/qualification EVIDENCE (which become inputs,
  not origins).
- THE APPROVED ACTIONABILITY INTERFACE -- a small set of functions in this module that RENDER
  / FORMAT authoritative action wording, each accepting ONLY an EffectivePermission (e.g.
  authoritative_verdict(ep), action_directive(ep) [IF NOW / PLAY], tier_label(ep),
  telegram_action_title(ep), report_execution_posture(ep), commit_trade_line(ep),
  cli_execution(ep)). Sinks CALL these; they do not author the wording.
- THE AUTHORITATIVE VOCABULARY -- all authoritative-action literals/enums live ONLY here (or
  are re-exported ONLY from here): the decision-state strings ("TRADE PERMITTED"/"STAY FLAT"/
  "HALT"/"OBSERVE ONLY"/"STATE UNAVAILABLE"), the outcome enum (TRADE/NO_TRADE/HALT), the
  permission-line table (collapsing the TRIPLICATION at runtime/_constants.py:96-103,
  output.py:199-206, market_control_card.py:42-54), IF_NOW_TAKE + GRADE_A_PLUS/SETUP_ACTIONABLE
  -> actionable, the A+ "ACTIONABLE" tier label, the "READY" title, the workflow "N trades"
  line, and the CLI EXECUTION line.

---

## 4. Approved-interface boundary (what "consume through an approved interface" means)

- Python sinks obtain ALL authoritative-action wording by calling the interface functions in
  effective_permission.py, passing an EffectivePermission. They may not import the vocabulary
  constants directly and may not contain the authoritative literals.
- The contract/persisted carriers expose the RESOLVED EffectivePermission fields (not raw
  proxies) so non-Python sinks have a single authoritative field to read:
  - ui/app.js (viewer) reads the resolved authoritative verdict/directives from ui/contract.json
    (EffectivePermission projection) and STOPS deriving from status+tradable / candidate
    presence.
  - the workflow commit-message step (cuttingboard.yml:481-509) reads the resolved
    authoritative line from latest_run.json (EffectivePermission projection), not re-derived
    from chain classification.
- EVIDENCE producers (regime posture, qualification/grade, market_map framing, watch,
  intraday state, macro) feed resolve_effective_permission(); they no longer reach the sinks
  as authoritative permission. Their non-authoritative analytical output (grades, posture,
  candidates, rankings, context) may still render, clearly labeled non-authoritative.

---

## 5. STRUCTURAL COMPLETENESS PROOF (the smallest genuinely-enforcing mechanism)

Chosen mechanism = frozen carrier (typed) + IMPORT/AST BOUNDARY guard, delivered as a pytest
test -- the repo's OWN proven enforcement idiom. Rationale: ruff has no plugin mechanism
(pyproject select E4/E7/E9/F only); there is no import-linter/grimp; but the repo already
enforces boundaries with AST-walking tests (tests/test_runtime_layering.py:20-41 walks module
ASTs asserting leaves never import runtime; tests/test_dash_boundary.py:19-46 asserts the
renderer namespace excludes `contract`). Both run in the AUTHORITATIVE ci.yml path (ruff +
`pytest tests/ -q`) AND in drift_full_suite.yml, with zero new CI wiring.

PROOF MECHANISM -- ADD `tests/test_effective_permission_boundary.py` (modeled verbatim on the
two existing guards): AST-walk cuttingboard/** and assert:
(i) the authoritative vocabulary constants/literals are DEFINED only in effective_permission.py;
(ii) no module outside effective_permission.py imports those constants except via the approved
     interface;
(iii) no module outside effective_permission.py contains the authoritative-action string
     literals (the decision-state strings, IF_NOW_TAKE-as-verdict, "A+ — ACTIONABLE", "READY"
     title, "TRADE PERMITTED", the permission-line values, the "N trades" line);
(iv) every registered authoritative sink obtains its wording through an interface call.
Because authoritative wording can be produced ONLY via the interface (which requires an
EffectivePermission), and the guard fails CI if the vocabulary/literal appears elsewhere, a
NEW or UNDISCOVERED sink CANNOT emit authoritative action without consuming the canonical
state. This is completeness BY CONSTRUCTION: the unprovable question "did we find every
consumer?" becomes the enforceable check "no module bypasses the carrier," and it is
regression-proof (a future bypass fails CI).

WHY the alternatives were not chosen (smallest-that-enforces):
- typed carrier alone: necessary but insufficient (Python has no sealed type; a literal can
  still be hand-written) -> it is the payload, the guard is the enforcement.
- one render API alone: nothing forces sinks to call it without the guard.
- schema constraint: constrains dict shape, not who synthesizes verdict strings; blind to
  market_map's independent if_now derivation.
- sink registry: heavier, itself bypassable, no repo precedent.
- standalone tools/ validator script: viable (validate_prd_registry shape) but needs an added
  ci.yml step and is redundant given the pytest path already runs in CI + drift.

NON-PYTHON boundary (design nuance -> owner Q9): the AST guard covers Python. Two sinks are
non-Python: ui/app.js (JS) and the workflow commit message (shell/YAML). Primary structural
control for them = the CARRIER PROVIDES THE ONLY AUTHORITATIVE FIELD (the contract/summary
carries the resolved verdict; the viewer/workflow read that field and have nothing else
authoritative to derive from), plus a lighter companion check (a node assertion for app.js; a
guard on the workflow step or making latest_run.json carry only the resolved line). Q9 asks
how far to extend structural enforcement beyond Python.

DEFENSE-IN-DEPTH (secondary, per the ruling): a lexical action-vocabulary scanner over
cuttingboard/ + ui/ + .github/ may be added to catch stragglers; it is NOT the primary proof.

---

## 6. Migration / sink list (reuses the prior inventory; the guard forces it complete)

The prior packet's inventory is the migration target. The guard passing IS the completeness
criterion, so every sink below must route through the interface (or be demoted to
non-authoritative) for CI to go green:

SINKS to route through the interface: dashboard_renderer.py (decision-state :2989-3009,
IF NOW :2415-2421, PLAY :2479-2480, A+ tier :972-977/:3452-3460, _regime_to_permission_verb
:1875-1928), dashboard_integrator.py (screen-verdicts), delivery/market_state_panel.py
(PERMISSION cell), ui/app.js (all blocks), output.py (daily Telegram build_notification_message
:1144-1210; render_report :293-630; render_report_from_payload :633-720), notifications/__init__.py
(_action_label :150-169, format_hourly_notification), notifications/formatter.py (READY titles;
duplicated OUTCOME copy :35-37), notifications/state.py (send-gate: read EP, not raw tradable),
delivery/payload.py (top_trades/summary), delivery/transport.py (CLI/JSON/HTML),
reports/premarket.py + postmarket.py, market_control_card.py (VALID_PERMISSION_VALUES /
candidate-implication), the workflow commit-message step (cuttingboard.yml:481-509).

PARALLEL ORIGINS to DEMOTE to evidence (RC2): market_map if_now/grade (market_map.py:489-509);
_regime_to_permission_verb; notifications _action_label independent derivation;
watch._execution_posture (watch.py:641-646); system_state.tradable-as-permission (contract.py:255-259).

DUPLICATIONS to collapse: the TRIPLICATED permission tables; the formatter's duplicated OUTCOME
enum; the two divergent permission-text tables.

CARRIERS needing monotonic/identity treatment (folds in the PRD-339 design-v6 publication
non-regression work): the plain-overwrite artifacts (latest_payload.json, hourly payload/html,
market_map.json), audit.jsonl (append/history), run_<ts>.json, ui/contract.json; publication
non-regression across all publish routes; the stale committed ui/*.html (owner-operational).

---

## 7. Root causes closed by this architecture

RC1 no canonical projection -> closed by the EffectivePermission authority (s3).
RC2 parallel/unconstrained origins -> closed by demotion to evidence + the guard (s6/s5).
RC3 decentralized restriction -> closed by centralizing resolution in resolve_effective_permission.
RC6 divergent permission tables -> closed by consolidation (s3).
RC4 non-monotonic carriers / publication-order authority + RC5 identity -> addressed by the
identity/version + non-regression work (design-v6 MCB-3), carried as the second slice (s9).
RC7 unsurfaced/vestigial authority -> the guard flags any wiring of it; owner-op cleanup.
The three-boundary-reset META-FINDING -> closed structurally: completeness no longer depends on
finding every sink.

---

## 8. Estimated surface (GOV-2 s5 -- ESTIMATED SURFACE, NOT YET APPROVED)

Core (small, high-leverage): NEW cuttingboard/effective_permission.py (carrier + resolver +
interface + consolidated vocabulary, ~200-350 LOC); NEW tests/test_effective_permission_boundary.py
(AST guard, ~150-300 LOC). These two deliver the authority + the structural proof.
Migration (forced complete by the guard): route ~13-18 Python sink files through the interface
+ demote ~4-5 parallel origins + collapse the duplications. Non-Python: ui/app.js + the
workflow step + a node/companion check. Publication non-regression + identity (second slice):
ci_push_artifacts.sh + the two workflows + monotonic guards on the plain-overwrite carriers +
tools/publish_authority_guard.py.
Full-scope ~28-34 production files; LOC large. The GUARD makes completeness provable regardless
of exact count. ESTIMATE only; first binding ceiling is Gate A.

---

## 9. Structure recommendation (owner Q3)

TWO ordered PRDs:
- PRD-A (authority + structural proof + Python migration): effective_permission.py carrier +
  resolver + interface + consolidated vocabulary + the AST boundary guard + route all PYTHON
  sinks through it + demote the parallel origins. The guard turning green is PRD-A's completeness
  gate. Consumers fail-closed to UNAVAILABLE where the resolved state is absent.
- PRD-B (non-Python boundary + publication non-regression + identity): ui/app.js + workflow
  commit message + companion checks; monotonic carriers; publication non-regression guard;
  identity/authority-version (design-v6 MCB-3).
A third PRD only if the owner separates the non-Python boundary from publication non-regression.
Recommend two.

---

## 10. Owner design-direction questions (method already ruled; these remain)

Q1 SESSION VALIDITY: carry admitted AM permission through the session unless a restriction/new
decision changes it, vs OBSERVE-ONLY-until-reconfirm. (Unchanged.)
Q3 STRUCTURE: one PRD vs two ordered (s9). Author rec: two.
Q4 RECOVERY: confirm only a full daily redecision restores permission; no auto-unlock; a still-
CANNOT_MONITOR setting is not cleared by a redecision.
Q6 CARRIER HOME: cuttingboard/effective_permission.py (new module, recommended) vs beside
is_actionable_trade in trade_decision.py. (Both idiomatic; the new module is the cleaner single
import target for the guard.)
Q7 CLASSIFICATION: confirm MATERIAL; rule CLASS (CONTRACT vs EXECUTION) + lane (HIGH-RISK); set
the PRD-242 / commissioned-review record for the post-ruling PRD review.
Q9 NON-PYTHON ENFORCEMENT SCOPE (NEW): how far to extend structural enforcement beyond Python
-- (a) contract/summary carries ONLY the resolved authoritative field so the JS viewer + the
workflow have nothing else to derive from (structural-by-data), plus (b) light companion checks
(node assertion for app.js; a guard on the workflow step), vs (c) accept the Python AST guard as
primary and treat JS/workflow as monitored-not-guaranteed. Author rec: (a)+(b).
Q11 DEFENSE-IN-DEPTH SCANNER (NEW, pending your truncated tail): confirm the lexical action-
vocabulary scanner is secondary/optional, and whether it gates CI or only warns. (Send the
truncated ruling tail if it constrained this.)

No question is invented for matters already determined by code or already ruled (the method is
ruled; these are the residual design/semantic + classification choices).

---

## 11. GOV-2 sequence status

1. Owner METHOD RULING (completeness-by-construction): RECEIVED.
2. Provisional structural packet: THIS DOCUMENT.
3. INITIAL PACKET REVIEW (independent Codex/Sol) against the committed SHA: pending ->
   CODEX_EVENT_1_REVIEW_STRUCTURAL_2026-09-12.md. The review question is now bounded and
   checkable: does the proposed carrier + AST boundary guard actually make bypass impossible
   (can a sink still emit authoritative action without consuming EffectivePermission)? -- NOT
   "did you enumerate every consumer."
4. ONE consolidated correction (if substantive): pending.
5. EXACT-CORRECTED-HEAD CONFIRMATION: pending ->
   CODEX_EVENT_2_CONFIRMATION_STRUCTURAL_2026-09-12.md.
6. STOP for Dustin's design-direction ruling from the review-clean packet, then PRD drafting.

No downstream authority proceeds until review-clean and Dustin rules. PRD-339 design (0348cee1)
remains provisional and must be reconciled to this architecture.

# PRD-339 EFFECTIVE-PERMISSION -- COMPLETENESS-BY-CONSTRUCTION Packet (2026-09-12)

STATUS: PROVISIONAL, CORRECTED once (GOV-2 s6 rebuild under Dustin's METHOD RULING of
2026-09-12: "REBUILD -- COMPLETENESS BY CONSTRUCTION"). The INITIAL PACKET REVIEW (Sol @
e5fdc624) returned DESIGN INCOMPLETE (mechanism unsound): the AST/vocabulary guard cannot
prove SEMANTIC completeness (assembled/synonymous/proxy-derived verdicts evade it; a sink
registry re-introduces enumeration). Per GOV-2 (this is a MECHANISM correction within the
ruled method, not an enumeration boundary reset -- the owner listed schema/dependency
constraints among the options and delegated the choice), the mechanism is CORRECTED to the
DATA / OUTPUT-CHANNEL BOUNDARY in s12; resolver placement corrected (finding 4); Q9(c)
dropped; estimate expanded. Recorded in CODEX_EVENT_1_REVIEW_STRUCTURAL_2026-09-12.md. The EXACT-CORRECTED-HEAD
CONFIRMATION (Sol @ c69ccd56, CODEX_EVENT_2_CONFIRMATION_STRUCTURAL_2026-09-12.md) returned
DESIGN INCOMPLETE (still mechanism-unsound): the Markdown report is an authoritative output
channel written BEFORE the resolver (runtime:1464/1483 before :1488) and omitted from the
finite set (F4 NOT resolved); provenance is forgeable (plain dataclass + JSON, no
capability/signature); and namespacing proxies does not strip decision-derivability. The
bounded GOV-2 cycle is EXHAUSTED -> STOP (no forced clean verdict). These residuals are
BOUNDED and CLOSABLE with a precise 4-point spec (see EVENT-2); the structural approach is
converging (F3/F6 resolved). DECISION returns to Dustin: authorize one more bounded correction
cycle applying the 4 constraints, or rule the mechanism, or park. [OWNER AUTHORIZED one more
bounded correction 2026-09-12; R1-R4 closure is s13 (the binding mechanism), pending ONE fresh
Sol exact-head confirmation.] Grants no downstream authority: no PRD drafting/review, no Gate
A, no implementation.

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
  ONCE at the CONVERGED finalization boundary [CORRECTED per initial-review finding 4; see
  s12]. That boundary is runtime/__init__.py:~1136-1147 (the "Inject dashboard-readable fields
  into system_state" block), where ALL paths converge -- validation-HALT (:1300-1302),
  kill-switch-HALT (:1303-1318), operator-lock (:1141-1144), and the decision-gate outcome --
  and outcome/permission are set uniformly, BEFORE contract finalization and any publication.
  It is NOT runtime:1051 (inside the non-HALT actionable expression, which the HALT branches
  skip). It consumes the decision + operator snapshot + safety state + market_map/qualification
  EVIDENCE (which become inputs, not origins), and it produces the HALT/UNAVAILABLE verdicts too.
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

## 5. STRUCTURAL COMPLETENESS PROOF (SUPERSEDED by s12 -- read s12 first)

[SUPERSEDED per initial-review: the AST/vocabulary-guard mechanism below was found UNSOUND
(a sink can assemble/synonymize/proxy-derive an authoritative verdict without importing the
carrier or containing a banned literal; a sink registry re-introduces enumeration). The
CORRECTED primary mechanism is the DATA / OUTPUT-CHANNEL BOUNDARY in s12; the AST + lexical
guards below are retained ONLY as defense-in-depth. The text below is kept for provenance.]

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
Q9 NON-PYTHON ENFORCEMENT IMPLEMENTATION (NEW) [CORRECTED per initial-review finding 3/6:
"monitored-not-guaranteed" is NOT a valid option -- the ruled invariant must hold for JS +
workflow too; the owner chooses the IMPLEMENTATION, not whether it holds]: (a) the served
contract/summary carries ONLY the provenanced resolved authoritative field(s), with the
proxy/evidence fields the viewer/workflow currently derive from (status+tradable at
ui/app.js:87; chain classification at cuttingboard.yml:497) REMOVED or moved to a clearly
non-authoritative namespace the output boundary rejects as decision-bearing; PLUS (b) a
companion boundary check for each (a node assertion for app.js; a guard on the workflow
commit-message step). Author rec: (a)+(b), both mandatory.
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

---

## 12. CONSOLIDATED CORRECTION -- mechanism redesign (initial-review response)

The initial review (Sol @ e5fdc624, DESIGN INCOMPLETE / mechanism unsound; STRUCTURAL
COMPLETENESS SOUND: NO) proved the AST/vocabulary guard (s4/s5) cannot prove SEMANTIC
completeness. All findings verified and dispositioned ACTIONED:

- F1/F5 (mechanism gap): a sink can emit an authoritative verdict by assembling fragments
  (`"".join(...)`, `.format`), mapping a proxy (grade/tradable/candidate-presence) to a
  SYNONYM (`GO`/`DO NOT ENTER`), or publishing a boolean/number another layer word-maps -- with
  NO carrier import and NO banned literal. Rule (iv)'s sink registry re-introduces enumeration.
  A finite word blacklist cannot prove the property.
- F2 (schema ambiguity): "authoritative vocabulary" is not precisely separable from analytical
  evidence (ACTIONABLE_CANDIDATES market_control_card.py:66; grade-derived actionability
  market_map.py:489); exact-string misses compounds, substring rejects legitimate evidence.
- F3 (non-Python gap): app.js derives TRADE_READY from status+tradable (ui/app.js:87); the
  workflow derives "N trades" from chain classification (cuttingboard.yml:497); adding one
  canonical field does not remove those proxies. Q9(c) contradicted the ruling -> dropped.
- F4 (factual): resolver cannot be at runtime:1051 -> corrected to the converged finalization
  boundary ~1136-1147 (s3).
- F6: Q9(c) insufficient (dropped); estimate omits test surface + contract/SCHEMA_MAP/
  CALL_SITE_MAP -> added below. Q1/Q3/Q4/Q6/Q7 confirmed genuine owner choices.

### CORRECTED PRIMARY MECHANISM -- DATA / OUTPUT-CHANNEL BOUNDARY (structural, semantic)

Completeness is enforced at the DATA layer and the OUTPUT-CHANNEL boundary, NOT by scanning
words. Three constraints, each testable:

1. CANONICAL PROVENANCED PROJECTION IS THE ONLY DECISION-BEARING DATA. resolve_effective_
   permission() produces the EffectivePermission with a PROVENANCE marker (it is the only code
   that can stamp it). The persisted/served carriers (contract, run summary, payload,
   ui/contract.json) carry the resolved authoritative field(s) AS THE ONLY decision-bearing
   data. The raw proxies sinks currently re-derive authority from -- system_state.tradable-as-
   authority, duplicated raw outcome, market_map if_now/grade-as-authority, the permission
   text tables, candidate/top_trades-presence-as-permission, watch execution-posture -- are
   REMOVED from the authoritative carriers or moved to a clearly NON-authoritative evidence
   namespace. A sink (Python, JS, or workflow) then has NO proxy to derive authority from.
2. OUTPUT-CHANNEL BOUNDARY VALIDATION. Enforce at every AUTHORITATIVE OUTPUT CHANNEL -- a
   FINITE, STABLE set, unlike the many/growing consumers: (i) publish (ci_push_artifacts.sh /
   the publish workflow step), (ii) Telegram send (output.py:729 send_telegram), (iii) the
   report/HTML file write (transport.deliver_html / deliver_json), (iv) CLI stdout
   (transport.deliver_cli), (v) the workflow commit message (cuttingboard.yml step), (vi) the
   served contract/board for the viewer. Each channel accepts and emits authoritative action
   state ONLY from a provenanced EffectivePermission projection, and REJECTS (fails closed) any
   bundle carrying an alternate decision-bearing field or a projection lacking provenance. A
   test asserts every output channel routes through this boundary validator (enumerating
   OUTPUT CHANNELS is tractable and stable; enumerating consumers is not).
3. RESOLVER AT THE CONVERGED BOUNDARY (s3, finding 4): one resolve call after all decision/
   HALT/lock/safety inputs converge (~1136-1147), before publication, producing every verdict
   incl. HALT/UNAVAILABLE.

WHY THIS IS SOUND WHERE THE GUARD WAS NOT: a sink cannot emit authoritative action from a proxy
because (1) removes the proxy from the authoritative data it receives, and (2) makes every
output channel reject any authoritative claim not backed by a provenanced projection. Bypass
would require inventing a provenance stamp (only resolve_effective_permission can) or adding a
new OUTPUT CHANNEL (finite set, guarded by the channel-coverage test). Completeness rests on the
FINITE output-channel set + the data invariant, not on finding every consumer.

DEFENSE-IN-DEPTH (secondary): the typed carrier (s3), an AST/import guard (s5, demoted), and a
lexical scanner (Q11) catch regressions/stragglers but are explicitly NOT the primary proof.

### CORRECTED MIGRATION (s6 reframed)

Enumerate the FINITE OUTPUT CHANNELS (i-vi above) and route each through the boundary validator;
STRIP the proxy/decision-bearing fields from the authoritative carriers (or namespace them
non-authoritative); demote the parallel origins to evidence; stamp provenance in the resolver.
The completeness gate is: (a) channel-coverage test green, (b) no-alternate-decision-field data
invariant green -- both pass/fail in CI.

### CORRECTED ESTIMATE (s8, finding 6)

Add: the broader affected-test surface; contract_types.py + docs/SCHEMA_MAP.md +
docs/CALL_SITE_MAP.md changes for the new persisted typed carrier + provenance; the
output-channel boundary validator (new, ~tools/ or a delivery module) + its channel-coverage
test. Full-scope ~30-36 production files + the test/schema surface; LOC large. ESTIMATE only;
not a Gate-A ceiling.

GOV-2 NEXT: this consolidated correction is committed; the exact-corrected-head confirmation
(Sol) runs against it -- the question is whether the DATA/OUTPUT-CHANNEL mechanism is now
sound (can a sink still emit authoritative action without a provenanced projection?). If it
finds the corrected mechanism ALSO unsound -> DESIGN INCOMPLETE, STOP, back to Dustin (no
forced clean verdict).

[UPDATE: confirmation @ c69ccd56 returned DESIGN INCOMPLETE with R1-R4 residuals; owner
authorized ONE more bounded correction. The authoritative corrected mechanism is now s13.]

---

## 13. OWNER-AUTHORIZED CORRECTION 2 -- R1-R4 closure (the binding mechanism)

Per Dustin's authorization (one further bounded correction + one fresh Sol confirmation), the
mechanism is corrected ONLY on the four confirmed residuals. This s13 is the AUTHORITATIVE
mechanism; s5 and the s12 output-channel description are superseded where they conflict.

### THREAT / TRUST BOUNDARY (stated explicitly, per the R3 instruction)

The adversary is NOT external and NOT cross-tenant/network. The authoritative carriers
(latest_run.json, latest_contract.json, ui/contract.json, latest_payload.json, the report
files) are written and read entirely within the project's own trust domain (the pipeline
process, the render step, the workflow shell, the operator's browser loading published bytes).
The real threat is a DOWNSTREAM CODE PATH -- a renderer, notifier, report writer, CLI, workflow
step, or browser script -- that emits authoritative actionability WITHOUT going through the
canonical resolver, either by (a) constructing an EffectivePermission look-alike, or (b)
re-deriving a verdict from a proxy. Because there is no external forger in scope, a
cryptographic signature/MAC or new secret is NOT required and is deliberately NOT introduced;
the guarantee is achieved by construction-capability + data-shape + fail-closed validation.
(If a future change moves an authoritative projection across a genuine trust boundary -- e.g.
an untrusted third party could write the carrier -- that would be a new threat model requiring
integrity verification; it is out of scope today and noted as a boundary condition.)

### R1 -- RESOLUTION-BEFORE-EVERY-RENDER/WRITE (structural ordering)

resolve_effective_permission() runs ONCE at the converged point where outcome, HALT
(validation :1300-1302 / kill-switch :1303-1318), operator-lock, and safety inputs are final,
BEFORE any authoritative render/write -- i.e. before render_report (runtime:1464) and before
the execute_run report writes (:417, :481), not at contract finalization (:1488).
STRUCTURAL GUARANTEE (not "call it earlier"): every authoritative render/write function is
changed to REQUIRE an EffectivePermission parameter (today render_report takes a raw
`outcome: str` at output.py:293-300; it will instead require the resolved EffectivePermission,
and the raw proxy is removed from its signature). Since an EffectivePermission can exist only
after resolution (R3), a call that renders/writes before resolution is a TYPE/argument error,
not a review concern. Rendering before resolving becomes impossible by signature.

### R2 -- CLOSED AUTHORITATIVE CHANNEL MODEL (precise)

The AUTHORITATIVE OUTPUT CHANNELS are a CLOSED, REGISTERED, FINITE set (finite and stable,
unlike consumers): (1) publish (ci_push_artifacts.sh / the publish workflow step); (2) Telegram
send (output.py:729 send_telegram); (3) the Markdown report writer (_write_markdown_report,
runtime:2259, called at :417/:481/:1483) -- NOW INCLUDED; (4) the HTML report writer
(html_renderer / transport.deliver_html); (5) the JSON payload writer insofar as it carries
authoritative fields (transport.deliver_json / delivery.payload); (6) CLI stdout
(transport.deliver_cli); (7) the served contract for the browser viewer (ui/contract.json ->
ui/app.js); (8) the workflow commit message (cuttingboard.yml:481-509/:545-548). Each channel
function requires an EffectivePermission (R1) and emits authoritative wording only via the
approved interface. A structural test asserts the registry is CLOSED: every module that writes
an authoritative output is registered and requires EP; adding a new authoritative writer
outside the registry fails the test.

### R3 -- NON-FORGEABLE PROVENANCE (per the actual trust boundary)

Guarantee: "No ordinary downstream producer or renderer can manufacture an accepted
authoritative permission projection without passing through the canonical resolver/validator
path." Realized in two layers matched to the data flow:
- IN-PROCESS (Python, same run): a PROCESS-LOCAL CONSTRUCTION CAPABILITY. EffectivePermission is
  constructed ONLY by resolve_effective_permission -- enforced by a guarded constructor
  (module-private construction; the public surface exposes only the resolver + the interface
  functions that require an existing instance), backed by the repo's AST import-boundary test
  (defense-in-depth) that fails if any other module constructs it or imports the vocabulary.
  Downstream self-assertion fails because the interface type-requires the real instance and no
  other code can construct one.
- CROSS-PROCESS / PERSISTED (disk -> render step / workflow / browser): NO integrity signature
  (trust boundary does not require it). The guarantee is instead: (a) the persisted
  authoritative carrier contains ONLY the resolved authoritative field(s), with decision
  proxies STRIPPED (R4), so a reader has NOTHING to re-derive from; (b) the ONLY writer of that
  field is the producer via the resolver (a single write path); (c) a READ/OUTPUT-BOUNDARY
  VALIDATOR at each channel that FAIL-CLOSES to UNAVAILABLE if the field is absent, malformed,
  prior-session, stale/expired, or if the bundle carries any alternate decision-bearing field.
  A downstream process cannot forge because it has no proxy to derive from and any alternate
  decision-bearing field is rejected.
WHY DOWNSTREAM SELF-ASSERTION FAILS (explicit): a plain dataclass/dict/JSON marker set by a
downstream path is not accepted because (Python) the interface only accepts the capability-
constructed instance, and (persisted) the reader ignores everything except the single resolver-
written authoritative field and fail-closes on anything anomalous. Naming conventions /
Python-private attributes alone are NOT relied upon; the construction capability + the stripped-
carrier data shape + fail-closed read validation together carry the guarantee.

### R4 -- STRIP PROXIES FROM AUTHORITATIVE RENDERERS

Authoritative renderers/channels do not namespace or relabel decision proxies -- they do not
RECEIVE them. The proxy fields (system_state.tradable-as-authority, regime posture-as-permission,
grade/setup_state -> if_now/TAKE, candidate/top_trades-presence-as-permission, the permission
text tables, watch execution-posture) are removed from the authoritative render/write inputs and
from the authoritative persisted carrier. Evidence/ranking/posture/framing/qualification may
still be shown as NON-authoritative facts/context, but authoritative action wording (TRADE
PERMITTED / IF NOW=TAKE / PLAY / A+ ACTIONABLE / READY / directional LONG-SHORT permission /
"N trades" / EXECUTION) derives ONLY from the EffectivePermission. The s12 "non-authoritative
namespace" ALTERNATIVE IS WITHDRAWN (it did not strip decision-derivability). A structural test
asserts authoritative channel functions do not read the proxy fields for authoritative output.

### 7. FAIL-CLOSED BEHAVIOR (requirement 7, explicit)

When the canonical EffectivePermission / capability is absent, invalid, prior-session, stale/
expired, or unverifiable at any authoritative channel: the channel emits UNAVAILABLE (or its
channel-equivalent no-action state) and NO action/permission wording -- never a proxy-derived
claim, never a retained prior grant. This applies in-process (missing instance -> the interface
cannot be called -> caller must render UNAVAILABLE) and cross-process (the read-boundary
validator rejects and the consumer renders UNAVAILABLE).

### 8. STRUCTURAL CI/TEST MECHANISM (requirement 8; proves R1-R4)

Delivered as pytest tests in the authoritative ci.yml path (+ drift), the repo's idiom:
- T1 (R1+R4): introspect/AST-assert every REGISTERED authoritative channel function requires an
  EffectivePermission parameter and does not accept/read the raw proxy fields for authoritative
  output. (Proves render-before-resolve is impossible + proxies stripped.)
- T2 (R2): assert the authoritative-channel registry is CLOSED -- enumerate authoritative
  writers (incl. the Markdown writer) and assert each is registered + EP-required; a bare
  authoritative-literal write outside a registered channel fails (defense-in-depth).
- T3 (R3 in-process): assert EffectivePermission is constructed only by the resolver (guarded
  constructor + AST import-boundary: no other module constructs it or imports the vocabulary).
- T4 (R3 cross-process + fail-closed): assert the persisted authoritative carrier carries only
  the resolved field, and each read-boundary validator fail-closes to UNAVAILABLE on
  absent/malformed/prior-session/stale/alternate-decision-field input.
Defense-in-depth (secondary): the AST import guard (s5) + a lexical action-vocabulary scanner.
These tests are the completeness proof: a NEW sink of an already-governed channel class cannot
emit authoritative action without an EP (T1), a new authoritative channel must register (T2),
no code can forge an EP (T3), and every channel fails closed (T4).

NO CLAIMS BEYOND SOURCE: this s13 specifies DESIGN INVARIANTS + the test mechanism; it does not
assert the code already implements them. Cited call sites (render_report:1464/output.py:293,
_write_markdown_report:2259 @ :417/:481/:1483, _build_and_finalize_contract:1488,
send_telegram:729, resolver convergence ~1136-1147/pre-1464) are verified against HEAD.

GOV-2 NEXT (s13): committed; ONE fresh Sol exact-head confirmation asks only whether R1-R4 are
closed (A-E of the owner charge). No second correction after that without Dustin's explicit
ruling.

# MATERIAL packet — Manual Manageability Lock (2026-08-14)

Compact upstream design packet for the next product slice. Dustin's product
direction is settled: when he cannot continuously monitor or manage a trade,
Cuttingboard must remain useful for observation but must not present a new trade
as actionable. Polygon GEX remains parked at its paid-data decision. This packet
does not authorize implementation and does not expand into broker automation.

## 1. PROBLEM / USER OUTCOME

Cuttingboard currently knows market conditions but not whether its operator can
safely manage a position. A valid setup may therefore appear actionable while
Dustin is at work or otherwise unable to monitor it. The required outcome is a
manual two-state lock which closes every action-bearing surface while preserving
market observations. This directly supports disciplined execution; it is not a
new trading signal.

## 2. CURRENT BOUNDARY

- Execution permission is derived from market/regime policy only. There is no
  operator-availability input.
- Daily decisions pass through `execution_policy` before contract, audit,
  payload, report, dashboard, and notification construction.
- Hourly/qualify-only notifications derive action titles, focus symbols, and
  triggers from the analytical `QualificationSummary`, independently of daily
  execution-policy decisions.
- The dashboard independently derives trade-permitting regime text and renders
  `A+ — ACTIONABLE`, `IF NOW`, action-accented `IN/OUT`, and `PLAY` content.
- The report/notification producer independently emits permission, bias,
  execution-posture, WATCH, and TRIGGERS language.
- Market Control Card permission is a closed seven-value vocabulary.
- No broker execution or position-management capability exists.

## 3. PROPOSED SEMANTIC

Introduce `CB_OPERATOR_AVAILABILITY` with exactly `AVAILABLE` and
`CANNOT_MONITOR` (trimmed, case-insensitive input; canonical uppercase value).
Resolve it exactly once at each runtime entrypoint and pass the frozen value
downstream; consumers never re-read the environment.

Recommended safety default: missing, empty, or invalid input resolves
`CANNOT_MONITOR`. Invalid input logs a variable-name-only warning and never the
raw value. Dustin explicitly initializes the local/GitHub repository variable
to `AVAILABLE` when active trading support is desired. There is no automatic
unlock, schedule, inference, or expiry.

Under `CANNOT_MONITOR`:

1. An otherwise allowed decision becomes `BLOCK_TRADE` at `EXECUTION_POLICY`
   with reason `operator_cannot_monitor`, zero size, and `policy_allowed=False`.
   A decision already blocked upstream retains its original block reason.
2. Market/qualification truth remains observationally unchanged. Contract
   `audit_summary.qualified_count` continues to mean pre-policy qualification;
   the run's existing post-policy/actionable count becomes zero; `top_trades`
   is empty and outcome is `NO_TRADE`.
3. Existing permission carriers use `No new trades permitted — operator cannot
   monitor.`; ASCII-only Telegram transport may project the dash as ` - `.
   System-halt permission continues to win.
4. Daily report and Telegram output retain market facts but omit permission-to-
   trade, executable bias/posture, WATCH/TRIGGERS, focus, READY, entry, and other
   candidate-action prompts. They include one operator-lock statement.
5. Hourly/qualify-only formatting receives a redacted copy/view with candidate
   lists removed; the original analytical summary remains available to existing
   artifacts. Titles/focus/triggers cannot name a candidate action. One lock
   statement is shown.
6. Dashboard retains symbols, grade, structure, price/level context,
   invalidation, reasoning, and watch observations. It replaces all permission
   and action vocabulary: no `Longs/Shorts/Momentum ... allowed`,
   `A+ — ACTIONABLE`, `IF NOW`, action-styled `IN/OUT`, or `PLAY`. It shows
   `OPERATOR LOCK — CANNOT MONITOR`, uses `A+ — OBSERVATION ONLY`, and renders
   levels/invalidation as neutral observation labels/styles.
7. Market Control Card admits the new permission string. No new schema key,
   schema version, persisted artifact, or analytical field is introduced.

## 4. AUTHORITY / CLASSIFICATION

MATERIAL under GOV-2 section 1: this creates a new execution-policy input and
crosses execution, contract projection, notification/reporting, dashboard, and
workflow layers. CLASS EXECUTION, LANE HIGH-RISK. Dustin retains every semantic
ruling, Gate A, repository-variable activation, and merge. Agents may prepare
the packet/PRD/reviews and, after Gate A only, implement and validate.

## 5. FILES / ESTIMATE

Production/workflow payload:

- `cuttingboard/config.py`
- `cuttingboard/execution_policy.py`
- `cuttingboard/runtime/__init__.py`
- `cuttingboard/output.py`
- `cuttingboard/market_control_card.py`
- `cuttingboard/delivery/dashboard_renderer.py`
- `.github/workflows/cuttingboard.yml`
- `.github/workflows/hourly_alert.yml`

Test payload may modify the matching existing config, execution-policy,
runtime-decision, output/notification, Market-Control-Card, dashboard-renderer,
and workflow-hygiene test files. Lifecycle and review artifacts are implicit.

Honest pre-Gate-A estimate: 260–340 added physical lines across the eight
production/workflow files, including closed-vocabulary validation, runtime
carrier plumbing, renderer/output suppression, and proof-support seams. Proposed
Gate-A ceiling: 380 additions-column lines; tests excluded; deletions never
offset additions. A ninth production/workflow file or >380 additions requires
GOV-2 section 5 renewal.

## 6. INVARIANTS / NEGATIVE BOUNDARY

- Market observations, qualification, grades, geometry, sizing inputs, regime,
  and data-provider truth do not change.
- No broker/order execution, position monitoring, automatic exit, portfolio
  state, new dependency, credential, service, database, secret, UI control,
  schema key/version, audit shape, or notification channel.
- No time/location/device/employment inference and no automatic state change.
- Existing halt/kill-switch precedence and notification dedup/audit semantics
  remain unchanged.
- `AVAILABLE` reproduces current behavior except for the intentional requirement
  that the variable be explicitly present; absence is locked, not compatible-
  open.

## 7. REQUIRED PROOF

- Tests first. Independently mutation-kill: missing/empty/invalid fail-closed;
  explicit AVAILABLE; invalid-value non-disclosure; exact-once resolution;
  policy predicate and upstream-block precedence; zero actionable output;
  qualification-count meanings; permission parity and halt precedence; daily,
  hourly, and qualify-only action suppression; Market Control Card vocabulary;
  every enumerated dashboard action phrase/style; both workflow relays.
- Prove locked candidate observations remain value-for-value and source objects
  are not mutated.
- Full focused/full pytest, ruff, YAML parse, registry validation, exact-head CI.
- Render and visually inspect locked and available A+ dashboards.
- Fresh-context PRD and implementation reviews plus a commissioned Sol
  second-model implementation artifact; one consolidated correction cycle and
  exact-corrected-head confirmation at each governed review stage.

## 8. RED / ROLLBACK

Stop for owner renewal if a ninth production/workflow file, >380 additions,
schema/artifact change, automatic inference, new secret/service/dependency,
analytical-truth change, or unenumerated action-bearing consumer is required.

Rollback is one repository-variable change to `CANNOT_MONITOR` (immediate
safe state) followed, if the implementation itself must be reverted, by the
normal owner-controlled PR revert. Never restore action by deleting the
variable because absence intentionally locks.

## 9. OWNER DESIGN-DIRECTION RULING REQUEST

KEEP the Manual Manageability Lock with the exact semantics above; ratify
fail-closed absence, the eight-file boundary, 260–340 estimate / proposed 380
ceiling, CLASS EXECUTION / HIGH-RISK / MATERIAL, and the commissioned Sol review.
After a review-clean packet, restart/reconcile PRD-304 from this authority,
obtain fresh independent PRD review, then return for explicit Gate A. No
implementation or repository-variable mutation occurs before those owner acts.

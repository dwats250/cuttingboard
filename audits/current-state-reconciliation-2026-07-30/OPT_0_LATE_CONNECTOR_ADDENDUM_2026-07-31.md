# OPT-0 Late Connector Addendum — 2026-07-31

```
STATUS: READ-ONLY SEAM-TRACE ADDENDUM
AUTHORIZES NO PRODUCTION IMPLEMENTATION
```

This append-only addendum supplements
`OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md` on PR #184.
It records three P2 findings that arrived after the original bounded correction
commit `6d27dbc`. Where this addendum conflicts with sections 9, 14, 17, 18,
21, or 22 of the original artifact, this addendum controls.

## Owner ruling

Dustin approved the corrected full-truth design on 2026-07-31:

- include premarket visibility;
- include an end-to-end runtime carrier test;
- explicitly authorize the bounded postmarket schema addition;
- allow up to seven production files, the evidence-required test files, and
  approximately 160 net production LOC;
- authorize no other schema, workflow, dependency, sizing-policy, threshold,
  provider, or unrelated change.

This resolves the former section-17 surface choice in favor of full truth.
It authorizes correction of the read-only evidence packet and PRD-278. It does
not itself authorize production implementation before PRD-278 review and
approval.

## Late finding 1 — premarket report

**Disposition: ACTIONED.**

`cuttingboard/runtime/__init__.py` builds the premarket report from the final
contract even when options sizing refuses every otherwise-qualified candidate.
`cuttingboard/reports/premarket.py::build_premarket_report` derives its focus
list from `trade_candidates` and does not consume `rejections[]`. Without a
change, an all-refused run can retain an empty focus list and omit
`SMALLEST_CONTRACT_EXCEEDS_BUDGET`; it may also preserve a broader tradability
signal that does not explain the terminal options-sizing refusal.

The full-truth production surface therefore adds:

- `cuttingboard/reports/premarket.py`

The asserting test surface adds:

- `tests/test_premarket_report.py`

Required behavior: a refusal-run premarket report must state the
`OPTIONS_SIZING` refusal and must not imply that the refused setup remains an
available focus trade.

## Late finding 2 — postmarket schema authorization

**Disposition: ACTIONED.**

The corrected trace proposed adding `OPTIONS_SIZING` to the exact-key
`rejection_breakdown` emitted by `build_postmarket_report`. Because
`tests/test_postmarket_report.py` pins that key set, this is a real output-schema
change, even though it is narrow and additive.

The prior statement that the full-truth design required "no schema change" is
withdrawn. The approved design authorizes exactly one bounded schema change:

- add `OPTIONS_SIZING` to the postmarket `rejection_breakdown` schema and its
  exact-key test.

No top-level contract key, payload section, artifact path, unrelated report
field, or other schema surface is authorized.

## Late finding 3 — runtime carrier integration

**Disposition: ACTIONED.**

The optional `refusals` out-parameter preserves the existing list return shape,
but its optionality creates a new silent-drop mutation: the sole production
caller could omit the argument, or runtime could fail to thread the populated
list into contract, audit, or presentation assembly while component tests still
pass.

The full-truth test surface therefore adds:

- `tests/test_runtime_decision.py`

At least one `_run_pipeline` integration test must generate a real
smallest-contract refusal through `build_option_setups` and assert the same
exact token reaches:

1. contract `rejections[]` with stage `OPTIONS_SIZING`;
2. the audit record;
3. the human-facing text report;
4. notification body;
5. HTML delivery;
6. premarket report; and
7. postmarket rejection aggregation.

A mutation that omits the out-parameter or drops any forwarding leg must turn
this integration test red.

## Corrected full-truth ceiling

### Production files — exactly seven

1. `cuttingboard/options.py`
2. `cuttingboard/runtime/__init__.py`
3. `cuttingboard/contract.py`
4. `cuttingboard/audit.py`
5. `cuttingboard/output.py`
6. `cuttingboard/reports/postmarket.py`
7. `cuttingboard/reports/premarket.py`

### Required test files — evidence-locked set

1. `tests/test_phase5.py`
2. `tests/test_contract.py`
3. `tests/test_audit.py`
4. `tests/test_postmarket_report.py`
5. `tests/test_premarket_report.py`
6. `tests/test_prd017_notification_stabilization.py`
7. `tests/test_prd267_alert_reason_coverage.py` only where its pinned fallback
   strings or branch assertions move
8. `tests/test_delivery.py`
9. `tests/test_runtime_decision.py`

The final asserting set remains subject to the PRD-158 pre-implementation grep
sweep. Removing a listed test file requires proof that another named test
exercises the same mutation-red seam. Adding any unlisted production file is a
stop-and-amend event.

### Size and change class

- production ceiling: approximately 160 net LOC;
- no dependency or workflow change;
- one explicitly authorized additive postmarket schema change only;
- no unrelated refactor.

## Corrected Gate A recommendation

> OPT-1 Gate A is approved for the seven-production-file full-truth design.
> Refuse at `cuttingboard/options.py::build_option_setups` when
> `risk_per_contract > 0` and the correlation-adjusted quantity is below one.
> Preserve the list return API and collect a minimal frozen refusal record via
> an optional `refusals` out-parameter. Use exact reason
> `SMALLEST_CONTRACT_EXCEEDS_BUDGET` and contract stage `OPTIONS_SIZING`.
> Thread the refusal through contract, audit, text report, notification body,
> HTML delivery, premarket report, and postmarket report. Add an end-to-end
> `_run_pipeline` test proving the same token reaches every required consumer.
> Explicitly authorize adding `OPTIONS_SIZING` to the postmarket
> `rejection_breakdown` exact-key schema; authorize no other schema change.
> Production FILES are exactly the seven paths listed above, with the
> evidence-required tests and an approximate 160-net-production-LOC ceiling.
> Any additional production file, broader schema change, workflow/dependency
> change, or unrelated behavior is a stop-and-amend event.

## Connector disposition summary

The three late P2 findings are all **ACTIONED** by this addendum. The original
five connector findings remain actioned by `6d27dbc`. The seam, reason token,
PRD-023-R2 preservation, positive-sizing contract, and refusal-vs-
`size_rounds_to_zero` distinction remain unchanged.

Held for Dustin. No production implementation is authorized by PR #184.
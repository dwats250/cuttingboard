> HISTORICAL EVIDENCE — IMPORTED OUT OF ORDER (2026-08-05): this packet's implementation (PRD-283, commit f806f5b2a0f6bccd7db67424ab4c2d5117454bb0, merged 2026-08-03) landed before the complete governed evidence chain was durably recorded. This import preserves the evidence; it does not rewrite authorization history. Source: PR #184 (closed as superseded by this import).

---

# OPT-0 Late Connector Addendum — 2026-07-31

```
STATUS: READ-ONLY SEAM-TRACE ADDENDUM
AUTHORIZES NO PRODUCTION IMPLEMENTATION
```

This append-only addendum supplements
`OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md` on PR #184.
It records connector findings that arrived after correction commit `6d27dbc`.
Where this addendum conflicts with sections 9, 14, 17, 18, 21, or 22 of the
original artifact, this addendum controls.

## Final owner ruling

Dustin approved the corrected full-truth design on 2026-07-31:

- refuse at options construction;
- preserve the list return API through an optional refusal out-parameter;
- use `SMALLEST_CONTRACT_EXCEEDS_BUDGET` and stage `OPTIONS_SIZING`;
- surface the refusal truthfully in contract, audit, text report,
  notification, HTML, premarket, postmarket, CLI, and dashboard;
- correct postmarket aggregate counts as well as its breakdown;
- suppress contradictory generic `no setups` / `no qualifying setups`
  wording when a sizing refusal is the actual cause;
- include an end-to-end runtime carrier test;
- authorize exactly nine production files, the evidence-required tests, and
  approximately 220 net production LOC;
- authorize exactly two bounded additive schema changes: the postmarket
  `rejection_breakdown` member and a dedicated audit refusal carrier;
- authorize no other schema, workflow, dependency, sizing-policy, threshold,
  provider, or unrelated change.

This resolves the former full-vs-reduced surface choice in favor of full truth.
It authorizes correction of the evidence packet and PRD-278. It does not itself
authorize production implementation before PRD-278 review and approval.

## Finding A — premarket report

**Disposition: ACTIONED.**

`build_premarket_report` derives its focus list from `trade_candidates` and does
not consume sizing rejections. The production surface includes
`cuttingboard/reports/premarket.py`; the test surface includes
`tests/test_premarket_report.py`.

Required behavior: an all-refused run states the `OPTIONS_SIZING` refusal and
does not imply the refused setup remains a tradable focus.

## Finding B — postmarket schema and aggregate truth

**Disposition: ACTIONED.**

Adding `OPTIONS_SIZING` to the exact-key `rejection_breakdown` is a real,
bounded output-schema change. It is explicitly authorized. In addition,
`trade_summary.rejected_count` must include options-sizing refusals; it may not
remain zero while the breakdown reports one sizing refusal.

Required production/test surface:

- `cuttingboard/reports/postmarket.py`
- `tests/test_postmarket_report.py`

Authorized schema change: add `OPTIONS_SIZING` to
`rejection_breakdown`. No unrelated postmarket key or top-level report change
is authorized.

## Finding C — runtime carrier integration

**Disposition: ACTIONED.**

The optional `refusals` out-parameter preserves the list return shape, but its
optionality creates a silent-drop mutation. The test surface includes
`tests/test_runtime_decision.py`.

At least one `_run_pipeline` integration test must generate a real refusal and
assert the same exact token reaches contract, audit, text report, notification,
HTML, premarket, postmarket, CLI, and dashboard. Omitting the out-parameter or
any forwarding leg must turn the test red.

## Finding D — CLI transport

**Disposition: ACTIONED.**

CLI delivery currently prints only the count of rejected entries. A bare
`REJECTED: 1` does not communicate the stable reason. The production surface
includes `cuttingboard/delivery/transport.py`. Existing delivery tests must pin
that an options-sizing refusal names the token or its stable plain-language
form in CLI output.

## Finding E — dashboard presentation

**Disposition: ACTIONED.**

The dashboard fallback can state `no qualified setups` when an otherwise-
qualified setup was refused later at options sizing. The production surface
includes `cuttingboard/delivery/dashboard_renderer.py`; the test surface
includes `tests/test_dashboard_renderer.py`.

Required behavior: the all-refused dashboard states the sizing refusal and
does not claim there were no qualified setups.

## Finding F — audit carrier schema

**Disposition: ACTIONED.**

The existing audit record has no truthful field for an options-layer refusal
plus its proving economics. Reusing qualification exclusions would
misattribute the layer; leaving null sizing would remain silent.

A second bounded additive schema change is explicitly authorized: add one
purpose-built audit refusal field or nested carrier containing symbol, strategy,
risk per contract, adjusted ceiling, risk modifier, stage, and exact reason.
The exact shape is implementation design space inside this envelope. No
existing audit field may be repurposed with false semantics, and no unrelated
audit schema change is authorized.

## Finding G — contradictory generic report reason

**Disposition: ACTIONED.**

Adding a refusal line is insufficient if the same report also states
`no qualifying setups`. When sizing refusals exist, the NO_TRADE report branch
must replace or suppress that generic reason. Tests must assert both presence
of the refusal and absence of the false generic wording.

## Corrected full-truth ceiling

### Production files — exactly nine

1. `cuttingboard/options.py`
2. `cuttingboard/runtime/__init__.py`
3. `cuttingboard/contract.py`
4. `cuttingboard/audit.py`
5. `cuttingboard/output.py`
6. `cuttingboard/reports/postmarket.py`
7. `cuttingboard/reports/premarket.py`
8. `cuttingboard/delivery/transport.py`
9. `cuttingboard/delivery/dashboard_renderer.py`

### Required test files — evidence-locked set

1. `tests/test_phase5.py`
2. `tests/test_contract.py`
3. `tests/test_audit.py`
4. `tests/test_postmarket_report.py`
5. `tests/test_premarket_report.py`
6. `tests/test_prd017_notification_stabilization.py`
7. `tests/test_prd267_alert_reason_coverage.py` only if its pinned fallback
   strings or branch assertions move
8. `tests/test_delivery.py`
9. `tests/test_runtime_decision.py`
10. `tests/test_dashboard_renderer.py`

The final asserting set remains subject to the PRD-158 pre-implementation grep
sweep. Removing a listed test requires proof that another named test exercises
the same mutation-red seam. Any unlisted production file is a stop-and-amend
event.

### Size and change class

- production ceiling: approximately 220 net LOC;
- no dependency or workflow change;
- exactly two bounded additive schema changes:
  1. postmarket `rejection_breakdown.OPTIONS_SIZING`;
  2. one dedicated audit refusal carrier;
- no unrelated refactor.

## Final Gate A recommendation

> OPT-1 Gate A is approved for the nine-production-file full-truth design.
> Refuse at `cuttingboard/options.py::build_option_setups` when
> `risk_per_contract > 0` and the correlation-adjusted quantity is below one.
> Preserve the list return API and collect a minimal frozen refusal record via
> an optional `refusals` out-parameter. Use exact reason
> `SMALLEST_CONTRACT_EXCEEDS_BUDGET` and stage `OPTIONS_SIZING`.
> Thread the refusal through contract, a purpose-built audit refusal carrier,
> text report, notification body, HTML delivery, premarket, postmarket, CLI,
> and dashboard. Correct postmarket `rejected_count`; suppress false generic
> `no setups` and `no qualifying setups` wording when sizing refusal is the
> cause. Add an end-to-end `_run_pipeline` test proving the same token reaches
> every required consumer. Explicitly authorize only the postmarket exact-key
> addition and the dedicated audit carrier as bounded schema changes.
> Production FILES are exactly the nine paths listed above, with the
> evidence-required tests and an approximate 220-net-production-LOC ceiling.
> Any additional production file, schema surface, workflow/dependency change,
> or unrelated behavior is a stop-and-amend event.

## Connector disposition summary

All connector findings through this addendum are **ACTIONED**. The seam, reason
token, PRD-023-R2 preservation, positive-sizing contract, and refusal-vs-
`size_rounds_to_zero` distinction remain unchanged. What changed is the
complete consumer inventory, the truthful aggregate requirements, and explicit
schema authorization.

Held for Dustin. No production implementation is authorized by PR #184.
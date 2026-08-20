# GEX-1 MATERIAL Packet — Event 1 Codex Review (durable record)

- **Event type:** INITIAL PACKET REVIEW
- **Reviewer:** Codex, fresh-context independent reviewer
- **Reviewed commit:** `70475f2bdd0bd7dd51525ba08a304b0f5add87a5`
- **Date:** 2026-08-20
- **Verdict:** DESIGN INCOMPLETE
- **Context:** Fresh, read-only, independent (not the packet author or same-session implementer)
- **Findings and recommendations:** verbatim Codex stdout supplied by Dustin, reproduced below without paraphrase or weakening

This file is the durable Event-1 evidence artifact required by
`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §2. The consolidated
single-cycle author correction that answers these findings is recorded in the
CORRECTION CYCLE section of
`audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.md`.
Event 2 (independent confirmation of the exact corrected head) is a separate
GOV-2 §7 step and is not represented here.

---

## Verbatim Codex stdout

```
REVIEWED COMMIT: 70475f2bdd0bd7dd51525ba08a304b0f5add87a5

VERDICT: DESIGN INCOMPLETE (material boundary omission)

REQUIRED FINDINGS:

1. **Packet §§0 and 5 — the consumer-enumeration MATERIAL leg is misstated, and the human consumer is omitted from the lifecycle.** GOV-2 §1 fires when work “claims to enumerate all consumers,” including when the claimed set is empty. Section 5 expressly labels itself a “complete artifact lifecycle,” declares “Readers today: none,” enumerates non-consumers, and provides a falsifier for that negative; therefore §0’s statement that this leg does not fire is wrong. More importantly, `docs/sidecar_doctrine.md` says the human reader is a valid observation-sidecar consumer, while this design says “Human inspection only” but proposes an artifact-map row with `Consumers: (none)`. The decisive current-tree searches do confirm no machine consumer: `rg -ni 'gex|gamma' cuttingboard/` exited 1; the current non-audit tree has no `gex_snapshot`/`logs/gex_snapshot.json` reader; and no `cuttingboard` module imports from `tools/`. Correct the intake to record the consumer-enumeration leg and identify Dustin/manual local inspection as the initial human consumer, while separately stating that there are no machine readers.

2. **Packet §1 — the reviewed commit does not contain the governing Cboe evidence it claims is repository truth.** At reviewed HEAD, `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md` does not exist, merge commit `ed87913` is not an ancestor of HEAD, and the checked-out workplan still says GEX-0 is `EVIDENCE INCOMPLETE`. `origin/main` contains the evidence packet and changes that row to the scoped Cboe `PROVIDER VIABLE` verdict, but the packet branch has not incorporated that canonical state. The packet’s assertion that the dependency is satisfied “so … observed feed facts … are repository truth” is therefore not true of the SHA under review. Incorporate current `main`, reconcile the workplan/decision state, and make the evidence packet available at the corrected reviewed head.

3. **Packet §4 D4/D6 — the eligible-input domain is materially incomplete.** The design requires only “present numeric” `gamma` and `open_interest`, while asserting call contributions are always nonnegative and put contributions always nonpositive. That guarantee fails for negative, non-finite, or boolean values; permissive Python JSON handling can also propagate `NaN` into a non-standard artifact. The packet likewise does not specify a positive finite `current_price`, validate the OCC expiry as a real calendar date, or state that only parsed roots `SPX` and `SPXW` are eligible. An unexpected parseable root would enter totals while having no declared `coverage.per_root` representation. Define finite, non-boolean, domain-valid inputs; a positive finite spot; valid calendar dates; and an explicit root allowlist. For every invalid class, specify fail-loud versus excluded-and-counted behavior, add coverage reason keys where applicable, and require a red mutation.

4. **Packet §4 D4a/D5 and R23 — the timestamp contract and test fixture do not match the observed provider shape.** The committed Cboe evidence records the actual top-level timestamp as a naïve text value such as `"2026-08-17 18:42:35"`, whose UTC meaning was established by comparison with the response headers. The design and R23 instead use `"2026-08-18T01:00Z"`. An implementation accepting only ISO-8601-with-`Z` could pass R23 and fail on the real feed. Specify parsing of the provider’s exact `YYYY-MM-DD HH:MM:SS` shape as UTC, normalization of `feed_timestamp_utc` to an unambiguous timezone-aware representation, fail-loud behavior for malformed timestamps, and an ET-boundary fixture using the actual provider format—for example `"2026-08-18 01:00:00"` interpreted as UTC.

5. **Packet §4 D4a/D5 — unavailable structural-output JSON shapes are ambiguous.** `call_wall`, `put_wall`, and `dominant_gamma` are each described as “`null` + `reason`,” but a JSON field cannot simultaneously be null and contain a reason, and no sibling reason-field names are declared. `zero_dte.share = null with a reason` is also not given an exact object shape. Freeze one representable schema—such as an always-present object with explicit `value`/metric and `reason`, or a nullable metric plus separately named reason field—and add tests for no calls, no puts, fully cancelling net strikes, and a zero 0DTE denominator. R1’s general happy-path type check does not resolve these unavailable shapes.

6. **Packet §4 D5 — the provenance claim is incomplete and partly misclassified.** The schema says `provenance` classifies every output, but its lists omit `schema_version`, `fetched_at_utc`, `data_delay`, `units`, `contract_multiplier`, and the unavailable reasons. It classifies all `coverage` counts as OBSERVED even though included/excluded, per-root, zero-value, and expiration-summary counts are producer-derived transformations. `source` and `endpoint` are configured producer constants rather than provider observations, and the `~15 min` delay is REPORTED evidence rather than observed in the artifact. Define provenance for every emitted field, adding CONFIGURED/REPORTED classes if necessary, and preserve the distinction between observed per-contract inputs, derived coverage/aggregates, and the inferred dealer-position interpretation.

7. **Packet §6 — several planned tests are proxies and do not kill every named mutation.** R7 tests only missing spot although the requirement also covers missing options and timestamp. R14 guarantees only that the OI winner differs from the call-GEX winner, so its named “select by net GEX” mutation can survive unless the fixture also makes the net winner different. R17’s “known signed-net peak” does not require a negative-magnitude winner larger than the maximum positive value or different from the call-side winner, so max-signed and call-only mutants can survive. R19 does not require mixed call/put contributions, so signed and absolute numerators can coincide. R23 uses a timestamp shape the provider did not supply. R12 should freeze an exhaustive forbidden raw-row key/container guard rather than demonstrate only `bid`/`ask`. Add the validation fixtures and red mutations required by findings 3–6 and make each named mutant discriminated by construction.

RECOMMENDED:

1. In the review charge, replace `rg -niE "gex|gamma" cuttingboard/` with `rg -ni 'gex|gamma' cuttingboard/`. With ripgrep, `-E` selects an encoding and the supplied command fails with `unknown encoding: gex|gamma`; the corrected command exited 1 as expected.

2. Give `roots` its own D5 schema row. The table says all top-level keys are listed, but currently combines `underlying` and `roots` in one row.

3. Use `python3 tools/validate_prd_registry.py --skip-commit-resolvability` consistently in §11. The `python` command is unavailable in this review environment, while the `python3` form passed. `git diff --check` also passed, and the working tree remained unchanged.

4. Consider naming the field `dominant_net_gamma` or embedding an equally explicit fixed label. The current computation is sound and distinct from the walls, but “dominant gamma” alone is easier for a future reader to mistake for unsigned provider gamma.

RATIONALE: The core design direction is appropriately small: one `_SPX` fetch, one new gitignored artifact, no provider abstraction or fallback, no consumer/cadence/pipeline import, an internally consistent `gamma × OI × 100 × spot² × 0.01` computation, deterministic call/put walls and net dominant strike, an honest date-only AM-SPX/PM-SPXW split, null-on-zero 0DTE share, and gamma flip correctly deferred. The FILES cone remains plausible and the 420-production-LOC ceiling is credible, subject to re-estimation after the omitted validation behavior is specified. The packet is not review-clean because its exact authority state, input admissibility, timestamp parsing, unavailable schema, provenance map, and several mutation-discriminating fixtures are not yet fully defined.
```

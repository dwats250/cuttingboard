# NS-4B — GOV-2 Event-1 INITIAL PACKET REVIEW — durable record

**Event type:** `INITIAL PACKET REVIEW` (GOV-2 §2 step 3; owner-commissioned by
Dustin, 2026-08-22).
**Reviewer identity / capability role:** independent Codex packet review
(`codex-cli 0.147.0`, model `gpt-5.6-sol`), fresh context, read-only.
**Reviewed commit SHA / packet revision:** `6e5f1767999fcf12169ea939238f4035c044664f`
— packet `NS4B_MOVEMENT_HEATMAP_MATERIAL_PACKET_v0.2.md` (reviewed as v0.2). Code
baseline: parent `80ac6eb2618eb419afff6764292dec5c838204ce` (intervening commits
changed only the packet).
**Review date:** 2026-08-22.
**Fresh-context / independence / run-isolation evidence:** invoked as
`codex exec -s read-only -c model_reasoning_effort=high` with the review prompt
piped via stdin; sandbox `read-only` (no repo write access); a separate Codex
session (id `01a0287e-...`) with no access to the Claude authoring context. Codex
wrote nothing to the repo; this record is transcribed by Claude Code from the
captured stdout.
**Reasoning effort:** high.
**Verdict:** `FINDINGS` — 3 BOUNDARY + 2 P1 + 1 P2; no rubber-stamp. Confirmed
targets: T-2, T-3, T-5, T-8, the zero-machine-reader claim, and O-1.

---

## Findings (verbatim substance)

- **[F1] BOUNDARY — publish seam mis-cited (falsifies T-1 / §6).** Packet §6 ends
  at `reports/output/dashboard.html`, which is only the renderer default output.
  The production publish seam is: hourly CI renders `--output ui/dashboard.html`,
  copies `ui/index.html`, runs readiness, commits/pushes `ui/` to the `publish`
  branch, and Pages deploys `ui/`. Evidence: `dashboard_renderer.py:56-62`;
  `.github/workflows/hourly_alert.yml:152-198`; `.github/workflows/pages.yml:30-38`.
  Disposition: replace §6 with the actual seam + workflow/publish ownership
  boundary.

- **[F2] BOUNDARY — artifact-only renderer cannot guarantee full-12 order/
  population (falsifies T-4/T-7/T-10 / R1-R2).** The writer serializes with
  `sort_keys=True`, so the on-disk `symbols` object is alphabetical and registry
  insertion order is unrecoverable; a pure artifact reader also has no explicit
  population/order/identity/completeness contract. Evidence:
  `universe_registry.py:50-65`; `watchlist_sidecar.py:68-83`;
  `runtime/__init__.py:2513-2519`; packet v0.2:272-283. Disposition: add an
  explicit artifact-level population + order + row-identity + completeness
  contract (or revise the full-12 claim); test against the actually serialized
  order.

- **[F3] BOUNDARY — validation/admission seam omitted; divergent quote ages real
  (falsifies T-1/T-6 / §3.1, Q-Freshness).** The sidecar receives all
  `normalized_quotes`, but validation separates `valid_quotes` from invalid
  non-HALT quotes; and `fetched_at_utc` is assigned before provider retries with
  no last-trade timestamp read, so a structurally valid snapshot can carry
  validation-invalid values and unconstrained, divergent exchange-observation
  ages. Evidence: `ingestion.py:293-327`, `:346-370`; `validation.py:93-108`,
  `:132-145`, `:177-200`; `runtime/__init__.py:549-552`, `:778-786`. Disposition:
  reconcile `normalized_quotes` vs `validation_summary.valid_quotes`; obtain an
  explicit design ruling on whether fetched-but-validation-invalid /
  unknown-age values may be shown as live; revise freshness + FILES/materiality
  if the ruling expands the carrier.

- **[F4] P1 — D-7 open but disconnected from the reader contract (falsifies
  T-4 / D-7).** Proposed validation does not state which `schema_version` /
  `source` is accepted, there is no identity/version mutation, and "additive
  compatibility" alone cannot decide how the first reader treats old v1 rows
  lacking the two new fields. Evidence: `watchlist_sidecar.py:79-83`;
  `gex_card.py:108-127`; packet v0.2:260-277. Disposition: make D-7 an acceptance
  matrix (current v1, proposed shape, unknown version, wrong source, missing new
  fields) bound to validation and discriminating tests. Zero-current-machine-
  reader claim remains confirmed.

- **[F5] P1 — suppression/mutation plan not killable as written (falsifies
  T-7/T-10).** M8/M9 demand byte-identical baselines but §10 permits substring-
  only checks; M11/M12 allow alternative outcomes rather than one falsifiable
  contract; M12's "explicit skip" contradicts full-12 visibility; M13's
  renderer-with-no-file case cannot detect a new daily writer call. Evidence:
  packet v0.2:397-408; `tests/test_dashboard_renderer.py:4496-4508`;
  `tests/test_watchlist_sidecar.py:239-271`. Disposition: close M11/M12 to exact
  outcomes; whole-output equality for absent + each invalid class; add
  incomplete/full-population + serialized-order cases; give M13 a cadence/
  call-site assertion that reddens on a daily writer.

- **[F6] P2 — FILES/LOC incomplete (falsifies T-9/T-11 / §§8-9).** Repository
  precedent places run-local/not-restored/not-staged guarantees in
  `tests/test_ci_artifact_hygiene.py` (absent from FILES); the ceiling also
  excludes the population/order, identity/version, admission, and publish-seam
  work exposed above. Evidence: `tests/test_ci_artifact_hygiene.py:760-780`;
  packet v0.2:342-362, :369-380. Disposition: add the artifact-hygiene asserting
  surface; re-estimate FILES/LOC after F1-F5; keep helper extraction open with
  "clearer/testable" separated from "smaller."

## Per-target disposition (Codex)

```
T-1 = [F1],[F3]      T-2 = CONFIRMED (12 enabled; 10 intersect ALL_SYMBOLS; UCO+GOOG absent)
T-3 = CONFIRMED (decimal (last-prev_close)/prev_close; x100 matches trend/macro)
T-4 = [F2],[F4]      T-5 = CONFIRMED (fetch wall-clock / run clock, not exchange ts)
T-6 = [F3]           T-7 = [F2],[F5]      T-8 = CONFIRMED (hourly-only; daily no write; gitignored)
T-9 = [F6]           T-10 = [F2],[F5]     T-11 = [F6]
```

Also confirmed: zero-machine-reader claim (only producer/writer/path surfaces;
renderer's existing `watchlist` access is the unrelated overnight-scan section);
O-1 (flow map "11-tuple" vs live 12).

## Independent verification by the authoring agent (before correction)

Every finding re-checked against `main`-base code at `6e5f176`: F1 output path
`dashboard_renderer.py:58` + hourly `--output ui/dashboard.html`
(`hourly_alert.yml:159-163`); F2 `sort_keys=True` in `_write_watchlist_snapshot`;
F3 `_write_watchlist_snapshot(normalized_quotes=normalized_quotes)` (`:784`) vs
`valid_quotes` used for regime/derived/structure (`:570/:588/:599`), with
`trend_structure` using the identical `normalized_quotes` input (`:770`); F6
`test_ci_artifact_hygiene.py` GEX pattern present. All CONFIRMED. The single
consolidated correction (GOV-2 §2 step 4) is applied in packet v0.3; the
CORRECTION CYCLE section of the packet records the per-finding dispositions.

# Cuttingboard — D5 live commissioning and GEX reference integration

2026-09-05 · PRODUCT / VISUAL INTEGRATION DESIGN · provisional implementation brief.

Runtime exposed: GPT-6. **OWNER-ATTESTED UI SEAT: GPT-6 Astra / High; runtime detail not exposed.** Parent context inherited; factual recon delegated to three GPT-5.6 Luna agents. No implementation, PR, dispatch, provider contact, or repository modification occurred. This file is an owner-reviewable design, not an implementation commission or a claim of independent review.

## 1. EXECUTIVE DECISION

**D5 is already on the normal published board. Build no D5 deployment wiring.**
Add one compact, native **GEX REFERENCE · SYNTHETIC EXAMPLE** disclosure at the DETAILS boundary, immediately after WATCHING and before the existing DETAILS / HISTORY disclosure.
Opening it reveals one frozen synthetic SPX example using the existing GEX card numbers, structural profile, SVG ladder and accessible table.
Keep the current TAPE availability row and current GEX artifact admission/suppression unchanged.
Use a separate reference carrier and typed entry point; never relabel an old production snapshot, spoof its clock, or give a synthetic example a provider identity.
Make reference identity visible in the collapsed label, expanded heading, ladder label and accessibility text.
Teach the existing structural vocabulary with a short reading guide; do not calculate relationships with today's market or make predictions.
No provider work, decision changes, new dashboard architecture, corpus browser, or new acquisition path belongs in this slice.

## 2. CURRENT REALITY

Canonical remote main was checked directly: **`9b46802ab9935162c5c16df1d1f96606be1ead1c`**. All source references below are at that SHA. A bare snapshot lives at `/tmp/cuttingboard-gex-reference-plan/canonical.git`; the older local checkout and its dirty generated files were not used as canonical evidence.

Local state: branch `claude/prd-234-manual-check-prominence`, HEAD `d58f3364047392a6b6261aa7ea05d77f0e38157c`; cached origin/main `45910ffda55ecab940b07504a0283c317801af23`. Remote inspection, rather than a fetch into this checkout, established current main.

**Publication is observed, not merely inferred from wiring.** [Live pipeline run 33954319542](https://github.com/dwats250/cuttingboard/actions/runs/33954319542), created 2026-09-05 08:05:35 UTC at the D5 SHA, completed live execution, verification, artifact commit and push successfully. [Pages run 33954366607](https://github.com/dwats250/cuttingboard/actions/runs/33954366607), created 08:06:38 UTC, succeeded. Publish head was `3338049e18c6d167323410031edd5a8942b36930`. The served [normal board](https://dwats250.github.io/cuttingboard/) matched BOTH publish HTML artifacts byte for byte, SHA256 `c4899677132af26c0ca9d0706727c6d54044b10b34507294849ccd75c99569c3`. Saved evidence: `published-index.html` beside this brief. This proves the published D5 output; it does not claim its market observations are current or prove a Cloudflare-triggered session.

The established daily path checks out main (`.github/workflows/cuttingboard.yml:108-116`), runs `python3 -m cuttingboard.delivery.dashboard_renderer --output ui/dashboard.html` (`:570`), then `cp ui/dashboard.html ui/index.html` (`:571`) before approved artifact commit/push. The hourly workflow uses the same renderer with hourly payload/run/map inputs (`hourly_alert.yml:205-210`). `pages.yml:23-38` checks out publish and deploys ui. Future merged renderer changes naturally ride the next successful eligible publish.

Existing GEX capability:

- `cuttingboard/delivery/gex_card.py:334-383`: current-artifact validation and immutable display model. Exact schema/source/delay identity; finite numeric domain; aware timestamp; maximum age 24h; maximum future skew 5m; anchor and profile reconciliation.
- `gex_card.py:104-157,257-331`: provider-neutral structural profile; 31 half-open 25-point bins, coverage, outside mass and raw-strike anchors. This is **SPX/SPXW structure**, not SPY.
- `gex_card.py:484-635`: shared ladder geometry, grayscale SVG, own spot rail, accessible full-bin table and structural disclosures.
- `gex_card.py:638-699`: card wrapper and freshness-preserving `render_fragment`. The current wrapper hardcodes Cboe/as-of wording and `#gex-context`; reference must not reuse that wrapper unchanged.
- `dashboard_renderer.py:3150-3162`: TAPE states GEX unavailable when no current card is admitted. `:3567-3575`: the current detail card is conditionally emitted inside DETAILS / HISTORY.
- No production reference/demo GEX path exists. `tests/test_gex_card.py::_rich` (`:493-517`) supplies a fully synthetic, structurally rich test scenario. The ordinary preview catalog has no GEX reference case.
- Current workflows do not acquire GEX; the sanctioned adapter remains dormant. No change to acquisition is required.

**Sanity pass:** (1) D5 needs no code or additional publish now; it is served. (2) There is reusable test geometry, but no existing production reference presentation satisfying this objective. (3) The decisive misleading shortcut would be pairing this synthetic SPX ladder with today's SPY price or timestamp as if they were contemporaneous observations. (4) Reference can remain entirely inside delivery and change no decisions. (5) Existing numeric/profile/ladder helpers can be reused; only reference admission, labeling and a small dashboard insertion are new.

## 3. PRODUCT MODEL

The operator continues to use the existing D5 board. TAPE's GEX field remains the authority for the availability of its current GEX context. Below all WATCHING content, a compact disclosure makes the learning instrument discoverable without expanding DETAILS / HISTORY first:

```text
GEX REFERENCE · SYNTHETIC EXAMPLE  ▸
Learning context only · current availability is shown in TAPE
```

The second line belongs to the always-visible summary area. Opening it shows:

```text
REFERENCE — SYNTHETIC SPX EXAMPLE
Scenario: spx-structure-v1 · Observation date: none (synthetic)
Source: Cuttingboard deterministic test scenario; no market feed

[existing modeled-magnitude rows and structural ladder]
REFERENCE · SYNTHETIC SPX — example spot 7,747.71
```

The existing `_rich` scenario supplies the example spot; all numbers remain frozen with that scenario. No fake market date is assigned. It is a teaching reference, not an empirical benchmark. There is one example and no scenario selector, live/reference toggle, saved preference, autoplay or time series. A native disclosure is the explicit choice to view reference context. It never switches the board's data source.

Keep a short guide, at most about 100 words, visible below the ladder:

> Read the example's spot against the distribution of modeled call and put magnitudes. The net tick is call minus put under the configured convention; it does not measure dealer positioning. In TAPE, separately note volatility, rates, DXY and regime; use NEXT EVENT for event timing and SPY SESSION for its own price context. Those observations do not update this example. Watch how the cockpit changes over successive sessions, without treating this frozen structure as an explanation of today's move. SPX strikes are not SPY price levels.

This slice teaches how to read structure alongside the cockpit. It cannot demonstrate historical gamma/macro co-movement because it contains no matched observed series. Do not suggest otherwise. Preserve existing detailed methodology, expiry and bin caveats with the component; do not add a textbook or new causal commentary engine.

## 4. GEX STATE CONTRACT

Current-artifact state and reference availability are **independent**, not a fallback chain. Changing or removing a current artifact must never change the reference's values, provenance or identity.

| State | Current surface | Reference surface |
|---|---|---|
| CURRENT, legitimately sanctioned and admitted | Preserve the existing current TAPE/card path, actual observation/source/delay labels and freshness checks. No claim of zero-delay live data. Acquisition or re-enablement is outside this slice. | Remains separately labeled and explicitly opened; never replaces the current card. Test coexistence offline. |
| UNAVAILABLE, intentional absence | Preserve TAPE `unavailable`; current detail card absent. No warning rail, retry instruction, credential request or setup call to action. | Frozen example remains available. Expanded copy explains that current acquisition is intentionally dormant in this release. |
| REFERENCE | Never populates TAPE or `#gex-context`; never counts as available current input. | Separate `#gex-reference`, `data-gex-kind="reference"`, scenario identity, synthetic provenance, no observation date and own example spot. |
| STALE current artifact | Existing suppression remains: TAPE unavailable, no current card. No new diagnostic taxonomy is required in the cockpit. | Same separately loaded example as before; stale artifact is never its input. No new label saying the stale artifact became reference. |
| INVALID current artifact | Preserve current fail-safe behavior. Malformed core/contradictory valid profile suppresses card; existing malformed/absent-profile-only suppression still permits an otherwise valid core card. | Independent reference remains unchanged. Do not infer a reference from rejected content. |
| INVALID or missing bundled reference | Current path unaffected. | Keep the labeled disclosure, show `Reference example unavailable.` and no numbers/ladder. No fallback to logs, provider, network or another fixture. Build validation must catch this before merge. |

Production freshness and provenance controls are not generalized into a permissive `mode`, `allow_stale` or `skip_validation` flag. This slice adds no new current-data capability. The dormant-release explanation must not claim that an admitted future current card is absent; when testing coexistence, omit that explanatory absence sentence and retain the generic summary above.

## 5. REFERENCE DATA PROVENANCE

Use **one frozen synthetic example**, derived mechanically from `tests/test_gex_card.py::_rich` and its `_coherent` numeric construction at the pinned main SHA. That helper deliberately spans the 31-bin window, includes near-balanced and unequal magnitudes, outside mass and a spot between strikes. It is suitable for demonstrating existing geometry; no new GEX calculation is proposed.

Add `cuttingboard/delivery/data/gex_reference_v1.json` as a bundled reference-only resource. It contains a distinct envelope: `reference_schema_version: 1`, `kind: "synthetic_reference"`, `scenario_id: "spx-structure-v1"`, `instrument: "SPX"`, `observation_date: null`, authoring basis SHA and helper path, a plain synthetic-source description, and the frozen numeric inputs needed by existing profile/card helpers. It must NOT contain production identity fields `schema_version`, `source`, `data_delay`, `fetched_at_utc` or production lineage/readiness identifiers. Human-readable source text belongs in reference provenance fields. Record the final resource digest in test evidence.

Use a separate immutable `GexReference` presentation type and `build_reference` / `render_reference_fragment` entry points in `cuttingboard/delivery/gex_reference.py`. Only this module reads the bundled resource; it has no caller-supplied path, clock, network, environment-selected source or `gex_snapshot` input. Strictly validate the reference envelope, expected scenario/instrument, finite numeric domain, coherent aggregates/anchors and a complete reconciled profile. Reject production snapshots even when numerically valid. The reference envelope must also be rejected by existing current admission.

Reuse existing numeric validation/profile math in `gex_card.py` through minimal pure helper factoring. Reuse metric formatting, profile, table and ladder geometry. Keep current `build_gex_card(snapshot, now=...)` and `render_fragment(snapshot, now=...)` signatures, clock checks and exact observable output intact. A reference adapter must not call current admission with fabricated Cboe metadata or `now` set to the fixture timestamp. Reference rendering has its own typed wrapper; neither a default live label nor the current wrapper is a permissible fallback.

Do not import test modules in production. Freeze their synthetic numeric result into the distinct resource during implementation. Do not use `_base` as provenance: its comment claims sample lineage. Do not copy `logs/gex_snapshot.json`, old published snapshots, undocumented samples or unverified historical captures. A future observed historical reference would need a separately approved provenance decision; it is not included here.

## 6. VISUAL INTEGRATION

Insert exactly one native `<details id="gex-reference">` after the closing `#watching-zone` at `dashboard_renderer.py:3559` and before the existing `#details-history` at `:3563`. Treat it as the first disclosure in the DETAILS area, not a seventh operating zone. The order remains VERDICT → TAPE → SPY SESSION → NEXT EVENT → WATCHING → DETAILS. Do not change any existing zone markup, WATCHING panel, or DETAILS / HISTORY internals.

Collapsed by default on desktop and phone; no numbers appear until explicitly opened. Use the current mono font, muted label text, neutral hairlines and native disclosure arrow. No green/red directional badges, amber error treatment, new palette, typography, shadow, rounded tile or header promotion. Reuse existing styles; any necessary CSS is scoped inside `#gex-reference`, leaving `_CSS` unchanged if possible.

Expanded order: reference heading → provenance → existing compact metric rows → shared grayscale ladder with visible synthetic identity → existing coverage/anchor/methodology disclosures and accessible table → short reading guide. Keep all data legible in ordinary document flow. A reference SVG must include reference/synthetic wording in its visible label and accessible name, so a ladder crop or screen-reader navigation does not lose its identity. Do not copy the current `as of … Cboe ~15m delayed` footer. Use distinct reference DOM IDs and scoped styles; coexistence must not duplicate IDs or bleed styles.

Retain existing responsive SVG width/max-width and geometry. Keep a single-column flow at every viewport; this is not a new desktop side panel. At 390×844 and 360×780, labels wrap, values remain legible, summaries have at least 44px touch height, and the accessible table uses the existing contained overflow behavior. No page-level overflow or `overflow:hidden` clipping. Keyboard Enter/Space opens the native disclosure; focus is visible; no hover-only content. No JavaScript, external requests, persistent selection or automatic opening is added.

Placing this outside `#details-history` preserves its legacy region oracle and avoids hiding the example two disclosures deep. Keeping it after WATCHING prevents competition with primary operating information.

## 7. IMPLEMENTATION BOUNDARY

**ESTIMATED SURFACE — NOT YET APPROVED.** These are exact proposed filenames, not an issued FILES ceiling.

| File | Permitted purpose in the future charge |
|---|---|
| `cuttingboard/delivery/dashboard_renderer.py` | Import/reference emission at the one DETAILS-boundary seam; no new arithmetic, live input plumbing, global state or CLI option. |
| `cuttingboard/delivery/gex_card.py` | Minimal pure numeric/presentation helper factoring for reuse; current entry points and rendered bytes unchanged. Reference-specific SVG labeling may use an explicit presentation argument whose current default is byte-identical. No admission bypass. |
| `cuttingboard/delivery/gex_reference.py` (new) | Bundled carrier load/validation, immutable reference type and separately labeled reference wrapper. |
| `cuttingboard/delivery/data/gex_reference_v1.json` (new) | One frozen synthetic resource with explicit provenance. |
| `tests/test_gex_reference.py` (new) | Carrier separation, frozen values, malformed/missing reference, label integrity, two-clock independence and semantic-isolation tests. |
| `tests/test_gex_card.py` | Add unchanged-current-output and cross-carrier rejection guards; retain existing suppression, profile and SVG assertions. |
| `tests/test_dashboard_renderer.py` | Reference integration/coexistence, exact unchanged decision regions and narrowly extended AST allowlist for the new delivery-only consumer; retain current absent/stale/invalid equality. |
| `tests/test_dashboard_d2_seam.py` | Only reviewed below-seam hash updates for the intentional sibling insertion; upper-region assertions unchanged. |
| `tests/data/dashboard_pre_gex_golden.html` and `tests/data/dashboard_pre_a1c_chart_golden.html` | Regenerate through renderer, review in dedicated oracle update; absent/stale/invalid current inputs must still produce identical output including the independent reference. |
| `docs/CALL_SITE_MAP.md` and `docs/SCHEMA_MAP.md` | Small factual reference-carrier/consumer entries during authorized documentation closeout; no duplicate architecture document. |

**Must remain untouched:** `tests/data/setup_chart_legacy_oracle.json`; D5 workspace and MANUAL CHECK tests except new tests elsewhere; current GEX producer/adapter and their tests; `tools/gex_snapshot.py`, `tools/gex_allaccess_adapter.py`; all workflows and Cloudflare code/config; runtime, contract/types, payload, decision, execution, qualification, ranking, primary selection, sizing, alerts, readiness, regime and publish-coherence modules; `delivery/setup_chart.py`; `ui/styles.css`, `ui/app.js`; generated `ui/dashboard.html`, `ui/index.html`, `logs/*`, `reports/*`; dependency manifests/locks. Generated UI updates belong only to the existing publish workflow.

No new browser framework, generator CLI or packaging change is estimated. Use the existing Python/browser environment for acceptance evidence outside the repository. If loading the bundled resource in the established runtime requires additional production files, stop for a revised ceiling.

The proposed production ceiling meets GOV-2 materiality; `dashboard_renderer.py` is protected and forces HIGH-RISK. This brief stops before downstream authorization. Reuse the existing bounded review/PRD process, with no new governance machinery. PRD-332's exception was expressly PRD-332-only. Future governance bookkeeping is separate from the production list and must be explicitly named by Helm. The injected registry gap for `PRD-332.impl-review.claude.md` must be resolved by the authorized documentation owner before saving a new PRD; no such save or registry edit occurs here.

## 8. ACCEPTANCE MATRIX

All checks below are required future implementation evidence; **none were executed in this DESIGN turn**.

| Case | Deterministic acceptance |
|---|---|
| Missing / stale / schema-invalid current artifact × valid reference | Current fragment remains empty; TAPE unavailable; the three whole-dashboard outputs remain equal under the same frozen clock. Identical reference resource/provenance/values in each. |
| Frozen valid current fixture × valid reference | Existing current fragment byte-identical to pinned baseline; separate reference fragment present; no duplicate IDs; current TAPE derives only from current fixture. No synthetic values outside reference subtree. |
| Carrier crossing | Pass complete reference envelope to current admission: rejected. Pass fresh, stale and invalid production snapshots to reference admission: rejected. Renaming kind or removing required provenance rejects; no fallback. |
| Reference clock isolation | Render same reference at two widely separated dates and with different current SPY/macro inputs: reference bytes/values unchanged. Current expiry behavior still follows its real injected clock. |
| Invalid reference | Missing resource, malformed JSON, wrong kind/instrument/scenario, boolean/NaN/nonfinite numbers, aggregate/anchor contradictions: no reference numeric card; explicit reference-unavailable copy; no network or current-artifact fallback; current path unchanged. |
| Semantic isolation | Across TRADE, NO_TRADE, HALT, mixed lineage, locked, zero/single/multiple setups and low-tier-primary fixtures, changing reference data/availability leaves verdict, permission, grades, ordering, primary/chart slot, sizing, alerts, readiness, regime, payload/run/contract inputs and WATCHING bytes unchanged. Test deep input immutability and prohibit upstream imports/consumers with a narrow dependency guard. |
| Geometry and language | Existing profile/ladder tests stay green: 31 bins, boundary ties, actual example spot, outside mass, grayscale, table parity. Reference SVG/heading/accessibility label say synthetic/reference; no current timestamp, Cboe feed claim, dealer-position assertion, SPY overlay, support/resistance/magnet/pin/prediction language. |
| Legacy oracles | `setup_chart_legacy_oracle.json`, current GEX fragments, D5 upper/WATCHING and existing DETAILS region stay unchanged. Only intentional full-document/below-seam insertion changes are rebaselined; no removed or weakened assertions. |
| Browser / phone | Chromium at 1280×960, 390×844 and 360×780 with asserted device-metric innerWidth. Check default, reference open, full-bin table open, every disclosure open, each setup selected and SPY LEVELS toggled. scrollWidth ≤ innerWidth; no clipped labels/numbers; MANUAL CHECK position unchanged; native keyboard operation and ≥44px summaries; exactly the pre-existing one script; no new requests/errors. |
| Operator usefulness | At 390px default, reference is discoverable at the DETAILS boundary and current TAPE remains clear. One activation exposes ladder and provenance. A capture containing just the ladder retains synthetic identity. An unfamiliar reader can distinguish example spot from SPY SESSION and cannot reasonably read the example as today's dealer positioning. Fable reviews captured evidence. |

Mutation evidence must demonstrate that routing the reference into current TAPE, laundering a stale artifact, dropping synthetic labeling, using today's SPY spot, or weakening current freshness makes a discriminating guard fail. Keep existing GEX producer and adapter tests green without editing them. Rebaseline goldens through the renderer, never by hand.

Validation order from the standing contract: targeted tests → ruff → `python tools/validate_prd_registry.py` → full suite; also `git diff --check`. Use the repository venv and required CI evidence at the exact implementation SHA. Do not bypass an unexplained failure or treat local green as CI proof. Browser PNGs plus metrics JSON should identify the exact head and fixture.

## 9. COMMISSIONING PLAN

**A. D5 on normal published output — already complete as observed here.** Use the normal board URL above. No dispatch, deploy, branch change or code is needed to achieve this objective now. A later refresh should use the established `cuttingboard.yml` dispatch with `mode: live` under an operational charge; do not hand-render committed UI files. The workflow's other inputs include slot and source; do not invent a slot for a simple refresh or assume live execution is notification-free.

**B. Reference GEX — future bounded implementation.** Dustin accepts or corrects this decision; the existing required material review/owner gates establish implementation authority. Opus then implements only the approved boundary, supplies deterministic/browser evidence and obtains required fresh-context review. After Dustin authorizes the merge through the permitted merge actor, the next successful normal main pipeline renders the bundled reference automatically. Verify the actual new main SHA, successful render/verify/push, publish artifact equality, Pages success and served reference labels/values. No workflow edit or GEX producer execution is required. A manual normal refresh, if desired, needs its own operational authorization; this brief does not issue one.

**C. Tuesday live Cloudflare/A1 proof — separate, still unproved.** The observed successful run was a manual dispatch; it does not prove Cloudflare scheduling. Recon found no Tuesday-specific acceptance document to quote. For the owner's Tuesday window (2026-09-08), use the separately authorized live-proof charge: record the actual Cloudflare scheduled event and slot, its matching GitHub execution identity, actual A1 producer observation/session/as-of/lineage, the rendered SPY SESSION consuming that observation, verification and artifact commit, then Pages deployment and served output. Compare the observed chain against the existing CF/A1 contracts, including their timing/session rules. Dispatch acceptance alone, a successful unrelated run, a fixture chart or an old published image is insufficient. No Worker/PAT setup, schedule change or evidence fabrication is authorized here. Lack of that Tuesday proof does not undo today's verified D5 publication and is not a reason to wire GEX acquisition.

## 10. SCOPE KILLERS / STOP CONDITIONS

- A current-artifact guard must be relaxed, a fake timestamp/source introduced, or stale/invalid production content used to populate reference.
- Any reference dependency reaches an upstream decision, TAPE current value, contract/payload, alert, readiness or publish-coherence path; any semantic invariant changes.
- A sanctioned fixture cannot be traced to the pinned synthetic helper, or the frozen numbers fail existing numeric/profile reconciliation. Do not substitute an old market capture.
- Shared rendering requires a second geometry implementation or changes the existing current fragment/geometry. Narrow the factoring first; if impossible, return to Helm.
- The chosen insertion requires changing existing D5 zones, WATCHING behavior, DETAILS internals or the immutable legacy chart oracle. Stop instead of reopening D5.
- Actual implementation needs an out-of-ceiling file, dependency, acquisition, provider policy, dormant adapter or Cloudflare/workflow change.
- A required test or browser check fails without an explained in-scope fix, or a reviewer finds reference/live ambiguity that the bounded design cannot remove.
- Implementation is attempted without the applicable reviewed Basis and Dustin's explicit Gate A. The registry gap blocks new PRD saving until repaired by its authorized owner; it does not block this temporary design artifact or invalidate the observed D5 publish.

No product choice remains open as a menu. The pending owner decision is whether to adopt this one bounded reference slice and authorize its existing review/implementation sequence.

## 11. OPUS 4.8 HANDOFF

**Draft charge for Dustin to issue only after the required gates; not issued by this brief.**

> MODE: IMPLEMENT. SEAT: Opus 4.8. Basis: this exact brief adopted by Dustin, the resulting review-clean design/PRD and explicit Gate A. Verify actual current origin/main at startup; recon basis is 9b46802ab9935162c5c16df1d1f96606be1ead1c. Objective: expose one bundled synthetic SPX reference at the DETAILS boundary, using existing GEX numerics/profile/ladder, without changing D5 or current GEX admission. D5 is already published; add no commissioning code. FILES: only the filenames in section 7 as explicitly approved at Gate A, plus specifically named required governance files. Implement the separate reference envelope/type/entry point, minimal pure shared helpers, unmistakable labels, native disclosure and deterministic tests. Keep current entry points/output, TAPE, all decision semantics, legacy region/chart oracles and acquisition unchanged. Execute section 8 validation and attach exact-head browser evidence; regenerate only the named test goldens. Stop on section 10. Return actual changed files, SHA, test/CI evidence, browser artifacts and independent review disposition to Helm. No merge, auto-merge, main push, live dispatch or provider action is authorized by this charge text.

## 12. FABLE 5.1 REVIEW HANDOFF

**Draft fresh-context review charge for separate commissioning.**

> MODE: REVIEW, read-only. SEAT: Fable 5.1. Start independently of the authoring/implementation session; attest actual seat, exact reviewed implementation SHA, fresh-context/run isolation and evidence provenance. Read this owner-adopted brief, applicable Basis and code/tests/browser evidence at that SHA. Attempt to falsify: (1) reference/live identity remains clear collapsed, expanded, screen-reader and cropped-ladder views; (2) no semantic or current-TAPE leakage; (3) stale current data cannot become reference; (4) frozen SPX example is useful without implying current SPY or historical co-movement; (5) D5 hierarchy, palette, mobile behavior and MANUAL CHECK visibility remain intact; (6) scope contains no acquisition, extra corpus, workflow changes or new decision behavior. Check the original current freshness tests and exact fragment/region oracles, not only newly rebaselined goldens. Review the implementation, not another review's prose. Return one findings pass using the repository Review Failure Taxonomy, severity, exact file:line and human-surface impact as INERT/DEGRADED where applicable. State unverified browser claims explicitly. Do not edit, merge, broaden scope or declare owner gates satisfied. This review does not inherit PRD-332's one-off waiver or substitute for any separately required GOV-2 event.

Design work stops here. CHECKPOINT.md preserves recon; this brief preserves the decision and handoff. Repository and stashes remain untouched.

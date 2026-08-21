# GEX-2 -- Free-path display-only GEX board card: MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET -- 2026-08-21 -- DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO CONSUMER BUILD, NO CADENCE,
NO GATE A, NO MERGE.
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 (independent Codex review) NOT YET RUN.
This packet is NOT review-clean and carries NO downstream authority until it
passes Event 1 (independent review), the ONE consolidated correction, and
Event 2 (exact-corrected-head confirmation). Ceilings below are ESTIMATES
(GOV-2 sec5), not constraints.
```

> This is the upstream MATERIAL design packet GOV-2 requires before any GEX-2
> PRD, decision entry establishing design direction, or implementation
> authority. It defines the smallest doctrine-compliant, FREE-path,
> display-only GEX board card so Dustin can issue a design-direction ruling
> from a review-clean packet. Nothing here is buildable authority.
>
> Sequence position: **provisional packet (this revision)** -> Event-1
> independent Codex review -> ONE consolidated author correction -> Event-2
> exact-corrected-head confirmation -> Dustin design-direction ruling ->
> Stage-0 PRD -> fresh-context PRD review -> Gate A -> implementation ->
> implementation review -> Dustin merge.
>
> This packet is a FRESH frame from current `main`. It does NOT continue,
> amend, rebase, or repair the frozen historical PR #261 packet
> (`audits/gex-2-material-packet-2026-08/...`, branch
> `worktree-gex-2-material-packet`, head `acced04`). PR #261 and the
> provider-evidence PRs #262/#263 are read-only historical evidence. Reusable
> truths retained and stale assumptions discarded from that work are
> enumerated in sec12.

---

## sec0 -- Intake classification (GOV-2 sec1)

**MATERIAL -- owner-directed at intake.** The commissioning owner card
classifies GEX-2 MATERIAL at intake ("Treat GEX-2 as MATERIAL at intake.
Reasons include the dashboard renderer / presentation seam and the prior
GEX-2 material history. Follow GOV-2. Do not attempt to classify this
downward merely to move faster."). Independently of that direction, GOV-2
sec1 legs fire on the merits:

- **Shared carrier / seam across pipeline layers (fires).** The card is added
  to `cuttingboard/delivery/dashboard_renderer.py` -- the single dashboard
  renderer that also feeds `ui/dashboard.html` -> `ui/index.html` ->
  the `publish` branch -> GitHub Pages (PRD-194). That renderer and publish
  carrier are shared across delivery/presentation and the published-site
  layer. Selecting that seam is a sec1 trigger.

- **Adds a presentation path to a persisted schema surface that then has more
  than one reader (fires).** `logs/gex_snapshot.json` today has exactly one
  reader class: **HUMAN -- Dustin, manual local inspection** (GEX-1 /
  PRD-306; `docs/artifact_flow_map.md` "machine consumers: none"). This slice
  makes `cuttingboard/delivery/dashboard_renderer.py` (via a new
  `cuttingboard/delivery/gex_card.py`) the **first machine reader / presentation
  path** of that schema surface. Adding a presentation path to a persisted
  schema surface that then has more than one reader is a sec1 trigger.

- **Establishes a production FILES and LOC ceiling (fires).** sec7 and sec8
  propose the production FILES cone and net-LOC ceiling for the
  implementation -- itself a sec1 trigger.

- **Consumer enumeration (fires).** sec5 claims to enumerate ALL consumers of
  `logs/gex_snapshot.json` and of the new presentation model after this
  change, enumerates non-consumers, and states falsifiers. GOV-2 sec1 fires
  on the enumeration claim itself.

Legs that do NOT fire: no governance guardrail change; no Critical/High
finding resolution; no contract/audit/payload/notification schema is added,
removed, renamed, or changed (the card reads an existing sidecar artifact and
writes nothing). MATERIAL classification does not convert this STANDARD-shaped
consumer slice into HIGH-RISK; the lane is decided by the normal matrix at PRD
time with MICRO disqualified by materiality (GOV-2 sec1). See sec9 Q1 for the
STANDARD-vs-HIGH-RISK question the frozen PR #261 answered "HIGH-RISK"; it is
Dustin's to rule.

---

## sec1 -- Authority (charge-template mirror)

- Operator ruling (design direction): **NONE YET.** This packet exists to
  earn one. Prior GEX ruling: `docs/DECISIONS.md` 2026-08-20 "GEX-1 DESIGN
  DIRECTION APPROVED" (producer only; consumer explicitly deferred to GEX-2).
- Governing plan: `docs/plans/decision-support-expansion-doctrine-v0.1.md`
  (G1-G10; sec4.4 GEX-2).
- Workplan packet: `docs/plans/decision-support-workplan-v0.1.md` sec8 "GEX-2 --
  Display consumer" (state today: `EVIDENCE BLOCKED`, gated behind GEX-1).
- Governing PRD: **READ-ONLY / NO PRD** (a Stage-0 PRD is drafted only AFTER
  Dustin's design-direction ruling on this review-clean packet).
- Related evidence (read-only):
  - `audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.md`
    (the producer design this card consumes; review-clean at `33f753f`).
  - `docs/prd_history/PRD-306.md` + `docs/prd_history/PRD-307.md` (the
    frozen producer contract R1-R43).
  - `tools/gex_snapshot.py` (the producer as built; the artifact schema).
  - Frozen PR #261 packet (historical): reusable/discarded lessons in sec12.
- Precedence on conflict: `VISION.md` -> `CLAUDE.md` / `docs/PRD_PROCESS.md`
  -> expansion doctrine -> dated operator decision -> active PRD -> this work
  charge. If two higher authorities conflict, STOP and report; do not choose.

---

## sec2 -- Objective

Add ONE compact, display-only, fully-removable GEX context card to the
existing Cuttingboard dashboard that reads the existing
`logs/gex_snapshot.json` sidecar, renders it when present-valid-fresh,
suppresses to byte-identical baseline when it is missing, invalid, or stale,
and never touches any decision surface -- built on the FREE Cboe path with no
new provider, no producer schema change, no new cadence, and no new board.

---

## sec3 -- Work type and preflight (charge-template mirror)

- Mode: DOCS-ONLY (this packet). The downstream implementation is a separate
  CONSUMER build, authorized only post-ruling + post-Gate-A.
- Mutation permission (this packet): create the packet directory
  `audits/gex-2-free-board-card-2026-08/` and its files, plus the GOV-2
  review-cycle records. No source, contract, or `main` mutation.
- Merge permission: NONE.

Preflight (recorded at packet authoring):

1. Repository: `dwats250/cuttingboard`.
2. Branch: `claude/gex-2-free-card-material-packet` (design/docs branch;
   GOV-2 sec4 permits a docs branch to carry the CARD/packet with NO
   implementation authority).
3. Starting `main`: `2b6dcc2068b5350ad7d422d10938a832206dd4bb` (confirmed
   `HEAD == origin/main` at session start; the expected starting main in the
   owner card).
4. Working tree at branch creation: clean (generated `logs/*` + `ui/` drift
   stashed to `stash@{0}` before branching).
5. Authority files read: GOV-2 (full); expansion doctrine (full); workplan
   (full); charge template (full); sidecar doctrine (full); artifact flow map
   (full); `tools/gex_snapshot.py` (schema + docstring); renderer seam recon
   (`cuttingboard/delivery/dashboard_renderer.py`); frozen PR #261 packet
   (evidence).

Decisive negatives re-run by the packet author directly (Author discipline
sec4; not delegated):

- `rg -ni 'gex|gamma' cuttingboard/` -> **exit 1 (no match).** No
  `cuttingboard/` module -- the renderer included, since it lives at
  `cuttingboard/delivery/dashboard_renderer.py` -- references GEX or gamma
  today. The card is a greenfield addition.
- `git ls-files --error-unmatch logs/gex_snapshot.json` -> **exit 1 (not
  tracked).** `git ls-tree origin/main -- logs/gex_snapshot.json` -> empty.
  `git check-ignore -v logs/gex_snapshot.json` -> **ignored by `.gitignore:49
  logs/`.** No workflow force-adds it. (Load-bearing; see D10.)
- No non-test module imports `tools.gex_snapshot`; the only tree reference is
  the `docs/artifact_flow_map.md` documentation row.

---

## sec4 -- Design: the consumer card

### D1. Placement -- a new pure module `cuttingboard/delivery/gex_card.py`

All GEX logic lives in ONE new module co-located with the renderer:
`cuttingboard/delivery/gex_card.py`. It is a pure loader + presentation model
+ fragment builder. `cuttingboard/delivery/dashboard_renderer.py` imports it,
calls it once, and either emits the returned HTML string or emits nothing.
Rationale:

- Keeps the renderer a formatter: no GEX arithmetic, no GEX validation, no GEX
  vocabulary in `dashboard_renderer.py` (honors the sidecar doctrine "dashboard
  as consumer, not computation engine"). The card's distance/freshness
  arithmetic is display geometry of the same kind the renderer already performs
  for surface ages (`dashboard_renderer.py:359` `age = now - dt`), but it is
  isolated in `gex_card.py` for a clean, independent test surface.
- One module = one testable unit for the pure loader, the pure model builder
  (clock injected), and the pure fragment builder.
- Isolation mirror of the producer: `gex_card.py` imports no `cuttingboard`
  decision module and is imported only by the renderer (sec5 enumerates and
  sec6 R-guards this).

Public surface (names indicative; the PRD pins them):

- `load_gex_snapshot(path) -> dict | None` -- soft loader mirroring
  `dashboard_renderer._load_trend_structure_snapshot` (`:953-965`): existence
  check; narrow `except (json.JSONDecodeError, OSError, UnicodeDecodeError)`;
  `isinstance(data, dict)` guard; returns `None` on any miss. NEVER raises
  (must not model on `_load_json_optional` `:935-941`, which raises on
  malformed JSON).
- `build_gex_card(snapshot, *, now) -> GexCard | None` -- pure. Validates
  schema identity, field domains, dominant-anchor presence, and staleness
  against the injected `now`; computes display-only distances and the
  freshness label; returns an immutable presentation model, or `None` to
  suppress. `now` is injected (no hidden clock).
- `render_gex_card_html(card) -> str` -- pure. Formats the model to a compact
  HTML fragment. Returns `""` for `None`/suppressed.
- One convenience `render_fragment(snapshot, *, now) -> str` composing the
  three, so the renderer's only new logic is `w(frag)` guarded by `if frag:`.

### D2. Card contents -- exact fields consumed and the mockup

Consumed from `logs/gex_snapshot.json` (exact dotted key paths, verified
against `tools/gex_snapshot.py:_build_artifact` `:339-360` and the live
sample `logs/gex_snapshot.json`):

| Card line | Artifact source (exact) | Presentation |
|---|---|---|
| Net | `gex_total_1pct_usd` (float, signed) | `/1e9`, one decimal, `$B`, sign kept; footnote-marked |
| Dominant | `dominant_net_gamma.strike` (+ computed distance) | strike (int if integer-valued) + distance% |
| Call wall | `call_wall.strike` (+ computed distance) | strike + distance% |
| Put wall | `put_wall.strike` (+ computed distance) | strike + distance% |
| 0DTE | `zero_dte.share` (float in [0,1] or null) | `*100`, one decimal, `%` |
| freshness | `fetched_at_utc` (our capture clock) + `data_delay` | absolute ET capture time + static delayed-source disclosure (D4) |
| spot (basis for distances) | `spot.value` (float > 0) | not necessarily shown; used to compute distances |
| provider label | `source` (= `cboe_delayed_quotes`) | short "Cboe (delayed)" style label |

Target compact mockup (final styling follows the dashboard's own idiom, D8):

```
GEX  (context only)
Net         -$56.3B *
Dominant     7640    -0.02%
Call wall    8000    +4.70%
Put wall     8000    +4.70%
0DTE          7.6%
as of 16:41 ET . Cboe ~15m delayed source
* net is signed under a configured positioning assumption; positioning is
  not measured.
```

CUT from the card (kept out by design; test-bound in sec6): gross wall
dollars; raw dominant magnitude; full-precision net; any per-strike table;
expiration/coverage/provenance/roots dumps; the endpoint URL; max pain;
vanna; charm; flow/CVD; dealer-position claims; and ALL interpretive labels
(AT SPOT, MAGNET, PIN, SUPPORT, RESISTANCE, SHORT/LONG-GAMMA REGIME, "tracks
spot", "dealers are short gamma", regime badges, any predictive phrasing).
See D9.

### D3. Distance-from-spot -- presentation geometry, not analytics

The artifact does NOT emit any distance field (verified: the wall/dominant
objects carry exactly `{strike, gex_1pct_usd, reason}`; the consumer must
compute distance). The card computes, for each of dominant/call/put:

```
distance_pct = (strike / spot.value - 1.0) * 100.0
```

display-only, two decimals, sign kept. This is pure geometry of two
producer-emitted numbers; it invents no market claim, threshold, state,
regime, inference, support/resistance, or signal. It is never compared to a
bound or used to gate anything. Guards: `strike` may be `null` when the wall
is unavailable (D5); `spot.value` is producer-guaranteed `> 0` and finite, but
the builder re-checks `> 0` and suppresses the whole card if violated (fail
loud on a malformed spot, never divide-by-zero).

### D4. Freshness / recency semantics -- our capture clock, no session claim

Recency is reported from **`fetched_at_utc`** -- the producer's own wall-clock
at fetch time (`tools/gex_snapshot.py:_require_aware(now)` `:156-159`), i.e.
"when this snapshot was captured." The card:

- displays an **absolute** capture time converted to ET (America/New_York,
  the dashboard's display tz), plus a **static** "Cboe ~15m delayed source"
  disclosure derived from the fact of `data_delay` (the internal REPORTED
  token string is not quoted verbatim on the card);
- makes **no** market-session or liveness claim, and does **NOT** display a
  relative "X min ago" on the card. Rationale: the published page is static
  between renders; a relative age computed at render time silently becomes
  false as the page ages (the owner card: "Do not imply that fetch time is
  the exact calculation age of every source Greek"; "Do not invent a precise
  Greek-age guarantee"). An absolute capture timestamp does not decay.
- does **NOT** bind freshness on `feed_timestamp_utc` (the feed's
  self-reported publish clock) or on `zero_dte.observation_trading_date` or
  `is_market_open` (a market-session gate). This explicitly rejects the frozen
  PR #261 freshness clock (E1-002) and the circular session gate (H-1); see
  sec12.

Staleness suppression (D5) is a separate, real-time elapsed check on
`fetched_at_utc` vs the injected render `now`; it is honest capture-age, not a
feed-derived session inference, so it is non-circular. The exact "as of"
format and whether to additionally show a relative age are sec9 Q3.

### D5. Suppression / staleness contract -- the failure behavior

The card renders ONLY when ALL hold; otherwise the renderer emits NOTHING for
the GEX section (true omission, not a placeholder row):

Hard suppression (card absent):
- file missing, unreadable, or not valid JSON, or top-level not a dict
  (loader returns `None`);
- `schema_version != 1` (semantic-identity guard: never render a schema the
  card was not written against);
- any card-required key absent or wrong-typed (`gex_total_1pct_usd`,
  `spot.value`, `fetched_at_utc`, and the wall/dominant/`zero_dte` objects);
- `spot.value` not finite or not `> 0`;
- `dominant_net_gamma.strike is null` (anchor unavailable -- reason
  `all_net_gamma_zero`): the card has no anchor row, so the whole card is
  suppressed;
- **stale**: `fetched_at_utc` older than `STALE_MAX` before the injected
  render `now`. Provisional default `STALE_MAX = 24h` (sec9 Q3 -- the single
  tunable knob; a generous default avoids the frozen work's H-1
  over-suppression while still hiding a genuinely multi-day-old snapshot).

Row-level typed-unavailable (card renders; that row omitted only):
- `call_wall.strike is null` (reason `no_eligible_calls` /
  `no_nonzero_call_gex`) -> omit the Call wall row;
- `put_wall.strike is null` (reason `no_eligible_puts` /
  `no_nonzero_put_gex`) -> omit the Put wall row;
- `zero_dte.share is null` (reason `zero_abs_gex_denominator`) -> omit the
  0DTE row. NOTE honest zero: `zero_dte.share == 0.0` with `reason: null` is a
  real 0.0% and IS shown (G6 honest absence: null is absent, 0.0 is present).

Malformed / out-of-domain values are treated as INVALID -> suppress; they are
never coerced to a neutral value, zero, or a generic label (G6).

### D6. Baseline-neutrality -- byte-identical golden

When the card is suppressed for ANY reason, `render_dashboard_html(...)` must
return output **byte-identical** to the pre-GEX baseline. The card insertion
is purely additive and fully removed on suppression (no empty wrapper div, no
stray whitespace, no CSS-only diff that survives suppression). The test oracle
is an INDEPENDENT pre-feature golden captured from the parent commit's
renderer output over a fixed fixture, committed as a test asset -- not a
same-run "None vs default None" comparison (which shares accidental
whitespace/CSS and is insufficient; frozen finding E1-007). See sec6 R1.

### D7. Renderer seam -- thread-and-emit, purity preserved

Exact seam in `cuttingboard/delivery/dashboard_renderer.py` (line anchors are
current-main and will be re-pinned by the PRD):

1. Add a path constant beside the sidecar block (`:55-60`):
   `_GEX_SNAPSHOT_PATH = Path("logs/gex_snapshot.json")`.
2. In `main()`, beside the trend-structure load (`:3391-3392`), auto-discover
   from `--logs-dir` (NO new CLI flag; mirrors the trend-structure sidecar):
   `gex_snapshot = gex_card.load_gex_snapshot(logs_dir / _GEX_SNAPSHOT_PATH.name)`.
3. Thread `gex_snapshot` through `write_dashboard(...)` (add kw param beside
   `:3214`) into `render_dashboard_html(...)` (add keyword-only param beside
   `:2066`), plus the render `now` the renderer already resolves (the clock
   used by the freshness helpers, e.g. `:488`).
4. At the chosen body position emit:
   `frag = gex_card.render_fragment(gex_snapshot, now=now)` then
   `if frag: w(frag)` -- no `else` branch, so suppression is true omission
   (mirrors the full-suppress precedent the renderer already uses for the
   alert-watchlist block).
5. Add the card's CSS rules into the module-level `_CSS` string (`:757-916`),
   reusing `.block` and the mobile-reflow idiom (D8). `disabled_class` is
   reused for per-run dimming consistency.

No GEX arithmetic, validation, or vocabulary is added to
`dashboard_renderer.py` beyond the load-and-emit wiring and the CSS.

### D8. Mobile layout -- genuinely usable on a phone

The card follows the dashboard's existing compact idioms (verified in `_CSS`
`:757-916`): the page is width-capped at `.wrap{max-width:640px}`; compact
cards either use a `<table>` with inline `display:block;overflow-x:auto` plus
a `@media(max-width:640px)` per-row flex reflow (the `.ts-table` pattern,
`:894-915`), or a label/value grid with `overflow-x:hidden` (the macro-tape
pattern, `:805-807`). The GEX card uses a small label/value layout (the
mockup in D2) so it never requires horizontal scrolling on a phone. No new
design system is introduced.

### D9. Context-only invariant and forbidden vocabulary

The card informs the board and never authorizes a trade. It must NOT become a
required payload section, contract field, coherent-publish requirement,
readiness marker, notification field, or audit requirement (sec5 proves each
non-coupling). The rendered fragment must contain NONE of the forbidden
tokens/labels in D2's CUT list (predictive, regime, pin/magnet,
support/resistance, "dealers are short gamma", short/long-gamma regime). The
only interpretive text is the sign-assumption footnote, which HEDGES rather
than claims: the net sign is "signed under a configured positioning
assumption; positioning is not measured" (matching
`tools/gex_snapshot.py:SIGN_CONVENTION` `:50-53`, which is classified
`provenance.inferred` and explicitly "not measured"). The producer never
labels negative net as "short gamma"; neither does the card.

### D10. Realizability and the carrier gap (frozen E1-001) -- stated honestly

**Load-bearing, and the headline for the design-direction ruling.**
`logs/gex_snapshot.json` is gitignored (`.gitignore:49 logs/`), not tracked,
and not on `main`; no workflow invokes `tools/gex_snapshot.py` (cadence is the
deferred GEX-3) and none force-adds the artifact. Consequences, stated per the
Realizability check (Author discipline sec3) and G6:

- On the **CI-published public board** (rendered from a clean checkout, where
  the GEX producer never runs), the artifact is **always absent**, so the card
  **always suppresses** and the published board stays byte-identical baseline.
  This is correct fail-soft behavior, not a defect.
- The card renders **only where a fresh `logs/gex_snapshot.json` exists** --
  i.e. a local/manual render after Dustin runs the producer by hand. That is
  exactly the owner's LIVE SMOKE TEST path ("obtain a free GEX snapshot
  through the existing free path; render the normal board; open the normal
  board on mobile").
- Therefore this slice delivers the **capability**: the board can show the GEX
  card, and does wherever a fresh snapshot is present. **Public-board
  visibility awaits the later free-cadence slice (GEX-3)** -- consistent with
  the owner's "Cadence/automation is NOT part of this slice ... A later
  free-cadence slice can follow after the card works." This packet designs NO
  carrier and changes NO workflow (honoring the owner boundary and G4).

This is the deliberate divergence from frozen PR #261, which escalated to a
producer-schema field + a cadence carrier slice specifically to force
current-session liveness on the public board NOW. The owner's free-first
direction defers that. sec9 Q2 is the explicit ruling this requires.

### D11. Producer truth-correction (frozen E1-003) -- one-line, non-functional

`tools/gex_snapshot.py:8` currently asserts the artifact has "no machine
consumer". Once the renderer reads it, that clause is false (docs-must-match-
code, VISION). The minimal honest correction is a ONE-LINE docstring edit
(e.g. "one optional observe-only renderer consumer; still no decision
authority (baseline-neutral)"), and the equivalent update to the
`docs/artifact_flow_map.md` gex_snapshot consumer row (G5). This is NOT a
functional or schema producer change. Because the owner card cautions against
touching the producer, this is surfaced as sec9 Q4: accept the one-line
docstring correction, or restrict the correction to `artifact_flow_map.md`
plus a docstring rewording the owner prefers. The producer file appears in
sec7 FILES flagged docstring-only-if-accepted.

---

## sec5 -- Seam trace (complete artifact lifecycle)

**`logs/gex_snapshot.json` consumers AFTER this change (claimed complete):**

1. HUMAN -- Dustin, manual local inspection (unchanged; GEX-1).
2. MACHINE -- `cuttingboard/delivery/dashboard_renderer.py`, via
   `cuttingboard/delivery/gex_card.py`, read-only, observe-only, suppressible.
   This is the FIRST and ONLY machine reader.

No other reader. Falsifier (re-run by the author, sec3): `rg -ni 'gex|gamma'
cuttingboard/` exits 1 today; after the change the only matches are the new
module and the renderer wiring. No `cuttingboard` decision module imports
`gex_card` or reads the artifact.

**`cuttingboard/delivery/gex_card.py` consumers (claimed complete):** exactly
one -- `dashboard_renderer.py`. Not imported by any decision module.

**Decision-path non-coupling (each asserted; sec6 R-guards):**

- The pipeline output contract, payload, run summary, market_map, audit,
  evaluation, and notifications are neither read nor written by the card.
- Qualification, regime, TRADE/NO_TRADE/HALT, setup grade, position size /
  risk budget, contract selection, and notification eligibility are untouched
  (G2). The card sits strictly downstream of the contract, on the renderer
  side, reading a separate sidecar artifact.
- Readiness / coherent-publish: the card adds NO new readiness marker and is
  NOT part of `validate_coherent_publish`'s hardcoded triple. The coupling to
  AVOID (adding a GEX readiness marker) is explicitly forbidden and
  R-guarded.
- Baseline-neutrality: with the artifact absent/invalid/stale, the entire
  rendered dashboard is byte-identical to the pre-GEX baseline (D6, R1).

**Publish carrier (unchanged):** renderer `--output ui/dashboard.html` ->
`cp ui/index.html` -> `tools/ci_push_artifacts.sh` -> `publish` branch ->
Pages (PRD-194). No workflow file is modified by this slice.

---

## sec6 -- Requirements and discriminating tests (design-stage; binds the PRD, not the tree)

Each requirement names an observable behavior, the test that asserts it, and
the mutation that must turn that test red. Tests assert resolved behavior at
the authoritative seam (the rendered fragment / full-document output and the
pure model), never a proxy or the presence of prose.

| # | Requirement (observable) | Test | Mutation that must turn it RED |
|---|---|---|---|
| R1 | Artifact absent -> card suppressed; full document byte-identical to the committed pre-GEX golden | `test_gex_absent_baseline_identical` (renderer, golden asset) | Emit an empty GEX wrapper div / placeholder on absence |
| R2 | Malformed JSON / non-dict -> suppressed (loader None) | `test_gex_malformed_suppressed` | Broaden loader to accept / to raise |
| R3 | `schema_version != 1` -> suppressed | `test_gex_wrong_schema_suppressed` | Drop the schema-version identity check |
| R4 | Required key missing/wrong-type -> suppressed | `test_gex_missing_key_suppressed` | Skip a required-field validation |
| R5 | `spot.value` <= 0 / non-finite -> suppressed (no div-by-zero) | `test_gex_bad_spot_suppressed` | Remove the spot-domain guard |
| R6 | `fetched_at_utc` older than STALE_MAX vs injected now -> suppressed | `test_gex_stale_suppressed` | Remove the staleness check |
| R7 | Fresh valid artifact -> Net/Dominant/Call/Put/0DTE rendered with exact values | `test_gex_valid_render_values` | Read a wrong key / wrong scale |
| R8 | Distance% = `(strike/spot-1)*100`, correct sign+magnitude | `test_gex_distance_math` | Flip the sign / drop the `-1` |
| R9 | `dominant_net_gamma.strike` null -> WHOLE card suppressed | `test_gex_dominant_null_suppressed` | Render the card without the anchor |
| R10 | Call/Put/0DTE unavailable (reason token) -> that row omitted only, rest renders | `test_gex_row_typed_unavailable` | Render null as "None"/0/"-" |
| R11 | `zero_dte.share == 0.0`, reason null -> honest 0.0% shown | `test_gex_zero_dte_honest_zero` | Treat 0.0 as unavailable and omit |
| R12 | Freshness uses `fetched_at_utc` capture clock; no relative "ago"; no session/liveness claim | `test_gex_freshness_source_and_wording` | Bind freshness on `feed_timestamp_utc` / add a session gate |
| R13 | Rendered fragment contains NONE of the forbidden vocabulary/labels (D9) | `test_gex_no_forbidden_vocabulary` | Add any pin/magnet/support/regime/short-gamma label |
| R14 | Sign-assumption footnote present; Net marked signed-under-assumption | `test_gex_sign_footnote_present` | Drop the footnote / assert "short gamma" |
| R15 | No `cuttingboard` decision module imports `gex_card`; producer has no machine reader beyond the renderer | `test_gex_no_decision_import` (grep-guard) | Import `gex_card` into any decision module |
| R16 | Card adds no readiness marker; not in `validate_coherent_publish` triple | `test_gex_no_readiness_marker` | Add a GEX readiness marker |
| R17 | Decision outputs (contract/payload/decision) byte-identical with vs without the artifact present | `test_gex_decision_outputs_unchanged` | Let the card mutate any decision surface |
| R18 | `dashboard_renderer.py` contains no GEX distance/freshness arithmetic (all in `gex_card.py`) | `test_renderer_has_no_gex_math` (structural) | Move card math into the renderer |

The mutation column is the design-stage promise; the PRD carries these as
red-proven guards (every guard ships a failing-when-violated test; PRD-198
invariant 4). R1 and R17 are the load-bearing baseline-neutrality guards.

---

## sec7 -- FILES cone (provisional -- ESTIMATED SURFACE, NOT YET APPROVED)

Production (2):
- `cuttingboard/delivery/gex_card.py` (NEW) -- loader + model + fragment.
- `cuttingboard/delivery/dashboard_renderer.py` (MODIFY) -- path const, load
  in `main()`, thread kw params, emit-or-suppress, card CSS.

Producer (conditional, sec9 Q4):
- `tools/gex_snapshot.py` (MODIFY -- docstring line 8 only, non-functional)
  IF the owner accepts the one-line truth-correction (D11); otherwise removed
  from FILES and handled entirely in `artifact_flow_map.md`.

Tests (2):
- `tests/test_gex_card.py` (NEW) -- pure loader/model/fragment (R2-R14).
- `tests/test_dashboard_renderer.py` (MODIFY) -- renderer integration +
  golden baseline-neutrality (R1, R7, R15-R18) + the committed pre-GEX golden
  asset.

Docs / lifecycle bookkeeping:
- `docs/artifact_flow_map.md` (MODIFY) -- gex_snapshot consumer row + the new
  module's read (G5, mandatory in the same PRD).
- `docs/CALL_SITE_MAP.md` (MODIFY) -- new call site renderer -> gex_card
  (frozen E1-008).
- `docs/SCHEMA_MAP.md` (MODIFY, if it indexes artifact consumers) -- new
  consumer of the gex_snapshot schema.
- `docs/plans/decision-support-workplan-v0.1.md` (MODIFY) -- GEX-2 state flip
  (lifecycle bookkeeping).
- Standard Stage-0 / same-PR-closeout bookkeeping: `docs/PRD_REGISTRY.md`,
  `docs/prd_index.json`, `docs/PROJECT_STATE.md` (charge-template implicit
  allowlist).

Pre-implementation grep sweep (PRD-158): before the PRD locks FILES, grep
`tests/` for any token this card renames/translates -- none is renamed here
(the card only reads), so no additional asserting test file is forced beyond
the two named; the PRD re-runs the sweep to confirm.

---

## sec8 -- Change-surface ceiling (provisional, GOV-2 sec5)

`ESTIMATED SURFACE -- NOT YET APPROVED`:

- Production files: 2 (+1 conditional producer docstring line).
- Test files: 2 (+1 committed golden asset).
- Net production LOC: `<= 200` across the two production files
  (`gex_card.py` ~120-150 incl. validation/suppression; renderer wiring +
  CSS ~40-60). Frozen PR #261 r3 independently estimated the GEX-2 consumer
  at ~120-190 with a 220 ceiling; this is consistent and slightly tighter.
- Zero new dependencies (stdlib + existing renderer imports only).
- No workflow, no schema, no contract, no cadence change.

The first BINDING ceiling is Dustin's Gate A on the reviewed PRD (GOV-2 sec5).
Any later increase is a stop-and-renew event.

---

## sec9 -- Open design questions for the design-direction ruling

1. **Lane: STANDARD or HIGH-RISK?** sec0 shows MATERIAL but STANDARD-shaped
   (a suppressible renderer-side reader of an existing sidecar; no decision
   surface, no schema change). Frozen PR #261 self-classified
   "CONSUMER / HIGH-RISK". Recommendation: STANDARD (the normal matrix with
   MICRO disqualified), because the change writes nothing to any decision or
   contract surface and its worst-case failure is a suppressed card. Dustin
   rules; HIGH-RISK fires only on an R11 trigger.
2. **Public-board visibility now, or capability-now / public-later?** (D10).
   Recommendation: capability-now / public-later -- ship the display-only
   card with NO carrier; it renders locally / in the smoke test now and goes
   live on the public board via the deferred free-cadence GEX-3 slice. The
   alternative (include a minimal carrier so it is live on Pages immediately)
   would expand this slice beyond the owner's stated "no new cadence" and
   beyond a pure consumer.
3. **Freshness display + STALE_MAX knob.** (D4/D5). Recommendation: absolute
   ET capture time + static "Cboe ~15m delayed source", no relative "ago";
   `STALE_MAX = 24h` provisional. Confirm the wording and the threshold, or
   direct a different single knob.
4. **Producer docstring truth-correction.** (D11). Recommendation: accept the
   one-line non-functional docstring edit to `tools/gex_snapshot.py:8` plus
   the `artifact_flow_map.md` row. Alternative: docs-only correction in
   `artifact_flow_map.md`, with a docstring rewording of the owner's choice.
5. **Dominant-unavailable rule.** (D5). Recommendation: `dominant_net_gamma`
   null -> suppress the whole card (no anchor). Confirm, or prefer showing
   Net + available rows without a dominant line.

---

## sec10 -- Review (GOV-2 packet cycle; charge-template mirror)

- Event 1 (INITIAL PACKET REVIEW): one independent Codex review, fresh
  context, read-only (`codex exec -s read-only - < CODEX_REVIEW_PROMPT...`),
  of THIS packet + the underlying repository surfaces it claims about (GOV-2
  sec2 step 3). Durable record:
  `audits/gex-2-free-board-card-2026-08/GEX_2_EVENT_1_CODEX_REVIEW_2026-08-21.md`.
- ONE consolidated author correction, recorded in this packet's CORRECTION
  CYCLE section.
- Event 2 (EXACT-CORRECTED-HEAD CONFIRMATION): one independent Codex
  confirmation of the exact corrected head SHA against the Event-1 findings
  list (GOV-2 sec7). Durable record:
  `audits/gex-2-free-board-card-2026-08/GEX_2_EVENT_2_CONFIRMATION_2026-08-21.md`.
- Maximum correction cycles: ONE (GOV-1 / GOV-2). A new material boundary
  omission at Event 2 returns the packet to DESIGN INCOMPLETE rather than
  starting a second cycle. Disagreement is Dustin's to adjudicate.

This packet author is not the independent reviewer; Codex (a separate model,
fresh context, no access to the authoring session) fills the GOV-2
auto-commissioned packet-review and exact-head-confirmation events.

## sec11 -- Validation, landing, stop conditions

- Docs-only validation for the packet branch:
  `python3 tools/validate_prd_registry.py --skip-commit-resolvability`
  (expected exit 0), `git diff --check`, `git status --short`.
- GOV-2 sec8 docs-only CI claim boundary applies: green CI on this branch
  confirms only that the documentation branch preserves the current green
  baseline. It does NOT execute or validate the proposed runtime design,
  consumer inventory, or regression plan.
- Landing: DRAFT only; GOV-0 hold (a decision-support expansion PR is opened
  as a draft and held for Dustin). Auto-merge FORBIDDEN. Merge FORBIDDEN. No
  other PR/branch touched.
- Stop conditions: authority conflict; a FILES expansion beyond sec7; any need
  to change the producer beyond the one-line docstring (Q4); any need for a
  workflow/cadence/schema change (that is GEX-3, out of scope); a boundary-
  reset trigger at Event 2.

## sec12 -- Reusable truths retained / stale assumptions discarded (frozen PR #261)

RETAINED (provider- and delivery-agnostic; still valid for a free display-only
card):
- Context-only invariant: GEX informs the board, never authorizes the trade;
  the card must not become a required payload/contract/publish/readiness/
  notification/audit surface.
- Typed-unavailable suppression semantics keyed on the producer's exact reason
  tokens (`all_net_gamma_zero`; `no_eligible_calls`/`no_nonzero_call_gex`;
  `no_eligible_puts`/`no_nonzero_put_gex`; `zero_abs_gex_denominator`).
- Field selection and the CUT list (D2); distance% as presentation geometry
  (frozen D-1); the compact label/value layout and the sign-assumption
  footnote.
- Baseline-neutrality via an INDEPENDENT pre-feature golden (not "None vs
  default None").
- Loader/renderer purity pattern: a bespoke soft loader modeled on
  `_load_trend_structure_snapshot` (never raises), one keyword-only param
  threaded through, `if frag:`-with-no-else full suppression.
- Keyless/free Cboe provider, stdlib-only, zero new deps.

DISCARDED (owner FREE-FIRST direction changes the target that forced them):
- Public-published-board LIVE current-session delivery as the v1 target (drove
  everything below). Replaced by capability-now / public-later (D10, Q2).
- The GEX-3 automated cadence/carrier slice as a prerequisite of the card
  (deferred, not required by this slice).
- The GEX-1b producer schema extension (`underlying_last_trade_utc`) and the
  session-recency Gate 6. Not needed; the card claims no live-session
  freshness.
- `feed_timestamp_utc` as a freshness clock (frozen E1-002) and
  `observation_trading_date`/`is_market_open` as a session gate (frozen H-1
  circular). The card uses `fetched_at_utc` capture-age only (D4/D5).
- The `MAX_FEED_AGE_MINUTES` 0..120 rule and the tunable SESSION_ACTIVITY /
  FETCH_RECENCY knobs. Replaced by one simple STALE_MAX capture-age knob (Q3).
- The single-file / <=120-LOC framing was itself discarded by frozen E1-009;
  this packet sets its own estimate honestly (sec8).
NOTE: there was never a paid-provider / auth / private-board assumption to
discard -- the prior work was already keyless/free; FREE-FIRST holds on the
provider axis with no change.

## sec13 -- Pre-review revision log

- 2026-08-21 r1: initial provisional packet authored from current `main`
  (`2b6dcc2`) on branch `claude/gex-2-free-card-material-packet`. Awaiting
  GOV-2 Event-1 independent Codex review.

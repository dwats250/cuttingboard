# GEX-0 — Polygon.io Provider Evidence Packet

```
STATUS: PROVISIONAL — 2026-08-06
AUTHORIZES NO IMPLEMENTATION
PROVISIONAL — NO PROVIDER SELECTED — NO IMPLEMENTATION AUTHORITY.
```

> ("NO PROVIDER SELECTED" = no provider has been **adopted for implementation**;
> Polygon.io is the **sole provider evaluated** in this bounded pass, per the
> owner-confirmed subject of the pass. This packet neither adopts nor rejects it
> for the track.)

**PROVIDER UNDER EVALUATION:** Polygon.io — raw options-chain data offering
(contracts reference, per-contract open interest, model-computed greeks, quotes,
underlying spot), from which a GEX figure would be *computed in-repo*. This is
explicitly **not** a derived-GEX vendor feed (no vendor-supplied flip / put-wall /
call-wall levels).

**Commissioned by:** Dustin (charge: "GEX-0 provider evidence", 2026-08-06).
**Lead:** Read-only recon (network research attempted; blocked).
**Base commit:** `daa7065d4fb5ee5a4a051de05bd1d18cae375afc` (== `origin/main`).
**Branch:** `claude/gex-0-provider-evidence-69q3eq`.

---

## §1 — Verdict (stated up front)

> **VERDICT (doctrine §4.3, scope: Polygon.io options-chain offering ONLY):
> `EVIDENCE INCOMPLETE`.**

This is an **evidentiary status of one provider in one bounded pass**. It is **not**
a provider selection, adoption, ranking, rejection, or track choice, and it speaks
to **no other provider**. The pass could not obtain the doctrine-required *current
provider documentation* or *a real sample response* because network egress to all
candidate provider hosts is denied at the proxy (see §5). Per
`docs/plans/decision-support-expansion-doctrine-v0.1.md` §4.3: "If any load-bearing
meaning above is unknowable, the result is `EVIDENCE INCOMPLETE`, with the specific
unknowns enumerated." The specific unknowns are enumerated in §8.

Per §4.3, `EVIDENCE INCOMPLETE` "ends the track until Dustin explicitly commissions
a fresh pass" and "does not authorize a second provider automatically." Whether this
egress-blocked pass is treated as *track-ended pending fresh commission* or as *the
same pass paused pending an egress grant* is an owner decision (see §13e); this
packet does not decide it and does not self-authorize a re-run.

---

## §2 — Authority & seam trace

**Classification.** GEX-0 is **NON-MATERIAL**. Applying
`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §1: this pass enumerates
no consumers, selects no shared implementation seam, sets no FILES/LOC ceiling,
adds/renames no contract/audit/report/payload/persisted-schema surface, changes no
governance guardrail, resolves no Critical/High finding, and crosses no pipeline
layers. GOV-2's material-packet workflow therefore does not apply.

**Governing authority (precedence).**
- `VISION.md` operating principles (description-not-prediction; read-only-sidecars;
  cuts-before-additions; system-serves-the-trader; docs-match-code).
- `docs/plans/decision-support-expansion-doctrine-v0.1.md` **§4** — the binding
  GEX contract and external-data honesty rules (§4.2 provider constraints, §4.3
  minimum honesty contract + verdict vocabulary, §4.4 construction gates). Global
  invariants **G1** (description, not prediction), **G2** (human-readable
  observation is not pipeline permission), **G6** (honest absence).
- `docs/plans/decision-support-workplan-v0.1.md` — GEX-0 ledger row ("one-provider
  live evidence pass … network research only").
- `docs/plans/agent-work-charge-template-v0.1.md` — the charge/packet structure
  mirrored below.
- `CLAUDE.md` recon-artifact clause — permits committing this findings artifact to
  the non-`main` feature branch.

**Doctrine constraints honored by this pass.** §4.2: exactly one provider; no
provider abstraction / comparison / consensus / averaging / fallback chain; first
pass is research only and makes **no repository code changes**; evidence must come
from current provider documentation and a real response, **not marketing copy or
memory**. Because the doctrine forbids memory-as-evidence, every memory-derived
value in this packet is fenced as a non-evidentiary inference (see §6, §9) and does
not lift the verdict above `EVIDENCE INCOMPLETE`.

**Seam trace (bounded, read-only).** No GEX code exists anywhere in `cuttingboard/`
(confirmed: `grep -rniE "gex|gamma" cuttingboard/` yields no producer, contract
field, or renderer; corroborated by `audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md`).
No GEX value reaches any consumer. The **plausible future artifact seam** (described,
not built) is a single JSON sidecar `logs/gex_snapshot.json` documented in
`docs/artifact_flow_map.md`, consumed display-only by the dashboard renderer — the
observation-sidecar shape of `cuttingboard/watchlist_sidecar.py`. **This pass creates
none of that.**

---

## §3 — Work-type block (charge-template mirror)

| Field | Value |
|---|---|
| Mode | READ-ONLY RECON |
| Mutation permission | Network research only (attempted; **blocked** at egress) |
| Repo mutation | One new findings artifact under `audits/…` only; no code/schema/contract/runtime/renderer/workflow/secret |
| Merge permission | **NONE** |
| Landing | Branch-only commit; **DRAFT**; auto-merge **FORBIDDEN**; no push/PR without separate Dustin authorization |
| PRD | READ-ONLY / NO PRD |

---

## §4 — Provider identity & exact evaluated offering

**Offering evaluated:** Polygon.io options data — the **raw options-chain** product
family (options *contracts reference*, per-contract *open interest*, *greeks* and
*implied volatility* as model-computed by Polygon, *quotes/trades*, and *underlying
spot*). GEX would be **computed descriptively in-repo** from these fields (Σ over
strikes of gamma · open-interest · contract-multiplier · dealer-sign convention ·
spot factor). Polygon is evaluated as a *raw-data* source, **not** a derived-GEX
vendor: it is not expected to ship flip / put-wall / call-wall levels (see row 16).

**Repository provenance of Polygon (corrected repo facts — observed at
`daa7065`).** A prior recon claim that Polygon is "currently integrated as a
free-tier fallback in `ingestion.py`" is **false at this SHA** and is corrected here:

- **Polygon integration was removed**, "never used in production"
  (`docs/DECISIONS.md:4250`; cleanup batch `audits/inventory-2026-05-22/03-dead-code.md`,
  `audits/cleanup-2026-05-22/`). `grep -rniE "polygon|apiKey" cuttingboard/` returns
  **nothing** — no live Polygon code remains in the tree.
- **Banned-import guards** actively prevent reintroduction of external-data libs
  into pure modules: `tests/test_scenario_engine.py:319`
  (`_BANNED = ["requests","yfinance","polygon","urllib","open(","fetch("]` asserted
  absent from `_generate_scenarios`) and `tests/test_levels.py:163`
  (`assert "import polygon" not in source` for the levels report module). A future
  producer must live outside these guarded modules.
- **Documented past security incident:** a Polygon `?apiKey=` URL was logged, causing
  109 historical exposures of `POLYGON_API_KEY`, remediated by out-of-band key
  rotation (`docs/DECISIONS.md:4275`–4291; `audits/cleanup-2026-05-22/gitleaks-output.md`).
  This is a concrete design constraint for any revival (see §11).
- **Doc drift:** `docs/system_logic_map.md:21` still reads "yfinance primary, Polygon
  fallback" — stale (Polygon removed). Already tracked as reconciliation finding CB-27
  (`audits/current-state-reconciliation-2026-07-30/EVIDENCE_INDEX.md:241`). Not edited
  by this pass (outside allowed files); flagged as owner bookkeeping (§13d).

The corrected picture keeps Polygon *plausible* (the repo and owner have prior
Polygon familiarity) while surfacing real cautions (deliberate removal on VISION
grounds; import guards; a prior key-leak incident). It does **not** change the
owner-confirmed choice to evaluate Polygon in this pass.

> **MEMORY — NOT EVIDENCE (fenced; must be confirmed against live docs + a real
> captured response):** candidate endpoints recalled from training, unverifiable
> while egress is blocked — options snapshot `GET /v3/snapshot/options/{underlyingAsset}`
> (and `/{underlyingAsset}/{optionContract}`); contracts reference
> `GET /v3/reference/options/contracts`; per-contract quotes/trades
> `GET /v3/quotes/{optionsTicker}`, `GET /v3/trades/{optionsTicker}`; aggregates
> `GET /v2/aggs/ticker/{optionsTicker}/range/…`. Host `api.polygon.io`. **None of
> these was reached or confirmed in this pass.**

---

## §5 — Environmental blockage record (the only experimentally-observed provider-side evidence)

Egress to every candidate provider host is denied at the agent proxy. Verbatim probe
(run `2026-08-07T01:10:40Z` UTC; local date 2026-08-06):

```
api.polygon.io      -> HTTP 000
api.tradier.com     -> HTTP 000
sandbox.tradier.com -> HTTP 000
api.orats.com       -> HTTP 000
cdn.cboe.com        -> HTTP 000
www.cboe.com        -> HTTP 000
api-v2.intrinio.com -> HTTP 000
www.deribit.com     -> HTTP 000
```

Proxy status (`$HTTPS_PROXY/__agentproxy/status`, `enabled: true`, `selective: false`)
recorded `connect_rejected` for each host, e.g.:

```
2026-08-07T01:10:40.941Z  connect_rejected  api.polygon.io:443
  -- gateway answered 403 to CONNECT (policy denial or upstream failure)
```

(identical `403 to CONNECT` denial for all eight hosts).

**Reproduction:**
```
for h in api.polygon.io api.tradier.com sandbox.tradier.com api.orats.com \
         cdn.cboe.com www.cboe.com api-v2.intrinio.com www.deribit.com; do
  curl -sS -o /dev/null -m 10 -w "$h -> HTTP %{http_code}\n" "https://$h/"
done
curl -sS "$HTTPS_PROXY/__agentproxy/status"
```

This corroborates the pre-existing state recorded in `docs/PROJECT_STATE.md`: GEX-0
"commissioned 2026-08-05 and still `EVIDENCE BLOCKED`: the first pass stopped without
a verdict because egress policy denied all provider hosts, so it waits on an egress
grant." The blockage is unchanged as of this pass.

---

## §6 — Evidence table (16 rows)

The 13 charter honesty points + 3 doctrine §4.3 additions ((14) rate limits,
(15) spot-price basis, (16) meaning of any flip/put-wall/call-wall level).

**Evidence-class vocabulary (fixed):** `directly-documented fact` /
`experimentally-observed fact` / `reasonable-but-unverified inference` /
`unavailable` / `claim-the-provider-cannot-truthfully-support`.

**Honesty rules for this pass:** **zero** provider-side cells are
`directly-documented fact` — no Polygon documentation page was reachable, so nothing
provider-published could be read (reachability itself is the disproof). Every
provider-side cell's evidence class NOW is `unavailable — egress blocked (proxy 403
CONNECT, 2026-08-07T01:10Z)`. The "expected value" column is fenced **MEMORY — NOT
doctrine-grade**; it exists only to make the future live pass a fill-in exercise, and
does not lift the verdict.

| # | Honesty item | §4.3 crosswalk | What a live pass MUST establish (checklist) | Evidence class NOW | Fenced MEMORY expectation (NOT evidence) |
|---|---|---|---|---|---|
| 1 | Exact product / endpoint | provider label; sample response | Exact plan name + exact endpoint URL(s) returning an options chain, from live docs; capture one real JSON response | unavailable — egress blocked | Polygon "Options" plan; `/v3/snapshot/options/{underlyingAsset}` for a chain snapshot |
| 2 | Exact fields available | field definitions | Enumerate every field in a real snapshot response body | unavailable — egress blocked | `open_interest`; `greeks{delta,gamma,theta,vega}`; `implied_volatility`; `day{o,h,l,c,v}`; `last_quote`; `last_trade`; `details{strike_price,expiration_date,contract_type,shares_per_contract}`; `underlying_asset{price,ticker}` |
| 3 | Underlying meaning of each required field | field definitions | Confirm from docs whether `greeks.gamma` is exchange-sourced or Polygon-model-computed, and the multiplier/units of `open_interest` | unavailable — egress blocked | gamma & IV are **Polygon-model-computed**, not exchange-authoritative; OI is per-contract; multiplier 100. **If gamma is model-derived, GEX built on it is a derived-of-derived quantity** — material to G1 |
| 4 | Symbol coverage | symbol coverage | Confirm US equity + index (esp. SPX/NDX) option coverage and any index entitlement gating, from docs | unavailable — egress blocked | US-listed equity/ETF options (OPRA) broadly; index options (SPX) likely entitlement-gated by plan |
| 5 | Strike & expiry coverage | expiration scope | Confirm full OPRA strike ladder + all listed expiries returned, and any pagination limits | unavailable — egress blocked | Full OPRA chain; pagination via `next_url` |
| 6 | Timestamp semantics & timezone | source timestamps | Confirm unit (ns?) and source (SIP/exchange vs Polygon receipt) and TZ of each timestamp field | unavailable — egress blocked | Unix **nanoseconds**, UTC; per-quote/trade SIP timestamps |
| 7 | Update frequency | update cadence | Confirm snapshot refresh cadence per plan (REST) and whether streaming exists | unavailable — egress blocked | Real-time on higher tiers; REST snapshot near-real-time; WebSocket on real-time plans |
| 8 | Real-time / delayed / historical / derived status | (viability-critical) | Confirm, per plan, whether options data is real-time or 15-min delayed; **do not assume real-time** | unavailable — egress blocked | Lower tiers **15-min delayed**; real-time requires a paid real-time options entitlement |
| 9 | Auth & access method | access terms | Confirm auth mechanism from docs (header vs query param) | unavailable — egress blocked | API key via `Authorization: Bearer` header **or** `?apiKey=` query (the query form is the past-leak vector — §11) |
| 10 | Pricing & practical account requirements | access terms and cost | Confirm current tier names/prices + non-professional vs professional data agreement | unavailable — egress blocked | Tiered monthly Options plans; a limited free tier; pro/non-pro distinction affects price & licensing |
| 11 | Licensing / redistribution / caching / retention | (viability-critical) | Read the subscriber agreement + OPRA terms: may cached values be persisted? displayed? for how long? | unavailable — egress blocked | OPRA-governed; redistribution/display restrictions likely; caching/retention limits plausible — **can flip verdict to NOT VIABLE** (§11) |
| 12 | Failure / staleness / missing-data behavior | staleness + unavailable behavior | Observe real responses for a missing/halted/stale contract: null vs omitted vs stale-timestamp | unavailable — egress blocked | Likely fields null/omitted with a stale `last_updated`; must be observed, not assumed (G6) |
| 13 | Provenance & reproducibility (**sample response**) | sample response | Capture ≥1 real response, hash it, record request+timestamp; this is the load-bearing gap | unavailable — egress blocked | — (a captured response is exactly what egress denial prevents; **this row alone caps the pass at EVIDENCE INCOMPLETE**) |
| 14 | Rate limits | rate limits | Confirm req/min per tier from docs + observed 429 behavior | unavailable — egress blocked | Free tier ~5 req/min; paid tiers higher/unmetered |
| 15 | Spot-price basis | spot-price basis | Confirm what `underlying_asset.price` represents (last trade? NBBO mid?) and its timestamp/TZ; for SPX confirm index-spot basis | unavailable — egress blocked | `underlying_asset.price` ~ last underlying trade; index spot basis for SPX must be confirmed separately |
| 16 | Exact meaning of any flip / put-wall / call-wall level | flip/put-wall/call-wall meaning | Confirm Polygon ships **no** such derived levels on the evaluated raw endpoints | unavailable — egress blocked (**N/A-by-construction**, marked inference) | Raw feed → **no vendor flip/put-wall/call-wall**; those would be computed in-repo. Marked inference until docs confirm absence |

---

## §7 — Supported claims (what this pass *can* stand behind)

All are `experimentally-observed` repository/environment facts at `daa7065`, or
direct citations of in-repo authority — **none** is a provider-published fact:

1. **Egress to all eight candidate provider hosts is denied** (`403 to CONNECT`) —
   observed, §5, reproducible.
2. **No GEX code exists** in `cuttingboard/` — observed grep + `stage0-04-gex-v0.1.md`.
3. **Polygon is not currently integrated**; it was integrated then removed as unused
   dead code — `docs/DECISIONS.md:4250`, `audits/inventory-2026-05-22/03-dead-code.md`.
4. **Banned-import guards** for `polygon`/`requests`/`yfinance`/`urllib` exist in
   `tests/test_scenario_engine.py:319` and `tests/test_levels.py:163`.
5. **A prior Polygon `?apiKey=` URL leak** (109 exposures) was remediated by rotation
   — `docs/DECISIONS.md:4275`–4291.
6. **Doc drift** at `docs/system_logic_map.md:21` ("Polygon fallback") — finding CB-27.
7. The governing authority, verdict vocabulary, and non-MATERIAL classification cited
   in §1–§2 are as quoted from the named repository documents.

---

## §8 — Known unknowns (enumerated — doctrine §4.3 compliance)

Every provider-side honesty item is presently **unknowable** because no Polygon
documentation page or real response was reachable. Enumerated by row (§6):

(1) exact product/endpoint · (2) exact fields · (3) field meanings incl. whether
gamma is model-computed · (4) symbol coverage incl. index gating · (5) strike/expiry
coverage · (6) timestamp semantics/TZ · (7) update cadence · (8) real-time vs delayed
status · (9) auth mechanism specifics · (10) pricing & account requirements ·
(11) licensing/redistribution/caching/retention · (12) failure/staleness behavior ·
(13) **a captured sample response** (load-bearing) · (14) rate limits · (15) spot-price
basis · (16) confirmation that no derived flip/put-wall/call-wall levels ship on the
raw endpoints.

**16 of 16 provider-side items unresolved.** The load-bearing one is (13): the
doctrine requires a real sample response as evidence, and egress denial makes it
unobtainable — which alone fixes the verdict at `EVIDENCE INCOMPLETE`.

---

## §9 — Unsupported / memory-flagged material (quarantine)

Everything in the §4 "MEMORY — NOT EVIDENCE" fence and every §6 "Fenced MEMORY
expectation" cell is training-derived recollection, **not** doctrine-grade evidence.
It is provided solely to accelerate the future live pass and MUST be confirmed against
current Polygon documentation and a captured response before any of it is relied upon.
None of it supports the verdict, and none of it may be cited elsewhere as established.
Per doctrine §4.2, memory is explicitly not evidence.

---

## §10 — Smallest plausible future manual producer boundary (NON-BINDING)

*Described only; nothing here is built, authorized, or scoped by this pass.* Mirrors
doctrine §4.4 `GEX-1`: a single **manual, cached** producer that fetches one
underlying's option chain once, computes a descriptive GEX figure, and writes a
**versioned** `logs/gex_snapshot.json`. Primary universe only. **No** consumer, **no**
cron/schedule, **no** notifications, **no** pipeline imports, **no** contract/schema
field. It must live outside the banned-import-guarded modules (§7.4). A separate PRD +
Gate A would be required before any of it is written. **NON-BINDING.**

---

## §11 — Security & licensing constraints

- **Licensing/redistribution/caching/retention (row 11) is presently `unavailable`
  and is viability-critical.** OPRA-governed options data typically carries
  redistribution/display and professional/non-professional restrictions; whether
  Polygon's subscriber agreement permits persisting/caching computed snapshots is
  unknown and **could alone flip a future verdict to `PROVIDER NOT VIABLE`.** No
  caching or producer design may precede reading these terms.
- **API-key handling.** A Polygon key is a secret: never committed, never logged. The
  repo has a **documented past failure** — the `?apiKey=` query-string form was
  logged, leaking the key 109 times (`docs/DECISIONS.md:4275`). Any revival must use
  the header auth form and must never emit the key in URLs/logs; `logs/` is gitignored
  since PRD-096 but that is not a substitute for not logging secrets.
- **This pass adds no secret, key, credential, or env var** and touches no code path.

---

## §12 — Stop conditions

For this pass and any future live pass:
- Egress **opens** mid-pass → **STOP** and report; the pass shape changes (real docs
  and a captured response become gatherable) and this packet was authorized under the
  blocked assumption. Do not silently upgrade scope.
- Any data behind a **paywall requiring purchase** to obtain evidence → STOP and ask.
- Any **ToS clause forbidding caching/redistribution** → record and STOP before any
  producer design.
- Any need to touch a file **outside** this packet directory → STOP (scope lock).
- A **second provider** appears warranted → STOP; doctrine forbids it in this pass and
  it requires a fresh Dustin commission.

---

## §13 — Unresolved owner decisions

- **(a)** Confirm or replace Polygon.io as the single provider for the eventual live
  pass. (Alternatives exist — CBOE delayed JSON, Tradier, ORATS, derived-level vendors
  — *listed, not compared*; comparison is doctrine-forbidden.)
- **(b)** Grant egress to the chosen provider host(s) so a real sample response can be
  captured (the gating blocker).
- **(c)** Free vs paid tier for the live pass (determines real-time vs delayed status,
  rate limits, and licensing terms — rows 8/10/11/14).
- **(d)** Whether `docs/PROJECT_STATE.md`'s GEX-0 line and `docs/system_logic_map.md:21`
  (stale "Polygon fallback", CB-27) should later be updated to reflect reality — **not
  done here** (outside allowed files); owner bookkeeping.
- **(e)** Whether this egress-blocked `EVIDENCE INCOMPLETE` pass is treated as
  *track-ended pending a fresh commission* or *the same pass paused pending an egress
  grant* (doctrine §4.3 track-ending clause; see §1). This packet does not decide it.

---

## §14 — Estimated future FILES / LOC surface (NON-BINDING)

*Rough order-of-magnitude only; not a ceiling, not authorization, not scope.* A future
`GEX-1`-style manual producer might touch ~2–3 files: one producer module
(e.g. `cuttingboard/gex_snapshot.py`), one schema/artifact-flow doc update
(`docs/artifact_flow_map.md` + `docs/SCHEMA_MAP.md`), and one test module — plausibly
low-hundreds of LOC total. **NON-BINDING.** Any real figure is set by a future PRD
after evidence exists.

---

## §15 — Provenance & reproducibility of this packet

- **Branch:** `claude/gex-0-provider-evidence-69q3eq`; **base commit:**
  `daa7065d4fb5ee5a4a051de05bd1d18cae375afc` (== `origin/main` at pass start).
- **Date:** 2026-08-06 (local); probe timestamp `2026-08-07T01:10:40Z` (UTC).
- **Egress probe:** command in §5; result: all 8 hosts `HTTP 000` / proxy `403 CONNECT`.
- **Local validation baseline (pre-write):**
  - `ruff check cuttingboard/ tests/` → **All checks passed!** (exit 0).
  - `python tools/validate_prd_registry.py --skip-commit-resolvability` → **passed**
    (exit 0).
  - `python -m pytest tests/ -q` → **3243 passed, 1 xfailed, 2 failed** in ~158s.
    The 2 failures (`tests/test_prd264_import_hardening.py::test_r1_conftest_prints_resolved_package_path`
    and `::test_r2_pythonpath_swap_resolves_swapped_package`) are a **local
    interpreter-split artifact**, not a code defect and not caused by this pass: those
    tests shell out to the bare `pytest` binary
    (`/root/.local/share/uv/tools/pytest/bin/python`, a uv-isolated tool venv **without**
    the project's runtime deps), whose nested collection fails on `ModuleNotFoundError`.
    The project deps are installed under `/usr/local/bin/python` (used by
    `python -m pytest`). Under CI parity (one shared environment) the suite is green
    per `docs/PROJECT_STATE.md`. **This packet changes no code, so the post-write
    re-run is identical (see the closing validation note).**
- **No network evidence was obtained.** Every provider-side value herein is either
  `unavailable` or fenced memory. CI/GitHub Actions is impaired; no remote check was
  triggered and no absent remote check is interpreted as acceptance.
```
PROVISIONAL — NO PROVIDER SELECTED — NO IMPLEMENTATION AUTHORITY.
```

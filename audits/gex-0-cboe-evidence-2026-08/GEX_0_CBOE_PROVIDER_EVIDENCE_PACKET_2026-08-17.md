# GEX-0 - Cboe delayed_quotes Provider Evidence Packet

```
STATUS: PROVISIONAL EVIDENCE - 2026-08-17
AUTHORIZES NO IMPLEMENTATION
GEX-0 EVIDENCE PASS - PROVIDER EVALUATED: Cboe delayed_quotes public JSON.
```

> This packet is a bounded GEX-0 live-provider evidence pass (doctrine §4.4:
> "bounded live-provider evidence, no code"). It evaluates ONE provider - the
> Cboe delayed_quotes public JSON feed - and records exactly one §4.3 verdict for
> that provider. It adopts no provider for the track, authorizes no GEX-1
> producer, and writes no production code, schema, consumer, cron, or pipeline
> import. Nothing here creates trade permission (doctrine §4.1, G2).

**PROVIDER UNDER EVALUATION:** Cboe Global Markets delayed_quotes public JSON -
the per-underlying options snapshot served at
`cdn.cboe.com/api/global/delayed_quotes/options/{SYMBOL}.json`. Keyless, no auth.
Returns a full per-contract chain including open interest, Cboe-computed Greeks
(delta/gamma/theta/vega/rho), implied volatility, a theoretical value, quotes
(bid/ask + sizes), daily OHLC, last trade, and an underlying reference price. A
GEX figure would be **computed descriptively in-repo** from OI x gamma per strike;
the feed ships no vendor flip/put-wall/call-wall levels.

**Commissioned by:** Dustin (HELM charge: "GEX-0 fresh evidence pass, provider
Cboe", 2026-08-17).
**Owner precondition ruling (recorded, not decided by this packet):** Dustin ruled
(a) observed live behavior + Cboe published site Terms of Use satisfy the doctrine
§4.2 documentation leg for this keyless public feed, and (b) evidence artifacts are
schema-and-excerpt only. This packet proceeds on that ruling and cites it where the
terms leg is load-bearing (§6 row 1, §9).
**Lead:** Live read-only fetch (network reachable this pass).
**Base commit:** `e3f0b597cf2312513252dea9dafd27e87e412b11` (== `origin/main` at
pass start).
**Branch:** harness-native worktree branch `worktree-claude+gex0-cboe-pass-0817`
(the harness worktree tool sanitizes `/`; the charge-requested name was
`claude/gex0-cboe-pass-<id>` - functional intent identical, naming deviation
flagged to owner).

---

## §1 - Verdict (stated up front)

> **VERDICT (doctrine §4.3, scope: the Cboe delayed_quotes public JSON feed for
> SPY and SPX/SPXW ONLY): `PROVIDER VIABLE`.**

Scoped precisely: for a **personal, non-redistributed, context-only** GEX
observation built on **~15-minute delayed** data, every load-bearing §4.3 meaning
was **established this pass - directly observed live, or owner-ruled/REPORTED where
noted** (the terms leg and the exact delay figure; §6, §8). The feed supplies the two inputs
a descriptive GEX requires and that a raw-data provider must expose - **per-strike
open interest** and **per-strike gamma** - plus IV, quotes, and an underlying spot
basis, for both the retail proxy (SPY) and the correct gamma underlying (SPX,
including AM-settled SPX and PM-settled SPXW roots).

This is an **evidentiary status of one provider in one bounded pass**. It is **not**
a provider adoption, a track choice, a GEX-1 authorization, or a statement about any
other provider. Per doctrine §4.3 the verdict "speaks only to the one provider
examined." Promotion to a GEX-1 producer remains gated behind a separate PRD and
Gate A (§4.4, §11).

Two honesty caveats that do NOT lower the verdict (neither is an unknowable
load-bearing meaning; both are enumerated in §8):
- the precise numeric market-data delay is labelled **REPORTED** "~15 minutes"
  (endpoint name + Cboe delayed-data posture); the pass **VERIFIED** an observed
  last-trade lag of ~16 minutes, consistent with it;
- the licensing/redistribution leg rests on **Dustin's precondition ruling** plus
  the non-redistribution, excerpt-only posture this packet enforces (§9), not on an
  independent contract review.

---

## §2 - Authority and seam trace

**Classification.** GEX-0 is **NON-MATERIAL**. Applying
`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md` §1: this pass enumerates
no consumers, selects no shared implementation seam, sets no production FILES/LOC
ceiling on the codebase, adds/renames no contract/audit/report/payload/persisted
schema surface, changes no governance guardrail, resolves no Critical/High finding,
and crosses no pipeline layers. GOV-2's material-packet workflow does not apply. The
lane is the routine gate: one fresh-context review plus the connector (advisory).

**Governing authority (precedence).**
- `VISION.md` operating principles (description-not-prediction; read-only sidecars;
  cuts-before-additions; system-serves-the-trader; docs-match-code).
- `docs/plans/decision-support-expansion-doctrine-v0.1.md` **§4** - the binding GEX
  contract: §4.2 provider constraints, §4.3 minimum honesty contract + verdict
  vocabulary, §4.4 construction gates. Global invariants **G1** (description, not
  prediction), **G2** (human-readable observation is not pipeline permission), **G6**
  (honest absence).
- `docs/plans/decision-support-workplan-v0.1.md` - the GEX-0 ledger row (updated by
  this same PR to record the Cboe verdict).
- `docs/plans/agent-work-charge-template-v0.1.md` - the charge/packet structure
  mirrored here.
- `CLAUDE.md` recon-artifact clause - permits committing this findings artifact and
  its evidence excerpts to the non-`main` feature branch; the branch-to-`main` merge
  stays human-held (GOV-1).

**Doctrine constraints honored.** §4.2: exactly one provider; no provider
abstraction, comparison, consensus, averaging, or fallback chain; the first pass is
research only and makes no repository **code** changes to the product. Unlike the
2026-08-06 Polygon pass (which could rely on neither docs nor a captured response
because egress was blocked), this pass obtained a **real captured response** and
established meaning from **direct observation**, not memory or marketing copy.

**Seam trace (bounded, read-only).** No GEX code exists anywhere in `cuttingboard/`
at this SHA (`grep -rniE "gex|gamma" cuttingboard/` yields no producer, contract
field, or renderer; corroborated by
`audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md`). No GEX value reaches any
consumer. The plausible future artifact seam (described, not built) would be a single
versioned JSON sidecar consumed display-only, mirroring the observation-sidecar
shape of `cuttingboard/watchlist_sidecar.py`. **This pass creates none of it.**

---

## §3 - Work-type block (charge-template mirror)

| Field | Value |
|---|---|
| Mode | READ-ONLY RECON + LIVE FETCH (keyless public feed) |
| Mutation permission | Network fetch only; no secret, key, or credential involved |
| Repo mutation | New findings artifact + truncated evidence excerpts + this dir's guards under `audits/gex-0-cboe-evidence-2026-08/` ONLY, plus the single GEX-0 status row in `docs/plans/decision-support-workplan-v0.1.md` |
| Merge permission | **NONE** - held for Dustin's GOV-1 merge |
| Landing | Branch commit; **READY** PR (not draft, so the connector runs); auto-merge FORBIDDEN |
| PRD | READ-ONLY / NO PRD (GEX-0 is evidence, not implementation) |
| Ceiling | <= 270 code LOC (guards only; no product code) |

---

## §4 - Provider identity and exact evaluated offering

**Offering evaluated:** the Cboe **delayed_quotes** public JSON options snapshot,
one HTTP GET per underlying:
- `https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json`
- `https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json` (leading
  underscore denotes the cash index)

This is the same delayed feed that backs Cboe's public option-quote web pages. It is
a **raw-data** source: Greeks and IV are Cboe-model-computed (see §6 row 4, a labelled
inference), and it ships **no** derived dealer-positioning levels (flip / put-wall /
call-wall). GEX would be computed in-repo as Σ over strikes of
gamma · open_interest · contract_multiplier · dealer-sign · spot factor.

**Repository provenance / constraints (observed at `e3f0b59`).**
- No live options-data code exists in `cuttingboard/`; **banned-import guards**
  actively prevent reintroducing `requests`/`urllib`/`polygon`/`yfinance` into pure
  modules (`tests/test_scenario_engine.py`, `tests/test_levels.py`). A future GEX-1
  producer must live outside those guarded modules. **This pass adds no such code.**
- No API key is used or stored - the feed is keyless, so the historical
  `?apiKey=`-in-URL leak class (a Polygon-era incident) does not apply here.

---

## §5 - Live capture record (directly-observed provider evidence)

All three requests below were issued this pass over the standard network path
(no proxy blockage, unlike the 2026-08-06 Polygon pass). Full timestamps and the
reproduction command are in §13. Header set captured per response.

| Request | HTTP | Contracts | Notable |
|---|---|---|---|
| `GET .../options/SPY.json` | 200 | 14,546 | root SPY; 34 expirations 2026-08-17..2028-12-15 |
| `GET .../options/_SPX.json` | 200 | 30,558 | roots SPX (10,208, AM) + SPXW (20,350, PM); 57 expirations 2026-08-17..2031-12-19 |
| `GET .../options/NOTAREALSYM.json` | 403 | - | S3 `<Error><Code>AccessDenied` XML (unavailable-symbol behavior) |

Observed response headers (both valid underlyings): `Content-Type: application/json`,
`Cache-Control: max-age=0, s-maxage=5` (5-second edge cache), `Last-Modified` ~1
minute before fetch, CloudFront/edge markers (`x-cache`, `x-amz-cf-pop`,
`cf-cache-status`). No `X-RateLimit-*` or `Retry-After` header on any response.

The committed truncated samples are `evidence/spy_sample.md` and
`evidence/spx_sample.md` - each a tracked markdown file wrapping one fenced `json`
block (schema + 2 partial contract rows; no full chain). Markdown wrapping is used
because a repo-wide `*.json` gitignore would otherwise drop raw `.json` evidence.

---

## §6 - §4.3 minimum honesty contract (all 13 legs)

Evidence-class labels: **VERIFIED** = directly observed live this pass;
**REPORTED** = from Cboe endpoint semantics / published posture / owner ruling, not
independently re-derived; **UNVERIFIABLE** = not establishable from this pass.

| # | §4.3 leg | Finding | Class |
|---|---|---|---|
| 1 | access terms and cost | Cost **$0**, keyless, no auth (HTTP 200 with no credential). Terms: governed by Cboe Global Markets Terms of Use; Dustin ruled (precondition) that observed behavior + Cboe published site terms satisfy the §4.2 documentation leg for this keyless feed. Use posture: personal, non-redistributed, context-only (§9). | VERIFIED (cost/access) + REPORTED (terms, owner-ruled) |
| 2 | rate limits | No published limit for this CDN path; **no 429 / Retry-After** observed across the pass's low-volume requests; `Cache-Control s-maxage=5`. Behavior at high request volume is not established. | VERIFIED (low-volume) + UNVERIFIABLE (high-volume ceiling) |
| 3 | symbol coverage | SPY (14,546 contracts); _SPX 30,558 = SPX (10,208) + SPXW (20,350). Both underlyings returned full chains. | VERIFIED |
| 4 | provider and model label | Provider = **Cboe Global Markets**. `delta/gamma/theta/vega/rho`, `iv`, `theo` are **Cboe-model-computed** values (feed carries no inline model citation; model-computed-not-exchange-authoritative is a reasonable inference). Material to G1: GEX on model gamma is a derived-of-derived quantity - label it as such downstream. | VERIFIED (provider) + REPORTED/inference (model) |
| 5 | field definitions | 23 per-contract fields observed with types (schema in `evidence/*_sample.md`). Load-bearing set all present and non-null on a live row: `open_interest, gamma, delta, theta, vega, rho, iv, bid, ask (+ *_size), volume, last_trade_price, last_trade_time, prev_day_close, theo, open, high, low, change, percent_change, tick, option` (OCC-style symbol). | VERIFIED |
| 6 | expiration scope | SPY: 34 distinct expirations, 2026-08-17..2028-12-15. _SPX: 57 distinct expirations, 2026-08-17..2031-12-19 (LEAPS). Settlement roots both present in _SPX: **SPX = AM-settled** (a.m. settlement, traditional monthly), **SPXW = PM-settled** (weeklys / end-of-month). | VERIFIED |
| 7 | update cadence | Endpoint path `delayed_quotes` + Cboe delayed-data posture => **~15-minute delayed** market data (REPORTED). Directly consistent: SPY sample `last_trade_time` 14:27:08 ET observed at 18:43 UTC (14:43 ET) = ~16 min lag (VERIFIED). Separately, the top-level `timestamp` and `Last-Modified` refresh ~1 min before fetch = edge regeneration cadence, distinct from the market-data delay. | REPORTED (figure) + VERIFIED (lag consistent) |
| 8 | source timestamps | Three surfaces: (a) top-level `timestamp` "YYYY-MM-DD HH:MM:SS" in **UTC** (matches `Date` header); (b) per-contract `last_trade_time` "YYYY-MM-DDTHH:MM:SS", **naive US/Eastern** (market local), = the contract's actual last trade; (c) HTTP `Last-Modified` (edge regen). A consumer MUST localize explicitly (mixed UTC / ET-naive). | VERIFIED |
| 9 | spot-price basis | `data.current_price` = underlying reference price: SPY **773.51**; _SPX **7755.51** = SPX **cash index level** (cash-settled; not a tradable last). `prev_day_close` and `close` also present. | VERIFIED |
| 10 | flip/put-wall/call-wall meaning | **N/A by construction**: the feed ships **no** derived dealer-positioning levels; the schema contains no flip/put-wall/call-wall/GEX field. Such a level would be computed in-repo from OI x gamma. This raw-data property is exactly what GEX needs. | VERIFIED (absence) |
| 11 | sample response | Real HTTP 200 JSON captured live for both underlyings this pass. Committed artifact is a **lawful truncated excerpt** (schema + 2 partial rows) per the owner redistribution ruling; full responses observed (14,546 / 30,558 contracts). Reproduction command in §13. | VERIFIED |
| 12 | staleness behavior | Untraded contracts carry a **stale `last_trade_time`** while model fields still populate: observed _SPX sample row `last_trade_time` **2026-08-11** (6 days old) with populated `theo`/OI/model fields (that row's own `gamma`/`iv` read 0.0, deep-ITM). Also observed degenerate Greeks (`gamma`=`iv`=0.0) on a deep-ITM expiring-today SPY contract. Consumer must treat last-trade freshness independently of quote/Greek presence (G6). | VERIFIED |
| 13 | unavailable/failure behavior | A nonexistent underlying returns **HTTP 403** with an S3-style `<Error><Code>AccessDenied` **XML** body (not a 200 JSON). A producer keys "unavailable" off non-200 status / non-JSON content-type and renders no GEX context (G6, baseline-neutral). | VERIFIED |

**All 13 load-bearing legs are established** (VERIFIED, or owner-ruled REPORTED for
the terms leg). No load-bearing §4.3 **meaning** is unknowable; per §4.3 the verdict
is therefore `PROVIDER VIABLE`, not `EVIDENCE INCOMPLETE`.

---

## §7 - Directly-observed facts this pass can stand behind

1. Both `SPY.json` and `_SPX.json` return HTTP 200 keyless with full per-contract
   chains (14,546 / 30,558 contracts). VERIFIED, reproducible (§13).
2. Every load-bearing GEX input is present on a live contract row: open interest,
   gamma (+ delta/theta/vega/rho), IV, bid/ask, volume, theo, last trade, OHLC.
3. SPX exposes both AM-settled (SPX) and PM-settled (SPXW) roots in one response.
4. The feed carries no vendor-derived flip/put-wall/call-wall level.
5. Delayed data: observed last-trade lag ~16 min, consistent with ~15-min delayed.
6. Untraded contracts show a stale `last_trade_time` alongside live model fields.
7. Unknown symbols yield a 403 AccessDenied XML, not a 200 - a clean unavailable
   signal.
8. No secret, key, or credential is involved anywhere in this pass.

---

## §8 - Enumerated non-VERIFIED items (honesty ledger)

Enumerated for completeness. **None is a load-bearing §4.3 meaning left unknowable**,
so none lowers the verdict below `PROVIDER VIABLE`; each is a bound on precision or a
future-risk, not a missing meaning:

- **Rate-limit ceiling at high volume** (UNVERIFIABLE this pass) - only low-volume
  access was exercised; a GEX-1 producer is manual/cached/low-volume by design (§11).
- **Precise numeric delay** (REPORTED ~15 min; VERIFIED ~16 min observed lag) - the
  exact contractual delay figure is not independently confirmed.
- **Exact Greek/IV model and inputs** (REPORTED/inference) - Cboe-computed; the model
  is not disclosed inline. Downstream GEX must be labelled derived-of-model.
- **Endpoint stability / SLA** (UNVERIFIABLE) - an undocumented public CDN path may
  change or disappear without notice; a producer must fail loud (§11, invariant 1).
- **Licensing beyond the ruled posture** (REPORTED, owner-ruled) - the non-
  redistribution, personal, context-only posture is owner-ruled sufficient; changing
  posture to any redistribution/display-to-others would require a fresh terms review
  and re-commission (§9, §12).

---

## §9 - Licensing / redistribution posture

- The evidence artifacts are **schema + truncated excerpt only** (2 partial contract
  rows per underlying). **No bulk chain data is committed.** The guard
  `test_gex0_cboe_evidence.py::test_excerpt_has_no_full_chain` fails if any committed
  evidence excerpt (the fenced json inside `evidence/*_sample.md`) contains a list
  longer than a small cap - i.e. the non-redistribution posture is machine-enforced,
  not merely promised.
- Use posture: **personal, non-redistributed, context-only.** Dustin ruled
  (precondition) that observed live behavior + Cboe published Terms of Use satisfy the
  §4.2 documentation leg for this keyless public feed. This packet does not assert
  Cboe affirmatively licenses redistribution; it records that redistribution is out of
  posture and out of scope.
- Cite: Cboe Global Markets Terms of Use (`cboe.com`, site Terms) as the governing
  terms surface for this public web data.

---

## §10 - Machine-checked claimed-observed fields

The guard `test_gex0_cboe_evidence.py::test_packet_claims_match_evidence` parses the
block below and fails if this packet claims any field that is absent from the
committed excerpt. Claiming an unobserved field turns that named test red.

<!-- CLAIMED-OBSERVED-FIELDS (machine-checked by test_gex0_cboe_evidence.py) -->
```json
{
  "contract_fields": [
    "open_interest", "gamma", "delta", "theta", "vega", "rho",
    "iv", "bid", "ask", "volume", "last_trade_time", "last_trade_price",
    "prev_day_close", "theo", "open", "high", "low", "option"
  ],
  "underlying_fields": ["price", "current_price", "prev_day_close", "last_trade_time"]
}
```

---

## §11 - Smallest plausible future GEX-1 producer boundary (NON-BINDING)

*Described only; nothing here is built, authorized, or scoped by this pass.* Mirrors
doctrine §4.4 `GEX-1`: a single **manual, cached** producer that fetches one
underlying's chain once (SPX being the correct gamma underlying), computes a
descriptive GEX figure, and writes a **versioned** JSON sidecar. Primary universe
only. **No** consumer, cron, notification, or pipeline import. It must live outside
the banned-import-guarded modules, must never present delayed data as real-time, must
fail loud on non-200 / non-JSON / missing load-bearing fields (invariant 1; §6 rows
2/12/13), and must not redistribute chain data. A separate PRD + Gate A precede any
of it.

---

## §12 - Stop conditions

- Any need to touch a file **outside** this packet directory or the single GEX-0
  workplan row -> STOP (scope lock).
- Any move toward a **second provider**, a provider comparison, or a fallback chain
  -> STOP; doctrine §4.2 forbids it in this pass.
- Any move to **build GEX-1**, add a consumer, a schema, a cron, or a pipeline import
  -> STOP; requires a separate PRD + Gate A.
- A shift of use posture toward **redistribution / display-to-others** -> STOP for a
  fresh Cboe terms review and re-commission.
- The endpoint starts requiring **auth or payment**, or returns a ToS/robots signal
  forbidding programmatic access -> STOP and report.

---

## §13 - Provenance and reproducibility

- **Branch:** `worktree-claude+gex0-cboe-pass-0817`; **base commit:**
  `e3f0b597cf2312513252dea9dafd27e87e412b11` (== `origin/main` at pass start).
- **Capture timestamps (UTC):** SPY/_SPX fetched 2026-08-17T18:43:25Z; failure probe
  same window. Feed-level `timestamp` observed 2026-08-17 18:42 UTC.
- **Reproduction (keyless; no credential):**
  ```
  curl -s "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json" \
    | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; \
      o=d['options']; print('contracts',len(o)); print(sorted(o[0].keys()))"
  ```
- **Evidence integrity guards (this dir, not `tests/`):**
  `test_gex0_cboe_evidence.py` - three guards (fetch-shape, excerpt cap,
  packet-claim/evidence agreement), each with a demonstrated red mutation.
  **Enforcement boundary (honest):** CI runs `pytest tests/ -q` and does **not**
  select this directory; wiring these into `tests/` would touch production files
  outside GEX-0 scope. The guards are committed, locally runnable, and their red
  mutations were demonstrated this pass; they are not CI-gated. Run:
  `python -m pytest audits/gex-0-cboe-evidence-2026-08/ -q`.
- **No secret or credential** appears anywhere in this pass; the feed is keyless.

```
PROVISIONAL EVIDENCE - PROVIDER VIABLE (Cboe delayed_quotes, scoped) - NO GEX-1 AUTHORITY.
```

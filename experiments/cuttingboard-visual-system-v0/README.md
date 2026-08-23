# Cuttingboard Visual System Lab V0

Three throwaway static prototypes test what Cuttingboard's mature visual architecture could become while preserving its current intelligence and truth boundaries.

This is exploratory code. It is not production-ready, does not allocate a PRD, and must not be copied into `cuttingboard/delivery/`. The entire lab is removable by deleting this directory.

## Authority and fixture truth

- Branch base: `8bf3b58a98120c43860a689756d84950a0b3aadb`
- Visual hierarchy audit: `c2299f9f7358ccbea2109b79a616717f34a97024`
- First-screen recon: `19178e504ef0a41caf54e544aacbcc61c047d174`
- Pinned publication artifact: `77e9fc8b0780133994058f5a8fb82daf60ed1a3d`
- Pinned public artifact SHA-256: `c5f451cc98f6b0360f41ec661e2af533236b3aa9ce5977bb6fa29ca9f65a289f`

NORMAL LONG-CONTENT carries the production values pinned in those sources: the stale board, EXPANSION environment, operator lock, OBSERVE ONLY / NO TRADE, full GEX delay and positioning-assumption qualifiers, 12/12 Movement, Opportunity Survival counts, the developing SPY setup, Macro Tape, Trend Structure, Changes, and Scoreboard history.

Amon Hen was treated only as a visual/product reference for hierarchy, grouping, typography roles, whitespace, and wide-screen composition. No trading semantics, terminology, signals, providers, or product modes were copied.

## Inspect the prototypes

- [Variant A — Evolutionary](variant-a/index.html)
- [Variant B — Zoned Cockpit](variant-b/index.html)
- [Variant C — Dense Responsive Desk](variant-c/index.html)
- [Measured comparison](COMPARISON.md)
- [Recommendation](RECOMMENDATION.md)
- [Machine-readable measurements](measurements.json)

The pages work directly from disk. A local server makes query-string switching convenient:

```bash
python3 -m http.server 4173 --directory experiments/cuttingboard-visual-system-v0
```

Then open:

- `http://127.0.0.1:4173/variant-a/`
- `http://127.0.0.1:4173/variant-b/`
- `http://127.0.0.1:4173/variant-c/`

Fixture modes can be selected in the lab toolbar or with `?fixture=`:

| Mode | Query value | Stress tested behavior |
|---|---|---|
| NORMAL LONG-CONTENT | `normal` | Stale board, long qualifiers, full candidate and context |
| HALT | `halt` | SYSTEM HALT, fail-closed reason, retained context |
| DEGRADED / CARRIER UNAVAILABLE | `degraded` | State unavailable, no inferred authorization, independent context clocks |
| RED-FOLDER EVENT PRESENT | `event` | Event alert/detail plus conditional Session Observation and Market Control |
| NO CANDIDATE | `no-candidate` | Zero setup count and an explicit empty candidate surface |

## The three hypotheses

| Variant | Hypothesis | Desktop behavior | Phone behavior |
|---|---|---|---|
| A — Evolutionary | The current board can improve substantially through type roles, lighter borders, tighter rhythm, and Opportunity continuity | A wider mostly vertical board; only GEX/Movement and history pair | Familiar sequence of quieter cards |
| B — Zoned Cockpit | Five strong zones can replace the feeling of many equal cards | MARKET/SYSTEM and Survival/Candidate compare inside broad zones | One bordered family at a time with internal hairlines |
| C — Dense Responsive Desk | A phone-first source order can become a true comparison desk only at 960px+ | State, Opportunity, Context, and History pairs; Macro/Trend use full rows | One continuous column with state and opportunity bands, then de-chromed detail |

## Semantic safety preserved

Every page keeps these facts visible without interaction:

- freshness and stale state
- separate MARKET STATE and SYSTEM STATE authority
- environment distinct from permission
- halt / operator lock / no-trade text
- critical event and carrier unavailability
- candidate identity, level, and invalidation when present
- GEX delayed-source qualifier
- configured positioning-assumption qualifier
- independent provenance clocks

Context is repeatedly labeled as context and never as authorization. There is no global score, global synchronized `as of`, predictive hero, bullish/bearish synthesis, or new semantic color contract. EXPANSION is deliberately neutral in the prototypes; this does not redefine production color semantics.

Safe disclosures are limited to candidate reason/watch, candidate level map, Macro drivers/prices, Scoreboard, and diagnostics. Every disclosure target is at least 44px high.

## Validation

Run the dependency-free headless Chrome suite:

```bash
node experiments/cuttingboard-visual-system-v0/tools/visual-test.mjs
```

Validated result:

```text
42 screenshots captured
0 overflow failures
0 critical-content failures
```

The runner uses Google Chrome through the Chrome DevTools Protocol. It captures exact viewports at device scale 1, checks source order, verifies fixture-specific text markers, checks critical content/provenance visibility, enforces 44px disclosure targets, rejects horizontal overflow, and records geometry in [measurements.json](measurements.json).

## Screenshot inventory

Each screenshot is an exact viewport capture with the prototype toolbar hidden.

### Variant A — 14 images

Directory: [screenshots/variant-a](screenshots/variant-a/)

- NORMAL: `360x800`, `390x844`, `430x932`, `768x1024`, `1280x800`, `1440x900`
- HALT: `390x844`, `1280x800`
- DEGRADED: `390x844`, `1280x800`
- EVENT: `390x844`, `1280x800`
- NO CANDIDATE: `390x844`, `1280x800`

### Variant B — 14 images

Directory: [screenshots/variant-b](screenshots/variant-b/)

- NORMAL: `360x800`, `390x844`, `430x932`, `768x1024`, `1280x800`, `1440x900`
- HALT: `390x844`, `1280x800`
- DEGRADED: `390x844`, `1280x800`
- EVENT: `390x844`, `1280x800`
- NO CANDIDATE: `390x844`, `1280x800`

### Variant C — 14 images

Directory: [screenshots/variant-c](screenshots/variant-c/)

- NORMAL: `360x800`, `390x844`, `430x932`, `768x1024`, `1280x800`, `1440x900`
- HALT: `390x844`, `1280x800`
- DEGRADED: `390x844`, `1280x800`
- EVENT: `390x844`, `1280x800`
- NO CANDIDATE: `390x844`, `1280x800`

## Isolation proof

- There are no production imports.
- No production module imports from `experiments/`.
- Fixture switching and rendering are local browser JavaScript only.
- No runtime, schema, producer, ingestion, notification, workflow, decision, or dashboard production source is changed.
- No PR or PRD is part of this lab.

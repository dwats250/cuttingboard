# Codex Event-2 exact-corrected-head confirmation — ATTEMPT 2

```
GOV-2 sec7 artifact. Confirmed head: 2f7f054. Invocation: codex exec -s read-only, captured verbatim from stdout 2026-09-02; original slot docs/prd_history/PRD-328.confirmation2.codex.md.
VERDICT: NOT CONFIRMED (2 residuals + 2 REQUIRED); repair 1d6108a.
```

---

# PRD-328 Confirmation #2 - Sol / Codex (narrow, exact-head)

**Confirmed head:** 2f7f054016d7305e228f417d51c4c49b2fc5e229  **Prior confirmation head:** 4ca0013  
**Verdict:** NOT CONFIRMED

## Residual table (1-4)

| Residual | Disposition | Evidence |
|---|---|---|
| 1. REQ-4: `market_map=None` precedence | NOT RESOLVED | R5 correctly assigns `market_map=None` exclusively to unhealthy branch (a), with branch (b) limited to healthy partial maps, at `PRD-328.md:375-387`; code confirms None produces missing lineage and health at `dashboard_renderer.py:782-808`, `:1357-1378`, and `:2415-2421`. T13 nevertheless still lists `market_map=None` in branch (b) while also assigning it exclusively to (a) at `PRD-328.md:597-602`. |
| 2. REC-1 / REQ-6: R7 source-cone oracle | NOT RESOLVED | The original self-rejection is fixed: keyword labels are excluded, `w` is allowed by the exact seven-name signature, and none of those seven names or ordinary chart/ladder locals matches the forbidden set at `PRD-328.md:443-460`; the required calls match `setup_chart.py:145-156` and `dashboard_renderer.py:1970-1978`. However, S2-Q1 MOVE requires MARKET CONTROL inside `#spy-session` at `PRD-328.md:474-480`, while R7 forbids `market_control_card`, permission, and candidate inputs and declares the whole section a five-input pure function at `PRD-328.md:432-459`. Thus the oracle remains self-rejecting for the still-permitted MOVE outcome. |
| 3. REQ-6: T15 grouping | RESOLVED | T15 bytes are group B under either ruling; position is group A under MOVE at `PRD-328.md:608-609` and group B under STAY at `PRD-328.md:619-622`. |
| 4. RECOMMENDED: `INVALID` health vocabulary | RESOLVED | `INVALID` is present in the health vocabulary at `PRD-328.md:260` and in R5(a)'s unhealthy list at `PRD-328.md:375-382`; the real return is verified at `dashboard_renderer.py:1374-1375`. |

## New findings

### REQUIRED 1 - R7 uses the wrong exact decision identifier

The correction newly forbids `decision_state` at `PRD-328.md:451-455`, but the renderer's actual identifier is `_decision_state` at `dashboard_renderer.py:2726-2744`. An exact AST-name oracle therefore does not reject a read of the real decision local.

### REQUIRED 2 - S2-Q1 MOVE is incompatible with R7

Under MOVE, R9 places MARKET CONTROL inside `#spy-session` at `PRD-328.md:474-480`. R7 simultaneously requires that section to contain no permission or candidate-implication text and depend only on its five observational inputs at `PRD-328.md:432-459`. The existing MCC reads `market_control_card` and emits `CANDIDATE-IMPLICATION` at `dashboard_renderer.py:3286` and `:3328-3344`. Both rules cannot be satisfied under MOVE.

### Newly invented symbol, path, or line number

Yes. `decision_state` is newly introduced as an exact forbidden identifier, but the existing renderer identifier is `_decision_state`. No newly invented path or line number was found. The confirmation path exists, the bounded diff contains only `PRD-328.md` and `PRD-328.confirmation1.codex.md`, and `_render_spy_session` plus its parameters are explicitly identified as planned new symbols rather than existing implementation.

## Blockers for Helm

- B1: Rule whether the PRD-as-packet precedent satisfies GOV-2 s2 or require the canonical two-artifact sequence.
- S2-Q1: STAY or MOVE for MARKET CONTROL. MOVE additionally requires reconciliation with R7's observational purity and source-cone rules.
- S2-Q2: Approve or decline the candidate-chart narrowing and same-symbol chart co-occurrence.
- S1-Q1: Confirm or decline the closed-C-tier secondary-evidence supersession.
- New: Remove `market_map=None` from T13 branch (b), leaving it under branch (a) only.
- New: Replace `decision_state` with the actual `_decision_state` identifier in the exact AST forbidden set.
- New: If MOVE remains available, revise R7's section-purity, forbidden-source, and byte-identity rules to account explicitly for MARKET CONTROL; otherwise rule STAY and remove MOVE as an implementation outcome.

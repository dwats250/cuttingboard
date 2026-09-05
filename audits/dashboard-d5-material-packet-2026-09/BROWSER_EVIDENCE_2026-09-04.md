# D5 (PRD-332) browser acceptance evidence — 2026-09-04

Headless Chrome via CDP `Emulation.setDeviceMetricsOverride` (real device metrics,
`innerWidth` asserted per the viewport-trap discipline — NOT `--window-size`).
Implementation head: `0f2b780`. Raw metrics + PNG screenshots produced under the
session scratchpad (`bevidence/metrics.json`, `bevidence/*.png`); this file is the
durable committed summary.

## Matrix

- Fixtures (4): `ws_permitted`, `ws_stay_flat`, `ws_halt` (2 high-grade chartable
  setups SPY A+/QQQ A + a NEEDS_MANUAL_CHECK alert candidate NVDA), and `ws_rc3`
  (RC-1/RC-3: canonical primary is a low-tier C card outside the workspace).
- Viewports (3): 390x844, 360x780, 1280x960.
- 12 case/viewport combinations.

## Results (all 12 combinations)

| Check | Result |
|---|---|
| `innerWidth == viewport width` (viewport-trap guard) | PASS (all) |
| Horizontal overflow, default (`scrollWidth <= innerWidth`) | 0 px (all) |
| Horizontal overflow, each setup tab selected in turn (native radio) | 0 px (all) |
| Horizontal overflow, every `<details>` expanded | 0 px (all) |
| MANUAL CHECK band present, visible, ABOVE `#setup-workspace` | PASS (all) |
| `.manual-check-flag` "MANUAL CHECK" visible | PASS (all) |
| `document.scripts.length == 1` (no JS added) | PASS (all) |
| Console errors | 0 (all) |
| Interactive targets `< 44px` (summary / .setup-tab / chart-toggle-label) | 0 (all) |

B1 (overflow), B2 (per-tab selection is CSS-only and adds no overflow), B3
(MANUAL CHECK position invariant across selection), B4 (44px targets), B5
(no JS / no console errors), B6 (LEVELS control unchanged — PRD-330 tests green):
all satisfied. The RC-3 fixture confirms that when the primary is a low-tier card
the workspace default tab shows `CHART >` and the inline chart renders with the
low-tier primary card (chart-slot semantics unchanged).

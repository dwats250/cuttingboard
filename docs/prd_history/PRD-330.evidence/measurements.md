# PRD-330 R9 / R14 acceptance record (2026-09-02)

Method: `measure.py` in this directory; Chrome 151 headless driven over the
DevTools protocol with `Emulation.setDeviceMetricsOverride` (mobile, DPR 2);
the script FAILS unless `innerWidth`/`innerHeight` equal the requested viewport.
Fixture: `spy_session_observed` (tests/preview_fixtures.py), rendered by the
implementation head. Result: `PRD-330 R9/R14 acceptance: PASS`.

| measure (CSS px) | 360x780 | 390x844 | 430x932 | R14 limit at 390 |
|---|---|---|---|---|
| viewport asserted | 360x780 | 390x844 | 430x932 | - |
| `#spy-session` top | 425 | 425 | 409 | <= 560 |
| SPY chart SVG top | 603 | 603 | 572 | <= 780 |
| `#watching-zone` top | 975 | 994 | 990 | - |
| first `.candidate-card` top | 1201 | 1206 | 1186 | <= 1320 |
| LEVELS label hit box (h x w) | 44 x 74 | 44 x 74 | 44 x 74 | >= 44 (D-5) |
| smallest rail label font | 9.44 | 10.32 | 11.50 | >= 9.0 (D-3) |
| `scrollWidth` == `innerWidth` | yes | yes | yes | no overflow |

R9 at every viewport: on load both LEVELS segments compute `display: none` and
the checkbox is unchecked; one tap on the label shows both segments; a second
tap hides them; focusing the input and pressing Space shows them again with the
label's focus outline `solid`; the SVG `innerHTML` is byte-identical before and
after every toggle. First-viewport tokens at 390x844 (decision word, verb and
title, regime, timestamp, macro bias, seven drivers, trend line, GEX and
PARTICIPATION cells, SPY SESSION heading): all present.

Screens: `prd330_<w>x<h>_levels_off.png` / `_levels_on.png` for the three
viewports.

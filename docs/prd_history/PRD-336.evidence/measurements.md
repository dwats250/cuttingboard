# PRD-336 R1 browser acceptance — four-across cockpit

Manual, fail-closed browser acceptance for the four-across macro cockpit
(PRD-336 R1). Rendered a macro-bearing dashboard into headless Chrome over the
DevTools protocol with device-metrics emulation (not `--window-size`, which
lies about the viewport — see the headless-Chrome viewport trap), asserting the
viewport settled to the exact target before measuring.

Reproduce:

```
google-chrome --headless=new --remote-debugging-port=9334 --no-sandbox \
    --hide-scrollbars --disable-gpu about:blank &
.venv/bin/python docs/prd_history/PRD-336.evidence/measure.py --port 9334
```

The macro snapshot path is pointed at a guaranteed-absent file so the browser
render takes its macro from the payload only and never bakes the ambient
`logs/macro_drivers_snapshot.json`.

## Results — PASS at both target widths

| Viewport | innerWidth | scrollWidth | horizontal overflow | grid columns / family | cells / family |
|---|---|---|---|---|---|
| 390×844 (mobile, DSF 2) | 390 | 390 | none | 4 / 4 / 4 / 4 | 3 / 4 / 4 / 4 |
| 1366×768 (desktop, DSF 1) | 1366 | 1366 | none | 4 / 4 / 4 / 4 | 3 / 4 / 4 / 4 |

Every macro family (`VOL / CRYPTO`, `RATES`, `FX`, `FUTURES`) renders as a real
4-column CSS grid. `VOL / CRYPTO` carries three members (VIX/BTC/ETH) and fills
the first three columns; the fourth stays empty, so its cells line up
column-for-column with the four-member families (the aligned-columns invariant).
At 390px the family cell left-edges are `[36, 117.5, 199, 280.5]`; the
3-member family matches the first three. No element extends past the viewport at
either width (`scrollWidth == innerWidth`, empty overflow list).

Screenshots: `prd336_390x844.png`, `prd336_1366x768.png`.

The harness FAILS (non-zero) unless the viewport settled, there is zero
horizontal overflow, all four families are present, every family row is a
4-column grid with the expected cell count, and the columns align across
families.

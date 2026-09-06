"""PRD-336 R1 browser acceptance (manual, fail-closed): renders a macro-bearing
dashboard into headless Chrome over the DevTools protocol with device metrics and
FAILS unless (a) the viewport settled, (b) there is no horizontal overflow, and
(c) the four-across cockpit renders as a real 4-column grid whose columns line up
across every macro family (the aligned-columns invariant). Measured at 390px
(mobile) and 1366px (desktop).

Start Chrome first, e.g.:
  google-chrome --headless=new --remote-debugging-port=9333 --no-sandbox \
      --hide-scrollbars about:blank &
Then:
  .venv/bin/python docs/prd_history/PRD-336.evidence/measure.py [--port 9333]
"""
from __future__ import annotations

import asyncio, base64, json, sys, tempfile, urllib.request  # noqa: E401
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html  # noqa: E402
from tests.dash_helpers import _macro_drivers, _market_map, _payload, _run  # noqa: E402

# (width, height, deviceScaleFactor, mobile)
VIEWPORTS = ((390, 844, 2, True), (1366, 768, 1, False))
# The four families the cockpit must render four-across (PRD-336 R1). VOL / CRYPTO
# carries three members (VIX/BTC/ETH); the others four. The invariant is a fixed
# 4-column grid so every family's cells line up column-for-column -- the 3-member
# family fills the first three columns and leaves the fourth empty.
FAMILIES = ("VOL / CRYPTO", "RATES", "FX", "FUTURES")
EXPECTED_CELLS = (3, 4, 4, 4)
# A guaranteed-absent macro snapshot: the browser render must not bake the ambient
# dirty logs/macro_drivers_snapshot.json; macro comes from the payload only.
NEUTRAL_MACRO = Path("/nonexistent/prd336_neutralized_macro_snapshot.json")

MEASURE_JS = """
(() => {
  const over = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.right > innerWidth + 0.5 && r.width > 0)
      over.push((el.tagName) + (el.id ? '#' + el.id : (el.className ? '.' + String(el.className).split(' ')[0] : '')));
  });
  const rows = [...document.querySelectorAll('.macro-drivers-row')].map(row => {
    const cs = getComputedStyle(row);
    const tracks = cs.gridTemplateColumns.split(' ').filter(Boolean);
    const cellLefts = [...row.children].map(c => +c.getBoundingClientRect().left.toFixed(1));
    return {gridCols: tracks.length, nCells: row.children.length, cellLefts};
  });
  return JSON.stringify({
    innerWidth, innerHeight,
    scrollW: document.scrollingElement.scrollWidth,
    overflow: over.slice(0, 8),
    macroRows: rows,
    macroTapePresent: !!document.getElementById('macro-tape'),
    familiesPresent: %s.filter(f => document.body.innerText.includes(f)),
    fullHtml: document.documentElement.outerHTML.slice(0, 500000)
  });
})()
""" % json.dumps(list(FAMILIES))


class CDP:
    def __init__(self, ws):
        self.ws, self.n, self.pending, self.events = ws, 0, {}, asyncio.Queue()

    async def send(self, method, **params):
        self.n += 1
        self.pending[self.n] = fut = asyncio.get_event_loop().create_future()
        await self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        return await fut

    async def pump(self):
        async for raw in self.ws:
            m = json.loads(raw)
            if m.get("id") in self.pending:
                self.pending.pop(m["id"]).set_result(m.get("result", m))
            elif "method" in m:
                await self.events.put(m)

    async def wait(self, name):
        while (m := await self.events.get())["method"] != name:
            pass
        return m


def _aligned(rows: list[dict], tol: float = 1.0) -> bool:
    """Every family's cells sit on the same 4-column grid: cell i shares column i's
    left edge across families (the dashboard aligned-columns invariant). A 3-member
    family (VOL / CRYPTO) matches the first three column positions."""
    ref = next((r["cellLefts"] for r in rows if r["nCells"] == 4), None)
    if ref is None:
        return False
    return all(all(abs(a - b) <= tol for a, b in zip(r["cellLefts"], ref)) for r in rows)


async def measure(cdp, width, height, dsf, mobile, url, out_dir):
    await cdp.send("Emulation.setDeviceMetricsOverride", width=width, height=height,
                   deviceScaleFactor=dsf, mobile=mobile)
    await cdp.send("Page.navigate", url=url)
    await cdp.wait("Page.loadEventFired")
    await asyncio.sleep(0.4)
    m = json.loads((await cdp.send("Runtime.evaluate", expression=MEASURE_JS,
                                   returnByValue=True))["result"]["value"])
    (out_dir / f"prd336_{width}x{height}.png").write_bytes(
        base64.b64decode((await cdp.send("Page.captureScreenshot", format="png"))["data"]))

    # fail-closed acceptance ------------------------------------------------
    assert (m["innerWidth"], m["innerHeight"]) == (width, height), \
        f"viewport did not settle: {m['innerWidth']}x{m['innerHeight']}"
    assert m["scrollW"] <= width and not m["overflow"], \
        f"horizontal overflow at {width}: scrollW={m['scrollW']} offenders={m['overflow']}"
    assert m["macroTapePresent"], "macro-tape not rendered"
    assert m["familiesPresent"] == list(FAMILIES), \
        f"missing macro families: {set(FAMILIES) - set(m['familiesPresent'])}"
    assert len(m["macroRows"]) == 4, f"expected 4 macro-family rows, saw {len(m['macroRows'])}"
    for i, r in enumerate(m["macroRows"]):
        assert r["gridCols"] == 4, f"family row {i} is not a 4-column grid: {r['gridCols']}"
        assert r["nCells"] == EXPECTED_CELLS[i], \
            f"family row {i} ({FAMILIES[i]}) has {r['nCells']} cells, expected {EXPECTED_CELLS[i]}"
    assert _aligned(m["macroRows"]), \
        f"four-across columns are not aligned across families: {[r['cellLefts'] for r in m['macroRows']]}"
    return {k: m[k] for k in ("innerWidth", "innerHeight", "scrollW", "overflow", "macroRows", "familiesPresent")}


async def main(port: int) -> None:
    html = render_dashboard_html(
        _payload(macro_drivers=_macro_drivers()), _run(), market_map=_market_map(),
        macro_snapshot_path=NEUTRAL_MACRO)
    tmp = Path(tempfile.mkdtemp()) / "prd336_fixture.html"
    tmp.write_text(html.replace('<meta http-equiv="refresh"', '<meta data-disabled-refresh="'), encoding="utf-8")
    out_dir = Path(__file__).resolve().parent
    page = next(t for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list"))
                if t["type"] == "page")
    results = {}
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = CDP(ws)
        pump = asyncio.create_task(cdp.pump())
        await cdp.send("Page.enable")
        for width, height, dsf, mobile in VIEWPORTS:
            results[f"{width}x{height}"] = await measure(cdp, width, height, dsf, mobile, tmp.as_uri(), out_dir)
        pump.cancel()
    print(json.dumps(results, indent=1))
    print("PRD-336 R1 four-across acceptance: PASS")


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9333
    asyncio.run(main(port))

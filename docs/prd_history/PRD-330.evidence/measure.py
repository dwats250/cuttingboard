"""PRD-330 R9 / R14 browser acceptance (manual, fail-closed): renders the
`spy_session_observed` fixture into headless Chrome over the DevTools protocol with
device metrics, FAILS unless the viewport settled, and measures placement, overflow,
the LEVELS toggle (tap + keyboard) and the control hit box.
Usage: .venv/bin/python docs/prd_history/PRD-330.evidence/measure.py [--port 9333]"""
from __future__ import annotations

import asyncio, base64, json, sys, tempfile, urllib.request  # noqa: E401
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html  # noqa: E402
from tests.preview_fixtures import SECTION_STATE_CASES  # noqa: E402

VIEWPORTS = ((390, 844), (360, 780), (430, 932))
THRESHOLDS_390 = {"spyTop": 560, "chartTop": 780, "firstCard": 1320}
FIRST_VIEWPORT_TOKENS = ("decision-state", "sys-verdict", "sys-context", "cb-updated", "macro-bias",
                         "tape-drivers", "tape-trend", "GEX", "PARTICIPATION", "SPY SESSION")

MEASURE_JS = """
(() => {
  const top = el => Math.round(el.getBoundingClientRect().top + scrollY);
  const svg = document.querySelector('#spy-session svg');
  const seg = svg.querySelectorAll('[data-layer="levels"]');
  const label = document.querySelector('.chart-toggle-label').getBoundingClientRect();
  const fonts = [...svg.querySelectorAll('[data-layer="levels"] text')].map(t => parseFloat(t.getAttribute('font-size')) * svg.getBoundingClientRect().width / 358);
  const over = []; document.querySelectorAll('body *').forEach(el => { const r = el.getBoundingClientRect();
    if (r.right > innerWidth + 0.5 && r.width > 0) over.push(el.tagName + (el.id ? '#' + el.id : '')); });
  return JSON.stringify({innerWidth, innerHeight, scrollW: document.scrollingElement.scrollWidth,
    spyTop: top(document.getElementById('spy-session')), chartTop: top(svg),
    watchingTop: top(document.getElementById('watching-zone')), firstCard: top(document.querySelector('.candidate-card')),
    controlH: Math.round(label.height), controlW: Math.round(label.width),
    levelsDisplay: [...seg].map(g => getComputedStyle(g).display), minLabelCss: +Math.min(...fonts).toFixed(2),
    svgHtml: svg.innerHTML, checked: document.getElementById('spy-levels').checked,
    firstViewportHtml: document.documentElement.outerHTML.slice(0, 400000), overflow: over.slice(0, 6)});
})()
"""


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


async def measure(cdp, width, height, url, out_dir):
    await cdp.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=2, mobile=True)
    await cdp.send("Page.navigate", url=url)
    await cdp.wait("Page.loadEventFired")
    await asyncio.sleep(0.4)

    async def read():
        return json.loads((await cdp.send("Runtime.evaluate", expression=MEASURE_JS, returnByValue=True))["result"]["value"])

    async def shot(name):
        (out_dir / name).write_bytes(base64.b64decode((await cdp.send("Page.captureScreenshot", format="png"))["data"]))

    m0 = await read()
    assert (m0["innerWidth"], m0["innerHeight"]) == (width, height), f"viewport did not settle: {m0['innerWidth']}x{m0['innerHeight']}"
    assert m0["scrollW"] == width and not m0["overflow"], f"overflow at {width}: {m0['overflow']}"
    assert m0["levelsDisplay"] == ["none", "none"] and not m0["checked"], "LEVELS must start OFF"
    assert m0["controlH"] >= 44, f"control hit box {m0['controlH']} px < 44"
    assert m0["minLabelCss"] >= 9.0, f"rail label {m0['minLabelCss']} CSS px < 9"
    await cdp.send("Runtime.evaluate", expression=f"window.scrollTo(0,{max(0, m0['spyTop'] - 8)})")
    await asyncio.sleep(0.2)
    await shot(f"prd330_{width}x{height}_levels_off.png")
    # R9: one tap on the label -> ON; second tap -> OFF; bytes identical throughout.
    await cdp.send("Runtime.evaluate", expression="document.querySelector('.chart-toggle-label').click()")
    await asyncio.sleep(0.15)
    m1 = await read()
    assert m1["levelsDisplay"] == ["inline", "inline"] and m1["checked"], "tap did not show LEVELS"
    assert m1["svgHtml"] == m0["svgHtml"], "SVG bytes changed on toggle"
    await shot(f"prd330_{width}x{height}_levels_on.png")
    await cdp.send("Runtime.evaluate", expression="document.querySelector('.chart-toggle-label').click()")
    await asyncio.sleep(0.15)
    m2 = await read()
    assert m2["levelsDisplay"] == ["none", "none"] and not m2["checked"], "second tap did not hide LEVELS"
    # R9 keyboard: focus the input and press Space.
    await cdp.send("Runtime.evaluate", expression="document.getElementById('spy-levels').focus()")
    for kind in ("keyDown", "keyUp"):
        await cdp.send("Input.dispatchKeyEvent", type=kind, key=" ", code="Space", windowsVirtualKeyCode=32, text=" ")
    await asyncio.sleep(0.15)
    m3 = await read()
    assert m3["levelsDisplay"] == ["inline", "inline"] and m3["checked"] and m3["svgHtml"] == m0["svgHtml"], "Space toggle"
    outline = (await cdp.send("Runtime.evaluate", expression="getComputedStyle(document.querySelector('.chart-toggle-label')).outlineStyle", returnByValue=True))["result"]["value"]
    result = {k: m0[k] for k in ("innerWidth", "innerHeight", "spyTop", "chartTop", "watchingTop", "firstCard",
                                 "controlH", "controlW", "minLabelCss", "scrollW")} | {"focusOutline": outline}
    if (width, height) == (390, 844):
        for key, limit in THRESHOLDS_390.items():
            assert result[key] <= limit, f"{key} {result[key]} > {limit}"
        missing = [t for t in FIRST_VIEWPORT_TOKENS if t not in m0["firstViewportHtml"]]
        assert not missing, f"first-viewport tokens missing: {missing}"
    return result


async def main(port: int) -> None:
    case = next(c for c in SECTION_STATE_CASES if c.name == "spy_session_observed")
    html = render_dashboard_html(case.payload, case.run, market_map=case.market_map, **case.render_kwargs)
    tmp = Path(tempfile.mkdtemp()) / "prd330_fixture.html"
    tmp.write_text(html.replace('<meta http-equiv="refresh"', '<meta data-disabled-refresh="'), encoding="utf-8")
    out_dir = Path(__file__).resolve().parent
    page = next(t for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list")) if t["type"] == "page")
    results = {}
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = CDP(ws)
        pump = asyncio.create_task(cdp.pump())
        await cdp.send("Page.enable")
        for width, height in VIEWPORTS:
            results[f"{width}x{height}"] = await measure(cdp, width, height, tmp.as_uri(), out_dir)
        pump.cancel()
    print(json.dumps(results, indent=1))
    print("PRD-330 R9/R14 acceptance: PASS")


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9333
    asyncio.run(main(port))

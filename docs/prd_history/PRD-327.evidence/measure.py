#!/usr/bin/env python3
"""PRD-327 design evidence: measure dashboard section geometry at a TRUE 390x844 viewport.

Drives headless Chrome over the DevTools protocol (Emulation.setDeviceMetricsOverride),
waits for the page load event plus a settle delay so the client-side staleness banner
has run, asserts window.innerWidth == 390 and innerHeight == 844 (fails loudly
otherwise), then reads getBoundingClientRect for the named sections.

Usage:
    python3 measure.py [--shots DIR] [--fresh] <html> [<html> ...]
--fresh  : also report the same page with the staleness banner forced hidden
           (simulates a fresh live board; reported as a second row "<case> [fresh]").
Requires: google-chrome on PATH, python `websockets`.
"""
import asyncio
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websockets

S = Path(__file__).parent
W, H = 390, 844
PORT = 9333
SEL = {
    "verdict": "#verdict-zone", "staleness": "#staleness-banner", "system_state": "#system-state",
    "tape": "#tape-zone", "today": "#today-zone", "context": "#context-zone",
    "watching": "#watching-zone", "opp": "#opportunity-survival", "board": "#candidate-board",
    "card": ".candidate-card", "card_header": ".candidate-card .card-header",
    "chart": ".candidate-card .setup-chart",
}
JS = """(function(){var out={};var sel=%s;for(var k in sel){var e=document.querySelector(sel[k]);
if(!e){out[k]=null;continue;}var r=e.getBoundingClientRect();
out[k]={top:Math.round(r.top+window.scrollY),bottom:Math.round(r.bottom+window.scrollY),
h:Math.round(r.height),hidden:!!(e.hidden||getComputedStyle(e).display==='none')};}
out.docH=document.documentElement.scrollHeight;out.vw=window.innerWidth;out.vh=window.innerHeight;
out.phone=window.matchMedia('(max-width:430px)').matches;return JSON.stringify(out);})()""" % json.dumps(SEL)
HIDE_BANNER = "(function(){var b=document.getElementById('staleness-banner');if(b){b.hidden=true;}return 1;})()"


class CDP:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def send(self, method, **params):
        self.n += 1
        await self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    async def wait_event(self, name, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(await asyncio.wait_for(self.ws.recv(), timeout))
            if msg.get("method") == name:
                return msg


async def measure_one(cdp, path, shot=None, fresh=False):
    await cdp.send("Page.enable")
    await cdp.send("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=1, mobile=True)
    await cdp.send("Page.navigate", url=f"file://{Path(path).resolve()}")
    await cdp.wait_event("Page.loadEventFired")
    await asyncio.sleep(0.5)  # let the inline staleness script settle
    if fresh:
        await cdp.send("Runtime.evaluate", expression=HIDE_BANNER)
        await asyncio.sleep(0.1)
    res = json.loads((await cdp.send("Runtime.evaluate", expression=JS, returnByValue=True))["result"]["value"])
    if res["vw"] != W or res["vh"] != H or not res["phone"]:
        raise SystemExit(f"FAIL: viewport not settled at {W}x{H} (got {res['vw']}x{res['vh']}, phone={res['phone']})")
    if shot:
        top = await cdp.send("Page.captureScreenshot", format="png")
        Path(f"{shot}_top.png").write_bytes(base64.b64decode(top["data"]))
        full = await cdp.send("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                              clip={"x": 0, "y": 0, "width": W, "height": res["docH"], "scale": 1})
        Path(f"{shot}_full.png").write_bytes(base64.b64decode(full["data"]))
    return res


async def run(paths, shotdir, fresh):
    proc = subprocess.Popen(
        ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         f"--remote-debugging-port={PORT}", "--user-data-dir=/tmp/prd327-chrome-profile", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
                break
            except Exception:
                await asyncio.sleep(0.2)
        else:
            raise SystemExit("FAIL: chrome devtools endpoint did not come up")
        ws_url = next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page")
        async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
            cdp = CDP(ws)
            hdr = (f"{'case':38} {'verd':>5} {'tape':>5} {'today':>5} {'ctx':>5} "
                   f"{'watch@':>6} {'hdr@':>6} {'chart@':>7} {'docH':>6} {'banner':>6}")
            print(hdr)
            out_dir = S / "measure"
            out_dir.mkdir(exist_ok=True)
            for p in paths:
                variants = [("", False)] + ([(" [fresh]", True)] if fresh else [])
                for suffix, fr in variants:
                    shot = (shotdir / (Path(p).stem + ("_fresh" if fr else ""))) if shotdir else None
                    r = await measure_one(cdp, p, shot=shot, fresh=fr)

                    def g(k):
                        return r.get(k) or {}

                    banner = "hidden" if g("staleness").get("hidden", True) else f"{g('staleness').get('h')}px"
                    print(f"{(Path(p).stem + suffix)[:38]:38} {g('verdict').get('h', '-'):>5} "
                          f"{g('tape').get('h', '-'):>5} {g('today').get('h', '-'):>5} "
                          f"{g('context').get('h', '-'):>5} {g('watching').get('top', '-'):>6} "
                          f"{g('card_header').get('top', '-'):>6} {g('chart').get('top', '-'):>7} "
                          f"{r.get('docH', '-'):>6} {banner:>6}")
                    (out_dir / (Path(p).stem + ("_fresh" if fr else "") + ".json")).write_text(json.dumps(r, indent=1))
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def main(argv):
    shotdir, fresh = None, False
    while argv and argv[0].startswith("--"):
        if argv[0] == "--shots":
            shotdir = Path(argv[1])
            shotdir.mkdir(parents=True, exist_ok=True)
            argv = argv[2:]
        elif argv[0] == "--fresh":
            fresh = True
            argv = argv[1:]
        else:
            raise SystemExit(f"unknown flag {argv[0]}")
    asyncio.run(run(argv, shotdir, fresh))


if __name__ == "__main__":
    main(sys.argv[1:])

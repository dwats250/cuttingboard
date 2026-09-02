#!/usr/bin/env python3
"""PRD-327 design evidence: measure dashboard section geometry at 390x844.

Injects a getBoundingClientRect reporter into a copy of each HTML file and
reads it back via headless Chrome --dump-dom. Usage:
    python3 measure.py [--shots DIR] <html> [<html> ...]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

S = Path(__file__).parent
SEL = {
    "verdict": "#verdict-zone",
    "staleness": "#staleness-banner",
    "system_state": "#system-state",
    "tape": "#tape-zone",
    "today": "#today-zone",
    "context": "#context-zone",
    "watching": "#watching-zone",
    "opp": "#opportunity-survival",
    "board": "#candidate-board",
    "card": ".candidate-card",
    "card_header": ".candidate-card .card-header",
    "chart": ".candidate-card .setup-chart",
    "page": "body",
}
JS = """<script>
(function(){var out={};var sel=%s;for(var k in sel){var e=document.querySelector(sel[k]);
if(!e){out[k]=null;continue;}var r=e.getBoundingClientRect();
out[k]={top:Math.round(r.top+window.scrollY),bottom:Math.round(r.bottom+window.scrollY),h:Math.round(r.height),hidden:e.hidden||getComputedStyle(e).display==='none'};}
out.docH=document.documentElement.scrollHeight;out.vw=window.innerWidth;out.vh=window.innerHeight;
var p=document.createElement('pre');p.id='__measure';p.textContent=JSON.stringify(out);document.body.appendChild(p);})();
</script>""" % json.dumps(SEL)

CHROME = ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
          "--hide-scrollbars", "--virtual-time-budget=2000"]


def measure(html_path, w=390, h=844, shot=None):
    src = Path(html_path).read_text()
    out_dir = S / "measure"
    out_dir.mkdir(exist_ok=True)
    tmp = out_dir / (Path(html_path).stem + ".m.html")
    injected = src.replace("</body>", JS + "</body>") if "</body>" in src else src + JS
    tmp.write_text(injected)
    cmd = CHROME + [f"--window-size={w},{h}", "--dump-dom", f"file://{tmp}"]
    dom = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    m = re.search(r'<pre id="__measure">(.*?)</pre>', dom, re.S)
    res = json.loads(m.group(1)) if m else {"error": "no measure"}
    if shot:
        for tag, hh in (("top", h), ("full", 4000)):
            subprocess.run(
                CHROME + [f"--window-size={w},{hh}", f"--screenshot={shot}_{tag}.png",
                          f"file://{Path(html_path).resolve()}"],
                capture_output=True, timeout=60,
            )
    return res


def main(argv):
    shotdir = None
    if argv and argv[0] == "--shots":
        shotdir = Path(argv[1])
        shotdir.mkdir(parents=True, exist_ok=True)
        argv = argv[2:]
    print(f"{'case':38} {'verd':>5} {'tape':>5} {'today':>5} {'ctx':>5} "
          f"{'watch@':>6} {'hdr@':>6} {'chart@':>7} {'docH':>6}")
    for p in argv:
        r = measure(p, shot=(shotdir / Path(p).stem) if shotdir else None)

        def g(k):
            return r.get(k) or {}

        print(f"{Path(p).stem[:38]:38} {g('verdict').get('h', '-'):>5} "
              f"{g('tape').get('h', '-'):>5} {g('today').get('h', '-'):>5} "
              f"{g('context').get('h', '-'):>5} {g('watching').get('top', '-'):>6} "
              f"{g('card_header').get('top', '-'):>6} {g('chart').get('top', '-'):>7} "
              f"{r.get('docH', '-'):>6}")
        (S / "measure" / (Path(p).stem + ".json")).write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

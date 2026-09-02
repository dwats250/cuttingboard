#!/usr/bin/env python3
"""D2 prototype generator: rewrites VERDICT/TAPE/TODAY of a rendered D1 fixture. No production code touched."""
import re
import sys
from pathlib import Path
S = Path(__file__).parent

def grab(pat, s, flags=re.S):
    m = re.search(pat, s, flags)
    return m.group(1) if m else None

def zone(src, zid):
    m = re.search(r'(<div class="block operator-zone" id="%s">.*?)(?=<div class="block operator-zone" id=)' % zid, src, re.S)
    return m.group(1)

def parse(src):
    v = zone(src, "verdict-zone")
    t = zone(src, "tape-zone")
    d = zone(src, "today-zone")
    p = {}
    p["coherence"] = grab(r'(<div class="verdict-warning" id="artifact-coherence".*?</div>\s*</div>)', v) or ""
    p["banner"] = grab(r'(<div class="block" id="staleness-banner".*?</script>)', v)
    p["state"] = grab(r'(<div class="decision-state [^"]*">.*?</div>)', v)
    p["verdict"] = grab(r'(<div class="sys-verdict [^>]*>.*?</div>)', v)
    p["why"] = grab(r'(<div class="sys-why">.*?</div>)', v) or ""
    p["kill"] = grab(r'(<div class="sys-context halted">Kill switch active</div>)', v) or ""
    p["perm"] = grab(r'(<div class="sys-permission">.*?</div>)', v) or ""
    p["ctx_cls"] = grab(r'<div class="(sys-context(?: halted)?)">(?!Kill)', v)
    p["regime"] = grab(r'<div class="sys-context(?: halted)?">((?!Kill)[^<]*)</div>', v)
    p["upd_iso"] = grab(r'id="cb-updated" data-updated-utc="([^"]*)"', v)
    p["upd_txt"] = grab(r'id="cb-updated"[^>]*>(.*?)</div>', v)
    p["macro"] = grab(r'<div class="tape-band-cap">MACRO</div>\s*<div class="zone-value">(.*?)</div>', t)
    p["drivers"] = grab(r'(<div class="tape-drivers">.*?</div></div>)', t)
    p["pressure"] = grab(r'<div class="tape-drivers">.*?<div class="zone-note">(.*?)</div>', t)
    p["trend_deriv"] = grab(r'data-derivation="([^"]*)"', t)
    p["trend"] = grab(r'data-derivation="[^"]*">(.*?)</div>', t)
    p["trend_chips"] = grab(r'(<div class="tape-trend">.*?</div></div>)', t)
    p["trend_any"] = bool(re.search(r'tape-trend-row tape-slot (up|down|flat)', t))
    # D2-Q2 (narrowed, Sol REQ-3): placeholder chips may leave the fold only when the
    # unchanged deep #trend-structure block enumerates the curated symbols (ts-table
    # present). Unhealthy lineage / inactive session render no table -> keep chips.
    p["deep_enumerates"] = 'class="ts-table"' in src.split('id="trend-structure"', 1)[1]
    p["keep_chips"] = p["trend_any"] or not p["deep_enumerates"]
    foot = grab(r'<div class="zone-grid tape-foot">(.*?)</div>\s*</div>\s*$', t)
    p["gex"] = grab(r'GEX · CONTEXT ONLY</div><div class="zone-value">(.*?)</div>', foot)
    p["gex_note"] = grab(r'GEX · CONTEXT ONLY</div><div class="zone-value">.*?</div><div class="zone-note">(.*?)</div>', foot) or ""
    p["part"] = grab(r'PARTICIPATION</div><div class="zone-value">(.*?)</div>', foot)
    p["part_note"] = grab(r'PARTICIPATION</div><div class="zone-value">.*?</div><div class="zone-note">(.*?)</div>', foot) or ""
    p["event"] = grab(r'EVENT RISK</div><div class="zone-value">(.*?)</div>', d)
    p["spy"] = grab(r'(SPY SESSION</div><div class="zone-value" data-raw-state="[^"]*">.*?</div>)', d)
    p["sunday"] = grab(r'(<div class="zone-item" id="premarket-banner">.*?</div></div>)', d)
    p["today_items"] = grab(r'<div class="zone-grid">(.*?)\s*</div>\s*</div>\s*$', d)
    return p, v + t + d

CSS_COMMON = ("<style>"
 "#system-state>h2{margin-bottom:.3rem}"
 ".sys-context #cb-updated{display:inline;font-size:inherit;color:#888}"
 ".tape-band{margin-top:6px}.tape-band:first-of-type{margin-top:0}"
 ".tape-foot{margin-top:6px}"
 "</style>")
CSS_B = ("<style>"
 "#context-zone .ctx-group{margin:0}"
 "#context-zone .ctx-row{display:grid;grid-template-columns:13ch minmax(0,1fr);column-gap:8px;align-items:baseline;margin-top:3px}"
 "#context-zone .ctx-row:first-child{margin-top:0}"
 "#context-zone .ctx-cap{color:#777;font-size:.64rem;text-transform:uppercase;letter-spacing:.1em}"
 "#context-zone .zone-value{margin-top:0}"
 "#context-zone .tape-drivers{margin:3px 0 0 0}#context-zone .zone-note{margin-top:2px}"
 "#context-zone .tape-trend{margin-top:3px}"
 "#context-zone #today-zone{margin-top:6px;padding-top:6px;border-top:1px solid #2a2a2a}"
 "#context-zone .ctx-sub{color:#aaa;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}"
 "#context-zone .ctx-cap-risk{color:#aaa;font-size:.75rem;letter-spacing:.05em}"
 "</style>")

def verdict_block(p):
    o = ['<div class="block operator-zone" id="verdict-zone">', p["coherence"], p["banner"],
         '<div class="block operator-subsection" id="system-state">', '  <h2>VERDICT</h2>',
         "  " + p["state"], "  " + p["verdict"]]
    if p["why"]:
        o.append("  " + p["why"])
    if p["kill"]:
        o.append("  " + p["kill"])
    if p["perm"]:
        o.append("  " + p["perm"])
    # Sol confirmation revision: keep the regime line and the #cb-updated element
    # byte-identical to base (no relocation); drop only the "UPDATED" label + sep.
    o.append(f'  <div class="{p["ctx_cls"]}">{p["regime"]}</div>')
    o.append(f'  <div class="value" id="cb-updated" data-updated-utc="{p["upd_iso"]}">{p["upd_txt"]}</div>')
    o += ["</div>", "</div>"]
    return "\n".join(x for x in o if x)

def concept_a(p):
    t = ['<div class="block operator-zone" id="tape-zone">', '  <h2>TAPE <span class="label">context only</span></h2>',
         '  <div class="tape-band">', '    <div class="tape-band-cap">MACRO</div>']
    if p["macro"] is not None:
        t.append(f'    <div class="zone-value">{p["macro"]}</div>')
    t += ["    " + p["drivers"], f'    <div class="zone-note">{p["pressure"]}</div>', "  </div>",
          '  <div class="tape-band">', '    <div class="tape-band-cap">TREND</div>',
          f'    <div class="zone-value" data-derivation="{p["trend_deriv"]}">{p["trend"]}</div>']
    if p["keep_chips"]:
        t.append("    " + p["trend_chips"])
    t += ["  </div>", '  <div class="zone-grid tape-foot">',
          f'    <div class="zone-item"><div class="label">GEX · CONTEXT ONLY</div><div class="zone-value">{p["gex"]}</div>' + (f'<div class="zone-note">{p["gex_note"]}</div>' if p["gex_note"] else "") + "</div>",
          f'    <div class="zone-item"><div class="label">PARTICIPATION</div><div class="zone-value">{p["part"]}</div>' + (f'<div class="zone-note">{p["part_note"]}</div>' if p["part_note"] else "") + "</div>",
          "  </div>", "</div>",
          '<div class="block operator-zone" id="today-zone">', '  <h2>TODAY</h2>', '  <div class="zone-grid">', p["today_items"], "  </div>", "</div>"]
    return verdict_block(p) + "\n" + "\n".join(t) + "\n"

def row(cap, val, extra="", cap_cls="ctx-cap"):
    return f'    <div class="ctx-row"><span class="{cap_cls}">{cap}</span><span class="zone-value"{extra}>{val}</span></div>'

def concept_b(p):
    t = ['<div class="block operator-zone" id="context-zone">',
         '  <h2>CONTEXT <span class="label">context only · independent facts</span></h2>',
         '  <div class="ctx-group" id="tape-zone">', '    <div class="ctx-sub">TAPE</div>']
    if p["macro"] is not None:
        t.append(f'    <div class="zone-value">{p["macro"]}</div>')
    t += ["    " + p["drivers"], f'    <div class="zone-note">{p["pressure"]}</div>',
          row("TREND", p["trend"], f' data-derivation="{p["trend_deriv"]}"')]
    if p["keep_chips"]:
        t.append("    " + p["trend_chips"])
    t.append(row("GEX",p["gex"] + (f' <span class="zone-note">{p["gex_note"]}</span>' if p["gex_note"] else "")))
    t.append(row("PARTICIPATION", p["part"] + (f' <span class="zone-note">{p["part_note"]}</span>' if p["part_note"] else "")))
    t += ["  </div>", '  <div class="ctx-group" id="today-zone">', '    <div class="ctx-sub">TODAY</div>',
          row("EVENT RISK", p["event"], cap_cls="ctx-cap ctx-cap-risk")]
    if p["spy"]:
        st = grab(r'data-raw-state="([^"]*)"', p["spy"])
        tx = grab(r'data-raw-state="[^"]*">(.*?)</div>', p["spy"])
        t.append(row("SPY SESSION", tx, f' data-raw-state="{st}"'))
    if p["sunday"]:
        t.append('    <div class="ctx-row" id="premarket-banner"><span class="ctx-cap">SESSION</span><span class="zone-value">SUNDAY PRE-MARKET CONTEXT · no cash session</span></div>')
    t += ["  </div>", "</div>"]
    return verdict_block(p) + "\n" + "\n".join(t) + "\n"

for f in sys.argv[1:]:
    src = Path(f).read_text()
    p, old = parse(src)
    for tag, fn, css in (("A", concept_a, CSS_COMMON), ("B", concept_b, CSS_COMMON + CSS_B)):
        out = src.replace(old, fn(p)).replace("</head>", css + "</head>")
        assert old not in out and 'id="watching-zone"' in out
        # below-seam invariance check for the prototype itself
        assert out.split('id="watching-zone"',1)[1] == src.split('id="watching-zone"',1)[1]
        (S / "proto" / tag / Path(f).name).write_text(out)
    print("ok", Path(f).name)

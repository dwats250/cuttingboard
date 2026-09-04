"""GEX-4 corrected prototype (post-Event-1, Event-2 attempt-2 repair): single neutral extent, single ink net bar,
model-bounded labels, coverage both ways, outside line with counts, full accessible table.
Static inline SVG, no JS, dashboard tokens. Input: per_strike.json from analyze_chain.py."""
import json, sys, math
from collections import defaultdict
S = sys.argv[1]; OUT = sys.argv[2]
D = json.load(open(f"{S}/per_strike.json")); spot = D["spot"]; B = 1e9
rows = {int(round(r["strike"] * 1000)): (r["call"], abs(r["put"])) for r in D["rows"]}   # strike mills; (call_modeled_magnitude, put_modeled_magnitude) both >= 0
BIN = 25000; HALF = 15; OUT_FRAC = 0.02; CAP = 6
GRAY = "#4a4a4a"; INK = "#e0e0e0"; MUTED = "#888"; AXIS = "#333"
def binm(m): return ((m + 12500) // 25000) * 25000
bins = defaultdict(lambda: [0.0, 0.0])
for m, (c, p) in rows.items():
    bins[binm(m)][0] += c; bins[binm(m)][1] += p
chain_mag = sum(c + p for c, p in bins.values()); chain_net = math.fsum(v for m in sorted(rows) for v in (rows[m][0], -rows[m][1]))  # pinned expression
center = binm(int(round(spot * 1000)))
window = [center + i * BIN for i in range(-HALF, HALF + 1)]
W = {b: bins.get(b, [0.0, 0.0]) for b in window}
outside = [b for b in sorted(bins) if b not in W and bins[b][0] + bins[b][1] >= OUT_FRAC * chain_mag and chain_mag > 0]
in_share = sum(c + p for c, p in W.values()) / chain_mag
# raw-strike anchors (producer semantics)
cw = max(rows, key=lambda m: (rows[m][0], -m)); pw = max(rows, key=lambda m: (rows[m][1], -m)); dm = max(rows, key=lambda m: (abs(rows[m][0] - rows[m][1]), -m))
anch = defaultdict(list); anch[binm(cw)].append("C"); anch[binm(pw)].append("P"); anch[binm(dm)].append("D")
def K(m): return m / 1000
def fN(x): return f"{x/B:+.1f}"
def fM(x): return f"{abs(x)/B:.1f}"
def dist(m): return (K(m) / spot - 1) * 100

def ladder():
    FW = 358; PITCH = 12; TOP = 28; LX = 40; X0 = 196; RX = 356; HALFW = 112
    H = TOP + PITCH * len(window) + 14
    scale = HALFW / max(max(c, p) for c, p in W.values())
    o = [f'<svg viewBox="0 0 {FW} {H}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="SPX call modeled magnitude and put modeled magnitude by 25-point strike bin with model net overlay" font-family="monospace" font-size="10.5">']
    o.append(f'<text x="{LX}" y="22" text-anchor="end" fill="{MUTED}">STRIKE</text>')
    o.append(f'<text x="{X0-6}" y="10" text-anchor="end" fill="{MUTED}" font-size="8.5">PUT MODELED MAGNITUDE &lt;</text><text x="{X0+6}" y="10" fill="{MUTED}" font-size="8.5">&gt; CALL MODELED MAGNITUDE</text>')
    o.append(f'<text x="{RX}" y="22" text-anchor="end" fill="{MUTED}">MODEL NET* $B</text>')
    o.append(f'<line x1="{X0}" y1="{TOP-2}" x2="{X0}" y2="{H-12}" stroke="{AXIS}" stroke-width="1"/>')
    for i, b in enumerate(reversed(window)):
        y = TOP + i * PITCH; cy = y + PITCH / 2; c, p = W[b]; n = c - p
        lab = f"{K(b):.0f}"; bold = (b % 100000 == 0)
        o.append(f'<g aria-label="bin {K(b):.0f} interval {K(b)-12.5:.1f} to {K(b)+12.5:.1f} call modeled magnitude {fM(c)}B put modeled magnitude {fM(p)}B model net {fN(n)}B">')
        o.append(f'<text x="{LX}" y="{cy+3.5}" text-anchor="end" fill="{INK if bold else MUTED}">{lab}</text>')
        if c or p:
            o.append(f'<rect x="{X0-p*scale:.1f}" y="{y+2}" width="{(p+c)*scale:.1f}" height="{PITCH-4}" fill="{GRAY}"/>')
        if n:
            w = abs(n) * scale; x = X0 if n > 0 else X0 - w
            o.append(f'<rect x="{x:.1f}" y="{y+3}" width="{w:.1f}" height="{PITCH-6}" fill="{INK}"/>')
        o.append(f'<text x="{RX}" y="{cy+3.5}" text-anchor="end" fill="{INK}">{fN(n)}</text>')
        if b in anch:
            o.append(f'<text x="{LX+22}" y="{cy+3.5}" fill="{INK}" font-size="9" text-anchor="end">{"".join(anch[b])}</text>')
        o.append('</g>')
    frac = (K(window[-1]) + 12.5 - spot) / (25 * len(window)); sy = TOP + frac * PITCH * len(window)
    o.append(f'<line x1="{LX+6}" y1="{sy:.1f}" x2="{RX}" y2="{sy:.1f}" stroke="{INK}" stroke-width="1" stroke-dasharray="3 2"/>')
    o.append(f'<text x="{LX+8}" y="{sy-2:.1f}" fill="{INK}" font-size="9">SPX CASH SPOT {spot:.2f}</text>')
    o.append('</svg>'); return "\n".join(o)

def outside_line():
    if not outside: return '<div class="label">outside bins &gt;= 2% of chain call+put modeled magnitude: none</div>'
    shown = outside[:CAP]
    parts = [f"{K(b):.0f} ({dist(b):+.1f}%) call+put modeled magnitude {fM(bins[b][0]+bins[b][1])}B model net* {fN(bins[b][0]-bins[b][1])}B" for b in shown]
    head = f"{len(shown)} of {len(outside)} outside bins &gt;= 2% of chain call+put modeled magnitude shown &middot; {len(outside)-len(shown)} more: " if len(outside) > CAP else "outside bins &gt;= 2% of chain call+put modeled magnitude: "
    return '<div class="label">' + head + "; ".join(parts) + '</div>'

def table():
    r = ['<details><summary class="label">all 31 bins + outside bins &#9656;</summary><div class="lvl-ladder">',
         '<div class="lvl-row label"><span>bin</span><span>interval</span><span>call modeled magnitude</span><span>put modeled magnitude</span><span>model net*</span></div>']
    for b in reversed(window):
        c, p = W[b]; r.append(f'<div class="lvl-row"><span>{K(b):.0f}{"".join(anch.get(b, []))}</span><span>{K(b)-12.5:.1f}-{K(b)+12.5:.1f}</span><span>{fM(c)}</span><span>{fM(p)}</span><span>{fN(c-p)}</span></div>')
    for b in outside:
        c, p = bins[b]; r.append(f'<div class="lvl-row"><span>{K(b):.0f} out</span><span>{dist(b):+.1f}%</span><span>{fM(c)}</span><span>{fM(p)}</span><span>{fN(c-p)}</span></div>')
    r.append('</div></details>'); return "\n".join(r)

pct_in = round(in_share * 100); pct_out = 100 - pct_in
head = f'''<div class="kv-grid">
<div class="label">Model net*</div><div class="value">{fN(chain_net)}B</div>
<div class="label">Largest raw-strike |model net|</div><div class="value">{K(dm):.0f} &nbsp; {dist(dm):+.2f}%</div>
<div class="label">Largest call-contract magnitude strike</div><div class="value">{K(cw):.0f} &nbsp; {dist(cw):+.2f}%</div>
<div class="label">Largest put-contract magnitude strike</div><div class="value">{K(pw):.0f} &nbsp; {dist(pw):+.2f}%</div>
<div class="label">0DTE</div><div class="value">2.5%</div>
<div class="label">Call+put modeled magnitude</div><div class="value">{fM(chain_mag)}B</div>
</div>
<div class="label">window shows {pct_in}% of chain call+put modeled magnitude &middot; {pct_out}% outside</div>'''
foot = '''<div class="label">C / P / D = raw-strike anchors (largest call-contract magnitude strike, largest put-contract magnitude strike, largest raw-strike |model net|) shown in their 25-pt bin; not the bin maximum.</div>
<div class="label">31 x 25-pt bins [b-12.5, b+12.5) around the SPX cash spot bin; recenters in 25-pt steps. Bin model net can near-balance across different strikes.</div>
<div class="label">All expirations combined, expiry mix hidden. SPX+SPXW combined, AM/PM settlement not modeled.</div>
<div class="label">* model net = call modeled magnitude - put modeled magnitude. Configured call-plus / put-minus convention; participant and dealer positioning are not measured. Call+put modeled magnitude = call modeled magnitude + put modeled magnitude, no sign assignment.</div>
<div class="label">as of 18:42 ET &middot; Cboe ~15m delayed source</div>'''
CSS = '''*{box-sizing:border-box;margin:0;padding:0}body{background:#0d0d0d;color:#e0e0e0;font-family:monospace;padding:8px}
.frame{width:360px}.block{border:1px solid #2a2a2a;border-radius:4px;margin-bottom:1rem;padding:1rem}
.label{color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em}.value{margin-top:0.25rem}
.kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:2px 0.75rem}h2{font-size:1rem;margin-bottom:.5rem}
.lvl-ladder{max-width:520px;font-size:0.72rem;line-height:1.5}.lvl-row{display:grid;grid-template-columns:5ch 11ch 1fr 1fr 6ch;column-gap:6px;white-space:nowrap;text-align:right}
summary{list-style:none;cursor:pointer}summary::-webkit-details-marker{display:none}svg{display:block;width:100%;height:auto;max-width:520px;margin:.5rem 0}'''
body = f'<div class="frame"><div class="block" id="gex-context"><h2>GEX <span class="label">(context only)</span></h2>{head}{ladder()}{outside_line()}{table()}{foot}</div></div>'
open(OUT, "w").write(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEX-4 corrected prototype</title><style>{CSS}</style><body>{body}</body>')
print("window", K(window[0]), K(window[-1]), "in", pct_in, "outside", [K(b) for b in outside], "anchors", {K(k): v for k, v in anch.items()})

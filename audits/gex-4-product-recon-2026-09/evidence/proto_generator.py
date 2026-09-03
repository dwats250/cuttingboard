"""GEX-4 prototypes: static inline SVG, no JS, dashboard tokens. Concepts A/B/C."""
import json, math, sys
from collections import defaultdict
S=sys.argv[1]; D=json.load(open(f"{S}/per_strike.json")); spot=D["spot"]; B=1e9
rows={r["strike"]:(r["call"],r["put"]) for r in D["rows"]}
BIN=25; HALF=15; OUT_FRAC=0.02
BLUE="#3987e5"; RED="#e66767"; GRAY="#4a4a4a"; INK="#e0e0e0"; MUTED="#888"; AXIS="#333"; SPOTC="#e0e0e0"
bins=defaultdict(lambda:[0.0,0.0])
for k,(c,p) in rows.items():
    b=math.floor((k+BIN/2)/BIN)*BIN; bins[b][0]+=c; bins[b][1]+=p
gross_total=sum(abs(c)+abs(p) for c,p in bins.values()); net_total=sum(c+p for c,p in bins.values())
center=math.floor((spot+BIN/2)/BIN)*BIN
window=[center+i*BIN for i in range(-HALF,HALF+1)]
W={b:bins.get(b,[0.0,0.0]) for b in window}
beyond=[b for b in sorted(bins) if b not in W and abs(bins[b][0])+abs(bins[b][1])>=OUT_FRAC*gross_total]
in_share=sum(abs(c)+abs(p) for c,p in W.values())/gross_total
# anchors from raw per-strike (producer semantics), mapped to bins
call_wall=max(rows, key=lambda k: rows[k][0]); put_wall=min(rows, key=lambda k: rows[k][1]); dom=max(rows, key=lambda k: abs(rows[k][0]+rows[k][1]))
def tobin(k): return math.floor((k+BIN/2)/BIN)*BIN
anch={tobin(call_wall):[], tobin(put_wall):[], tobin(dom):[]}
anch[tobin(call_wall)].append("C"); anch[tobin(put_wall)].append("P"); anch[tobin(dom)].append("D")
def fB(x): return f"{x/B:+.1f}"
def fG(x): return f"{x/B:.1f}"

def ladder(kind):
    """kind: 'net' (A) or 'netgross' (B). Vertical ladder, highest strike on top."""
    FW=358; PITCH=12; TOP=16; LX=40; X0=196; RX=356; HALFW=112
    H=TOP+PITCH*len(window)+14
    if kind=="net": scale=HALFW/max(abs(c+p) for c,p in W.values())
    else: scale=HALFW/max(max(abs(c),abs(p)) for c,p in W.values())
    o=[f'<svg viewBox="0 0 {FW} {H}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="SPX gamma notional by 25-point strike bin" font-family="monospace" font-size="10.5">']
    o.append(f'<text x="{LX}" y="10" text-anchor="end" fill="{MUTED}">STRIKE</text>')
    o.append(f'<text x="{X0-6}" y="10" text-anchor="end" fill="{RED}">put-side &lt;</text><text x="{X0+6}" y="10" fill="{BLUE}">&gt; call-side</text>')
    o.append(f'<text x="{RX}" y="10" text-anchor="end" fill="{MUTED}">NET $B</text>')
    o.append(f'<line x1="{X0}" y1="{TOP-2}" x2="{X0}" y2="{H-12}" stroke="{AXIS}" stroke-width="1"/>')
    for i,b in enumerate(reversed(window)):
        y=TOP+i*PITCH; cy=y+PITCH/2
        c,p=W[b]; n=c+p
        lab=f"{b:.0f}"; bold = (b%100==0)
        o.append(f'<text x="{LX}" y="{cy+3.5}" text-anchor="end" fill="{INK if bold else MUTED}">{lab}</text>')
        if kind=="netgross" and (c or p):
            o.append(f'<rect x="{X0-abs(p)*scale:.1f}" y="{y+2}" width="{(abs(p)+abs(c))*scale:.1f}" height="{PITCH-4}" fill="{GRAY}"/>')
        if n:
            w=abs(n)*scale; x=X0 if n>0 else X0-w
            o.append(f'<rect x="{x:.1f}" y="{y+3}" width="{w:.1f}" height="{PITCH-6}" fill="{BLUE if n>0 else RED}"><title>{b:.0f}: net {fB(n)}B (call-side {fG(c)}B, put-side {fG(abs(p))}B)</title></rect>')
        o.append(f'<text x="{RX}" y="{cy+3.5}" text-anchor="end" fill="{INK}">{fB(n)}</text>')
        if b in anch:
            o.append(f'<text x="{LX+22}" y="{cy+3.5}" fill="{INK}" font-size="9" text-anchor="end">{"".join(anch[b])}</text>')
    # spot line at exact position between rows
    frac=(window[-1]+BIN/2-spot)/(BIN*len(window)); sy=TOP+frac*PITCH*len(window)
    o.append(f'<line x1="{LX+6}" y1="{sy:.1f}" x2="{RX}" y2="{sy:.1f}" stroke="{SPOTC}" stroke-width="1" stroke-dasharray="3 2"/>')
    o.append(f'<text x="{LX+8}" y="{sy-2:.1f}" fill="{SPOTC}" font-size="9">SPX {spot:.2f}</text>')
    o.append('</svg>')
    return "\n".join(o)

def columns():
    """C: horizontal axis (strike left->right), net columns above/below zero, gross faint."""
    FW=358; H=170; L=8; R=352; TOPY=14; BOT=140; ZY=(TOPY+BOT)/2
    n=len(window); cw=(R-L)/n; halfh=(BOT-TOPY)/2
    scale=halfh/max(max(abs(c),abs(p)) for c,p in W.values())
    o=[f'<svg viewBox="0 0 {FW} {H}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" font-family="monospace" font-size="9.5">']
    o.append(f'<line x1="{L}" y1="{ZY}" x2="{R}" y2="{ZY}" stroke="{AXIS}"/>')
    for i,b in enumerate(window):
        x=L+i*cw; c,p=W[b]; nn=c+p
        if c or p:
            o.append(f'<rect x="{x+1:.1f}" y="{ZY-abs(c)*scale:.1f}" width="{cw-2:.1f}" height="{(abs(c)+abs(p))*scale:.1f}" fill="{GRAY}"/>')
        if nn:
            h=abs(nn)*scale; y=ZY-h if nn>0 else ZY
            o.append(f'<rect x="{x+2:.1f}" y="{y:.1f}" width="{cw-4:.1f}" height="{h:.1f}" fill="{BLUE if nn>0 else RED}"><title>{b:.0f}: net {fB(nn)}B</title></rect>')
        if b%100==0:
            o.append(f'<text x="{x+cw/2:.1f}" y="{BOT+12}" text-anchor="middle" fill="{MUTED}">{b:.0f}</text>')
        if b in anch:
            o.append(f'<text x="{x+cw/2:.1f}" y="{TOPY-3}" text-anchor="middle" fill="{MUTED}" font-size="8">{"".join(anch[b])}</text>')
    sx=L+((spot-(window[0]-BIN/2))/(BIN*n))*(R-L)
    o.append(f'<line x1="{sx:.1f}" y1="{TOPY}" x2="{sx:.1f}" y2="{BOT}" stroke="{SPOTC}" stroke-dasharray="3 2"/>')
    o.append(f'<text x="{sx+3:.1f}" y="{BOT+24}" fill="{SPOTC}" font-size="9">SPX {spot:.0f}</text>')
    o.append(f'<text x="{L}" y="{TOPY+8}" fill="{BLUE}">call-side up</text><text x="{L}" y="{BOT-2}" fill="{RED}">put-side down</text>')
    o.append('</svg>')
    return "\n".join(o)

def numeric_ladder(n=8):
    top=sorted(W, key=lambda b:-(abs(W[b][0])+abs(W[b][1])))[:n]
    r=['<details><summary class="label">strike bins by gross &#9656;</summary><div class="lvl-ladder">',
       '<div class="lvl-row label"><span>bin</span><span>dist</span><span>call-side</span><span>put-side</span><span>net</span></div>']
    for b in sorted(top, reverse=True):
        c,p=W[b]; r.append(f'<div class="lvl-row"><span>{b:.0f}</span><span>{(b/spot-1)*100:+.1f}%</span><span>{fG(c)}</span><span>{fG(abs(p))}</span><span>{fB(c+p)}</span></div>')
    r.append('</div></details>'); return "\n".join(r)

def beyond_line():
    if not beyond: return '<div class="label">beyond window: none &gt;= 2% of chain gross</div>'
    parts=[f"{b:.0f} ({(b/spot-1)*100:+.1f}%) gross {fG(abs(bins[b][0])+abs(bins[b][1]))}B net {fB(bins[b][0]+bins[b][1])}B" for b in beyond]
    return '<div class="label">beyond window: '+"; ".join(parts)+'</div>'

head = f'''<div class="kv-grid">
<div class="label">Net</div><div class="value">{fB(net_total)}B *</div>
<div class="label">Gross</div><div class="value">{fG(gross_total)}B &nbsp; <span class="label">{in_share*100:.0f}% within window</span></div>
</div>'''
foot = '''<div class="label">31 x 25-pt strike bins around SPX spot; all expirations; SPX+SPXW. C / P / D = largest call-side, put-side, |net| strike.</div>
<div class="label">* net is signed under a configured positioning assumption (calls +1 / puts -1); positioning is not measured. gray = call-side + put-side gross, no sign assumption.</div>
<div class="label">as of 18:42 ET &middot; Cboe ~15m delayed source</div>'''
CSS='''*{box-sizing:border-box;margin:0;padding:0}body{background:#0d0d0d;color:#e0e0e0;font-family:monospace;padding:8px}
.frame{width:360px;display:inline-block;vertical-align:top;margin:0 8px 16px 0}.block{border:1px solid #2a2a2a;border-radius:4px;margin-bottom:1rem;padding:1rem}
.label{color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em}.value{margin-top:0.25rem}
.kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:2px 0.75rem}h2{font-size:1rem;margin-bottom:.5rem}
.lvl-ladder{max-width:520px;font-size:0.72rem;line-height:1.5}.lvl-row{display:grid;grid-template-columns:5ch 6ch 1fr 1fr 6ch;column-gap:8px;white-space:nowrap;text-align:right}
summary{list-style:none;cursor:pointer}summary::-webkit-details-marker{display:none}svg{display:block;width:100%;height:auto;max-width:520px;margin:.5rem 0}'''
def page(title, body):
    return f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style><body>{body}</body>'
def card(t, inner):
    return f'<div class="frame"><div class="block" id="gex-context"><h2>GEX <span class="label">(context only)</span> <span class="label">{t}</span></h2>{head}{inner}{beyond_line()}{numeric_ladder()}{foot}</div></div>'
A=card("A: net ladder", ladder("net")); Bc=card("B: net + gross ladder", ladder("netgross")); C=card("C: columns + ladder", columns())
open(f"{S}/proto_a.html","w").write(page("PROTO A",A)); open(f"{S}/proto_b.html","w").write(page("PROTO B",Bc)); open(f"{S}/proto_c.html","w").write(page("PROTO C",C))
open(f"{S}/proto_b_final.html","w").write(page("PROTO B final",Bc))
print("written; window",window[0],window[-1],"beyond",beyond,"in_share",round(in_share,2),"anchors",anch)

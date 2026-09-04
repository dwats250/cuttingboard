"""Per-strike GEX structure analysis using the producer's own admissibility + formula."""
import sys, json, math
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "tools")
import gex_snapshot as g

S = sys.argv[1]
p = json.load(open(f"{S}/spx_raw.json"))
options, spot, feed_dt = g._validate_top_level(p)
obs_date = feed_dt.astimezone(ZoneInfo(g.EASTERN)).date()
inc = []
for r in options:
    c, why = g._classify_row(r)
    if c: inc.append(c)
print(f"spot={spot} feed={feed_dt.isoformat()} obs_date={obs_date} included={len(inc)}/{len(options)}")

call = defaultdict(float); put = defaultdict(float)
call0 = defaultdict(float); put0 = defaultdict(float)
by_exp = defaultdict(float); by_exp_net = defaultdict(float)
by_strike_exp = defaultdict(lambda: defaultdict(float))
for c in inc:
    v = g._gex(c, spot)
    (call if c.cp=="C" else put)[c.strike] += v
    by_exp[c.expiry] += abs(v); by_exp_net[c.expiry] += v
    by_strike_exp[c.strike][c.expiry] += v
    if c.expiry == obs_date:
        (call0 if c.cp=="C" else put0)[c.strike] += v
strikes = sorted(set(call)|set(put))
net = {k: call.get(k,0.0)+put.get(k,0.0) for k in strikes}
ab  = {k: abs(call.get(k,0.0))+abs(put.get(k,0.0)) for k in strikes}
tot = sum(net.values()); atot = sum(ab.values())
B=1e9
print(f"\nTOTAL net={tot/B:+.1f}B  abs={atot/B:.1f}B  |net|/abs={abs(tot)/atot:.3f}  strikes={len(strikes)}  range={strikes[0]}..{strikes[-1]}")
print(f"call_wall={g._select_call_wall(call)}  put_wall={g._select_put_wall(put)}  dominant={g._select_dominant(net)}")

def d(k): return (k/spot-1)*100
def row(k): return f"{k:8.0f} {d(k):+6.2f}%  call={call.get(k,0)/B:+7.2f}B put={put.get(k,0)/B:+7.2f}B net={net[k]/B:+7.2f}B abs={ab[k]/B:6.2f}B  |net|/abs={abs(net[k])/ab[k] if ab[k] else 0:.2f}"

print("\nTOP 15 by |net|:")
for k in sorted(strikes, key=lambda k:-abs(net[k]))[:15]: print(row(k))
print("\nTOP 15 by abs (call+put magnitude):")
for k in sorted(strikes, key=lambda k:-ab[k])[:15]: print(row(k))
print("\nTOP 10 call:")
for k in sorted(call, key=lambda k:-call[k])[:10]: print(row(k))
print("\nTOP 10 put (most negative):")
for k in sorted(put, key=lambda k:put[k])[:10]: print(row(k))

print("\nCANCELLATION: strikes with abs >= 1% of abs-total AND |net|/abs < 0.35")
big = [k for k in strikes if ab[k] >= 0.01*atot]
for k in big:
    if abs(net[k])/ab[k] < 0.35: print(row(k))
print(f"(strikes with abs>=1% of total: {len(big)}; their abs share={sum(ab[k] for k in big)/atot:.2f}; their net sum={sum(net[k] for k in big)/B:+.1f}B)")

print("\nWINDOW SHARES (of abs total / of net total) within +/- pct of spot:")
for w in (1,2,3,5,7,10):
    ks=[k for k in strikes if abs(d(k))<=w]
    print(f"  +/-{w:2d}%: strikes={len(ks):4d} abs_share={sum(ab[k] for k in ks)/atot:.2f} net_sum={sum(net[k] for k in ks)/B:+.1f}B  (|net| sum inside={sum(abs(net[k]) for k in ks)/B:.1f}B)")

print("\nSTRIKE GRID near spot (pitch between consecutive strikes with abs>0):")
near=[k for k in strikes if abs(d(k))<=3 and ab[k]>0]
pitches=defaultdict(int)
for a,b in zip(near,near[1:]): pitches[b-a]+=1
print("  ", dict(sorted(pitches.items())), f"n={len(near)}")
near5=[k for k in near if k%25==0]
print(f"  strikes on 25-grid within 3%: {len(near5)}; abs share of 25-grid among near: {sum(ab[k] for k in near5)/sum(ab[k] for k in near):.2f}")

print("\nEXPIRY abs share (top 10):")
for e in sorted(by_exp, key=lambda e:-by_exp[e])[:10]:
    print(f"  {e} dte={(e-obs_date).days:4d} abs={by_exp[e]/B:6.1f}B share={by_exp[e]/atot:.3f} net={by_exp_net[e]/B:+6.1f}B")
zero = [c for c in inc if c.expiry==obs_date]
print(f"\n0DTE contracts={len(zero)} abs={sum(abs(g._gex(c,spot)) for c in zero)/B:.1f}B share={sum(abs(g._gex(c,spot)) for c in zero)/atot:.3f}")
net0={k:call0.get(k,0)+put0.get(k,0) for k in set(call0)|set(put0)}
print("0DTE top 8 by |net|:")
for k in sorted(net0, key=lambda k:-abs(net0[k]))[:8]:
    print(f"  {k:8.0f} {d(k):+6.2f}% call={call0.get(k,0)/B:+6.2f}B put={put0.get(k,0)/B:+6.2f}B net={net0[k]/B:+6.2f}B")

print("\nWHERE DOES THE 8000-STYLE FAR STRIKE COME FROM (top-abs strike, by expiry):")
kk = max(strikes, key=lambda k: ab[k])
for e,v in sorted(by_strike_exp[kk].items(), key=lambda kv:-abs(kv[1]))[:5]:
    print(f"  strike {kk} exp {e} dte={(e-obs_date).days} net={v/B:+.2f}B")
# call/put by expiry at that strike
ce=defaultdict(float); pe=defaultdict(float)
for c in inc:
    if c.strike==kk: (ce if c.cp=="C" else pe)[c.expiry]+=g._gex(c,spot)
for e in sorted(set(ce)|set(pe), key=lambda e:-(abs(ce.get(e,0))+abs(pe.get(e,0))))[:4]:
    print(f"    {e} call={ce.get(e,0)/B:+.2f}B put={pe.get(e,0)/B:+.2f}B")

# Save per-strike table for prototypes
out=[{"strike":k,"dist_pct":d(k),"call":call.get(k,0.0),"put":put.get(k,0.0),"net":net[k],"abs":ab[k],
      "call0":call0.get(k,0.0),"put0":put0.get(k,0.0)} for k in strikes]
json.dump({"spot":spot,"feed":feed_dt.isoformat(),"obs_date":obs_date.isoformat(),"total":tot,"abs_total":atot,"rows":out},
          open(f"{S}/per_strike.json","w"))

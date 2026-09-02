# PRD-327 D2 measurements (design evidence, 390x844, headless Chrome 151)

Method: `scripts/preview_fixtures.py` renders the PRD-326 preview fixtures at
main `f555b48`; `measure.py` injects a `getBoundingClientRect` reporter into a
copy of each file and reads it back with `google-chrome --headless=new
--dump-dom --window-size=390,844`. `proto_gen.py` rewrites ONLY the
VERDICT/TAPE/TODAY HTML of each rendered fixture into Concept A / Concept B
and asserts the HTML from `id="watching-zone"` onward is byte-identical to the
D1 render. Values are pixels from the document top (scrollY-adjusted).
Fixture timestamps are in the past, so the client-side staleness banner
("BOARD Nd OLD", ~48 px incl. margin) is VISIBLE in every capture; a fresh
live board hides it and every position below shifts up by ~48 px.

Columns: verd/tape/today/ctx = zone heights; watch@ = top of #watching-zone;
hdr@ = top of first .candidate-card .card-header; chart@ = top of first
.candidate-card .setup-chart; docH = document height.

## D1 baseline (main f555b48)

| case | verd | tape | today | watch@ | hdr@ | chart@ | docH |
|---|---|---|---|---|---|---|---|
| primary_chart_stay_flat | 202 | 294 | 95 | 655 | 950 | 1093 | 1770 |
| primary_chart_locked | 203 | 294 | 95 | 655 | 950 | 1060 | 1705 |
| primary_chart_permitted | 182 | 294 | 95 | 635 | 930 | 1073 | 2003 |
| red_folder_expiring | 202 | 294 | 130 | 690 | 985 | - | 1278 |
| macro_tape_no_data | 202 | 294 | 95 | 655 | 950 | - | 1243 |
| market_map_stale_with_bars | 202 | 294 | 95 | 655 | - | - | 1011 |
| candidate_no_candidates | 202 | 294 | 95 | 655 | - | - | 1062 |
| primary_chart_c_grade | 202 | 294 | 95 | 655 | - | 1160 | 1622 |

## Concept A (three zones kept; overhead trimmed)

| case | verd | tape | today | watch@ | hdr@ | chart@ | docH |
|---|---|---|---|---|---|---|---|
| primary_chart_stay_flat | 135 | 223 | 95 | 516 | 811 | 954 | 1632 |
| primary_chart_locked | 136 | 223 | 95 | 517 | 812 | 922 | 1567 |
| primary_chart_permitted | 115 | 223 | 95 | 496 | 791 | 934 | 1865 |
| red_folder_expiring | 135 | 223 | 130 | 552 | 847 | - | 1140 |
| coherence_mixed | 219 | 223 | 95 | 600 | - | - | 868 |
| market_map_stale_with_bars | 135 | 223 | 95 | 516 | - | - | 872 |
| candidate_no_candidates | 135 | 223 | 95 | 516 | - | - | 923 |
| primary_chart_c_grade | 135 | 223 | 95 | 516 | - | 1021 | 1484 |

## Concept B (VERDICT + one CONTEXT block; RECOMMENDED)

| case | verd | ctx | (tape sub) | (today sub) | watch@ | hdr@ | chart@ | docH |
|---|---|---|---|---|---|---|---|---|
| primary_chart_stay_flat | 135 | 219 | 129 | 24 | 402 | 697 | 840 | 1518 |
| primary_chart_locked | 136 | 219 | 129 | 24 | 403 | 698 | 808 | 1453 |
| primary_chart_permitted | 115 | 219 | 129 | 24 | 382 | 677 | 820 | 1750 |
| red_folder_expiring | 135 | 237 | 129 | 41 | 420 | 715 | - | 1008 |
| sunday_premarket | 135 | 258 | 129 | 62 | 440 | - | - | 847 |
| coherence_mixed | 219 | 219 | 129 | 24 | 486 | - | - | 757 |
| market_map_stale_with_bars | 135 | 219 | 129 | 24 | 402 | - | - | 758 |
| candidate_no_candidates | 135 | 219 | 129 | 24 | 402 | - | - | 809 |
| primary_chart_c_grade | 135 | 219 | 129 | 24 | 402 | - | 907 | 1370 |

Stay-flat deltas vs D1: pre-WATCHING 655 -> 402 (-253 px, -39%); primary
header 950 -> 697 (-253); chart top 1093 -> 840 (-253). Fixture-visible
staleness banner included; fresh live board: header ~649, chart ~792.

Files: `conceptB_*.html` and `conceptA_*.html` are the prototype renders
measured above; `d1_baseline_*.html` is the D1 render they were derived from.
Re-run: `python3 measure.py <html...>` from this directory (needs
google-chrome). Screenshots are not committed; regenerate with
`google-chrome --headless=new --no-sandbox --hide-scrollbars --window-size=390,844 --screenshot=out.png file://<html>`.

## Golden below-seam SHA-256 at main f555b48 (slice from the watching-zone open tag to EOF)

```
{
 "tests/data/dashboard_pre_gex_golden.html": "3f0f59a1289024466ee22a0f3ad2dbfe503a0c4cec96ba04dc868ded759da412",
 "tests/data/dashboard_pre_a1c_chart_golden.html": "b1302d8a87c5e6db2bff466128face24a47a4c8d0d05f2777af206856b5ad00c"
}
```

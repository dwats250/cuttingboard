# PRD-327 D2 measurements (design evidence, TRUE 390x844 CSS viewport, headless Chrome 151)

Method (revised after Sol REQ-1): `scripts/preview_fixtures.py` renders the
PRD-326 preview fixtures at main `f555b48` into the git-ignored
`reports/output/`; `measure.py` drives headless Chrome over the DevTools
protocol, applies `Emulation.setDeviceMetricsOverride(390x844, mobile)`, waits
for the load event plus a 500 ms settle so the inline staleness script has run,
and FAILS unless `window.innerWidth == 390`, `innerHeight == 844` and the
`(max-width:430px)` phone media query matches. `proto_gen.py` rewrites ONLY the
VERDICT/TAPE/TODAY HTML of each rendered fixture into Concept A / Concept B and
asserts the HTML from `id="watching-zone"` onward is byte-identical to the D1
render. Values are CSS px from the document top.

The earlier committed tables (a0a116b) were captured by `--window-size` +
`--dump-dom`, which yielded a 500x757 viewport with the phone block inactive
and the banner unsettled; they are withdrawn and replaced by the tables below.

Two rows per case: the fixture as rendered (timestamps are historical, so the
client-side banner "BOARD Nd OLD" is VISIBLE, 26 px + 8 px margin), and
`[fresh]` = same page with the banner forced hidden, simulating a fresh live
board. Columns: verd/tape/today/ctx = zone heights; watch@ = top of
`#watching-zone`; hdr@ = top of the first `.candidate-card .card-header`;
chart@ = top of the first `.candidate-card .setup-chart`; docH = document height.

## D1 baseline (main f555b48)

```
case                                    verd  tape today   ctx watch@   hdr@  chart@   docH banner
fixture_primary_chart_stay_flat          210   305    94     -    641    864    1007   1589   26px
fixture_primary_chart_stay_flat [fresh   176   305    94     -    607    830     973   1555 hidden
fixture_primary_chart_locked             230   305    94     -    660    883     993   1543   26px
fixture_primary_chart_locked [fresh]     196   305    94     -    626    849     959   1509 hidden
fixture_primary_chart_permitted          192   305    94     -    623    846     989   1824   26px
fixture_primary_chart_permitted [fresh   158   305    94     -    589    812     955   1790 hidden
fixture_red_folder_expiring              210   305   111     -    657    881       -   1132   26px
fixture_red_folder_expiring [fresh]      176   305   111     -    623    847       -   1098 hidden
fixture_macro_tape_no_data               210   290    94     -    626    849       -   1100   26px
fixture_macro_tape_no_data [fresh]       176   290    94     -    592    815       -   1066 hidden
fixture_market_map_stale_with_bars       210   305    94     -    641      -       -    943   26px
fixture_market_map_stale_with_bars [fr   176   305    94     -    607      -       -    909 hidden
fixture_candidate_no_candidates          210   305    94     -    641      -       -    933   26px
fixture_candidate_no_candidates [fresh   176   305    94     -    607      -       -    899 hidden
fixture_sunday_premarket                 210   305   111     -    657      -       -    950   26px
fixture_sunday_premarket [fresh]         176   305   111     -    623      -       -    916 hidden
fixture_coherence_mixed                  296   305    94     -    727      -       -    926   26px
fixture_coherence_mixed [fresh]          262   305    94     -    693      -       -    892 hidden
fixture_session_inactive                 210   305    94     -    641      -       -    933   26px
fixture_session_inactive [fresh]         176   305    94     -    607      -       -    899 hidden
fixture_trend_awaiting_data              210   305    94     -    641    864       -   1115   26px
fixture_trend_awaiting_data [fresh]      176   305    94     -    607    830       -   1081 hidden
fixture_primary_chart_c_grade            210   305    94     -    641      -    1089   1456   26px
fixture_primary_chart_c_grade [fresh]    176   305    94     -    607      -    1055   1422 hidden
```

## Concept A (three zones kept; overhead trimmed; D2-Q2 narrowed) - RECOMMENDED

```
case                                    verd  tape today   ctx watch@   hdr@  chart@   docH banner
fixture_primary_chart_stay_flat          168   234    94     -    527    750     893   1476   26px
fixture_primary_chart_stay_flat [fresh   134   234    94     -    493    716     859   1442 hidden
fixture_primary_chart_locked             187   234    94     -    547    770     880   1430   26px
fixture_primary_chart_locked [fresh]     153   234    94     -    513    736     846   1396 hidden
fixture_primary_chart_permitted          150   234    94     -    509    732     875   1711   26px
fixture_primary_chart_permitted [fresh   116   234    94     -    475    698     841   1677 hidden
fixture_red_folder_expiring              168   234   111     -    544    767       -   1018   26px
fixture_red_folder_expiring [fresh]      134   234   111     -    510    733       -    984 hidden
fixture_macro_tape_no_data               168   219    94     -    513    736       -    987   26px
fixture_macro_tape_no_data [fresh]       134   219    94     -    479    702       -    953 hidden
fixture_market_map_stale_with_bars       168   283    94     -    576      -       -    878   26px
fixture_market_map_stale_with_bars [fr   134   283    94     -    542      -       -    844 hidden
fixture_candidate_no_candidates          168   234    94     -    527      -       -    844   26px
fixture_candidate_no_candidates [fresh   134   234    94     -    493      -       -    844 hidden
fixture_sunday_premarket                 168   283   111     -    593      -       -    885   26px
fixture_sunday_premarket [fresh]         134   283   111     -    559      -       -    851 hidden
fixture_coherence_mixed                  254   283    94     -    662      -       -    861   26px
fixture_coherence_mixed [fresh]          220   283    94     -    628      -       -    844 hidden
fixture_session_inactive                 168   283    94     -    576      -       -    868   26px
fixture_session_inactive [fresh]         134   283    94     -    542      -       -    844 hidden
fixture_trend_awaiting_data              168   234    94     -    527    750       -   1001   26px
fixture_trend_awaiting_data [fresh]      134   234    94     -    493    716       -    967 hidden
fixture_primary_chart_c_grade            168   234    94     -    527      -     975   1343   26px
fixture_primary_chart_c_grade [fresh]    134   234    94     -    493      -     941   1309 hidden
```

## Concept B (VERDICT + one CONTEXT block with visible TAPE/TODAY sub-captions) - alternative, not recommended

```
case                                    verd  tape today   ctx watch@   hdr@  chart@   docH banner
fixture_primary_chart_stay_flat          168   173    40   262    454    677     820   1403   26px
fixture_primary_chart_stay_flat [fresh   134   173    40   262    420    643     786   1369 hidden
fixture_primary_chart_locked             187   173    40   262    474    697     807   1357   26px
fixture_primary_chart_locked [fresh]     153   173    40   262    440    663     773   1323 hidden
fixture_primary_chart_permitted          150   173    40   262    436    659     802   1638   26px
fixture_primary_chart_permitted [fresh   116   173    40   262    402    625     768   1604 hidden
fixture_red_folder_expiring              168   173    57   279    471    694       -    945   26px
fixture_red_folder_expiring [fresh]      134   173    57   279    437    660       -    911 hidden
fixture_macro_tape_no_data               168   158    40   248    440    663       -    914   26px
fixture_macro_tape_no_data [fresh]       134   158    40   248    406    629       -    880 hidden
fixture_market_map_stale_with_bars       168   220    40   309    501      -       -    844   26px
fixture_market_map_stale_with_bars [fr   134   220    40   309    467      -       -    844 hidden
fixture_candidate_no_candidates          168   173    40   262    454      -       -    844   26px
fixture_candidate_no_candidates [fresh   134   173    40   262    420      -       -    844 hidden
fixture_sunday_premarket                 168   220    77   346    538      -       -    844   26px
fixture_sunday_premarket [fresh]         134   220    77   346    504      -       -    844 hidden
fixture_coherence_mixed                  254   220    40   309    587      -       -    844   26px
fixture_coherence_mixed [fresh]          220   220    40   309    553      -       -    844 hidden
fixture_session_inactive                 168   220    40   309    501      -       -    844   26px
fixture_session_inactive [fresh]         134   220    40   309    467      -       -    844 hidden
fixture_trend_awaiting_data              168   173    40   262    454    677       -    928   26px
fixture_trend_awaiting_data [fresh]      134   173    40   262    420    643       -    894 hidden
fixture_primary_chart_c_grade            168   173    40   262    454      -     902   1270   26px
fixture_primary_chart_c_grade [fresh]    134   173    40   262    420      -     868   1236 hidden
```

## Golden below-seam SHA-256 at main f555b48

Slice = bytes after the FIRST occurrence of the literal opening tag
`<div class="block operator-zone" id="watching-zone">` to end of file, read as
raw bytes from `git show f555b48:<path>` (identical to the checked-out file;
no newline normalisation). Command:

```
python3 -c 'import hashlib,subprocess,sys;seam=b"<div class=\"block operator-zone\" id=\"watching-zone\">";b=subprocess.run(["git","show","f555b48:"+sys.argv[1]],capture_output=True).stdout;print(hashlib.sha256(b.split(seam,1)[1]).hexdigest())' tests/data/dashboard_pre_gex_golden.html
```

```
{
 "tests/data/dashboard_pre_gex_golden.html": "3f0f59a1289024466ee22a0f3ad2dbfe503a0c4cec96ba04dc868ded759da412",
 "tests/data/dashboard_pre_a1c_chart_golden.html": "b1302d8a87c5e6db2bff466128face24a47a4c8d0d05f2777af206856b5ad00c"
}
```

## Preview-fixture below-seam SHA-256 at main f555b48

Same slice rule applied to each `reports/output/fixture_<case>.html` written by
`scripts/preview_fixtures.py` at f555b48 (hermetic; re-rendering twice gave
identical hashes). These are the R9 per-fixture constants.

```
{
 "fixture_candidate_no_candidates.html": "93353b41dd00809ab208a7513ee021c633ede3e0335343d2ff2d02074449fff0",
 "fixture_coherence_mixed.html": "51850ddad0d7dbca7f3f32edcf7aa6499f87939c10e6c94371111546606c1e61",
 "fixture_healthy_baseline.html": "22411afea2b845921c3f3e4d89ba20545772026e5af1963639ebc4ddd598e46d",
 "fixture_lineage_missing.html": "f2c400a09a706294849390fb89b8f2e30b2e366ef2b0359eb52ed49c845e27f8",
 "fixture_macro_tape_no_data.html": "9d851f47b37977f0f5e6951cae3f167fc8d9648a170aec8c6a0b2e0fef626bf1",
 "fixture_market_map_stale_with_bars.html": "a961e8b6d33de01538eb673acde9bb26551707fb2c4637eb9a616a9db2e7db86",
 "fixture_primary_chart_c_grade.html": "29e1f92eebb7a683036272fe7e10659c4b0a451c092fb63eb98b6341b7e3abe3",
 "fixture_primary_chart_locked.html": "880d12815f169b01a2c5dd4d8f67ab0136e5a0a68ef4926f55429f6e89b092e2",
 "fixture_primary_chart_permitted.html": "6efe17066e345d61e9ea5fccef512399269aa8b4d34585a1a83a84bcfb484150",
 "fixture_primary_chart_stay_flat.html": "4975826b1399252807f5975170f51c1e7012026ed0e3982cb83cdfb8d75ce83e",
 "fixture_red_folder_error.html": "42cd240687c02587b52a2b5d2fc80558d51adf2ed4b4151e47f50577f7c9a06a",
 "fixture_red_folder_expiring.html": "6c66fa8278a92f5ab226714304387a51de1aa464dc18185467512317c05c1dac",
 "fixture_session_inactive.html": "eb0377a5a4038523c0c86876e58b204e6f623b3c75b6887202873adb8a8c974a",
 "fixture_sunday_premarket.html": "e92f5871f26d42dd4e6f483348309a323c0d7553c2f8a3d7027c21d57604d43a",
 "fixture_trend_awaiting_data.html": "633814ecb2d118b07b08651cb31ef336bdc942837a2fd01c0727a14d91324030",
 "fixture_trend_no_data.html": "e211363ed9962c96e7b8c925bc70660481ee18c2c0c1d5acdba490a5b9888a4c"
}
```

Files: `conceptA_*.html` / `conceptB_*.html` are REPRESENTATIVE prototype
renders (five Concept A cases, three Concept B cases); every other table row
is regenerated by `proto_gen.py` from the fixture renders. `d1_baseline_*.html`
is the D1 render they derive from. Screenshots are not committed; `measure.py
--shots DIR` writes `<case>_top.png` (390x844) and `<case>_full.png`.

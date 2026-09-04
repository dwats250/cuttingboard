#!/usr/bin/env python3
"""Deterministic literal pin for the GEX-4 current candidate (Event-2 final mechanical repair).

Pins the outside-bin quantity label as exactly MODEL NET* in (1) the recon section 12
contract line, (2) the prototype generator source, (3) the generated prototype HTML, and
asserts the superseded bare forms (NET <y>B / "model net <value>") cannot silently return
on the outside-bin line. Stdlib only. Exit 0 = all pins hold; non-zero = a pin failed.
Run from the repository root: python audits/gex-4-product-recon-2026-09/evidence/check_outside_bin_label.py
"""
import re, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent
RECON = D / "GEX_4_PRODUCT_RECON_2026-09-03.md"
GEN = D / "evidence" / "proto_generator_corrected.py"
HTML = D / "evidence" / "proto_corrected_ladder.html"
failures = []

recon = RECON.read_text(encoding="utf-8")
m = re.search(r'- outside line: "OUTSIDE BINS >= 2% OF CHAIN CALL\+PUT MODELED MAGNITUDE: <bin> \(<dist>\) CALL\+PUT MODELED MAGNITUDE <x>B ([^\n]+)\n  <y>B"', recon)
if not m: failures.append("recon: section-12 outside line not found in the expected shape")
elif m.group(1) != "MODEL NET*": failures.append(f"recon: outside-bin label is {m.group(1)!r}, expected 'MODEL NET*'")
if re.search(r'<x>B NET\n  <y>B', recon): failures.append("recon: superseded bare 'NET <y>B' form present")

gen = GEN.read_text(encoding="utf-8")
line = next((l for l in gen.splitlines() if "for b in shown]" in l), "")
if "model net* {fN(" not in line: failures.append("generator: outside_line() does not print 'model net*'")
if re.search(r"B model net \{fN", line): failures.append("generator: superseded bare 'model net' on the outside line")

html = HTML.read_text(encoding="utf-8")
outside = re.findall(r'<div class="label">([^<]*outside bins &gt;= 2%[^<]*)</div>', html)
if not outside: failures.append("html: outside-bin line not found")
for l in outside:
    if re.search(r"\bmodel net [-+0-9]", l): failures.append("html: superseded bare 'model net <value>' on the outside line")
    if "model net*" not in l and "none" not in l.lower(): failures.append("html: outside line lacks 'model net*'")

for f in failures: print("FAIL:", f)
print("PIN OK: outside-bin label == MODEL NET* in recon section 12, generator, generated prototype" if not failures else f"{len(failures)} pin failure(s)")
sys.exit(1 if failures else 0)

#!/usr/bin/env bash
# prd_open.sh — scaffold the Stage-0 artifacts for a new PRD.
#
# Mirror of scripts/prd_close.sh for the *opening* edits. Updates (does NOT
# commit unless --commit):
#   - docs/prd_history/PRD-NNN.md  : new scaffold with a STATUS: IN PROGRESS line
#   - docs/PRD_REGISTRY.md         : insert an IN PROGRESS row
#   - docs/prd_index.json          : insert a sorted IN PROGRESS entry
#                                    (latest_complete / next_prd are NOT touched)
#
# Usage:
#   scripts/prd_open.sh \
#       --prd 161 \
#       --title "Hourly market_map robustness" \
#       --lane STANDARD \
#       --class CONSUMER \
#       --summary "logs/market_map.json is shared across modes ..." \
#       [--commit]
#
# After running, review the diff (`git diff`) and stage / commit explicitly,
# or pass --commit to commit as "PRD-NNN: stage 0".

set -euo pipefail

PRD=""
TITLE=""
LANE=""
CLASS=""
SUMMARY=""
DO_COMMIT=0

usage() {
    cat <<'USAGE'
Usage: prd_open.sh --prd <NNN> --title "<title>" --lane <LANE> --class <CLASS> \
                   [--summary "<one-line problem>"] [--commit]

  --commit   stage + commit the scaffold as "PRD-NNN: stage 0"
USAGE
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prd)     PRD="$2"; shift 2 ;;
        --title)   TITLE="$2"; shift 2 ;;
        --lane)    LANE="$2"; shift 2 ;;
        --class)   CLASS="$2"; shift 2 ;;
        --summary) SUMMARY="$2"; shift 2 ;;
        --commit)  DO_COMMIT=1; shift ;;
        -h|--help) usage ;;
        *) echo "unknown arg: $1" >&2; usage ;;
    esac
done

[ -n "$PRD" ]   || { echo "missing --prd"   >&2; usage; }
[ -n "$TITLE" ] || { echo "missing --title" >&2; usage; }
[ -n "$LANE" ]  || { echo "missing --lane"  >&2; usage; }
[ -n "$CLASS" ] || { echo "missing --class" >&2; usage; }

# Normalize PRD identifier; zero-pad to 3 digits (registry rows require it).
case "$PRD" in
    PRD-*) PRD_NUM="${PRD#PRD-}";;
    *)     PRD_NUM="$PRD";;
esac
PRD_NUM=$((10#$PRD_NUM))
NNN=$(printf "%03d" "$PRD_NUM")
PRD_ID="PRD-${NNN}"
PRD_FILE="docs/prd_history/${PRD_ID}.md"
REGISTRY="docs/PRD_REGISTRY.md"
INDEX="docs/prd_index.json"

[ -f "$REGISTRY" ] || { echo "$REGISTRY does not exist" >&2; exit 1; }
[ -f "$INDEX" ]    || { echo "$INDEX does not exist"    >&2; exit 1; }
[ -e "$PRD_FILE" ] && { echo "$PRD_FILE already exists — refusing to overwrite" >&2; exit 1; }

TODAY=$(date -u +%Y-%m-%d)

python3 - "$PRD_FILE" "$REGISTRY" "$INDEX" "$PRD_ID" "$PRD_NUM" "$TITLE" "$LANE" "$CLASS" "$SUMMARY" "$TODAY" <<'PYEOF'
import json
import re
import sys
from pathlib import Path

(prd_path, registry_path, index_path, prd_id, prd_num,
 title, lane, klass, summary, today) = sys.argv[1:]
prd_num = int(prd_num)

# --- 1. PRD-NNN.md scaffold ----------------------------------------------
# PRD-232: emit the docs/PRD_TEMPLATE.md shape (header fields, section
# order, A/M/D FILES format) — not a divergent third skeleton. The A/M/D
# FILES lines are what .claude/hooks/protect_files.sh parses.
problem = summary.strip() or "TODO: state the problem this PRD solves."
prd_body = f"""{prd_id} — {title}

Status: IN PROGRESS
Filed: {today}

LANE
{lane}

CLASS
{klass}

WHY NOW
{problem}

MAX EXPECTED DELTA
TODO: binding ceiling (production LOC / file count / other measurable bound).

GOAL
TODO: one sentence — what this PRD delivers and why.

SCOPE
- TODO

OUT OF SCOPE
- TODO

FILES
M TODO/replace/with/every/file.py

REQUIREMENTS

R1 — TODO
TODO: deterministic description of what must be true.

FAIL: TODO — observable, binary failure condition.

DATA FLOW
TODO ([source] -> [transform] -> [output], or "n/a" for docs-only)

FAIL CONDITIONS
- TODO: list all binary failure conditions across all requirements.

VALIDATION
Manual:
- TODO: step-by-step verification with binary expected results.

STATUS: IN PROGRESS
"""
Path(prd_path).write_text(prd_body, encoding="utf-8")
print(f"created  {prd_path}")

# --- 2. PRD_REGISTRY.md row ----------------------------------------------
reg_p = Path(registry_path)
reg_text = reg_p.read_text(encoding="utf-8")
if re.search(rf"^\|\s*{re.escape(prd_id)}\s*\|", reg_text, flags=re.MULTILINE):
    print(f"skip     {registry_path}: row for {prd_id} already present")
else:
    row = (
        f"| {prd_id} | — | {title} | IN PROGRESS | "
        f"[{prd_id}](prd_history/{prd_id}.md) |"
    )
    lines = reg_text.splitlines(keepends=True)
    # Restrict the scan to the MAIN PRD table. A trailing "## Audit Reports"
    # table also contains "| PRD-NNN |" rows (e.g. PRD-016); scanning the whole
    # file would land the new row there instead of the main table (PRD-164 R1).
    boundary = len(lines)
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Audit Reports", line):
            boundary = i
            break
    last_idx = -1
    for i in range(boundary):
        if re.match(r"^\|\s*PRD-\d{3}\s*\|", lines[i]):
            last_idx = i
    if last_idx < 0:
        print(f"ERROR: no existing PRD rows found in {registry_path}", file=sys.stderr)
        sys.exit(1)
    lines.insert(last_idx + 1, row + "\n")
    reg_p.write_text("".join(lines), encoding="utf-8")
    print(f"inserted {registry_path}: row for {prd_id}")

# --- 3. prd_index.json entry (sorted; counters untouched) ----------------
idx_p = Path(index_path)
idx = json.loads(idx_p.read_text(encoding="utf-8"))
entries = idx.setdefault("entries", [])
if any(e.get("number") == prd_num for e in entries):
    print(f"skip     {index_path}: entry {prd_id} already present")
else:
    new_entry = {
        "number": prd_num,
        "title": title,
        "status": "IN PROGRESS",
        "commit": None,
    }
    pos = len(entries)
    for i, e in enumerate(entries):
        if isinstance(e.get("number"), int) and e["number"] > prd_num:
            pos = i
            break
    entries.insert(pos, new_entry)
    idx_p.write_text(json.dumps(idx, indent=2) + "\n", encoding="utf-8")
    print(f"inserted {index_path}: entry {prd_id} (latest_complete/next_prd unchanged)")
PYEOF

OPEN_FILES=("$PRD_FILE" "$REGISTRY" "$INDEX")

echo ""
echo "=== unstaged diff preview ==="
git diff --stat -- "${OPEN_FILES[@]}" 2>/dev/null || true

if [ "$DO_COMMIT" -eq 1 ]; then
    echo ""
    git add -- "${OPEN_FILES[@]}"
    git commit -m "${PRD_ID}: stage 0" \
               -m "Scaffold PRD doc + IN PROGRESS registry row + prd_index entry." \
               -m "Co-authored-by: Claude <claude@anthropic.com>"
else
    echo ""
    echo "Review the diff, then stage and commit:"
    echo "  git add ${OPEN_FILES[*]}"
    echo "  git commit -m \"${PRD_ID}: stage 0\""
    echo ""
    echo "Or rerun with --commit to do it in one shot."
fi

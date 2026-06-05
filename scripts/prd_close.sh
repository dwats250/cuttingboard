#!/usr/bin/env bash
# prd_close.sh — apply the mechanical closeout edits for a completed PRD.
#
# Updates (does NOT commit):
#   - docs/prd_history/PRD-NNN.md       : STATUS line -> "COMPLETE @ <hash>"
#   - docs/PRD_REGISTRY.md              : append a row for PRD-NNN
#   - docs/PROJECT_STATE.md             : "Last completed PRD", "Last work completed",
#                                         test baseline count, prepend history table row
#
# Usage:
#   scripts/prd_close.sh \
#       --prd 120 \
#       --hash d20d906 \
#       --title "Dashboard Source-Health Diagnostics and Permission Display Correction" \
#       --tests 2226 \
#       --added 25 \
#       --summary "PRD-120: renderer-only source-health diagnostics ..."
#
# After running, review the diff (`git diff`) and stage / commit explicitly.
# This script does NOT stage or commit — that is your decision.

set -euo pipefail

PRD=""
HASH=""
TITLE=""
TESTS=""
ADDED=""
SUMMARY=""
NEXT=""
DO_COMMIT=0
DO_PUSH=0

usage() {
    cat <<'USAGE'
Usage: prd_close.sh --prd <NNN> --hash <commit> --title "<title>" \
                    --tests <total_passing> --added <new_tests_added> \
                    --summary "<one-paragraph what + why>" \
                    [--next "<next-step text>"] [--commit] [--push]

  --next     set the PROJECT_STATE "**Next step" line; when omitted, that
             line is left unchanged
  --commit   stage + commit the closeout edits with a canned message
  --push     also git push (implies --commit)
USAGE
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prd)     PRD="$2"; shift 2 ;;
        --hash)    HASH="$2"; shift 2 ;;
        --title)   TITLE="$2"; shift 2 ;;
        --tests)   TESTS="$2"; shift 2 ;;
        --added)   ADDED="$2"; shift 2 ;;
        --summary) SUMMARY="$2"; shift 2 ;;
        --next)    NEXT="$2"; shift 2 ;;
        --commit)  DO_COMMIT=1; shift ;;
        --push)    DO_COMMIT=1; DO_PUSH=1; shift ;;
        -h|--help) usage ;;
        *) echo "unknown arg: $1" >&2; usage ;;
    esac
done

[ -n "$PRD" ]     || { echo "missing --prd"     >&2; exit 2; }
[ -n "$HASH" ]    || { echo "missing --hash"    >&2; exit 2; }
[ -n "$TITLE" ]   || { echo "missing --title"   >&2; exit 2; }
[ -n "$TESTS" ]   || { echo "missing --tests"   >&2; exit 2; }
[ -n "$ADDED" ]   || { echo "missing --added"   >&2; exit 2; }
[ -n "$SUMMARY" ] || { echo "missing --summary" >&2; exit 2; }

# Normalize PRD identifier.
case "$PRD" in
    PRD-*) PRD_NUM="${PRD#PRD-}";;
    *)     PRD_NUM="$PRD";;
esac
PRD_ID="PRD-${PRD_NUM}"
PRD_FILE="docs/prd_history/${PRD_ID}.md"
REGISTRY="docs/PRD_REGISTRY.md"
STATE="docs/PROJECT_STATE.md"
INDEX="docs/prd_index.json"

[ -f "$PRD_FILE" ] || { echo "$PRD_FILE does not exist" >&2; exit 1; }
[ -f "$REGISTRY" ] || { echo "$REGISTRY does not exist" >&2; exit 1; }
[ -f "$STATE" ]    || { echo "$STATE does not exist"    >&2; exit 1; }
[ -f "$INDEX" ]    || { echo "$INDEX does not exist"    >&2; exit 1; }

TODAY=$(date -u +%Y-%m-%d)

python3 - "$PRD_FILE" "$REGISTRY" "$STATE" "$INDEX" "$PRD_ID" "$HASH" "$TITLE" "$TESTS" "$ADDED" "$SUMMARY" "$TODAY" "$NEXT" <<'PYEOF'
import json
import re
import sys
from pathlib import Path

(prd_path, registry_path, state_path, index_path,
 prd_id, commit_hash, title, tests, added, summary, today, next_step) = sys.argv[1:]

# --- 1. PRD-NNN.md status markers ----------------------------------------
# Two distinct markers, two distinct completed forms (PRD-164 R3):
#   - the capital-S "Status:" header line -> "Status: COMPLETE" (no hash)
#   - the trailing all-caps "STATUS:" line -> "STATUS: COMPLETE @ <hash>"
# The pre-PRD-164 script flipped only the trailing marker, leaving the header
# at IN PROGRESS. Case-sensitive anchors keep the two lines from colliding.
prd_p = Path(prd_path)
prd_text = prd_p.read_text(encoding="utf-8")
new_trailing = f"STATUS: COMPLETE @ {commit_hash}"
prd_text, n_header = re.subn(
    r"^Status:.*$", "Status: COMPLETE", prd_text, count=1, flags=re.MULTILINE,
)
prd_text, n_trailing = re.subn(
    r"^STATUS:.*$", lambda _m: new_trailing, prd_text, flags=re.MULTILINE,
)
if n_trailing == 0:
    print(f"WARN: {prd_path} trailing STATUS line not found; appending", file=sys.stderr)
    prd_text = prd_text + f"\n{new_trailing}\n"
if n_header == 0:
    print(f"WARN: {prd_path} 'Status:' header line not found", file=sys.stderr)
prd_p.write_text(prd_text, encoding="utf-8")
print(f"updated  {prd_path}: Status: COMPLETE / {new_trailing}")

# --- 2. PRD_REGISTRY.md row ----------------------------------------------
# PRD-164 R2: the Stage-0 row already exists (prd_open.sh created it), so flip
# it in place to COMPLETE instead of skipping. The missing-row case keeps the
# prior append-when-absent fallback (defensive only; the closeout-skill
# preflight refuses a missing row before this script runs).
reg_p = Path(registry_path)
reg_text = reg_p.read_text(encoding="utf-8")
row = (
    f"| {prd_id} | {commit_hash} | {title} | COMPLETE | "
    f"[{prd_id}](prd_history/{prd_id}.md) |"
)
row_re = re.compile(rf"^\|\s*{re.escape(prd_id)}\s*\|.*$", re.MULTILINE)
# callable replacement: title may contain regex-template metacharacters.
reg_text_new, n_row = row_re.subn(lambda _m: row, reg_text)
if n_row >= 1:
    reg_p.write_text(reg_text_new, encoding="utf-8")
    print(f"updated  {registry_path}: row for {prd_id} -> COMPLETE @ {commit_hash}")
else:
    # No existing row — append after the last MAIN-table row (stop at the
    # trailing '## Audit Reports' table, which also carries | PRD-NNN | rows).
    lines = reg_text.splitlines(keepends=True)
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
    print(f"appended {registry_path}: row for {prd_id}")

# --- 3. PROJECT_STATE.md -------------------------------------------------
state_p = Path(state_path)
state_text = state_p.read_text(encoding="utf-8")

# (a) Last updated
state_text, n = re.subn(
    r"^\*\*Last updated:\*\*.*$",
    f"**Last updated:** {today}",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    print("WARN: 'Last updated' marker not found in PROJECT_STATE.md", file=sys.stderr)

# (b) Last completed PRD
# callable replacement bypasses re.sub template parsing of backslash escapes
# in user-supplied --title; otherwise a title like 'foo \d bar' raises
# re.PatternError: bad escape \d.
state_text, n = re.subn(
    r"^\*\*Last completed PRD:\*\*.*$",
    lambda _m: f"**Last completed PRD:** {prd_id} - {title} (commit {commit_hash})",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    print("WARN: 'Last completed PRD' marker not found in PROJECT_STATE.md", file=sys.stderr)

# (c) Last work completed — one-line `**Last work completed:** YYYY-MM-DD — <summary>`
# callable replacement bypasses re.sub template parsing of backslash escapes
# in user-supplied --summary; otherwise a summary containing 'r"PRD-(\d+)"'
# raises re.PatternError: bad escape \d (observed during PRD-145 closeout).
state_text, n = re.subn(
    r"^\*\*Last work completed:\*\*.*$",
    lambda _m: f"**Last work completed:** {today} — {summary}",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    print("WARN: 'Last work completed' marker not found in PROJECT_STATE.md", file=sys.stderr)

# (d) Test baseline bullet
state_text, n = re.subn(
    r"^- \*\*\d[\d,]* passing\*\*[^\n]*$",
    f"- **{tests} passing** (as of {today}; {prd_id} added {added} tests)",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    print("WARN: test baseline bullet not found in PROJECT_STATE.md", file=sys.stderr)

# (f) Active PRD pointer reset (PRD-164 R4) — always reset to `none`; the
# just-closed PRD is recorded on the "Last completed PRD" line above.
state_text, n = re.subn(
    r"^\*\*Active PRD:\*\*.*$",
    "**Active PRD:** none",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    print("WARN: 'Active PRD' marker not found in PROJECT_STATE.md", file=sys.stderr)

# (g) Next-step line (PRD-164 R5) — rewritten only when --next is supplied;
# omitted leaves it byte-for-byte unchanged. Callable replacement so the text
# may contain regex-template metacharacters.
if next_step:
    state_text, n = re.subn(
        r"^\*\*Next step.*$",
        lambda _m: f"**Next step:** {next_step}",
        state_text, count=1, flags=re.MULTILINE,
    )
    if n != 1:
        print("WARN: 'Next step' marker not found in PROJECT_STATE.md", file=sys.stderr)

# (e) Recent PRD history table — prepend a row after the header separator.
new_row = f"| {prd_id} | {title} | COMPLETE | {today} |"
header_marker = "| PRD | Title | Status | Completed |"
sep_marker    = "|-----|-------|--------|-----------|"
lines = state_text.splitlines(keepends=True)
inserted = False
for i, line in enumerate(lines):
    if line.strip() == sep_marker:
        if i + 1 < len(lines) and prd_id in lines[i + 1]:
            print(f"skip     {state_path}: history row for {prd_id} already present")
            inserted = True
            break
        lines.insert(i + 1, new_row + "\n")
        inserted = True
        print(f"prepended {state_path}: history row for {prd_id}")
        break
if not inserted:
    print(f"WARN: history table separator not found in {state_path}", file=sys.stderr)

state_p.write_text("".join(lines), encoding="utf-8")

# --- 4. prd_index.json ---------------------------------------------------
idx_p = Path(index_path)
idx = json.loads(idx_p.read_text(encoding="utf-8"))
prd_num = int(prd_id.split("-")[1])
existing = next((e for e in idx["entries"] if e.get("number") == prd_num), None)
new_entry = {
    "number": prd_num,
    "title": title,
    "status": "COMPLETE",
    "commit": commit_hash,
}
if existing:
    existing.update(new_entry)
    print(f"updated  {index_path}: entry {prd_id}")
else:
    idx["entries"].append(new_entry)
    print(f"appended {index_path}: entry {prd_id}")
if prd_num > idx.get("latest_complete", 0):
    idx["latest_complete"] = prd_num
    idx["next_prd"] = prd_num + 1
idx_p.write_text(json.dumps(idx, indent=2) + "\n", encoding="utf-8")
PYEOF

CLOSE_FILES=("$PRD_FILE" "$REGISTRY" "$STATE" "$INDEX")
REVIEW_FILE="docs/prd_history/${PRD_ID}.review.codex.md"
[ -f "$REVIEW_FILE" ] && CLOSE_FILES+=("$REVIEW_FILE")

echo ""
echo "=== unstaged diff preview ==="
git diff --stat -- "${CLOSE_FILES[@]}" 2>/dev/null || true

if [ "$DO_COMMIT" -eq 1 ]; then
    echo ""
    git add -- "${CLOSE_FILES[@]}"
    git commit -m "Close ${PRD_ID} bookkeeping" \
               -m "STATUS COMPLETE @ ${HASH}; PROJECT_STATE + prd_index updated." \
               -m "Co-authored-by: Claude <claude@anthropic.com>"
    if [ "$DO_PUSH" -eq 1 ]; then
        git push
    fi
else
    echo ""
    echo "Review the diff, then stage and commit:"
    echo "  git add ${CLOSE_FILES[*]}"
    echo "  git commit -m \"Close ${PRD_ID} bookkeeping\""
    echo ""
    echo "Or rerun with --commit (or --push) to do it in one shot."
fi

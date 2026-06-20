#!/usr/bin/env bash
# prd_close.sh — apply the mechanical closeout edits for a completed PRD.
#
# Targets the current "Current state / Recent ships" PROJECT_STATE.md format
# (PRD-183). Updates (does NOT commit unless --commit):
#   - docs/prd_history/PRD-NNN.md  : STATUS markers -> "COMPLETE @ <hash>"
#   - docs/PRD_REGISTRY.md         : flip the PRD-NNN row to COMPLETE @ <hash>
#   - docs/PROJECT_STATE.md        : Last updated, Test baseline (count + commit,
#                                    xfailed preserved), Active PRD reset to none,
#                                    prepend a "Recent ships" row; --next optional
#   - docs/prd_index.json          : entry -> COMPLETE @ <hash>; counters bumped
#
# The pre-PRD-183 "Last completed PRD" / "Last work completed" prose lines were
# removed by the doc realignment; the --summary is now recorded in the closeout
# commit body instead.
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
# After running, review the diff (`git diff`) and stage / commit explicitly,
# or pass --commit (or --push) to do it in one shot.

set -euo pipefail

PRD=""
HASH=""
TITLE=""
TESTS=""
ADDED=""
SUMMARY=""
NEXT=""
CI_SUMMARY=""
CI_RUN=""
DO_COMMIT=0
DO_PUSH=0

usage() {
    cat <<'USAGE'
Usage: prd_close.sh --prd <NNN> --hash <commit> --title "<title>" \
                    (--ci-summary <file> | --tests <total_passing>) \
                    --added <new_tests_added> \
                    --summary "<one-paragraph what + why>" \
                    [--next "<next-step text>"] [--ci-run <id>] [--commit] [--push]

  --ci-summary  path to a captured CI pytest summary (the `test`-job log/step
                summary for the merge commit on `main`). The recorded baseline
                is the passing count parsed from it ("N passed[, M xfailed]"),
                so a sandbox-local count can never become the anchor (PRD-196).
                Overrides --tests; fails loud if the file is missing or carries
                no parseable pytest summary.
  --tests       fallback baseline count when --ci-summary is not supplied.
  --next        set the PROJECT_STATE "**Next step" line; when omitted, that
                line is left unchanged
  --ci-run      optional CI run id; recorded in the Test baseline line as
                ", run <id>" when supplied
  --commit      stage + commit the closeout edits (summary goes in the commit body)
  --push        also git push (implies --commit)
USAGE
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prd)        PRD="$2"; shift 2 ;;
        --hash)       HASH="$2"; shift 2 ;;
        --title)      TITLE="$2"; shift 2 ;;
        --tests)      TESTS="$2"; shift 2 ;;
        --ci-summary) CI_SUMMARY="$2"; shift 2 ;;
        --ci-run)     CI_RUN="$2"; shift 2 ;;
        --added)      ADDED="$2"; shift 2 ;;
        --summary)    SUMMARY="$2"; shift 2 ;;
        --next)       NEXT="$2"; shift 2 ;;
        --commit)     DO_COMMIT=1; shift ;;
        --push)       DO_COMMIT=1; DO_PUSH=1; shift ;;
        -h|--help)    usage ;;
        *) echo "unknown arg: $1" >&2; usage ;;
    esac
done

[ -n "$PRD" ]     || { echo "missing --prd"     >&2; exit 2; }
[ -n "$HASH" ]    || { echo "missing --hash"    >&2; exit 2; }
[ -n "$TITLE" ]   || { echo "missing --title"   >&2; exit 2; }
[ -n "$ADDED" ]   || { echo "missing --added"   >&2; exit 2; }
[ -n "$SUMMARY" ] || { echo "missing --summary" >&2; exit 2; }
if [ -z "$TESTS" ] && [ -z "$CI_SUMMARY" ]; then
    echo "missing --tests or --ci-summary" >&2; exit 2
fi

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

python3 - "$PRD_FILE" "$REGISTRY" "$STATE" "$INDEX" "$PRD_ID" "$HASH" "$TITLE" "$TESTS" "$ADDED" "$TODAY" "$NEXT" "$CI_SUMMARY" "$CI_RUN" <<'PYEOF'
import json
import re
import sys
from pathlib import Path

(prd_path, registry_path, state_path, index_path,
 prd_id, commit_hash, title, tests, added, today, next_step, ci_summary, ci_run) = sys.argv[1:]

# --- 0. CI-sourced baseline (PRD-196 defect b) ---------------------------
# When a CI pytest summary file is supplied, the recorded baseline is the
# passing count parsed from it — the authoritative `test`-job count for the
# merge commit on `main` — rather than a hand-supplied (possibly sandbox-local)
# --tests value. Fail loud if the file is absent or carries no parseable
# pytest summary; never silently fall back to a local number.
if ci_summary:
    ci_p = Path(ci_summary)
    if not ci_p.exists():
        sys.exit(f"ERROR: --ci-summary file not found: {ci_summary}")
    ci_text = ci_p.read_text(encoding="utf-8")
    m = re.search(r"(\d[\d,]*)\s+passed\b", ci_text)
    if not m:
        sys.exit(
            f"ERROR: no pytest pass count ('N passed') found in CI summary "
            f"{ci_summary}; refusing to record a baseline"
        )
    tests = m.group(1).replace(",", "")

# Contracted PROJECT_STATE edits accumulate failures here; if any contracted
# bullet cannot be located, the script writes NOTHING and exits non-zero
# (PRD-196 defect a — no soft WARN-and-continue path survives).
errors: list[str] = []

# All edits are computed in memory below; nothing is written until the
# contracted-bullet error gate at the end passes (PRD-196 atomicity).

# --- 1. PRD-NNN.md status markers ----------------------------------------
# Two distinct markers, two distinct completed forms (PRD-164 R3):
#   - the capital-S "Status:" header line -> "Status: COMPLETE" (no hash)
#   - the trailing all-caps "STATUS:" line -> "STATUS: COMPLETE @ <hash>"
# This path is unchanged by PRD-196 (defect a is PROJECT_STATE hygiene); its
# defensive WARN/append fallbacks are retained.
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

# --- 2. PRD_REGISTRY.md row ----------------------------------------------
# Flip the existing Stage-0 row in place (PRD-164 R2); append-when-absent is a
# defensive fallback only (the closeout-skill preflight refuses a missing row).
reg_p = Path(registry_path)
reg_text = reg_p.read_text(encoding="utf-8")
row = (
    f"| {prd_id} | {commit_hash} | {title} | COMPLETE | "
    f"[{prd_id}](prd_history/{prd_id}.md) |"
)
row_re = re.compile(rf"^\|\s*{re.escape(prd_id)}\s*\|.*$", re.MULTILINE)
reg_out, n_row = row_re.subn(lambda _m: row, reg_text)
if n_row >= 1:
    print(f"updated  {registry_path}: row for {prd_id} -> COMPLETE @ {commit_hash}")
else:
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
        sys.exit(f"ERROR: no existing PRD rows found in {registry_path}")
    lines.insert(last_idx + 1, row + "\n")
    reg_out = "".join(lines)
    print(f"appended {registry_path}: row for {prd_id}")

# --- 3. PROJECT_STATE.md (new "Current state / Recent ships" format) ------
# Every contracted bullet is anchored on its bold label and fails LOUD (records
# an error, writes nothing) when absent — no soft WARN-and-continue (PRD-196 a).
state_p = Path(state_path)
state_text = state_p.read_text(encoding="utf-8")

# (a) Last updated -> today + commit ref
state_text, n = re.subn(
    r"^\*\*Last updated:\*\*.*$",
    f"**Last updated:** {today} (commit {commit_hash})",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    errors.append("'**Last updated:**' line not found in PROJECT_STATE.md")

# (b) Test baseline bullet — canonical whole-bullet REBUILD (PRD-203).
# Earlier logic patched the count in place and refreshed the commit ref only for
# the ``at `<hex>` `` form, so a bullet in the ``for `<hash>` `` / "CI truth ...
# run <id>" form kept a stale commit + provenance while the count advanced
# (caught by alignment cadence #4). Regenerate the ENTIRE bullet from the closeout
# inputs so count and provenance can never diverge. Fails loud (records an error,
# writes nothing) when the labelled bullet is absent (PRD-196 atomicity).
xfailed = ""
if ci_summary:
    mxf = re.search(r"(\d[\d,]*)\s+xfailed\b", ci_text)
    if mxf:
        xfailed = mxf.group(1).replace(",", "")
# Match the whole bullet item: the label line plus any continuation lines that
# are not a new bullet ("- "), a heading ("#"), or blank.
bullet_re = re.compile(
    r"^- \*\*Test baseline:\*\*.*(?:\n(?!\s*-\s|\s*#|\s*$).*)*",
    re.MULTILINE,
)
mb = bullet_re.search(state_text)
if mb is None:
    errors.append("'- **Test baseline:**' bullet not found in PROJECT_STATE.md")
else:
    if not xfailed:
        # Preserve a prior "M xfailed" from the bullet being replaced.
        mxf_prev = re.search(r"(\d[\d,]*)\s+xfailed\b", mb.group(0))
        if mxf_prev:
            xfailed = mxf_prev.group(1).replace(",", "")
    xf = f", {xfailed} xfailed" if xfailed else ""
    run = f", run {ci_run}" if ci_run else ""
    new_bullet = (
        f"- **Test baseline:** {tests} passing{xf} "
        f"(CI truth on `main`; `test` job for `{commit_hash}`{run})."
    )
    state_text = state_text[: mb.start()] + new_bullet + state_text[mb.end():]

# (c) Active PRD pointer reset (PRD-164 R4) — the bulleted, single-line form
# (PRD-183). The just-closed PRD is recorded in the Recent ships table below.
state_text, n = re.subn(
    r"^- \*\*Active PRD:\*\*.*$",
    "- **Active PRD:** none in progress.",
    state_text, count=1, flags=re.MULTILINE,
)
if n != 1:
    errors.append("'- **Active PRD:**' bullet not found in PROJECT_STATE.md")

# (d) Next-step line (PRD-164 R5) — rewritten only when --next is supplied;
# fails loud when supplied but the line is absent.
if next_step:
    state_text, n = re.subn(
        r"^\*\*Next step.*$",
        lambda _m: f"**Next step:** {next_step}",
        state_text, count=1, flags=re.MULTILINE,
    )
    if n != 1:
        errors.append("'**Next step**' line not found in PROJECT_STATE.md (--next supplied)")

# (e) Recent ships table — prepend a 3-column row under the "## Recent ships"
# header's separator row (| PRD | Title | Completed |).
new_row = f"| {prd_id} | {title} | {today} |"
lines = state_text.splitlines(keepends=True)
inserted = False
in_recent = False
for i, line in enumerate(lines):
    if line.strip().lower().startswith("## recent ships"):
        in_recent = True
        continue
    if in_recent and re.match(r"^\|[-\s|:]+\|\s*$", line):
        if i + 1 < len(lines) and prd_id in lines[i + 1]:
            print(f"skip     {state_path}: Recent ships row for {prd_id} already present")
            inserted = True
            break
        lines.insert(i + 1, new_row + "\n")
        inserted = True
        print(f"prepended {state_path}: Recent ships row for {prd_id}")
        break
if not inserted:
    errors.append(f"'## Recent ships' table not found in {state_path}")
state_out = "".join(lines)

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
    idx_msg = f"updated  {index_path}: entry {prd_id}"
else:
    idx["entries"].append(new_entry)
    idx_msg = f"appended {index_path}: entry {prd_id}"
if prd_num > idx.get("latest_complete", 0):
    idx["latest_complete"] = prd_num
    idx["next_prd"] = prd_num + 1

# --- error gate: a missing contracted PROJECT_STATE bullet aborts the whole
# closeout before ANY file is written (PRD-196 fail-loud + atomicity) ---------
if errors:
    print("ERROR: prd_close.sh aborted — contracted PROJECT_STATE bullet(s) "
          "could not be located; no files were modified:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)

# --- commit all edits to disk -------------------------------------------------
prd_p.write_text(prd_text, encoding="utf-8")
print(f"updated  {prd_path}: Status: COMPLETE / {new_trailing}")
reg_p.write_text(reg_out, encoding="utf-8")
state_p.write_text(state_out, encoding="utf-8")
idx_p.write_text(json.dumps(idx, indent=2) + "\n", encoding="utf-8")
print(idx_msg)
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
               -m "STATUS COMPLETE @ ${HASH}." \
               -m "${SUMMARY}" \
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

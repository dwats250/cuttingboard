#!/usr/bin/env bash
# Fires on UserPromptSubmit.
# Registry-gap check ONLY: flags docs/prd_history/PRD-*.md files that have no
# registry row (excluding review/adjudication/codex-prompt/impl-notes/proposal
# sidecars, PRD-108/143/248).
#
# PRD-243 retired the keyword detectors that used to live here (PRD-body
# review-mode injection, implementation-request sequencing gate): they keyed
# on PRD-NNN tokens + section keywords with no channel discrimination, so
# they fired on subagent task notifications and other non-prompt traffic
# (six misfires in one audited session), while the sequencing concern is now
# enforced where truth is determined — tools/validate_prd_registry.py on the
# CI merge path (PRD-200), with closeout folded into the implementation PR
# (PRD-229). History: PRD-108 -> 143 -> 145 patched this detector's
# false-positive classes three times; the class regenerated each time.
set -euo pipefail

INPUT=$(cat)

PROMPT=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    print(d.get('prompt') or d.get('message') or '')
except Exception:
    print('')
" "$INPUT" 2>/dev/null || true)

if [ -z "$PROMPT" ]; then
    exit 0
fi

REGISTRY="docs/PRD_REGISTRY.md"

HAS_PRD_NUM=$(echo "$PROMPT" | grep -cE 'PRD-[0-9]+' 2>/dev/null; true)
HAS_PRD_NUM=${HAS_PRD_NUM:-0}

# ---------------------------------------------------------------------------
# Registry completeness check: flag prd_history/*.md files with no registry row
# ---------------------------------------------------------------------------
REGISTRY_GAP=""
if [ -f "$REGISTRY" ] && [ "${HAS_PRD_NUM}" -gt 0 ] 2>/dev/null; then
    REGISTRY_GAP=$(python3 - "$REGISTRY" <<'PYEOF'
import sys, re, os, glob

registry_path = sys.argv[1]
prd_dir = os.path.join(os.path.dirname(registry_path), "prd_history")

file_stems = set()
for f in glob.glob(os.path.join(prd_dir, "PRD-*.md")):
    name = os.path.basename(f)
    # Review, adjudication, codex-prompt, impl-notes, and proposal sidecars
    # are not PRDs and must not have registry rows -- this list IS the
    # single source of truth for that exclusion (PRD-254; docs/
    # PRD_REVIEW_TEMPLATE.md points here rather than restating it;
    # PRD-248 added .proposal.md).
    if (
        ".review." in name
        or name.endswith(".adjudication.md")
        or name.endswith(".codex_prompt.md")
        or ".impl_notes." in name
        or name.endswith(".proposal.md")
    ):
        continue
    file_stems.add(name.replace(".md", ""))

try:
    text = open(registry_path, encoding="utf-8").read()
except OSError:
    sys.exit(0)

# A file is registered if its stem appears anywhere in any registry table row
# (catches variant ID formats like "PRD-012 (cleanup)" and "PRD-053 PATCH")
missing = []
for stem in sorted(file_stems):
    if not any(stem in line for line in text.splitlines() if line.startswith("|")):
        missing.append(stem)

if not missing:
    sys.exit(0)

lines = ["REGISTRY GAP — prd_history files with no registry row:"]
for m in missing:
    lines.append(f"  {m}.md")
lines.append("Add a registry row for each before saving new PRDs.")
print("\n".join(lines))
PYEOF
    )
fi

# ---------------------------------------------------------------------------
# Emit context (registry gap only; empty output = no injection)
# ---------------------------------------------------------------------------
python3 - "$REGISTRY_GAP" <<'PYEOF'
import json, sys

registry_gap = sys.argv[1].strip()

if not registry_gap:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": registry_gap
    }
}))
PYEOF

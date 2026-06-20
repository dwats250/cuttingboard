#!/usr/bin/env bash
# PreToolUse / Read -- non-blocking canonical-doc re-read reminder (PRD-201).
#
# When the Read tool targets a doc that is already injected into the system
# prompt at session start (the repo-root CLAUDE.md, or the auto-memory
# MEMORY.md), emit a model-visible `additionalContext` reminder that re-reading
# is redundant. This hook NEVER blocks: it always allows the Read and exits 0.
# For every other path it emits nothing.
INPUT=$(cat)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}" python3 - "$INPUT" <<'PY'
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    fp = (json.loads(raw).get("tool_input", {}) or {}).get("file_path", "") or ""
except Exception:
    fp = ""
if not fp:
    sys.exit(0)

resolved = os.path.realpath(fp)
project_dir = os.environ.get("PROJECT_DIR") or os.getcwd()
claude_md = os.path.realpath(os.path.join(project_dir, "CLAUDE.md"))

reason = ""
if resolved == claude_md:
    reason = (
        "CLAUDE.md is already injected into your system prompt at session start "
        "(project instructions). Re-reading it is redundant; if you just edited "
        "it, the Edit already confirmed the change."
    )
elif (
    os.path.basename(resolved) == "MEMORY.md"
    and f"{os.sep}.claude{os.sep}" in resolved
    and resolved.endswith(f"{os.sep}memory{os.sep}MEMORY.md")
):
    reason = (
        "MEMORY.md (auto-memory) is already injected into your system prompt at "
        "session start. Re-reading it is redundant."
    )

if not reason:
    sys.exit(0)

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": reason,
            }
        }
    )
)
PY

exit 0

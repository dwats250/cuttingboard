#!/usr/bin/env bash
# Stop hook — writes .claude/state/snapshot.json with active task state.

mkdir -p .claude/state

python3 << 'EOF'
import json, subprocess, os
from datetime import datetime, timezone


def read_file(path, default="unknown"):
    try:
        with open(path) as f:
            val = f.read().strip()
            return val if val else default
    except Exception:
        return default


def read_optional_file(path):
    try:
        with open(path) as f:
            val = f.read().strip()
            return val or None
    except Exception:
        return None


def run_cmd(cmd, default="unknown"):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return default


snapshot = {
    "active_prd":  read_file(".claude/state/active_prd.txt", "none"),
    "branch":      run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    "commit":      run_cmd(["git", "rev-parse", "--short", "HEAD"]),
    "timestamp":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}

next_action = read_optional_file(".claude/state/next_action.txt")
if next_action:
    snapshot["next_action"] = next_action

out = ".claude/state/snapshot.json"
with open(out, "w") as f:
    json.dump(snapshot, f, indent=2)

print(f"[stop_snapshot] Snapshot written to {out}")
print(f"  active_prd  : {snapshot['active_prd']}")
print(f"  branch      : {snapshot['branch']}")
print(f"  commit      : {snapshot['commit']}")
print(f"  timestamp   : {snapshot['timestamp']}")
if "next_action" in snapshot:
    print(f"  next_action : {snapshot['next_action']}")
EOF

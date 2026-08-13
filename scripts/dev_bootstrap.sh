#!/usr/bin/env bash
# PRD-293 (QW-5): idempotent, version-true developer bootstrap.
set -uo pipefail

SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SELF_DIR/.." && pwd -P)"
VENV="$REPO_ROOT/.venv"
VPY="$VENV/bin/python"
LOCKFILE="$REPO_ROOT/.dev_bootstrap.lock"
RECLAIM_LOCK="$LOCKFILE.reclaim"
LOCK_TRIES="${DEV_BOOTSTRAP_LOCK_TRIES:-120}"
LOCK_SLEEP="${DEV_BOOTSTRAP_LOCK_SLEEP:-0.5}"
BEGIN="# >>> dev_bootstrap (PRD-293) >>>"
END="# <<< dev_bootstrap (PRD-293) <<<"
UNDER_CLAUDE=0; [ -n "${CLAUDE_ENV_FILE:-}" ] && UNDER_CLAUDE=1

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PIP_TARGET PIP_REQUIRE_VIRTUALENV \
      PIP_USER PIP_CONFIG_FILE 2>/dev/null || true

_have_lock=0
_lock_tmp=""

_pid_live() {
  case "${1:-}" in ''|*[!0-9]*) return 1;; esac
  case "$1" in *[1-9]*) ;; *) return 1;; esac  # reject 0 / all-zero: kill -0 0 probes the group
  kill -0 "$1" 2>/dev/null
}

_lock_owned() {
  local pid
  [ "$_have_lock" = 1 ] && [ -f "$LOCKFILE" ] &&
    IFS= read -r pid <"$LOCKFILE" && [ "$pid" = "$$" ]
}

_unlock() {
  [ "$_have_lock" = 1 ] || return 0
  if ! _lock_owned; then
    echo "dev_bootstrap: FAIL [lock ownership lost] $LOCKFILE" >&2
    return 1
  fi
  if ! rm -f "$LOCKFILE"; then
    echo "dev_bootstrap: FAIL [lock release] $LOCKFILE" >&2
    return 1
  fi
  _have_lock=0
}

_on_exit() {
  local rc=$? _p
  [ -n "$_lock_tmp" ] && rm -f "$_lock_tmp"
  [ -e "$RECLAIM_LOCK" ] && IFS= read -r _p <"$RECLAIM_LOCK" 2>/dev/null && [ "$_p" = "$$" ] && rm -f "$RECLAIM_LOCK"
  _unlock || rc=2
  trap - EXIT
  exit "$rc"
}
trap _on_exit EXIT
trap 'exit 2' HUP INT TERM

# Remove acquisition temps (.new.PID.*) and reclaim graves (.stale.PID) left by
# DEAD processes; a live owner's is kept. Handles file and empty-dir graves.
_sweep_stale() {
  local t pid
  for t in "$LOCKFILE".new.* "$LOCKFILE".stale.*; do
    [ -e "$t" ] || continue
    pid="${t#"$LOCKFILE".new.}"; pid="${pid#"$LOCKFILE".stale.}"; pid="${pid%%.*}"
    _pid_live "$pid" || { rm -f "$t" "$t/pid" 2>/dev/null; rmdir "$t" 2>/dev/null; }
  done
}

# Serialized reclaim of a dead regular-file lock: acquire the fixed-name RECLAIM_LOCK
# (atomic `link`; only one reclaimer at a time), then remove $LOCKFILE only if its pid
# is dead/absent. A live owner is never reclaimed and no second reclaimer runs
# concurrently, so there is no compare-then-unlink race against a fresh owner.
_reclaim_lock() {
  local pid
  link "$_lock_tmp" "$RECLAIM_LOCK" 2>/dev/null || return 1
  { IFS= read -r pid <"$LOCKFILE" 2>/dev/null && _pid_live "$pid"; } || rm -f "$LOCKFILE"
  rm -f "$RECLAIM_LOCK"
}

# Legacy (pre-PRD-301) DIRECTORY carrier, routed by an explicit [ -d ] test (a `link`
# failure is EEXIST for a file OR a dir and cannot distinguish them). Live pid -> wait
# (return 1); dead/malformed CLEAN dir -> reclaim; a stray non-pid child -> return 3
# (fail loud); a non-empty retained grave after the move -> return 4 (fail loud);
# pid-less -> wait (caller fails loud after the bound).
_reclaim_legacy_dir() {
  local pid grave="$LOCKFILE.stale.$$"
  [ -s "$LOCKFILE/pid" ] && IFS= read -r pid <"$LOCKFILE/pid" 2>/dev/null && [ -n "$pid" ] || return 1
  _pid_live "$pid" && return 1
  [ "$(ls -A "$LOCKFILE" 2>/dev/null)" = pid ] || return 3
  mv "$LOCKFILE" "$grave" 2>/dev/null || return 1
  rm -f "$grave/pid" 2>/dev/null
  rmdir "$grave" 2>/dev/null && return 0
  echo "dev_bootstrap: FAIL [legacy grave retained] $grave -- a non-pid entry moved into the grave; ensure no dev_bootstrap process is running, inspect $grave, and remove it manually only when safe (never rm -rf)" >&2
  return 4
}

# Acquire with the exact-pathname `link` utility: link a pid-bearing temp onto $LOCKFILE
# (EEXIST is the mutex), so the lock, the instant it exists, already holds the owner pid
# (no publication window). `link` fails EEXIST on a directory too, so a legacy directory
# is routed by the explicit [ -d ] test before any link attempt.
_lock() {
  local i=0 _r
  _sweep_stale
  _lock_tmp="$(mktemp "$LOCKFILE.new.$$.XXXXXX")" || return 1
  printf '%s\n' "$$" >"$_lock_tmp" || { rm -f "$_lock_tmp"; _lock_tmp=""; return 1; }
  while :; do
    if [ -d "$LOCKFILE" ]; then
      _reclaim_legacy_dir; _r=$?
      [ "$_r" -eq 3 ] && { echo "dev_bootstrap: FAIL [legacy lock directory with stray content] $LOCKFILE -- inspect and, if no dev_bootstrap is running, remove it manually" >&2; return 2; }
      [ "$_r" -eq 4 ] && return 2
    elif link "$_lock_tmp" "$LOCKFILE" 2>/dev/null; then
      break
    else
      _reclaim_lock || true
    fi
    i=$((i + 1))
    if [ "$i" -gt "$LOCK_TRIES" ]; then
      rm -f "$_lock_tmp"; _lock_tmp=""
      [ -d "$LOCKFILE" ] && [ ! -s "$LOCKFILE/pid" ] && { echo "dev_bootstrap: FAIL [legacy lock directory without pid] $LOCKFILE -- ensure no dev_bootstrap process is running, then remove it with: rmdir \"$LOCKFILE\"" >&2; return 2; }
      [ -e "$RECLAIM_LOCK" ] && { echo "dev_bootstrap: FAIL [stale reclaim lock] $RECLAIM_LOCK -- ensure no dev_bootstrap process is running, then remove it with: rm -f \"$RECLAIM_LOCK\"" >&2; return 2; }
      return 1
    fi
    sleep "$LOCK_SLEEP"
  done
  rm -f "$_lock_tmp"; _lock_tmp=""
  _have_lock=1
}

_env_update() {
  local add="$1" tmp vline pline
  [ "$UNDER_CLAUDE" = 1 ] || return 0
  _lock_owned || return 1
  [ -e "$CLAUDE_ENV_FILE" ] && [ ! -f "$CLAUDE_ENV_FILE" ] && return 1
  tmp="$(mktemp "${CLAUDE_ENV_FILE}.dev_bootstrap.XXXXXX" 2>/dev/null)" || return 1
  vline="$(printf 'export VIRTUAL_ENV=%q' "$VENV")"
  pline="$(printf 'export PATH=%q:"$PATH"' "$VENV/bin")"
  if [ -f "$CLAUDE_ENV_FILE" ]; then
    awk -v b="$BEGIN" -v e="$END" -v v="$vline" -v p="$pline" '
      $0 == b {
        x=$0; n1=getline a; n2=n1 ? getline c : 0; n3=n2 ? getline d : 0
        if (n1 && n2 && n3 && a == v && c == p && d == e) next
        print x
        if (n1) print a
        if (n2) print c
        if (n3) print d
        next
      }
      { print }
    ' "$CLAUDE_ENV_FILE" >"$tmp" || { rm -f "$tmp"; return 1; }
  else
    : >"$tmp" || { rm -f "$tmp"; return 1; }
  fi
  if [ "$add" = 1 ]; then
    printf '%s\n%s\n%s\n%s\n' "$BEGIN" "$vline" "$pline" "$END" >>"$tmp" ||
      { rm -f "$tmp"; return 1; }
  fi
  mv -f "$tmp" "$CLAUDE_ENV_FILE" || { rm -f "$tmp"; return 1; }
}

fail() {
  echo "dev_bootstrap: FAIL [$1] (venv $VENV)" >&2
  if [ "$_have_lock" = 1 ]; then
    _env_update 0 || echo "dev_bootstrap: FAIL [CLAUDE_ENV_FILE cleanup]" >&2
    _unlock || true
  fi
  exit 2
}

_bind() {
  if [ "$UNDER_CLAUDE" = 1 ]; then
    _env_update 1
  else
    echo "dev_bootstrap: run: source $VENV/bin/activate  (or use $VENV/bin/*)"
  fi
}

_ready() {
  [ -x "$VPY" ] || return 1
  "$VPY" -I - "$REPO_ROOT" >/dev/null 2>&1 <<'PY'
import importlib.metadata as md
import importlib.util as iu
import json
import os
import subprocess
import sys
from urllib.parse import unquote, urlparse

try:
    import tomllib
    from packaging.requirements import Requirement
except Exception:
    sys.exit(1)

root = os.path.realpath(sys.argv[1])
venv = os.path.join(root, ".venv")
rp = os.path.realpath

def inside(path, boundary):
    try:
        return os.path.commonpath((rp(path), rp(boundary))) == rp(boundary)
    except ValueError:
        return False

if rp(sys.prefix) != rp(venv) or sys.base_prefix == sys.prefix:
    sys.exit(1)
if rp(sys.executable) != rp(os.path.join(venv, "bin", "python")):
    sys.exit(1)

package = os.path.join(root, "cuttingboard")
spec = iu.find_spec("cuttingboard")
if not spec or not spec.origin or not inside(spec.origin, package):
    sys.exit(1)

try:
    direct = json.loads(md.distribution("cuttingboard").read_text("direct_url.json") or "{}")
    url = str(direct.get("url", ""))
    if not direct.get("dir_info", {}).get("editable") or not url.startswith("file:"):
        sys.exit(1)
    if rp(unquote(urlparse(url).path)) != root:
        sys.exit(1)
except Exception:
    sys.exit(1)

for entry in sys.path:
    path = rp(entry or os.getcwd())
    parts = os.path.normpath(path).split(os.sep)
    if ("site-packages" in parts or "dist-packages" in parts) and not inside(path, venv):
        sys.exit(1)

try:
    with open(os.path.join(root, "pyproject.toml"), "rb") as f:
        project = tomllib.load(f)["project"]
    requirements = list(project.get("dependencies", []))
    requirements += list(project.get("optional-dependencies", {}).get("dev", []))
    for raw in requirements:
        req = Requirement(raw)
        version = md.version(req.name)
        if req.specifier and not req.specifier.contains(version, prereleases=True):
            sys.exit(1)
except Exception:
    sys.exit(1)

def run(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True)
    except Exception:
        return None

ruff = run(os.path.join(venv, "bin", "ruff"), "--version")
pytest = run(os.path.join(venv, "bin", "pytest"), "--version")
isolated_pytest = run(os.path.join(venv, "bin", "python"), "-I", "-m", "pytest", "--version")
if not ruff or ruff.returncode or "0.15.22" not in (ruff.stdout or ""):
    sys.exit(1)
if not pytest or pytest.returncode or not isolated_pytest or isolated_pytest.returncode:
    sys.exit(1)
PY
}

_venv_valid() {
  [ -d "$VENV" ] && [ ! -L "$VENV" ] && [ -x "$VPY" ] || return 1
  "$VPY" -I -c 'import os,sys
root=os.path.realpath(sys.argv[1]); venv=os.path.realpath(os.path.join(root,".venv"))
sys.exit(0 if os.path.realpath(sys.prefix)==venv and sys.base_prefix!=sys.prefix else 1)' \
    "$REPO_ROOT" >/dev/null 2>&1
}

_base_py() {
  local candidate
  for candidate in python3 python; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    "$candidate" -I -c 'import sys; sys.exit(sys.version_info[:2] < (3, 11))' \
      >/dev/null 2>&1 || continue
    "$candidate" -I -c 'import venv' >/dev/null 2>&1 || continue
    printf '%s' "$candidate"
    return 0
  done
  return 1
}

cd -- "$REPO_ROOT" || fail "cd repo root"
_lock || { _rc=$?; [ "$_rc" -eq 2 ] || fail "lock contention >60s"; exit 2; }

if _ready; then
  _bind || fail "CLAUDE_ENV_FILE publish"
  _unlock || fail "lock release"
  echo "dev_bootstrap: ready ($VENV)"
  exit 0
fi

if [ -e "$VENV" ]; then
  _venv_valid || fail "existing .venv broken/non-isolated/symlinked; remove it manually and re-run"
else
  BASE_PY="$(_base_py)" || fail "no python3/python >=3.11 with venv available"
  "$BASE_PY" -I -m venv "$VENV" || fail "venv creation"
fi

PIP_CONFIG_FILE=/dev/null "$VPY" -I -m pip --isolated install --no-cache-dir \
  --no-input --disable-pip-version-check --retries 0 --timeout 30 -e ".[dev]" >&2 ||
  fail "pip install"
_ready || fail "post-install readiness (deps/version/provenance)"
_bind || fail "CLAUDE_ENV_FILE publish"
_unlock || fail "lock release"
echo "dev_bootstrap: bootstrapped ($VENV)"
exit 0

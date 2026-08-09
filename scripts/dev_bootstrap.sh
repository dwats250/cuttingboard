#!/usr/bin/env bash
# PRD-293 (QW-5): idempotent, version-true developer bootstrap.
set -uo pipefail

SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SELF_DIR/.." && pwd -P)"
VENV="$REPO_ROOT/.venv"
VPY="$VENV/bin/python"
LOCKDIR="$REPO_ROOT/.dev_bootstrap.lock"
BEGIN="# >>> dev_bootstrap (PRD-293) >>>"
END="# <<< dev_bootstrap (PRD-293) <<<"
UNDER_CLAUDE=0; [ -n "${CLAUDE_ENV_FILE:-}" ] && UNDER_CLAUDE=1

unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PIP_TARGET PIP_REQUIRE_VIRTUALENV \
      PIP_USER PIP_CONFIG_FILE 2>/dev/null || true

_have_lock=0

_lock_owned() {
  local pid
  [ "$_have_lock" = 1 ] && [ -d "$LOCKDIR" ] && [ -f "$LOCKDIR/pid" ] &&
    IFS= read -r pid <"$LOCKDIR/pid" && [ "$pid" = "$$" ]
}

_unlock() {
  [ "$_have_lock" = 1 ] || return 0
  if ! _lock_owned; then
    echo "dev_bootstrap: FAIL [lock ownership lost] $LOCKDIR" >&2
    return 1
  fi
  if ! rm -f "$LOCKDIR/pid" || ! rmdir "$LOCKDIR"; then
    echo "dev_bootstrap: FAIL [lock release] $LOCKDIR" >&2
    return 1
  fi
  _have_lock=0
}

_on_exit() {
  local rc=$?
  _unlock || rc=2
  trap - EXIT
  exit "$rc"
}
trap _on_exit EXIT
trap 'exit 2' HUP INT TERM

_dead_lock() {
  local pid
  [ -f "$LOCKDIR/pid" ] || return 0
  IFS= read -r pid <"$LOCKDIR/pid" || return 0
  case "$pid" in ''|*[!0-9]*) return 0;; esac
  kill -0 "$pid" 2>/dev/null && return 1
  return 0
}

_reclaim_lock() {
  local grave="$LOCKDIR.stale.$$"
  _dead_lock || return 1
  mv "$LOCKDIR" "$grave" 2>/dev/null || return 1
  rm -f "$grave/pid" 2>/dev/null || true
  rmdir "$grave" 2>/dev/null || true
  return 0
}

_lock() {
  local i=0
  while ! mkdir "$LOCKDIR" 2>/dev/null; do
    _reclaim_lock || true
    i=$((i + 1))
    [ "$i" -le 120 ] || return 1
    sleep 0.5
  done
  if ! printf '%s\n' "$$" >"$LOCKDIR/pid"; then
    rmdir "$LOCKDIR" 2>/dev/null || true
    return 1
  fi
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
_lock || fail "lock contention >60s"

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

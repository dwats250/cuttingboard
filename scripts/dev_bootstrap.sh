#!/usr/bin/env bash
# PRD-293 (QW-5): idempotent developer bootstrap. Owns only <repo>/.venv;
# version-true isolated readiness; lock-serialized; transactional
# CLAUDE_ENV_FILE binding; fail-loud (exit 2). Human-runnable standalone.
set -uo pipefail

# --- physical repo root from THIS script's location (invariant 1) -------------
SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SELF_DIR/.." && pwd -P)"
VENV="$REPO_ROOT/.venv"
VPY="$VENV/bin/python"
LOCKDIR="$REPO_ROOT/.dev_bootstrap.lock"
BEGIN="# >>> dev_bootstrap (PRD-293) >>>"
END="# <<< dev_bootstrap (PRD-293) <<<"
UNDER_CLAUDE=0; [ -n "${CLAUDE_ENV_FILE:-}" ] && UNDER_CLAUDE=1

# Neutralize caller pollution for our own invocations (invariant 4/5).
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PIP_TARGET PIP_REQUIRE_VIRTUALENV \
      PIP_USER PIP_CONFIG_FILE 2>/dev/null || true

_have_lock=0
_unlock() { [ "$_have_lock" = 1 ] && rmdir "$LOCKDIR" 2>/dev/null; _have_lock=0; }

# Remove any block THIS script owns from CLAUDE_ENV_FILE (transactional).
_env_strip() {
  [ "$UNDER_CLAUDE" = 1 ] && [ -f "$CLAUDE_ENV_FILE" ] && [ -w "$CLAUDE_ENV_FILE" ] || return 0
  local tmp; tmp="$(mktemp "${CLAUDE_ENV_FILE}.XXXXXX" 2>/dev/null)" || return 0
  if awk -v b="$BEGIN" -v e="$END" '$0==b{s=1;next} $0==e{s=0;next} !s{print}' \
        "$CLAUDE_ENV_FILE" >"$tmp" 2>/dev/null; then mv -f "$tmp" "$CLAUDE_ENV_FILE"; else rm -f "$tmp"; fi
}
# Failure must never add OR retain a positive success binding (invariant 15).
fail() { echo "dev_bootstrap: FAIL [$1] (venv $VENV)" >&2; _env_strip; _unlock; exit 2; }
trap '_unlock' EXIT INT TERM

# Bind session env AFTER readiness only: strip prior owned block, write exactly
# one normalized block (no append accumulation / duplicates) (invariant 15).
_bind() {
  [ "$UNDER_CLAUDE" = 1 ] || { echo "dev_bootstrap: run: source $VENV/bin/activate  (or use $VENV/bin/*)"; return 0; }
  _env_strip
  { [ -e "$CLAUDE_ENV_FILE" ] && [ ! -w "$CLAUDE_ENV_FILE" ]; } && { echo "dev_bootstrap: NOTE CLAUDE_ENV_FILE unwritable; PATH not bound (use $VENV/bin)" >&2; return 0; }
  { printf '%s\n' "$BEGIN"
    printf 'export VIRTUAL_ENV=%q\n' "$VENV"
    printf 'export PATH=%q:"$PATH"\n' "$VENV/bin"
    printf '%s\n' "$END"; } >>"$CLAUDE_ENV_FILE" 2>/dev/null \
    || echo "dev_bootstrap: NOTE CLAUDE_ENV_FILE unwritable; PATH not bound (use $VENV/bin)" >&2
}

# Version-true, isolated readiness probe (invariants 2,5-9,12). Exit 0 == ready.
PROBE='
import sys, os, json, subprocess
try: import tomllib
except Exception: sys.exit(1)
root=os.path.realpath(sys.argv[1]); venv=os.path.join(root,".venv")
rp=os.path.realpath
if rp(sys.prefix)!=rp(venv) or sys.base_prefix==sys.prefix: sys.exit(1)
import importlib.util as u, importlib.metadata as md
sp=u.find_spec("cuttingboard")
if not sp or not sp.origin or not rp(sp.origin).startswith(rp(os.path.join(root,"cuttingboard"))): sys.exit(1)
try:
    d=json.loads(md.distribution("cuttingboard").read_text("direct_url.json") or "{}")
    if not d.get("dir_info",{}).get("editable"): sys.exit(1)
    from urllib.parse import urlparse, unquote
    if not str(d.get("url","")).startswith("file:") or rp(unquote(urlparse(d["url"]).path))!=root: sys.exit(1)
except Exception: sys.exit(1)
for p in list(sys.path):
    if p and "site-packages" in p and not rp(p).startswith(rp(venv)) and rp(p)!=root: sys.exit(1)
try:
    from packaging.requirements import Requirement
    with open(os.path.join(root,"pyproject.toml"),"rb") as f: pp=tomllib.load(f)
    reqs=list(pp["project"].get("dependencies",[]))+list(pp["project"].get("optional-dependencies",{}).get("dev",[]))
    for r in reqs:
        req=Requirement(r)
        try: v=md.version(req.name)
        except Exception: sys.exit(1)
        if req.specifier and not req.specifier.contains(v, prereleases=True): sys.exit(1)
except Exception: sys.exit(1)
def run(*a):
    try: return subprocess.run(list(a),capture_output=True,text=True)
    except Exception: return None
r=run(os.path.join(venv,"bin","ruff"),"--version")
if not r or r.returncode!=0 or "0.15.22" not in (r.stdout or ""): sys.exit(1)
if run(os.path.join(venv,"bin","pytest"),"--version") is None or run(os.path.join(venv,"bin","pytest"),"--version").returncode!=0: sys.exit(1)
if run(os.path.join(venv,"bin","python"),"-I","-m","pytest","--version").returncode!=0: sys.exit(1)
sys.exit(0)
'
_ready() { [ -x "$VPY" ] && "$VPY" -I -c "$PROBE" "$REPO_ROOT" >/dev/null 2>&1; }

# Existing venv validated by runtime identity, not directory existence (inv 2,13).
_venv_valid() {
  [ -d "$VENV" ] && [ ! -L "$VENV" ] && [ -x "$VPY" ] || return 1
  "$VPY" -I -c 'import sys,os; r=sys.argv[1]
sys.exit(0 if os.path.realpath(sys.prefix)==os.path.realpath(os.path.join(r,".venv")) and sys.base_prefix!=sys.prefix else 1)' "$REPO_ROOT" >/dev/null 2>&1
}
# First usable base interpreter (>=3.11 + venv), invoked -I; never runs pip (inv 3).
_base_py() {
  local c
  for c in python3 python; do
    command -v "$c" >/dev/null 2>&1 || continue
    "$c" -I -c 'import sys; sys.exit(0 if sys.version_info[:2]>=(3,11) else 1)' >/dev/null 2>&1 || continue
    "$c" -I -c 'import venv' >/dev/null 2>&1 || continue
    printf '%s' "$c"; return 0
  done
  return 1
}

cd -- "$REPO_ROOT" || fail "cd repo root"
if _ready; then _bind; echo "dev_bootstrap: ready ($VENV)"; exit 0; fi   # fast pre-lock path

# Serialize create/install; re-probe after acquiring the lock (invariant 14).
i=0
while ! mkdir "$LOCKDIR" 2>/dev/null; do
  i=$((i+1)); [ "$i" -gt 120 ] && { echo "dev_bootstrap: FAIL [lock contention >60s] $LOCKDIR" >&2; exit 2; }
  sleep 0.5
done
_have_lock=1
if _ready; then _bind; _unlock; echo "dev_bootstrap: ready ($VENV)"; exit 0; fi

if [ -e "$VENV" ]; then
  _venv_valid || fail "existing .venv broken/non-isolated/symlinked; remove it manually and re-run"
else
  BP="$(_base_py)" || fail "no python3/python >=3.11 with venv available"
  "$BP" -I -m venv "$VENV" || fail "venv creation"
fi
"$VPY" -I -m pip install --isolated --no-input --disable-pip-version-check \
       --retries 0 --timeout 30 -e ".[dev]" >&2 || fail "pip install"
_ready || fail "post-install readiness (deps/version/provenance)"
_bind
_unlock
echo "dev_bootstrap: bootstrapped ($VENV)"
exit 0

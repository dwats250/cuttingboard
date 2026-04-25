#!/usr/bin/env python3
"""
engine_doctor.py — cuttingboard pipeline health authority

Usage:
    python3 tools/engine_doctor.py                                    # human-readable report
    python3 tools/engine_doctor.py --json                             # machine-readable JSON
    python3 tools/engine_doctor.py --tests --strict                   # fail on any warn
    python3 tools/engine_doctor.py --impact regime                    # blast radius
    python3 tools/engine_doctor.py --baseline tools/baseline.json     # validate against snapshot
    python3 tools/engine_doctor.py --json --tests --strict --baseline tools/baseline.json

Exit codes:
    0  OK
    1  Unexpected test failures
    2  Import failures
    3  New circular dependencies
    4  Missing required runtime files
    5  Baseline mismatch
    Priority (highest wins): 5 > 3 > 2 > 1 > 4
"""

import argparse
import ast
import importlib
import json
import re
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path

# ── project root ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── ANSI (suppressed in --json mode) ─────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def g(s): return f"{GREEN}{s}{RESET}"
def r(s): return f"{RED}{s}{RESET}"
def y(s): return f"{YELLOW}{s}{RESET}"
def c(s): return f"{CYAN}{s}{RESET}"
def b(s): return f"{BOLD}{s}{RESET}"
def d(s): return f"{DIM}{s}{RESET}"

# ── Enums ─────────────────────────────────────────────────────────────────────

class SystemStatus(str, Enum):
    OK   = "OK"
    WARN = "WARN"
    FAIL = "FAIL"

class FailureType(str, Enum):
    IMPORT_FAILURE       = "IMPORT_FAILURE"
    TEST_FAILURE         = "TEST_FAILURE"
    CIRCULAR_DEP         = "CIRCULAR_DEP"
    RUNTIME_FILE_MISSING = "RUNTIME_FILE_MISSING"
    BASELINE_MISMATCH    = "BASELINE_MISMATCH"

# Exit code priority: 5 > 3 > 2 > 1 > 4
_EXIT_PRIORITY = [5, 3, 2, 1, 4]

def _determine_exit_code(codes: set[int]) -> int:
    for code in _EXIT_PRIORITY:
        if code in codes:
            return code
    return 0

# ── Pipeline catalog ──────────────────────────────────────────────────────────
# (layer, short_name, full_module, key_exports)
PIPELINE = [
    ("1",  "config",                "cuttingboard.config",                  ["constants", "get_flow_data_path"]),
    ("2",  "ingestion",             "cuttingboard.ingestion",               ["RawQuote", "fetch_all", "fetch_quote"]),
    ("3",  "normalization",         "cuttingboard.normalization",           ["NormalizedQuote", "normalize_quotes"]),
    ("4",  "validation",            "cuttingboard.validation",              ["ValidationSummary", "validate_quotes", "validate_all"]),
    ("5",  "derived",               "cuttingboard.derived",                 ["DerivedMetrics", "compute_all_derived"]),
    ("6",  "structure",             "cuttingboard.structure",               ["StructureResult", "classify_all_structure"]),
    ("7",  "regime",                "cuttingboard.regime",                  ["RegimeState", "compute_regime"]),
    ("8",  "qualification",         "cuttingboard.qualification",           ["QualificationSummary", "qualify_all", "TradeCandidate"]),
    ("9",  "options",               "cuttingboard.options",                 ["OptionSetup", "build_option_setups"]),
    ("10", "chain_validation",      "cuttingboard.chain_validation",        ["ChainValidationResult", "validate_option_chains"]),
    ("11", "output",                "cuttingboard.output",                  ["render_report", "send_notification"]),
    ("—",  "audit",                 "cuttingboard.audit",                   ["write_audit_record", "write_notification_audit"]),
    ("—",  "contract",              "cuttingboard.contract",                ["build_pipeline_output_contract", "build_error_contract"]),
    ("—",  "flow",                  "cuttingboard.flow",                    ["FlowPrint", "apply_flow_gate"]),
    ("—",  "watch",                 "cuttingboard.watch",                   ["WatchSummary", "classify_watchlist"]),
    ("—",  "intraday_state_engine", "cuttingboard.intraday_state_engine",   ["compute_intraday_state", "IntraState"]),
    ("—",  "notifications",         "cuttingboard.notifications",           ["format_notification", "format_run_alert"]),
    ("—",  "run_intraday",          "cuttingboard.run_intraday",            ["main"]),
    ("—",  "runtime",               "cuttingboard.runtime",                 ["cli_main", "execute_run"]),
    ("—",  "time_utils",            "cuttingboard.time_utils",              ["get_now_et", "is_market_open"]),
    ("—",  "universe",              "cuttingboard.universe",                ["is_tradable_symbol"]),
    ("—",  "sector_router",         "cuttingboard.sector_router",           ["apply_sector_router"]),
    ("—",  "confirmation",          "cuttingboard.confirmation",            ["evaluate_level_confirmation"]),
]

ALL_MODULES = {mod: (layer, short, exports) for layer, short, mod, exports in PIPELINE}

RUNTIME_FILES = [
    ("logs/audit.jsonl",                  "audit log"),
    ("logs/last_notification_state.json", "notification state"),
    (".env",                              ".env secrets"),
    ("config.toml",                       "config.toml"),
]

# ── AST dependency analysis ───────────────────────────────────────────────────

def _short(mod: str) -> str:
    return mod.split(".")[-1]


def _extract_deps(filepath: Path) -> set[str]:
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return set()
    deps = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("cuttingboard"):
                parts = node.module.split(".")
                mod = ".".join(parts[:2]) if len(parts) > 1 else parts[0]
                if mod != "cuttingboard":
                    deps.add(mod)
            elif node.level > 0:
                sub = node.module or ""
                fqn = "cuttingboard." + sub if sub else "cuttingboard"
                if fqn != "cuttingboard":
                    parts = fqn.split(".")
                    mod = ".".join(parts[:2])
                    deps.add(mod)
    return deps


def build_dep_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    pkg = ROOT / "cuttingboard"
    for pyfile in pkg.rglob("*.py"):
        if pyfile.name.startswith("__"):
            continue
        rel = pyfile.relative_to(pkg)
        parts = list(rel.parts)
        parts[-1] = parts[-1][:-3]
        fqn = "cuttingboard." + ".".join(parts)
        top2 = ".".join(fqn.split(".")[:2])
        deps = _extract_deps(pyfile)
        if top2 not in graph:
            graph[top2] = set()
        graph[top2] |= deps
    for mod in ALL_MODULES:
        graph.setdefault(mod, set())
    return graph


def build_reverse_graph(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    rev: dict[str, set[str]] = {m: set() for m in graph}
    for mod, deps in graph.items():
        for dep in deps:
            rev.setdefault(dep, set()).add(mod)
    return rev


def _find_raw_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    visited: set[str] = set()
    stack: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]):
        visited.add(node)
        stack.add(node)
        for dep in sorted(graph.get(node, set())):
            if dep not in visited:
                dfs(dep, path + [dep])
            elif dep in stack:
                cycle_start = path.index(dep) if dep in path else 0
                cycles.append(path[cycle_start:] + [dep])
        stack.discard(node)

    for node in sorted(graph):
        if node not in visited:
            dfs(node, [node])
    return cycles


def _normalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    """Collapse a raw cycle path to a canonical sorted tuple of short names."""
    return tuple(sorted(set(_short(m) for m in cycle)))


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return deduplicated, normalized cycles. Self-loops excluded."""
    seen: set[tuple[str, ...]] = set()
    result: list[list[str]] = []
    for raw in _find_raw_cycles(graph):
        key = _normalize_cycle(raw)
        if len(key) < 2:  # self-loop artifact from subpackage normalization
            continue
        if key not in seen:
            seen.add(key)
            result.append(list(key))
    return sorted(result)


def all_downstream(target: str, rev: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    queue = [target]
    while queue:
        cur = queue.pop()
        for dep in rev.get(cur, set()):
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return seen

# ── Import health check ───────────────────────────────────────────────────────

def check_imports() -> dict[str, tuple[bool, str]]:
    results = {}
    for mod in ALL_MODULES:
        t0 = time.perf_counter()
        try:
            importlib.import_module(mod)
            elapsed = time.perf_counter() - t0
            results[mod] = (True, f"{elapsed*1000:.0f}ms")
        except Exception as exc:
            results[mod] = (False, str(exc).split("\n")[0][:120])
    return results

# ── Runtime file check ────────────────────────────────────────────────────────

def check_runtime_files() -> dict[str, bool]:
    """Return {relative_path_str: exists}."""
    return {rel: (ROOT / rel).exists() for rel, _ in RUNTIME_FILES}

# ── Test runner ───────────────────────────────────────────────────────────────

def _parse_pytest(output: str) -> tuple[int, int, list[str]]:
    passed = 0
    failed = 0
    failed_tests: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("FAILED "):
            name = stripped[7:].split(" - ")[0].strip()
            if "::" in name:
                name = name.split("::")[-1]
            failed_tests.append(name)
        m = re.search(r"(\d+) passed", stripped)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) failed", stripped)
        if m:
            failed = int(m.group(1))
    return passed, failed, sorted(set(failed_tests))


def run_tests() -> tuple[str, int, int, list[str]]:
    """Returns (raw_output, passed, failed, failed_test_names)."""
    result = subprocess.run(
        ["python3", "-m", "pytest", "--tb=line", "-q", "--no-header"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    raw = (result.stdout + result.stderr).strip()
    passed, failed, failed_tests = _parse_pytest(raw)
    return raw, passed, failed, failed_tests

# ── Baseline ──────────────────────────────────────────────────────────────────

def load_baseline(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(r(f"  baseline not found: {path}"), file=sys.stderr)
        sys.exit(1)
    return json.loads(p.read_text())


def _normalize_baseline_cycles(raw: list[list[str]]) -> list[list[str]]:
    return sorted(tuple(sorted(entry)) for entry in raw)

# ── Report builder ────────────────────────────────────────────────────────────

def build_report(
    health: dict[str, tuple[bool, str]] | None,
    cycles: list[list[str]],
    file_status: dict[str, bool],
    test_result: tuple[int, int, list[str]] | None,
    baseline: dict | None,
    impact_target: str | None,
    rev: dict[str, set[str]],
    strict: bool,
) -> tuple[dict, SystemStatus, set[int]]:
    """
    Returns (report_dict, status, exit_codes).
    report_dict has all required JSON keys.
    """
    status = SystemStatus.OK
    exit_codes: set[int] = set()
    failures: list[str] = []

    def escalate(new_status: SystemStatus, code: int, reason: str):
        nonlocal status
        failures.append(reason)
        exit_codes.add(code)
        if new_status == SystemStatus.FAIL or (new_status == SystemStatus.WARN and strict):
            status = SystemStatus.FAIL
        elif new_status == SystemStatus.WARN and status == SystemStatus.OK:
            status = SystemStatus.WARN

    # ── modules ──────────────────────────────────────────────────────────────
    failed_imports: list[str] = []
    if health is not None:
        for mod, (ok, _) in health.items():
            if not ok:
                failed_imports.append(_short(mod))
        if failed_imports:
            escalate(SystemStatus.FAIL, 2, f"import failures: {failed_imports}")

    modules_block = {
        "total":      len(ALL_MODULES),
        "importable": (len(ALL_MODULES) - len(failed_imports)) if health is not None else None,
        "failed":     sorted(failed_imports),
    }

    # ── tests ─────────────────────────────────────────────────────────────────
    expected_failures: list[str] = (baseline or {}).get("expected_failed_tests", [])
    if test_result is not None:
        passed, failed_count, failed_tests = test_result
        unexpected = [t for t in failed_tests if t not in expected_failures]
        now_passing = [t for t in expected_failures if t not in failed_tests]
        if unexpected:
            escalate(SystemStatus.FAIL, 1, f"unexpected test failures: {unexpected}")
            if baseline:
                escalate(SystemStatus.FAIL, 5, "baseline mismatch: unexpected test failures")
        if now_passing:
            # expected failure is now passing — baseline is stale
            if strict:
                escalate(SystemStatus.FAIL, 5, f"baseline mismatch: expected failures now passing: {now_passing}")
            else:
                escalate(SystemStatus.WARN, 5, f"expected failures now passing (update baseline): {now_passing}")
        tests_block = {
            "passed":           passed,
            "failed":           failed_count,
            "expected_failures": sorted(expected_failures),
        }
    else:
        tests_block = {
            "passed":           None,
            "failed":           None,
            "expected_failures": sorted(expected_failures),
        }

    # ── runtime files ─────────────────────────────────────────────────────────
    required = (baseline or {}).get("required_runtime_files", [])
    missing = sorted(p for p, exists in file_status.items() if not exists)
    present = sorted(p for p, exists in file_status.items() if exists)
    missing_required = [p for p in missing if p in required]
    if missing_required:
        escalate(SystemStatus.FAIL, 4, f"missing required files: {missing_required}")
        if baseline:
            escalate(SystemStatus.FAIL, 5, "baseline mismatch: missing required runtime files")

    runtime_block = {
        "missing": missing,
        "present": present,
    }

    # ── dependencies ─────────────────────────────────────────────────────────
    expected_cycles = _normalize_baseline_cycles(
        (baseline or {}).get("expected_circular_dependencies", [])
    )
    detected_set = {tuple(c) for c in cycles}
    expected_set = {tuple(c) for c in expected_cycles}
    new_cycles = sorted(list(c) for c in detected_set - expected_set)
    if new_cycles:
        escalate(SystemStatus.FAIL, 3, f"new circular dependencies: {new_cycles}")
        if baseline:
            escalate(SystemStatus.FAIL, 5, "baseline mismatch: new circular dependencies")

    deps_block = {
        "circular":     cycles,
        "new_circular": new_cycles,
    }

    # ── impact ───────────────────────────────────────────────────────────────
    impact_block: dict = {}
    if impact_target:
        target_mod = _resolve_module(impact_target)
        if target_mod:
            downstream = all_downstream(target_mod, rev)
            downstream.discard(target_mod)
            direct     = sorted(_short(m) for m in rev.get(target_mod, set()) if m in ALL_MODULES)
            transitive = sorted(_short(m) for m in downstream - {target_mod} if m not in {
                mm for mm in rev.get(target_mod, set())
            } and m in ALL_MODULES)
            impact_block[impact_target] = {
                "direct":     direct,
                "transitive": transitive,
            }

    report = {
        "status":        status.value,
        "modules":       modules_block,
        "tests":         tests_block,
        "runtime_files": runtime_block,
        "dependencies":  deps_block,
        "impact":        impact_block,
    }

    return report, status, exit_codes


def _resolve_module(name: str) -> str | None:
    for _, short, mod, _ in PIPELINE:
        if short == name or mod == name or mod.endswith("." + name):
            return mod
    return None

# ── Human-readable rendering ──────────────────────────────────────────────────

def _print_header():
    print()
    print(b("━" * 70))
    print(b("  CUTTINGBOARD ENGINE DOCTOR"))
    print(b("━" * 70))


def _print_pipeline(health: dict[str, tuple[bool, str]] | None):
    print()
    print(b("PIPELINE LAYERS"))
    print("─" * 70)
    fmt = "  {layer:>3}  {name:<26}  {status:<14}  {exports}"
    print(d(fmt.format(layer="L", name="MODULE", status="STATUS", exports="KEY EXPORTS")))
    print(d("─" * 70))

    for layer, short, mod, exports in PIPELINE:
        result = health.get(mod) if health is not None else None
        if result is None:
            status_str = d("—  skipped")
        elif result[0]:
            status_str = g(f"✓ ok  {result[1]:>5}")
        else:
            status_str = r("✗ FAIL")
        print(fmt.format(layer=layer, name=short, status=status_str, exports=d(", ".join(exports))))

    if health:
        n_ok   = sum(1 for ok, _ in health.values() if ok)
        n_fail = sum(1 for ok, _ in health.values() if not ok)
        print()
        if n_fail == 0:
            print(f"  {g(f'All {n_ok} modules import cleanly.')}")
        else:
            print(f"  {g(str(n_ok))} ok   {r(str(n_fail) + ' FAILED')}")
        for mod, (ok, detail) in health.items():
            if not ok:
                print(f"\n  {r('ERROR')} in {_short(mod)}:")
                print(f"    {detail}")


def _print_dep_graph(graph: dict[str, set[str]], rev: dict[str, set[str]], cycles: list[list[str]]):
    print()
    print(b("DEPENDENCY GRAPH  (direct imports only)"))
    print("─" * 70)
    for _, short, mod, _ in PIPELINE:
        deps = graph.get(mod, set())
        dep_names = sorted(_short(x) for x in deps if x in ALL_MODULES)
        rev_names = sorted(_short(x) for x in rev.get(mod, set()) if x in ALL_MODULES)
        if deps or rev.get(mod):
            print(f"  {c(short):<26} ← {d(', '.join(dep_names) or 'none')}")
            if rev_names:
                print(f"  {'':26}   {d('used by: ' + ', '.join(rev_names))}")

    if cycles:
        print()
        print(f"  {y('⚠  Circular dependencies detected:')}")
        for cyc in cycles:
            print(f"    {' → '.join(cyc)}")


def _print_runtime_files(file_status: dict[str, bool], required: list[str]):
    print()
    print(b("RUNTIME FILES"))
    print("─" * 70)
    for rel, label in RUNTIME_FILES:
        exists = file_status.get(rel, False)
        req_marker = ""
        if rel in required:
            req_marker = " (required)" if not exists else ""
        if exists:
            size = (ROOT / rel).stat().st_size
            print(f"  {g('✓')}  {label:<32}  {d(f'{size:,} bytes  {ROOT / rel}')}")
        else:
            marker = r("✗ MISSING" + req_marker) if rel in required else y("—")
            print(f"  {marker}  {label:<32}  {d(f'not found  {ROOT / rel}')}")


def _print_impact(target: str, rev: dict[str, set[str]]):
    target_mod = _resolve_module(target)
    if not target_mod:
        print(r(f"\n  Unknown module: {target}"))
        print("  Valid names: " + ", ".join(s for _, s, _, _ in PIPELINE))
        return

    downstream = all_downstream(target_mod, rev)
    downstream.discard(target_mod)
    direct     = {m for m in rev.get(target_mod, set()) if m in ALL_MODULES}
    transitive = downstream - direct

    print()
    print(b(f"IMPACT ANALYSIS — if {target} is changed or removed"))
    print("─" * 70)

    if not downstream:
        print(f"  {g('No other cuttingboard modules depend on')} {c(target)}.")
        return

    if direct:
        print(f"  {y('Direct dependents')}  ({len(direct)}):")
        for mod in sorted(direct):
            layer = ALL_MODULES[mod][0] if mod in ALL_MODULES else "—"
            print(f"    L{layer:<4} {_short(mod)}")

    if transitive:
        print(f"\n  {d('Transitive dependents')}  ({len(transitive)}):")
        for mod in sorted(transitive):
            layer = ALL_MODULES[mod][0] if mod in ALL_MODULES else "—"
            print(f"    L{layer:<4} {d(_short(mod))}")


def _print_tests(raw: str, passed: int, failed: int, failed_tests: list[str], expected: list[str]):
    print()
    print(b("TEST SUITE"))
    print("─" * 70)
    lines = raw.splitlines()
    display = lines[-12:] if len(lines) > 12 else lines
    for line in display:
        stripped = line.strip()
        if "passed" in stripped and "failed" not in stripped:
            print(f"  {g(stripped)}")
        elif stripped.startswith("FAILED") or "failed" in stripped or "error" in stripped.lower():
            print(f"  {r(stripped)}")
        else:
            print(f"  {d(stripped)}")

    unexpected = [t for t in failed_tests if t not in expected]
    now_passing = [t for t in expected if t not in failed_tests]
    if unexpected:
        print(f"\n  {r('Unexpected failures:')} {', '.join(unexpected)}")
    if now_passing:
        print(f"\n  {y('Expected failures now passing (update baseline):')} {', '.join(now_passing)}")


def _print_status_summary(status: SystemStatus, exit_codes: set[int], strict: bool):
    print()
    print(b("STATUS"))
    print("─" * 70)
    if status == SystemStatus.OK:
        print(f"  {g('OK')}  — all checks passed")
    elif status == SystemStatus.WARN:
        print(f"  {y('WARN')}  — warnings present (use --strict to treat as failure)")
    else:
        print(f"  {r('FAIL')}  — system health check failed")
    code = _determine_exit_code(exit_codes)
    if code != 0:
        print(f"  exit code: {r(str(code))}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cuttingboard engine health authority")
    parser.add_argument("--json",             action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--strict",           action="store_true", help="Escalate WARN to FAIL")
    parser.add_argument("--tests",            action="store_true", help="Run test suite")
    parser.add_argument("--impact",           metavar="MODULE",    help="Impact analysis for a module")
    parser.add_argument("--baseline",         metavar="PATH",      help="Validate against baseline snapshot")
    parser.add_argument("--no-import-check",  action="store_true", help="Skip import check (faster)")
    args = parser.parse_args()

    # Build dependency graph (always — fast, no imports)
    graph  = build_dep_graph()
    rev    = build_reverse_graph(graph)
    cycles = find_cycles(graph)

    # Load baseline
    baseline = load_baseline(args.baseline) if args.baseline else None

    # Import health
    if args.no_import_check:
        health = None
    else:
        if not args.json:
            print(d("\n  Checking imports..."), end="", flush=True)
        health = check_imports()
        if not args.json:
            print(d(" done."))

    # Runtime files
    file_status = check_runtime_files()

    # Tests
    test_result = None
    raw_test_output = ""
    if args.tests:
        if not args.json:
            print(d("  Running pytest..."), end="", flush=True)
        raw_test_output, t_passed, t_failed, t_failed_tests = run_tests()
        test_result = (t_passed, t_failed, t_failed_tests)
        if not args.json:
            print(d(" done."))

    # Build report
    required_files = (baseline or {}).get("required_runtime_files", [])
    report, status, exit_codes = build_report(
        health=health,
        cycles=cycles,
        file_status=file_status,
        test_result=test_result,
        baseline=baseline,
        impact_target=args.impact,
        rev=rev,
        strict=args.strict,
    )

    # Output
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_header()
        _print_pipeline(health)
        _print_dep_graph(graph, rev, cycles)
        _print_runtime_files(file_status, required_files)
        if args.impact:
            _print_impact(args.impact, rev)
        if test_result is not None:
            expected = (baseline or {}).get("expected_failed_tests", [])
            _print_tests(raw_test_output, *test_result, expected)
        _print_status_summary(status, exit_codes, args.strict)
        print()
        print(b("━" * 70))
        print()

    sys.exit(_determine_exit_code(exit_codes))


if __name__ == "__main__":
    main()

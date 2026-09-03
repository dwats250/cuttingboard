#!/usr/bin/env python3
"""Deterministic review-preparation evidence report for a git range.

Facts only. The tool resolves a base..head range and emits one Markdown
report: file inventory with numstat and coarse class, blob identity, diff
hunk pointers (or bounded inline diffs with --diff), touched Python symbols
(added / removed / modified, via ``ast`` over the base and head blobs), test
and fixture files that reference touched production modules or symbols
(bounded ``git grep`` over ``tests/`` at head), authority identifiers named in
the diff (PRD-NNN, GOV-N, DECISIONS, Gate A/B, VISION), supersession /
predecessor lines, and the ``git diff --check`` result.

It never interprets, classifies risk, or issues a verdict. Anything it cannot
determine reliably is reported as UNKNOWN or NOT FOUND. No model calls, no
network, no state: the same range on the same repository yields byte-identical
output.

Usage:
    python tools/review_prep.py --base <ref> --head <ref> [--path P ...]
                                [--diff] [--out FILE]
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

CLASS_PRODUCTION = "production"
CLASS_TEST = "test"
CLASS_DOCS = "docs/governance"
CLASS_INFRA = "workflow/infrastructure"
CLASS_FIXTURE = "fixture/golden"
CLASS_OTHER = "other"
CLASS_ORDER = (
    CLASS_PRODUCTION,
    CLASS_TEST,
    CLASS_FIXTURE,
    CLASS_DOCS,
    CLASS_INFRA,
    CLASS_OTHER,
)

# Bounded inline-diff budget per file under --diff; larger files fall back to
# hunk pointers so the report never pastes huge bodies.
INLINE_DIFF_MAX_LINES = 400
# Symbol reference sweep is bounded: only names this long or longer are
# searched (short names produce meaningless hits), and at most this many.
SYMBOL_MIN_LEN = 4
SYMBOL_SEARCH_MAX = 80
EXCERPT_MAX = 200

_AUTHORITY_RE = re.compile(
    r"\b(PRD-\d{1,4}(?:\s+R\d{1,3})?|GOV-\d|DECISIONS(?:\.md)?|Gate\s+[AB]\b|VISION(?:\.md)?)"
)
_SUPERSESSION_RE = re.compile(
    r"\b(SUPERSEDED(?:\s+IN\s+PART)?|SUPERSEDES|[Ss]upersed\w*|[Pp]redecessor|DEPRECATED|[Rr]eplaces\b)"
)
_FIXTURE_NAME_RE = re.compile(r"(golden|oracle|fixture|snapshot)", re.IGNORECASE)


# ---------------------------------------------------------------- git helpers
def _git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _git_bytes(repo: Path, *args: str) -> bytes | None:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def resolve_sha(repo: Path, ref: str) -> str:
    out = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", out):
        raise SystemExit(f"cannot resolve {ref!r} to a commit")
    return out


def blob_sha(repo: Path, rev: str, path: str) -> str:
    out = _git(repo, "ls-tree", rev, "--", path, check=False).strip()
    if not out:
        return "ABSENT"
    return out.split()[2]


# ------------------------------------------------------------- classification
def classify(path: str) -> str:
    p = path.replace("\\", "/")
    name = Path(p).name
    if p.startswith("tests/"):
        if p.startswith(("tests/data/", "tests/fixtures/")):
            return CLASS_FIXTURE
        if p.endswith(".py"):
            return CLASS_TEST
        return CLASS_FIXTURE
    if p.startswith((".github/", "tools/", "scripts/", ".claude/")) or name in (
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "wrangler.toml",
        "wrangler.example.toml",
        "Makefile",
    ):
        return CLASS_INFRA
    if p.startswith("docs/") or p.endswith(".md"):
        return CLASS_DOCS
    if p.startswith(("cuttingboard/", "runtime/", "workers/")):
        return CLASS_PRODUCTION
    if p.startswith(("logs/", "reports/", "ui/", "data/")) or _FIXTURE_NAME_RE.search(
        name
    ):
        return CLASS_FIXTURE
    return CLASS_OTHER


# ------------------------------------------------------------------ inventory
def numstat(
    repo: Path, base: str, head: str, paths: list[str]
) -> "OrderedDict[str, tuple[str, str]]":
    out = _git(repo, "diff", "--numstat", base, head, "--", *paths)
    rows: dict[str, tuple[str, str]] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        adds, dels, path = parts
        rows[path] = (adds, dels)
    return OrderedDict(sorted(rows.items()))


def name_status(repo: Path, base: str, head: str, paths: list[str]) -> dict[str, str]:
    out = _git(repo, "diff", "--name-status", base, head, "--", *paths)
    status: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status[parts[-1]] = parts[0]
    return status


def hunk_pointers(repo: Path, base: str, head: str, path: str) -> list[str]:
    out = _git(repo, "diff", "-U0", "--no-color", base, head, "--", path, check=False)
    return [ln for ln in out.splitlines() if ln.startswith("@@")]


def inline_diff(repo: Path, base: str, head: str, path: str) -> str | None:
    out = _git(repo, "diff", "--no-color", base, head, "--", path, check=False)
    if "Binary files" in out:
        return None
    if len(out.splitlines()) > INLINE_DIFF_MAX_LINES:
        return None
    return out


# -------------------------------------------------------------------- symbols
def _symbol_table(source: bytes) -> dict[str, tuple[int, str]]:
    """Qualified def/class names -> (lineno, sha1 of the node's source)."""
    try:
        text = source.decode("utf-8")
        tree = ast.parse(text)
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return {}
    table: dict[str, tuple[int, str]] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qname = f"{prefix}{child.name}"
                seg = ast.get_source_segment(text, child) or ""
                table[qname] = (
                    child.lineno,
                    hashlib.sha1(seg.encode()).hexdigest()[:12],
                )
                if isinstance(child, ast.ClassDef):
                    visit(child, qname + ".")

    visit(tree, "")
    return table


def symbol_delta(repo: Path, base: str, head: str, path: str) -> dict[str, list[str]]:
    before = _git_bytes(repo, "show", f"{base}:{path}") or b""
    after = _git_bytes(repo, "show", f"{head}:{path}") or b""
    tb, ta = _symbol_table(before), _symbol_table(after)
    added = sorted(n for n in ta if n not in tb)
    removed = sorted(n for n in tb if n not in ta)
    modified = sorted(n for n in ta if n in tb and ta[n][1] != tb[n][1])
    return {
        "added": [f"{n} (L{ta[n][0]})" for n in added],
        "removed": [f"{n} (base L{tb[n][0]})" for n in removed],
        "modified": [f"{n} (L{ta[n][0]})" for n in modified],
        "_names": sorted(set(added) | set(modified)),
    }


def module_name(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    parts = Path(path).with_suffix("").parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


# ------------------------------------------------------------ test references
def grep_tests(repo: Path, head: str, needle: str, word: bool = False) -> list[str]:
    flags = ["-l", "-F", "-w"] if word else ["-l", "-F"]
    out = _git(repo, "grep", *flags, "-e", needle, head, "--", "tests", check=False)
    files = []
    for line in out.splitlines():
        # format: <rev>:<path>
        _, _, p = line.partition(":")
        files.append(p)
    return sorted(set(files))


# ------------------------------------------------------------------ authority
def diff_lines(repo: Path, base: str, head: str, path: str) -> list[tuple[str, str]]:
    """(sign, text) for +/- lines of a text diff; empty for binary."""
    out = _git(repo, "diff", "--no-color", base, head, "--", path, check=False)
    if "Binary files" in out:
        return []
    rows = []
    for ln in out.splitlines():
        if ln.startswith(("+++", "---")):
            continue
        if ln[:1] in "+-":
            rows.append((ln[0], ln[1:]))
    return rows


def authority_refs(lines: list[tuple[str, str]]) -> "OrderedDict[str, int]":
    counts: dict[str, int] = {}
    for sign, text in lines:
        if sign != "+":
            continue
        for m in _AUTHORITY_RE.finditer(text):
            key = re.sub(r"\s+", " ", m.group(1))
            counts[key] = counts.get(key, 0) + 1
    return OrderedDict(sorted(counts.items()))


def supersession_lines(lines: list[tuple[str, str]]) -> list[str]:
    hits = []
    for sign, text in lines:
        if sign == "+" and _SUPERSESSION_RE.search(text):
            t = text.strip()
            hits.append(t if len(t) <= EXCERPT_MAX else t[: EXCERPT_MAX - 3] + "...")
    return hits


def diff_check(
    repo: Path, base: str, head: str, paths: list[str]
) -> tuple[int, list[str]]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--check", base, head, "--", *paths],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return proc.returncode, proc.stdout.splitlines()[:40]


# --------------------------------------------------------------------- report
def build_report(
    repo: Path, base_ref: str, head_ref: str, paths: list[str], with_diff: bool
) -> str:
    base = resolve_sha(repo, base_ref)
    head = resolve_sha(repo, head_ref)
    stats = numstat(repo, base, head, paths)
    status = name_status(repo, base, head, paths)
    out: list[str] = []
    w = out.append

    w("# REVIEW PREP EVIDENCE (facts only; no verdict)")
    w("")
    w(f"- base: `{base}` (requested `{base_ref}`)")
    w(f"- head: `{head}` (requested `{head_ref}`)")
    w(f"- path filter: {', '.join(f'`{p}`' for p in paths) if paths else 'none'}")
    commits = _git(
        repo, "log", "--reverse", "--format=%h %s", f"{base}..{head}"
    ).splitlines()
    w(f"- commits in range: {len(commits)} (oldest first)")
    for c in commits:
        w(f"  - `{c[:120]}`")
    w("")

    # 1. inventory + class totals
    w("## 1. Changed-file inventory")
    w("")
    w("| class | file | status | +/- | base blob | head blob |")
    w("|---|---|---|---|---|---|")
    totals: dict[str, list[int]] = {c: [0, 0, 0] for c in CLASS_ORDER}
    classes: dict[str, str] = {}
    for path, (adds, dels) in stats.items():
        cls = classify(path)
        classes[path] = cls
        totals[cls][2] += 1
        if adds != "-":
            totals[cls][0] += int(adds)
            totals[cls][1] += int(dels)
        delta = "binary" if adds == "-" else f"+{adds}/-{dels}"
        w(
            f"| {cls} | `{path}` | {status.get(path, '?')} | {delta} "
            f"| {blob_sha(repo, base, path)[:12]} | {blob_sha(repo, head, path)[:12]} |"
        )
    w("")
    w("### Totals by class (git numstat lines; binary files counted as files only)")
    w("")
    w("| class | files | added | deleted | net |")
    w("|---|---|---|---|---|")
    for cls in CLASS_ORDER:
        a, d, n = totals[cls]
        if n:
            w(f"| {cls} | {n} | {a} | {d} | {a - d:+d} |")
    w("")

    # 2. diff pointers / inline
    w("## 2. Diff regions")
    w("")
    for path in stats:
        w(f"### `{path}`")
        body = inline_diff(repo, base, head, path) if with_diff else None
        if body is not None:
            w("")
            w("```diff")
            out.extend(body.rstrip("\n").splitlines())
            w("```")
        else:
            hunks = hunk_pointers(repo, base, head, path)
            if not hunks:
                w("- hunks: NOT FOUND (binary or empty diff)")
            for h in hunks:
                w(f"- `{h}`")
        w("")

    # 3. symbols
    w("## 3. Touched Python symbols (ast over base/head blobs)")
    w("")
    symbol_names: dict[str, list[str]] = {}
    any_py = False
    for path in stats:
        if not path.endswith(".py"):
            continue
        any_py = True
        delta = symbol_delta(repo, base, head, path)
        symbol_names[path] = delta["_names"]
        w(f"### `{path}`")
        for kind in ("added", "removed", "modified"):
            items = delta[kind]
            w(f"- {kind}: " + (", ".join(f"`{i}`" for i in items) if items else "none"))
        w("")
    if not any_py:
        w("NOT FOUND (no Python files in range)")
        w("")

    # 4. test / fixture references
    w(
        "## 4. Tests and fixtures referencing touched production files or symbols (git grep at head, `tests/`)"
    )
    w("")
    w(
        "Symbol rows are whole-word identifier matches; a same-named symbol elsewhere also matches."
    )
    w("")
    prod_py = [p for p in stats if classes[p] == CLASS_PRODUCTION and p.endswith(".py")]
    if not prod_py:
        w("NOT FOUND (no production Python files in range)")
        w("")
    searched = 0
    for path in prod_py:
        w(f"### `{path}`")
        mod = module_name(path)
        stem = Path(path).stem
        refs = set()
        if mod:
            refs.update(grep_tests(repo, head, mod))
        refs.update(grep_tests(repo, head, stem))
        refs.discard(path)
        w(
            "- module references: "
            + (", ".join(f"`{r}`" for r in sorted(refs)) if refs else "NOT FOUND")
        )
        for name in symbol_names.get(path, []):
            leaf = name.rsplit(".", 1)[-1]
            if len(leaf) < SYMBOL_MIN_LEN or leaf.startswith("__"):
                continue
            if searched >= SYMBOL_SEARCH_MAX:
                w(f"- symbol sweep truncated at {SYMBOL_SEARCH_MAX} names")
                break
            searched += 1
            hits = grep_tests(repo, head, leaf, word=True)
            hit_desc = ", ".join(f"`{h}`" for h in hits) if hits else "NOT FOUND"
            w(f"- `{name}`: {hit_desc}")
        w("")

    # 5/6. authority refs + supersession
    w("## 5. Authority identifiers introduced by the diff (+ lines only)")
    w("")
    any_ref = False
    all_super: list[tuple[str, str]] = []
    for path in stats:
        lines = diff_lines(repo, base, head, path)
        refs = authority_refs(lines)
        for t in supersession_lines(lines):
            all_super.append((path, t))
        if refs:
            any_ref = True
            w(f"- `{path}`: " + ", ".join(f"{k} x{v}" for k, v in refs.items()))
    if not any_ref:
        w("NOT FOUND")
    w("")
    w("## 6. Supersession / predecessor lines introduced by the diff")
    w("")
    if all_super:
        counted: "OrderedDict[tuple[str, str], int]" = OrderedDict()
        for key in all_super:
            counted[key] = counted.get(key, 0) + 1
        for (path, t), n in counted.items():
            w(f"- `{path}`: {t}" + (f" (x{n})" if n > 1 else ""))
    else:
        w("NOT FOUND")
    w("")

    # 7. diff --check
    rc, lines = diff_check(repo, base, head, paths)
    w("## 7. git diff --check")
    w("")
    w(f"- exit code: {rc} ({'clean' if rc == 0 else 'whitespace issues'})")
    for ln in lines:
        w(f"- `{ln}`")
    w("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument(
        "--path", action="append", default=[], help="pathspec filter (repeatable)"
    )
    ap.add_argument(
        "--diff",
        action="store_true",
        help=f"inline text diffs up to {INLINE_DIFF_MAX_LINES} lines per file",
    )
    ap.add_argument("--repo", default=".", help="repository root (default: cwd)")
    ap.add_argument("--out", help="write the report here instead of stdout")
    args = ap.parse_args(argv)
    report = build_report(Path(args.repo), args.base, args.head, args.path, args.diff)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

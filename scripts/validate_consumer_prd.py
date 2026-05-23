#!/usr/bin/env python3
"""Real-data validation harness for CONSUMER-class PRDs.

Runs a consumer (parser/normalizer/etc.) against a real-data fixture
and scaffolds a defect log at
``docs/prd_history/PRD-NNN.validation.md`` for Claude/human review.

This script does NOT decide whether the consumer's output is correct.
It captures output, surfaces exceptions, and lays down the defect-log
structure so the validate-then-fix discipline (see
``docs/DECISIONS.md`` 2026-05-22, PRD-153 closeout) is mechanical
rather than ad-hoc.

Usage:
    python scripts/validate_consumer_prd.py \\
        --prd PRD-153 \\
        --module cuttingboard.moomoo_parser \\
        --fn parse_statement \\
        --fixture private/moomoo/some-statement.pdf

The named function is called with the fixture path as a single
positional argument. Output is captured as ``repr()`` (truncated to
keep the log readable). Exceptions are captured with traceback.
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import pathlib
import sys
import textwrap
import traceback


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "prd_history"
MAX_REPR_CHARS = 16_000


def _load_callable(module_path: str, fn_name: str):
    module = importlib.import_module(module_path)
    if not hasattr(module, fn_name):
        raise AttributeError(
            f"module {module_path!r} has no attribute {fn_name!r}"
        )
    return getattr(module, fn_name)


def _truncated_repr(value: object) -> tuple[str, bool]:
    text = repr(value)
    if len(text) <= MAX_REPR_CHARS:
        return text, False
    return text[:MAX_REPR_CHARS] + "\n... [truncated] ...", True


def _run(fn, fixture: pathlib.Path) -> dict:
    try:
        result = fn(fixture)
    except Exception:  # noqa: BLE001 — we want the traceback in the log
        return {
            "ok": False,
            "traceback": traceback.format_exc(),
            "output_repr": None,
            "truncated": False,
        }
    output_repr, truncated = _truncated_repr(result)
    return {
        "ok": True,
        "traceback": None,
        "output_repr": output_repr,
        "truncated": truncated,
    }


def _scaffold(prd: str, module: str, fn: str, fixture: pathlib.Path, run: dict) -> str:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    fixture_rel = fixture
    try:
        fixture_rel = fixture.relative_to(REPO_ROOT)
    except ValueError:
        pass
    header = textwrap.dedent(f"""\
        # {prd} — Real-data validation log

        - Generated: {now}
        - Consumer: `{module}.{fn}`
        - Fixture: `{fixture_rel}`
        - Harness: `scripts/validate_consumer_prd.py`

        This artifact captures a real-data validation pass for
        a CONSUMER-class PRD (see `docs/PRD_PROCESS.md` and the
        validate-then-fix discipline in `docs/DECISIONS.md`,
        2026-05-22 PRD-153 closeout). The harness ran the consumer
        against the fixture above and captured the output verbatim.
        Defects are filled in by review, not by the harness.

        ## Run outcome

        """)
    if run["ok"]:
        body = textwrap.dedent(f"""\
            Status: **completed without exception**

            ### Captured output (`repr`)

            ```
            {run["output_repr"]}
            ```
            """)
        if run["truncated"]:
            body += "\n_Output was truncated. Re-run with a smaller fixture or inspect interactively if full output is needed._\n"
    else:
        body = textwrap.dedent(f"""\
            Status: **exception during run**

            ### Traceback

            ```
            {run["traceback"]}
            ```
            """)

    defects_section = textwrap.dedent("""\

        ## Observed defects

        Fill in one entry per defect surfaced by comparing the run
        output above against expected behavior. Leave the section
        empty if the run was clean.

        ### Defect 1

        - **Where:** (file:line or row identifier in the fixture)
        - **Observed:** (what the consumer produced)
        - **Expected:** (what should have been produced)
        - **Root cause:** (one-line)
        - **Amend-vs-spawn classification:**
          - [ ] Amend in-flight PRD (same domain, fits existing shape, <~10 LOC)
          - [ ] Spawn follow-up PRD (cross-domain, new contract field, or larger)
          - Rationale:
        - **Resolution:** (code change summary OR follow-up PRD number)

        ## Closeout

        - [ ] All defects resolved or formally deferred
        - [ ] PRD amendments (if any) recorded in PRD NOTES section
        - [ ] Follow-up PRDs (if any) drafted and linked
        - [ ] Test added covering the real-data case for each amended defect
        """)
    return header + body + defects_section


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prd", required=True, help="PRD identifier, e.g. PRD-153")
    parser.add_argument("--module", required=True, help="Dotted module path of the consumer")
    parser.add_argument("--fn", required=True, help="Function name within the module")
    parser.add_argument("--fixture", required=True, type=pathlib.Path, help="Path to real-data fixture")
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=None,
        help=f"Output path (default: {DEFAULT_OUT_DIR}/PRD-NNN.validation.md)",
    )
    args = parser.parse_args(argv)

    fixture = args.fixture.resolve()
    if not fixture.exists():
        print(f"error: fixture not found: {fixture}", file=sys.stderr)
        return 2

    out_path = args.out or (DEFAULT_OUT_DIR / f"{args.prd}.validation.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure repo root is on sys.path so the consumer module imports cleanly.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    fn = _load_callable(args.module, args.fn)
    run = _run(fn, fixture)
    scaffold = _scaffold(args.prd, args.module, args.fn, fixture, run)
    out_path.write_text(scaffold)

    status = "ok" if run["ok"] else "exception"
    print(f"wrote {out_path} (run: {status})")
    return 0 if run["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

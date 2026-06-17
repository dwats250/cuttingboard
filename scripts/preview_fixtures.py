#!/usr/bin/env python3
"""PRD-179 — local dashboard preview harness for synthetic section states.

Renders every case in ``tests.preview_fixtures.SECTION_STATE_CASES`` to a
NON-ui path (``reports/output/fixture_<name>.html``), alongside — never instead
of — the fresh-data preview shipped by PRD-178
(``scripts/preview_dashboard.sh``). Fixture output is structurally barred from
``ui/`` (PRD-118 R5); this harness only ever writes under ``reports/output/``.

Usage:
    python scripts/preview_fixtures.py            # render all cases
    python scripts/preview_fixtures.py --list     # list case names + markers
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cuttingboard.delivery.dashboard_renderer import (  # noqa: E402
    _output_under_ui,
    render_dashboard_html,
)
from tests.preview_fixtures import SECTION_STATE_CASES  # noqa: E402

OUT_DIR = ROOT / "reports" / "output"


def render_all(out_dir: Path = OUT_DIR) -> list[Path]:
    """Render each case to out_dir/fixture_<name>.html; fail if a marker is missing.

    Refuses any output path resolving under the repo's ``ui/`` directory: this
    writer bypasses ``validate_coherent_publish`` (it writes HTML directly), so
    without this guard an override like ``Path("ui")`` would emit fixture HTML
    into the publish tree, contradicting the module's "structurally barred from
    ui/" claim. The directory is checked once up front (fail before mkdir), and
    each composed file path is re-checked before writing — ``_output_under_ui``
    resolves symlinks, so a planted ``reports/output/fixture_*.html`` symlink into
    the publish tree is refused rather than followed by ``write_text``. Both
    checks reuse the same helper ``validate_coherent_publish`` uses.
    """
    if _output_under_ui(out_dir):
        raise SystemExit(
            f"FAIL: render_all refuses to write fixture HTML under ui/ (got {out_dir}); "
            "fixture output is structurally barred from the publish tree (PRD-118 R5)."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for case in SECTION_STATE_CASES:
        html = render_dashboard_html(
            case.payload,
            case.run,
            market_map=case.market_map,
            fixture_mode=case.fixture_mode,
            **case.render_kwargs,
        )
        if case.marker not in html:
            raise SystemExit(f"FAIL: case {case.name!r} missing marker {case.marker!r}")
        for extra in case.extra_markers:
            if extra not in html:
                raise SystemExit(f"FAIL: case {case.name!r} missing extra marker {extra!r}")
        out = out_dir / f"fixture_{case.name}.html"
        if _output_under_ui(out):
            raise SystemExit(
                f"FAIL: render_all refuses to write {out} — it resolves under ui/ "
                "(e.g. a symlink into the publish tree); fixture output is "
                "structurally barred from the publish tree (PRD-118 R5)."
            )
        out.write_text(html, encoding="utf-8")
        written.append(out)
        print(f"  {case.name:24s} -> {out}  [{case.marker}]")
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="PRD-179 fixture preview harness")
    ap.add_argument("--list", action="store_true", help="list case names and markers")
    args = ap.parse_args()
    if args.list:
        for case in SECTION_STATE_CASES:
            print(f"{case.name:24s} {case.marker}")
        return
    written = render_all()
    print(f"\npreview written: {len(written)} fixture renders under {OUT_DIR}")


if __name__ == "__main__":
    main()

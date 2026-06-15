#!/usr/bin/env python3
"""Macro-Awareness materiality eval harness (PRD-187 R8).

The ONLY thing that speaks to materiality / false-positive discipline. CI never
asserts materiality; this harness does, over a human-labeled corpus, with a pinned
model and an explicit threshold T. It is the PRD-188 gate.

Usage (NOT run in CI; needs a labeled corpus + a threshold T set by the human):
    python3 tools/macro_awareness_eval.py \
        --corpus data/macro_awareness_eval_corpus.json \
        --threshold 0.05 \
        --out audits/2026-06-15/macro_awareness_eval.md

The harness refuses to run until every case carries a ground-truth label.
It imports the producer's classify + build_snapshot so it tests the real path.
(Importing tools.* from tools/ is fine; only cuttingboard<->collector imports are
forbidden by PRD-187 R1.)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import macro_awareness_collector as mac  # sibling tool; see module docstring


def _load_corpus(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entries_for(case: dict) -> list[mac.Entry]:
    entries: list[mac.Entry] = []
    for row in case.get("entries", []):
        entries.append(mac.Entry(
            source_name=row.get("source_name", ""),
            entity=row.get("entity", ""),
            domain=row.get("domain", ""),
            title=row.get("title", ""),
            summary=row.get("summary", ""),
            link=row.get("link", ""),
            published_at=row.get("published_at", ""),
        ))
    return entries


def run_eval(corpus: dict, *, model: str, now: datetime) -> dict:
    """Classify every case and tally a confusion matrix + false-positive rate.

    A case's predicted status is SHOCK iff the producer would build a SHOCK
    snapshot from the model's classification. Novelty is intentionally NOT applied
    (the eval measures the classifier, not dedup)."""
    cases = corpus.get("cases", [])
    unlabeled = [c.get("id") for c in cases if c.get("label") not in ("QUIET", "SHOCK")]
    if not cases or unlabeled:
        raise SystemExit(
            f"corpus not fully labeled (unlabeled: {unlabeled or 'no cases'}); "
            "fill ground-truth labels before running the eval."
        )

    tp = fp = tn = fn = 0
    rows = []
    for case in cases:
        entries = _entries_for(case)
        classification = mac.classify(entries, model=model)
        snapshot = mac.build_snapshot(entries, classification, now)
        predicted = snapshot["status"]
        label = case["label"]
        if label == "SHOCK" and predicted == "SHOCK":
            tp += 1
        elif label == "QUIET" and predicted == "SHOCK":
            fp += 1
        elif label == "QUIET" and predicted == "QUIET":
            tn += 1
        else:
            fn += 1
        rows.append({"id": case.get("id"), "label": label, "predicted": predicted})

    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "fp_rate": fp_rate, "rows": rows}


def _render(result: dict, *, model: str, threshold: float | None, now: datetime) -> str:
    lines = [
        "# Macro-Awareness Materiality Eval (PRD-187 R8 / PRD-188 gate)",
        "",
        f"- generated_at: {now.isoformat()}",
        f"- model (pinned): {model}",
        f"- threshold T: {threshold if threshold is not None else 'NOT SET'}",
        "",
        "## Confusion matrix",
        f"- true positives (SHOCK->SHOCK): {result['tp']}",
        f"- false positives (QUIET->SHOCK): {result['fp']}",
        f"- true negatives (QUIET->QUIET): {result['tn']}",
        f"- false negatives (SHOCK->QUIET): {result['fn']}",
        "",
        f"- **false-positive rate: {result['fp_rate']:.4f}**",
    ]
    if threshold is not None:
        verdict = "PASS" if result["fp_rate"] <= threshold else "FAIL"
        lines.append(f"- **gate (fp_rate <= {threshold}): {verdict}**")
    lines += ["", "## Per-case", "| id | label | predicted |", "|----|-------|-----------|"]
    lines += [f"| {r['id']} | {r['label']} | {r['predicted']} |" for r in result["rows"]]
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Macro-Awareness materiality eval (PRD-187)")
    parser.add_argument("--corpus", default="data/macro_awareness_eval_corpus.json")
    parser.add_argument("--model", default=mac.DEFAULT_MODEL)
    parser.add_argument("--threshold", type=float, default=None,
                        help="False-positive threshold T (set by Dustin); omit to report only.")
    parser.add_argument("--out", default=None, help="Result artifact path under audits/.")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    corpus = _load_corpus(Path(args.corpus))
    result = run_eval(corpus, model=args.model, now=now)
    report = _render(result, model=args.model, threshold=args.threshold, now=now)

    out = args.out or f"audits/{now:%Y-%m-%d}/macro_awareness_eval.md"
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

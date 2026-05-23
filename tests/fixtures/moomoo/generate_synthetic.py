"""Deterministic generator for the synthetic Moomoo statement PDF fixture.

The generated PDF (``synthetic_statement.pdf`` in this directory) is
committed alongside this script. Regenerate only when intentionally
changing the fixture; otherwise tests must read the committed file
without regeneration.

All timestamps and randomness sources are pinned so that running this
script produces a byte-identical output every time.
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet


FIXTURE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = FIXTURE_DIR / "synthetic_statement.pdf"

# Pinned timestamp baked into the PDF metadata (deterministic output).
PINNED_TIMESTAMP_EPOCH = 1_700_000_000

ACTIVITY_HEADERS = ["Date", "Type", "Description", "Quantity", "Price ($)", "Amount ($)"]

CAD_ROWS = [
    ["", "", "Opening Balance", "", "", "0.00"],
    ["Feb 17, 2026", "E-transfer Deposit", "INTERAC DEPOSIT", "", "", "200.00"],
    ["Feb 23, 2026", "FX Sell Trade", "USD/CAD@1.36799", "", "", "(300.00)"],
    ["", "", "Closing Balance", "", "", "600.00"],
]

USD_ROWS = [
    ["", "", "Opening Balance", "", "", "0.00"],
    ["Feb 18, 2026", "Buy", "CALL 100 GLD 02/25/26 480", "1", "5.000", "(501.00)"],
    ["Feb 19, 2026", "Sell", "CALL 100 GLD 02/25/26 480", "(1)", "4.900", "489.00"],
    ["Feb 20, 2026", "Expired Option", "PUT 100 SLV 02/20/26 67", "(1)", "0.000", "0.00"],
    ["Feb 23, 2026", "FX Buy Trade", "USD/CAD@1.36799", "", "", "438.59"],
    ["Feb 25, 2026", "Buy", "SPY", "10", "580.000", "(5800.00)"],
    ["Feb 25, 2026", "Sell", "SPY", "(10)", "585.000", "5850.00"],
    ["", "", "Closing Balance", "", "", "50.00"],
]

NEXT_PERIOD_ROWS = [
    ["Feb 27, 2026", "Buy", "QQQ", "5", "510.000", "(2550.00)"],
]


def _table(rows: list[list[str]]) -> Table:
    data = [ACTIVITY_HEADERS] + rows
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_pdf(output_path: Path = OUTPUT_PATH) -> Path:
    # Pin SOURCE_DATE_EPOCH so reportlab's PDF metadata timestamps are deterministic.
    os.environ["SOURCE_DATE_EPOCH"] = str(PINNED_TIMESTAMP_EPOCH)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        title="Synthetic Moomoo Statement",
        author="cuttingboard tests",
        subject="moomoo synthetic fixture",
        creator="cuttingboard",
        producer="cuttingboard",
    )

    story = [
        Paragraph("Client Statement", styles["Title"]),
        Paragraph("Period Ending: Feb 28, 2026", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Account Activity - Margin Account (CAD) - 7R5-MF8E-1", styles["Heading3"]),
        _table(CAD_ROWS),
        Spacer(1, 12),
        Paragraph("Account Activity - Margin Account (USD) - 7R5-MF8F-1", styles["Heading3"]),
        _table(USD_ROWS),
        Spacer(1, 12),
        Paragraph("Transactions to settle after current period", styles["Heading3"]),
        _table(NEXT_PERIOD_ROWS),
    ]

    doc.build(story)
    return output_path


if __name__ == "__main__":
    path = build_pdf()
    print(f"Wrote {path}")

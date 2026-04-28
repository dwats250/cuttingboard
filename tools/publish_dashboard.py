"""
Publish reports/output/dashboard.html → docs/dashboard.html.

Performs a byte-for-byte copy with post-copy verification.
No mutation, no engine imports, no runtime dependencies.
"""

import hashlib
import shutil
import sys
from pathlib import Path

SOURCE = Path("reports/output/dashboard.html")
TARGET = Path("docs/dashboard.html")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish() -> None:
    if not SOURCE.exists():
        print(f"FAIL: source not found: {SOURCE}", file=sys.stderr)
        sys.exit(1)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)

    if _sha256(SOURCE) != _sha256(TARGET):
        print("FAIL: published file does not match source (byte mismatch)", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {SOURCE} → {TARGET} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    publish()

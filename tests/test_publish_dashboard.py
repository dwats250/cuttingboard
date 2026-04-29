import hashlib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_publish(monkeypatch, source_root: Path):
    """Import publish_dashboard with SOURCE/TARGET rooted under source_root."""
    import tools.publish_dashboard as mod
    monkeypatch.setattr(mod, "SOURCE", source_root / "reports/output/dashboard.html")
    monkeypatch.setattr(mod, "TARGET", source_root / "docs/dashboard.html")
    return mod


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_missing_source_fails(tmp_path, monkeypatch):
    mod = _load_publish(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as exc:
        mod.publish()
    assert exc.value.code == 1


def test_creates_docs_directory(tmp_path, monkeypatch):
    source = tmp_path / "reports/output/dashboard.html"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"<html>test</html>")

    mod = _load_publish(monkeypatch, tmp_path)
    mod.publish()

    assert (tmp_path / "docs").is_dir()
    assert (tmp_path / "docs/dashboard.html").exists()


def test_publishes_dashboard_html(tmp_path, monkeypatch):
    content = b"<html><body>dashboard</body></html>"
    source = tmp_path / "reports/output/dashboard.html"
    source.parent.mkdir(parents=True)
    source.write_bytes(content)

    mod = _load_publish(monkeypatch, tmp_path)
    mod.publish()

    target = tmp_path / "docs/dashboard.html"
    assert target.read_bytes() == content


def test_exact_byte_copy(tmp_path, monkeypatch):
    content = b"\x00\xFF" * 512 + b"<html/>"
    source = tmp_path / "reports/output/dashboard.html"
    source.parent.mkdir(parents=True)
    source.write_bytes(content)

    mod = _load_publish(monkeypatch, tmp_path)
    mod.publish()

    target = tmp_path / "docs/dashboard.html"
    assert _sha256(source) == _sha256(target)


def test_no_engine_imports():
    forbidden = {
        "cuttingboard.runtime",
        "cuttingboard.regime",
        "cuttingboard.qualification",
        "cuttingboard.ingestion",
        "cuttingboard.delivery.dashboard_renderer",
        "cuttingboard.delivery.payload",
    }
    import tools.publish_dashboard as mod
    source = Path(mod.__file__).read_text()
    for name in forbidden:
        assert name not in source, f"Forbidden import found: {name}"

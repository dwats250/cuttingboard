"""PRD-162 — outcome / actionable-trade reconciliation acceptance tests.

Covers AC1–AC4 of PRD-162, including the required runtime/output
outcome-agreement test: the runtime outcome (object adapter over
TradeDecision at runtime.py:875) and the render_report_from_payload outcome
(derived from the gated payload top_trades) agree for the same candidate set.

The four contradictions reconciled here:
  D1 — non-tradable symbols as trade-like candidates (^VIX in top_trades)
  D2 — sized-but-blocked candidates surfacing as actionable
  D3 — populated top_trades under a NO_TRADE outcome

The reconciliation gates the *actionable* projection (payload top_trades) and
the runtime outcome on one shared rule, while leaving contract.trade_candidates
intact as the broader audit surface.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from cuttingboard import config, runtime
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.output import render_report_from_payload
from cuttingboard.trade_decision import ALLOW_TRADE

# Reuse the sanctioned runtime fixture-pipeline harness.
from tests.test_runtime_decision import _setup_runtime_mocks


FIXTURE = Path("tests/fixtures/2026-04-12.json")
RUN_DATE = date.fromisoformat("2026-04-28")


def _force_allow(monkeypatch, symbol: str) -> None:
    """Force the decision stage to emit an ALLOW_TRADE decision for `symbol`.

    Fixture mode otherwise blocks every candidate (MANUAL_CHECK), so an
    ALLOW_TRADE path must be injected to exercise the actionable case.
    """
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        symbol: ChainValidationResult(
            symbol=symbol,
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))


def _run(monkeypatch, tmp_path, symbol: str, *, allow: bool):
    """Drive the fixture pipeline for `symbol`; return (result, payload, rendered)."""
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)
    if allow:
        _force_allow(monkeypatch, symbol)
    else:
        # Leave chain + decision REAL → fixture mode yields BLOCK_TRADE.
        monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
            symbol: ChainValidationResult(
                symbol=symbol,
                classification=MANUAL_CHECK,
                reason="fixture mode skips live chain validation",
                spread_pct=None,
                open_interest=None,
                volume=None,
                expiry_used=None,
                data_source=None,
            )
        })
    result = runtime._run_pipeline(mode=runtime.MODE_FIXTURE, run_date=RUN_DATE, fixture_file=FIXTURE)
    payload = build_report_payload(result.contract, fixture_mode=True)
    rendered = render_report_from_payload(payload)
    return result, payload, rendered


def _output_outcome(rendered: str) -> str:
    """Map the rendered text back to the output-side outcome literal.

    render_report_from_payload renders "A+ TRADES" for TRADE and "NO TRADE" for
    NO_TRADE (regime is None in the payload adapter path).
    """
    if "A+ TRADES" in rendered:
        return runtime.OUTCOME_TRADE
    if "NO TRADE" in rendered:
        return runtime.OUTCOME_NO_TRADE
    raise AssertionError(f"could not classify rendered outcome:\n{rendered}")


# ---------------------------------------------------------------------------
# AC1 — runtime / output outcome agreement on the actionable set
# ---------------------------------------------------------------------------

def test_ac1_outcome_agreement_actionable_case(monkeypatch, tmp_path):
    # One actionable (tradable, ALLOW_TRADE, sized) SPY candidate.
    result, payload, rendered = _run(monkeypatch, tmp_path, "SPY", allow=True)
    assert result.outcome == runtime.OUTCOME_TRADE
    assert _output_outcome(rendered) == runtime.OUTCOME_TRADE
    # The two derivations agree, and top_trades is non-empty.
    assert result.outcome == _output_outcome(rendered)
    assert [t["symbol"] for t in payload["sections"]["top_trades"]] == ["SPY"]


def test_ac1_outcome_agreement_non_actionable_case(monkeypatch, tmp_path):
    # A NON_TRADABLE ^VIX allow: actionable on neither side → both NO_TRADE.
    assert "^VIX" in config.NON_TRADABLE_SYMBOLS
    result, payload, rendered = _run(monkeypatch, tmp_path, "^VIX", allow=True)
    assert result.outcome == runtime.OUTCOME_NO_TRADE
    assert _output_outcome(rendered) == runtime.OUTCOME_NO_TRADE
    assert result.outcome == _output_outcome(rendered)
    assert payload["sections"]["top_trades"] == []


# ---------------------------------------------------------------------------
# AC2 — D1: no non-tradable symbol in top_trades
# ---------------------------------------------------------------------------

def test_ac2_non_tradable_excluded_from_top_trades(monkeypatch, tmp_path):
    _, payload, _ = _run(monkeypatch, tmp_path, "^VIX", allow=True)
    symbols = [t["symbol"] for t in payload["sections"]["top_trades"]]
    assert all(s not in config.NON_TRADABLE_SYMBOLS for s in symbols)
    assert "^VIX" not in symbols
    # But ^VIX is retained on the contract surface (unchanged by this PRD).
    assert "^VIX" not in symbols
    contract_syms = [c["symbol"] for c in payload["sections"]["trade_decision_detail"]]
    assert "^VIX" in contract_syms


# ---------------------------------------------------------------------------
# AC3 — D2: blocked candidate suppressed from top_trades, retained on contract
# ---------------------------------------------------------------------------

def test_ac3_blocked_suppressed_but_retained(monkeypatch, tmp_path):
    result, payload, _ = _run(monkeypatch, tmp_path, "SPY", allow=False)
    # Suppressed from the actionable projection...
    assert payload["sections"]["top_trades"] == []
    for t in payload["sections"]["top_trades"]:
        assert t["decision_status"] != "BLOCK_TRADE"
    # ...but retained intact on contract.trade_candidates with sizing fields.
    candidate = result.contract["trade_candidates"][0]
    assert candidate["symbol"] == "SPY"
    assert candidate["decision_status"] == "BLOCK_TRADE"
    assert candidate["position_size"] == 2
    assert candidate["dollar_risk"] == 150.0


# ---------------------------------------------------------------------------
# AC4 — D3: no actionable candidate ⇒ empty top_trades + NO_TRADE
# ---------------------------------------------------------------------------

def test_ac4_no_actionable_yields_empty_top_trades(monkeypatch, tmp_path):
    result, payload, rendered = _run(monkeypatch, tmp_path, "SPY", allow=False)
    assert result.outcome == runtime.OUTCOME_NO_TRADE
    assert payload["sections"]["top_trades"] == []
    assert _output_outcome(rendered) == runtime.OUTCOME_NO_TRADE

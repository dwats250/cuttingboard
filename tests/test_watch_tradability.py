from cuttingboard.universe import is_tradable_symbol


def test_is_tradable_symbol_rules():
    assert is_tradable_symbol("^VIX") is False
    assert is_tradable_symbol("BTC-USD") is False
    assert is_tradable_symbol("SPY") is True

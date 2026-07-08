"""Тесты гейта деградации: чистая логика без БД."""
from forecast_service import monitoring as m


def test_gate_ok():
    acc = {"n_points": 100, "wmape": 0.3, "bias": 0.05, "coverage": 0.8}
    rep = m.gate(acc, [{"feature": "units", "psi": 0.03}])
    assert rep["ok"]
    assert rep["warnings"] == []


def test_gate_bias_and_coverage():
    acc = {"n_points": 100, "wmape": 0.3, "bias": 0.3, "coverage": 0.5}
    rep = m.gate(acc, None)
    assert not rep["ok"]
    assert any("смещение" in w for w in rep["warnings"])
    assert any("покрытие" in w for w in rep["warnings"])


def test_gate_wmape():
    acc = {"n_points": 100, "wmape": 0.9, "bias": 0.0, "coverage": 0.8}
    rep = m.gate(acc, None)
    assert not rep["ok"]
    assert any("WMAPE" in w for w in rep["warnings"])


def test_gate_drift():
    rep = m.gate(None, [{"feature": "sell_price", "psi": 0.4}])
    assert not rep["ok"]
    assert any("дрейф" in w for w in rep["warnings"])


def test_gate_no_data():
    rep = m.gate(None, None)
    assert rep["ok"]

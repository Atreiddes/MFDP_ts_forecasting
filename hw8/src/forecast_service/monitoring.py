"""Гейт деградации модели: сводит точность прогноз-факт, калибровку интервалов и дрейф
входа в набор предупреждений и флаг ok. Пробой гейта - сигнал к переобучению (см. dags).

Логика чистая (без чтения БД и файлов): на вход готовые точность и дрейф, на выход отчёт.
Пороги - демо-значения для FOODS M5, в рабочей системе подбираются по своей истории.
"""
from __future__ import annotations

WMAPE_GATE = 0.6       # WMAPE свежего прогноза хуже - точность просела
BIAS_GATE = 0.15       # модуль смещения больше - систематический пере- или недопрогноз
COVERAGE_FLOOR = 0.65  # доля факта в интервале P10-P90 ниже номинальных 0.8 с запасом - интервалы узкие
PSI_GATE = 0.25        # PSI признака выше - заметный дрейф входа


def gate(accuracy: dict | None, drift: list | None) -> dict:
    """Собирает сигналы деградации в предупреждения. accuracy - результат прогноз-факт
    (или None, если факта ещё нет), drift - список признаков с PSI (или None)."""
    warnings = []
    if accuracy:
        wmape = accuracy.get("wmape")
        bias = accuracy.get("bias")
        coverage = accuracy.get("coverage")
        if wmape is not None and wmape > WMAPE_GATE:
            warnings.append(f"WMAPE {wmape:.2f} хуже порога {WMAPE_GATE}")
        if bias is not None and abs(bias) > BIAS_GATE:
            warnings.append(f"смещение {bias:+.2f} по модулю больше порога {BIAS_GATE}")
        if coverage is not None and coverage < COVERAGE_FLOOR:
            warnings.append(f"покрытие интервала {coverage:.2f} ниже порога {COVERAGE_FLOOR}")
    if drift:
        wide = [f["feature"] for f in drift if f.get("psi") is not None and f["psi"] > PSI_GATE]
        if wide:
            warnings.append(f"дрейф признаков: {', '.join(wide)} (PSI выше {PSI_GATE})")
    return {"ok": not warnings, "warnings": warnings, "accuracy": accuracy, "drift": drift}

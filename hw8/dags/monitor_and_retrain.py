"""Airflow DAG: переобучение по деградации, а не только по расписанию.

Периодически спрашивает у сервиса гейт деградации (/api/monitoring). Если модель просела
по точности, смещению, калибровке интервалов или дрейфу - запускает DAG переобучения
(retrain_artifact), где новый артефакт ещё проходит порог качества перед выкаткой.

Это ops-компонент поверх сервиса, в рантайм сервиса не входит. Airflow ставится отдельно
в окружении оркестратора. Адрес сервиса задаётся переменной SERVICE_URL (по умолчанию
внутренний хост compose).
"""
from __future__ import annotations

import json
import os
import urllib.request

import pendulum
from airflow.decorators import dag
from airflow.operators.python import ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


def _is_degraded(**_) -> bool:
    """Опрашивает гейт сервиса. Возвращает True (продолжаем к переобучению) только при
    деградации: ShortCircuitOperator при False пропускает запуск переобучения."""
    url = os.getenv("SERVICE_URL", "http://api:8000").rstrip("/") + "/api/monitoring"
    report = json.load(urllib.request.urlopen(url, timeout=10))
    for w in report.get("warnings", []):
        print("!", w, flush=True)
    if report["ok"]:
        print("гейт чистый, переобучение не требуется", flush=True)
    return not report["ok"]


@dag(
    schedule="@daily",  # проверяем деградацию чаще, чем плановое недельное переобучение
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["forecast", "monitoring", "retrain"],
)
def monitor_and_retrain():
    gate = ShortCircuitOperator(task_id="gate_degradation", python_callable=_is_degraded)
    trigger = TriggerDagRunOperator(task_id="trigger_retrain", trigger_dag_id="retrain_artifact")
    gate >> trigger


monitor_and_retrain()

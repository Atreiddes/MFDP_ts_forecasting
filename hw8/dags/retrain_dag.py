"""Airflow DAG периодического переобучения артефакта модели.

Продакшн-обёртка над офлайн-пайплайном: приём новых недель -> проверка входных данных
(pandera) -> переобучение артефакта -> бэктест -> quality gate -> деплой. Если бэктест
просел выше порога, новый артефакт не выкатывается (алерт, остаётся прежний). Это ловит
случай, когда переобучение ухудшает качество.

Это ops-компонент, в рантайм сервиса не входит (сервис только применяет готовый артефакт).
Airflow и apache-airflow ставятся отдельно в окружении оркестратора, в зависимости сервиса
не входят. Запуск в окружении обучения (lightgbm + пайплайн hw5).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

HW8 = Path(__file__).resolve().parent.parent
WRMSSE_GATE = 0.75  # порог: если бэктест хуже, артефакт не деплоим


@dag(
    schedule="@weekly",  # данные недельные: приём раз в неделю, переобучение по расписанию
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["forecast", "retrain"],
)
def retrain_artifact():
    @task
    def validate_input() -> int:
        """Контракт входных данных: типы, границы, допустимые категории (pandera)."""
        import pandas as pd

        sys.path.insert(0, str(HW8 / "src"))
        from forecast_service.config import settings
        from forecast_service.ml.schemas import validate_sample, weekly_input_schema

        df = pd.read_parquet(settings.data_path)
        validate_sample(df, weekly_input_schema)  # падает при нарушении контракта
        return int(len(df))

    @task
    def rebuild() -> None:
        """Пересборка артефакта модели на свежих данных."""
        subprocess.run([sys.executable, "scripts/train_artifact.py"], cwd=HW8, check=True)

    @task
    def backtest() -> None:
        """Walk-forward бэктест: WRMSSE по 12 уровням -> metrics/cv_summary_foods.csv."""
        subprocess.run([sys.executable, "scripts/foods_metrics.py"], cwd=HW8, check=True)

    @task
    def quality_gate() -> float:
        """Не выкатываем артефакт, если бэктест хуже порога."""
        import pandas as pd

        sys.path.insert(0, str(HW8 / "src"))
        from forecast_service.config import settings

        wrmsse = float(pd.read_csv(settings.metrics_dir / "cv_summary_foods.csv")["value"].mean())
        if wrmsse > WRMSSE_GATE:
            raise AirflowFailException(
                f"WRMSSE {wrmsse:.4f} хуже порога {WRMSSE_GATE}: артефакт не деплоим, нужен разбор")
        return wrmsse

    @task
    def deploy(wrmsse: float) -> None:
        """Прошло gate: артефакт готов к выкатке. В проде здесь промоушен из staging и
        рестарт воркеров, чтобы подхватили новый артефакт."""
        print(f"артефакт прошёл gate (WRMSSE={wrmsse:.4f}), готов к деплою", flush=True)

    checked = validate_input()
    rebuilt = rebuild()
    tested = backtest()
    gate = quality_gate()
    checked >> rebuilt >> tested >> gate
    deploy(gate)


retrain_artifact()

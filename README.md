# MFDP: weekly demand forecast (M5)

Учебный проект MFDP 2026. Прогноз недельного спроса на открытых данных M5 Walmart как прокси
FMCG (PepsiCo). Из четырёх задач первоначального анализа в прототип и baseline вынесена одна,
прогноз спроса; остальные три в roadmap.

## Карта работ

| Этап | Что | Где |
|---|---|---|
| stage1 | Бизнес-анализ: 4 задачи на M5 (прогноз, эластичность, promo uplift, оптимизация цен) | [stage1/business_analysis.md](stage1/business_analysis.md) |
| stage2 | Прототип weekly demand forecast для demand planner-а, сужение scope, SaaS-дизайн | [stage2/prototype.md](stage2/prototype.md) |
| stage3 | Презентация и расчёты (Google Slides / Sheets) | [stage3/](stage3/) |
| stage4 | Датасет M5 + EDA для weekly demand forecast | [stage4/](stage4/) |
| stage5-6 | Baseline-решение: модели, метрики, сервис | [stage5/](stage5/) |

## Главный результат (stage5-6)

Недельный прогноз спроса item × store на 4 недели, 30490 рядов. Лучшая модель LightGBM ансамбль,
WRMSSE 0.748 (8 фолдов walk-forward), обходит простой MA-4 (0.802) на 6.8%. Лестница моделей от
наива до бустинга в [stage5/metriclog.md](stage5/metriclog.md), разбор метрик в
[stage5/evaluation.md](stage5/evaluation.md). Точка входа в решение: [stage5/README.md](stage5/README.md).

## Сужение scope

stage1 ставил четыре задачи на дневном горизонте. В stage2 для пилота с demand planner-ом оставлена
одна, прогноз спроса (недельный горизонт, понятный планировщику KPI). Эластичность, promo uplift
и оптимизация цен надстраиваются над прогнозом и вынесены в roadmap, для baseline они не нужны.

Dmitrii Gertsovskii.

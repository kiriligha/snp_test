# SNP Heuristic — распределение дефицита по неделям

Python 3.10+, только стандартная библиотека.

## Запуск

```bash
python3 run.py data
```

Код завершения: 0 — весь спрос покрыт, 1 — есть непокрытый спрос, 2 — данные некорректны, расчёт не выполнялся.

## Отказ и валидный расчёт

В исходных данных CASE_03 противоречив, поэтому расчёт по `data` завершается кодом 2 со списком ошибок:

```bash
python3 run.py data; echo $?                       # 2
```

Исходные CSV не изменяются. Вход для валидного расчёта строит скрипт: он копирует `data`, убирая строки CASE_03, значения не трогает.

```bash
python3 tools/make_demo.py data demo
python3 run.py demo; echo $?                       # 1
```

## Тесты

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

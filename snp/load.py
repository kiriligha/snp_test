import csv
import re
from pathlib import Path

from .planner import Case, Policy, Request


class DataError(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


def read(path, columns, errors):
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or set(columns) - set(reader.fieldnames):
                errors.append(f"{path.name}: ожидаются колонки {', '.join(columns)}")
                return []
            return [(f"{path.name}:{reader.line_num}", {k: (v or "").strip() for k, v in row.items()})
                    for row in reader]
    except OSError as e:
        errors.append(f"{path.name}: {e.strerror}")
        return []


def num(value, where, name, errors, lo=0, hi=None):
    if not re.fullmatch(r"-?[0-9]+", value):
        errors.append(f"{where}: {name}={value!r} — ожидается целое число")
        return None
    n = int(value)
    if n < lo or (hi is not None and n > hi):
        bound = f">= {lo}" if hi is None else f"от {lo} до {hi}"
        errors.append(f"{where}: {name}={n}, ожидается {bound}")
        return None
    return n


def load_policy(d, errors):
    params = {r["parameter"]: (w, r["value"]) for w, r in read(d / "policies.csv", ["parameter", "value"], errors)}
    values = {}
    for name, lo in [("assembly_multiple", 1), ("assembly_lead_weeks", 0), ("horizon", 1)]:
        if name in params:
            values[name] = num(params[name][1], params[name][0], name, errors, lo)
        else:
            errors.append(f"policies.csv: нет параметра {name}")
    bom = read(d / "bom.csv", ["component", "product", "qty_per_unit"], errors)
    if [(r["component"], r["product"]) for _, r in bom] != [("C", "P")]:
        errors.append("bom.csv: поддерживается только одна строка C,P")
        return None
    per_unit = num(bom[0][1]["qty_per_unit"], bom[0][0], "qty_per_unit", errors, 1)
    if errors:
        return None
    return Policy(values["assembly_multiple"], values["assembly_lead_weeks"], values["horizon"], per_unit)


def load(data_dir):
    d = Path(data_dir)
    if not d.is_dir():
        raise DataError([f"нет каталога {d}"])
    errors = []
    pol = load_policy(d, errors)
    if pol is None:
        raise DataError(errors)
    last = pol.horizon - 1

    stock = {}
    for w, r in read(d / "stock.csv", ["case_id", "product", "initial_qty"], errors):
        key = (r["case_id"], r["product"])
        if r["product"] not in ("P", "C"):
            errors.append(f"{w}: {r['case_id']}: неизвестный продукт {r['product']!r}")
        elif key in stock:
            errors.append(f"{w}: {r['case_id']}: запас {r['product']} задан повторно")
        else:
            stock[key] = num(r["initial_qty"], w, "initial_qty", errors)

    receipts = {}
    for w, r in read(d / "receipts.csv", ["case_id", "period", "product", "qty"], errors):
        w = f"{w}: {r['case_id']}"
        if r["product"] not in ("P", "C"):
            errors.append(f"{w}: неизвестный продукт {r['product']!r}")
            continue
        week = num(r["period"], w, "period", errors, 0, last)
        qty = num(r["qty"], w, "qty", errors)
        if week is not None and qty is not None:
            rec = receipts.setdefault(r["case_id"], {"P": [0] * pol.horizon, "C": [0] * pol.horizon})
            rec[r["product"]][week] += qty

    demand = {}
    columns = ["case_id", "period", "request_id", "priority", "qty", "min_lot"]
    for w, r in read(d / "demand.csv", columns, errors):
        w = f"{w}: {r['case_id']}/{r['request_id']}"
        week = num(r["period"], w, "period", errors, 0, last)
        prio = num(r["priority"], w, "priority", errors, 1)
        qty = num(r["qty"], w, "qty", errors)
        min_lot = num(r["min_lot"], w, "min_lot", errors, 0, qty)
        reqs = demand.setdefault(r["case_id"], {})
        if r["request_id"] in reqs:
            errors.append(f"{w}: request_id повторяется")
        elif None not in (week, prio, qty, min_lot):
            reqs[r["request_id"]] = Request(r["request_id"], week, prio, qty, min_lot)

    if errors:
        raise DataError(errors)
    cases = []
    for cid in sorted({c for c, _ in stock} | set(receipts) | set(demand)):
        rec = receipts.get(cid, {"P": [0] * pol.horizon, "C": [0] * pol.horizon})
        cases.append(Case(cid, stock.get((cid, "P"), 0), stock.get((cid, "C"), 0),
                          rec["P"], rec["C"], list(demand.get(cid, {}).values())))
    return pol, cases

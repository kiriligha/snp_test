from dataclasses import dataclass
from itertools import groupby


@dataclass(frozen=True)
class Policy:
    multiple: int
    lead: int
    horizon: int
    per_unit: int


@dataclass(frozen=True)
class Request:
    request_id: str
    period: int
    priority: int
    qty: int
    min_lot: int


@dataclass(frozen=True)
class Case:
    case_id: str
    stock_p: int
    stock_c: int
    receipts_p: list
    receipts_c: list
    requests: list


@dataclass(frozen=True)
class Plan:
    shipped: dict
    reasons: dict
    assembly: list
    stock_p: list
    stock_c: list


def capacity(case, pol):
    batch = pol.multiple * pol.per_unit
    built, c = [], case.stock_c
    for t in range(pol.horizon):
        c += case.receipts_c[t]
        built.append(c // batch * pol.multiple)
    cap, p = [], case.stock_p
    for t in range(pol.horizon):
        p += case.receipts_p[t]
        cap.append(p + (built[t - pol.lead] if t >= pol.lead else 0))
    return cap


def allocate(case, pol):
    cap = capacity(case, pol)
    slack = cap[:]
    shipped = {r.request_id: 0 for r in case.requests}
    reasons = {}

    def take(r, qty):
        for t in range(r.period, pol.horizon):
            slack[t] -= qty
        shipped[r.request_id] += qty

    order = sorted(case.requests, key=lambda r: (r.priority, r.period, r.request_id))
    for _, group in groupby(order, key=lambda r: r.priority):
        group = list(group)
        before = slack[:]
        failed = {}
        for r in group:
            if r.min_lot:
                avail = min(slack[r.period:])
                if avail >= r.min_lot:
                    take(r, r.min_lot)
                else:
                    failed[r.request_id] = avail
        for r in group:
            if r.request_id not in failed:
                take(r, min(r.qty - shipped[r.request_id], min(slack[r.period:])))
        for r in group:
            if shipped[r.request_id] < r.qty:
                reasons[r.request_id] = reason(r, shipped[r.request_id], cap, before,
                                               failed.get(r.request_id))
    return shipped, reasons


def reason(r, got, cap, before, failed_avail):
    alone = min(min(cap[r.period:]), r.qty)
    left = min(min(before[r.period:]), alone)
    parts = []
    if failed_avail is not None:
        parts.append(f"доступно {failed_avail} < min_lot {r.min_lot}")
        got = failed_avail
    if alone < r.qty:
        parts.append(f"к неделе {r.period} можно отгрузить не более {alone}")
    if left < alone:
        parts.append(f"{alone - left} занято более приоритетными заявками")
    if got < left:
        parts.append(f"{left - got} занято заявками того же приоритета")
    return "; ".join(parts)


def assemble(case, pol, out):
    need = [0] * pol.horizon
    p, total = case.stock_p, 0
    for t in range(pol.horizon):
        p += case.receipts_p[t]
        total += out[t]
        if total > p:
            assert t >= pol.lead
            batches = -(-(total - p) // pol.multiple)
            need[t - pol.lead] = max(need[t - pol.lead], batches * pol.multiple)
    assembly, done = [], 0
    for t in range(pol.horizon):
        assembly.append(max(done, need[t]) - done)
        done += assembly[-1]
    return assembly


def plan_case(case, pol):
    shipped, reasons = allocate(case, pol)
    out = [0] * pol.horizon
    for r in case.requests:
        out[r.period] += shipped[r.request_id]
    assembly = assemble(case, pol, out)
    stock_p, stock_c = [], []
    p, c = case.stock_p, case.stock_c
    for t in range(pol.horizon):
        p += case.receipts_p[t] - out[t] + (assembly[t - pol.lead] if t >= pol.lead else 0)
        c += case.receipts_c[t] - assembly[t] * pol.per_unit
        assert p >= 0 and c >= 0
        stock_p.append(p)
        stock_c.append(c)
    return Plan(shipped, reasons, assembly, stock_p, stock_c)

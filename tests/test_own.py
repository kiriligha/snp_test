import random
import time

from snp.planner import Case, Policy, Request, plan_case

POL = Policy(multiple=10, lead=1, horizon=8, per_unit=2)


def test_min_lot_reserved_before_lower_priority():
    """Сначала min_lot всех заявок приоритета, потом добор: B получает 70, младшая L — 0; при простом порядке по неделям L забрала бы запас B вопреки строгому приоритету."""
    reqs = [Request("A", 1, 1, 60, 0), Request("B", 2, 1, 70, 70), Request("L", 3, 2, 40, 0)]
    plan = plan_case(Case("T", 100, 0, [0] * 8, [0] * 8, reqs), POL)
    assert plan.shipped == {"A": 30, "B": 70, "L": 0}


def test_tie_resolved_by_request_id_regardless_of_row_order():
    """Ничья (одна неделя, один приоритет, дефицит) решается по request_id при любом порядке строк; иначе повторный запуск на переупорядоченной выгрузке даст другой план."""
    reqs = [Request("R-B", 3, 1, 30, 0), Request("R-A", 3, 1, 30, 0)]
    plans = [plan_case(Case("T", 30, 0, [0] * 8, [0] * 8, order), POL) for order in (reqs, reqs[::-1])]
    assert plans[0] == plans[1]
    assert plans[0].shipped == {"R-A": 30, "R-B": 0}


def test_52_weeks_10000_requests_in_seconds():
    """52 недели, 10 000 заявок и поступления каждую неделю считаются за секунды; ломается, если распределение станет квадратичным по числу заявок."""
    rng = random.Random(1)
    pol = Policy(multiple=10, lead=1, horizon=52, per_unit=2)
    reqs = [Request(f"R-{i}", rng.randrange(52), rng.randint(1, 5), rng.randint(10, 100),
                    rng.choice([0, 10])) for i in range(10_000)]
    case = Case("BIG", 1000, 2000, [rng.randint(0, 3000) for _ in range(52)],
                [rng.randint(0, 6000) for _ in range(52)], reqs)
    start = time.perf_counter()
    plan_case(case, pol)
    assert time.perf_counter() - start < 5

import argparse
import sys

from .load import DataError, load
from .planner import plan_case


def row(label, values):
    return f"  {label:<10}" + "".join(f"{v:>6}" for v in values)


def report(case, plan, pol):
    reqs = sorted(case.requests, key=lambda r: (r.period, r.priority, r.request_id))
    lines = [f"=== {case.case_id} ===", "Отгрузки (заявка: неделя, приоритет, отгружено / запрошено):"]
    lines += [f"  {r.request_id}: {r.period}, {r.priority}, {plan.shipped[r.request_id]} / {r.qty}"
              for r in reqs]
    lines += ["По неделям:", row("неделя", range(pol.horizon)), row("сборка", plan.assembly),
              row("запас P", plan.stock_p), row("запас C", plan.stock_c)]
    short = [r for r in reqs if r.request_id in plan.reasons]
    lines.append("Непокрытый спрос:" if short else "Непокрытый спрос: нет")
    lines += [f"  {r.request_id}: {r.qty - plan.shipped[r.request_id]} — {plan.reasons[r.request_id]}"
              for r in short]
    lines.append(f"Статус: заявок {len(reqs)}, покрыто {len(reqs) - len(short)}, непокрыто {len(short)}\n")
    return "\n".join(lines), len(short)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir")
    args = parser.parse_args(argv)
    try:
        pol, cases = load(args.data_dir)
    except DataError as e:
        for err in e.errors:
            print(f"ОШИБКА: {err}", file=sys.stderr)
        print("Расчёт не выполнялся.", file=sys.stderr)
        return 2
    uncovered = 0
    for case in cases:
        text, short = report(case, plan_case(case, pol), pol)
        print(text)
        uncovered += short
    return 1 if uncovered else 0


if __name__ == "__main__":
    sys.exit(main())

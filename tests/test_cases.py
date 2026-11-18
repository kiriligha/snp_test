from pathlib import Path

from snp.cli import main
from snp.load import load
from snp.planner import plan_case
from tools.make_demo import build

DATA = Path(__file__).parent.parent / "data"

EXPECTED = {
    "CASE_01": {"R-1": 30, "R-2": 40, "R-3": 40},
    "CASE_02": {"R-1": 50, "R-2": 60},
    "CASE_04": {"R-1": 60, "R-2": 120},
    "CASE_05": {"R-1": 30, "R-2": 70},
    "CASE_06": {"R-1": 60, "R-2": 0},
    "CASE_07": {"R-1": 99},
    "CASE_08": {"R-1": 40, "R-2": 30, "R-3": 100},
    "CASE_09": {"R-1": 20, "R-2": 20},
}


def test_original_data_rejected(capsys):
    """Исходный data/ отвергается с кодом 2 и четырьмя ошибками CASE_03; если валидацию ослабить, план посчитается на противоречивых данных."""
    assert main([str(DATA)]) == 2
    assert capsys.readouterr().err.count("CASE_03") == 4


def test_valid_cases_match_hand_calculation(tmp_path):
    """Кейсы без CASE_03 дают вручную посчитанные отгрузки и код 1; ломается при любом изменении правила распределения."""
    build(DATA, tmp_path)
    pol, cases = load(tmp_path)
    assert {c.case_id: plan_case(c, pol).shipped for c in cases} == EXPECTED
    assert main([str(tmp_path)]) == 1

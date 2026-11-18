import shutil
import sys
from pathlib import Path


def build(src, dst, exclude=("CASE_03",)):
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("bom.csv", "policies.csv"):
        shutil.copyfile(src / name, dst / name)
    for name in ("stock.csv", "receipts.csv", "demand.csv"):
        header, *rows = (src / name).read_text(encoding="utf-8").splitlines()
        kept = [r for r in rows if r.split(",")[0] not in exclude]
        (dst / name).write_text("\n".join([header, *kept]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])

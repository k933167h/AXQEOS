"""Operator-owned defect oracle; zero exit means the defect was REPRODUCED."""
import argparse
from pathlib import Path

def check(defect: str, fixture: Path) -> int:
    source = fixture.read_text(encoding="utf-8")
    if defect == "D001":
        return 0 if "return amount + discount" in source else 1
    if defect == "D002":
        return 0 if "return not is_admin" in source else 1
    raise ValueError("unknown seeded defect ID")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("defect", choices=["D001","D002"])
    p.add_argument("file")
    a = p.parse_args()
    return check(a.defect, Path(a.file))

if __name__ == "__main__":
    raise SystemExit(main())

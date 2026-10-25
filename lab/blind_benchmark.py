"""Blind review evaluation: reviewer input never contains hidden defect labels.

Run reviews and save predictions first. Scoring consumes a separately protected
answer key only after predictions have been frozen.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def public_manifest(cases: list[dict]) -> list[dict]:
    output = []
    for row in cases:
        if not isinstance(row, dict):
            raise ValueError("invalid case")
        allowed = {"case_id", "requirement_id", "diff_ref", "repository_snapshot"}
        if not all(isinstance(row.get(key), str) and row.get(key) for key in allowed):
            raise ValueError("case missing public fields")
        output.append({key: row[key] for key in sorted(allowed)})
    ids = [r["case_id"] for r in output]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate case")
    return output

def _index(rows):
    ids = [r["case_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate IDs")
    return {r["case_id"]: r for r in rows}

def grade(predictions: list[dict], hidden_truth: list[dict]) -> dict:
    """Match by independent defect ID supplied during human adjudication.

    Never use this function inside the reviewer process.
    """
    predicted = _index(predictions)
    truth = _index(hidden_truth)
    if set(predicted) != set(truth):
        raise ValueError("prediction and truth case sets differ")
    tp = fp = fn = 0
    per_case = []
    for case_id in sorted(truth):
        expected = set(truth[case_id]["defect_ids"])
        detected = set(predicted[case_id]["adjudicated_detected_ids"])
        if not truth[case_id].get("adjudicated", False):
            raise ValueError("ground truth not independently adjudicated")
        if not all(isinstance(x, str) and x for x in expected | detected):
            raise ValueError("invalid defect ID")
        hit = len(expected & detected)
        miss = len(expected - detected)
        false = len(detected - expected)
        tp += hit; fp += false; fn += miss
        per_case.append({"case_id": case_id, "tp": hit, "fp": false, "fn": miss})
    return {
        "cases": len(truth), "tp": tp, "fp": fp, "fn": fn,
        "recall": tp/(tp+fn) if tp+fn else None,
        "precision": tp/(tp+fp) if tp+fp else None,
        "case_counts": per_case,
        "disclaimer": "Post-adjudication offline scoring, not automatic proof of reviewer correctness",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("manifest", "grade"))
    p.add_argument("--cases")
    p.add_argument("--predictions")
    p.add_argument("--truth")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    def load(path):
        if not path: p.error("missing input file")
        return json.loads(Path(path).read_text(encoding="utf-8"))
    if args.mode == "manifest":
        result = public_manifest(load(args.cases))
    else:
        if Path(args.predictions).resolve() == Path(args.truth).resolve():
            p.error("predictions and truth must be separate files")
        result = grade(load(args.predictions), load(args.truth))
    target = Path(args.output)
    if args.truth and target.resolve() == Path(args.truth).resolve():
        p.error("refusing to overwrite truth")
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), "mode": args.mode}))
if __name__ == "__main__":
    main()

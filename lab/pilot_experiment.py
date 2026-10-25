"""Adjudicated experiment analysis; no synthetic observations are counted as results."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

REQUIRED = {"case_id", "arm", "ground_truth_ids", "detected_ids", "human_minutes",
            "agent_cost_usd", "reviewer", "adjudicated"}

def report(rows):
    groups = defaultdict(list)
    seen = set()
    for r in rows:
        missing = REQUIRED - set(r)
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        if not r["adjudicated"]:
            raise ValueError("unadjudicated case: " + str(r["case_id"]))
        if r["arm"] not in ("baseline", "pilot"):
            raise ValueError("arm must be baseline or pilot")
        key = (r["case_id"], r["arm"])
        if key in seen:
            raise ValueError("duplicate case/arm")
        seen.add(key)
        if float(r["human_minutes"]) < 0 or float(r["agent_cost_usd"]) < 0:
            raise ValueError("negative duration or cost")
        if not isinstance(r["ground_truth_ids"], list) or not isinstance(r["detected_ids"], list):
            raise ValueError("defect id fields must be arrays")
        groups[r["arm"]].append(r)
    if set(groups) != {"baseline", "pilot"}:
        raise ValueError("both arms required")
    a = {r["case_id"] for r in groups["baseline"]}
    b = {r["case_id"] for r in groups["pilot"]}
    if a != b:
        raise ValueError("cases must be paired across arms")
    for case_id in a:
        x = next(r for r in groups["baseline"] if r["case_id"] == case_id)
        y = next(r for r in groups["pilot"] if r["case_id"] == case_id)
        if set(x["ground_truth_ids"]) != set(y["ground_truth_ids"]):
            raise ValueError("truth differs between paired arms: " + case_id)
    totals = {}
    for arm, records in groups.items():
        tp = fp = fn = 0
        minutes = cost = 0.
        for row in records:
            truth, detected = set(row["ground_truth_ids"]), set(row["detected_ids"])
            tp += len(truth & detected)
            fp += len(detected - truth)
            fn += len(truth - detected)
            minutes += float(row["human_minutes"])
            cost += float(row["agent_cost_usd"])
        totals[arm] = {
            "cases": len(records), "true_positives": tp, "false_positives": fp,
            "false_negatives": fn,
            "recall": tp/(tp+fn) if tp+fn else None,
            "precision": tp/(tp+fp) if tp+fp else None,
            "mean_human_minutes": minutes/len(records),
            "total_agent_cost_usd": round(cost, 4)
        }
    base, pilot = totals["baseline"], totals["pilot"]
    totals["comparison"] = {
        "recall_delta": (pilot["recall"] - base["recall"]
                         if base["recall"] is not None and pilot["recall"] is not None else None),
        "human_minutes_reduction": (1 - pilot["mean_human_minutes"]/base["mean_human_minutes"]
                                    if base["mean_human_minutes"] > 0 else None),
        "pilot_minus_baseline_false_positives": pilot["false_positives"] - base["false_positives"],
        "paired_cases": len(a),
        "decision": "insufficient_data" if len(a) < 20 else "requires_sme_and_statistical_review",
        "note": "Descriptive statistics only; no causal inference or automatic promotion."
    }
    return totals

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = report(json.loads(Path(args.input).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["comparison"], indent=2))

if __name__ == "__main__":
    main()

"""Append-only, local pilot evidence registry and conservative promotion decision."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from .pilot_experiment import report

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def record(registry: Path, event: dict) -> dict:
    if not isinstance(event, dict) or not event.get("case_id") or not event.get("kind"):
        raise ValueError("case_id and kind required")
    registry.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    if registry.is_file():
        for line in registry.read_text(encoding="utf-8").splitlines():
            if line:
                prior = json.loads(line)
                if prior["previous_sha256"] != previous:
                    raise ValueError("broken evidence chain")
                payload = {k: v for k, v in prior.items() if k != "sha256"}
                expected = hashlib.sha256(canonical(payload).encode()).hexdigest()
                if expected != prior["sha256"]:
                    raise ValueError("modified historical evidence")
                previous = expected
    entry = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "previous_sha256": previous, "event": event}
    entry["sha256"] = hashlib.sha256(canonical(entry).encode()).hexdigest()
    # Single-writer prototype only; external durable storage must lock writes.
    with registry.open("a", encoding="utf-8") as f:
        f.write(canonical(entry) + "\n")
    return entry

def decision(measurements: list[dict], controls: dict) -> dict:
    result = report(measurements)
    c = result["comparison"]
    reasons = []
    if c["paired_cases"] < 20:
        reasons.append("insufficient_paired_cases")
    if c["recall_delta"] is None or c["recall_delta"] < 0:
        reasons.append("recall_not_improved_or_unknown")
    if c["human_minutes_reduction"] is None or c["human_minutes_reduction"] <= 0:
        reasons.append("human_time_not_reduced")
    if c["pilot_minus_baseline_false_positives"] > 0:
        reasons.append("false_positive_burden_increased")
    for key in ("ci_passed", "sandbox_verified", "live_adapters_verified",
                "statistical_review_approved", "sme_approved"):
        if controls.get(key) is not True:
            reasons.append("missing_" + key)
    return {"decision": "eligible_for_manual_promotion" if not reasons else "hold",
            "reasons": reasons, "measurements": result,
            "automatically_promoted": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("record", "decision"))
    p.add_argument("--input", required=True)
    p.add_argument("--registry")
    p.add_argument("--controls")
    p.add_argument("--output")
    args = p.parse_args()
    rows = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if args.mode == "record":
        if not args.registry:
            p.error("--registry required")
        result = record(Path(args.registry), rows)
    else:
        if not args.controls or not args.output:
            p.error("--controls and --output required")
        controls = json.loads(Path(args.controls).read_text(encoding="utf-8"))
        result = decision(rows, controls)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"decision": result.get("decision"), "sha256": result.get("sha256")}))
if __name__ == "__main__":
    main()

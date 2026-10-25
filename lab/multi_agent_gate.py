"""Pilot-only, fail-closed multi-agent review + evidence + quality gate.

Reviewer adapters are external processes. They receive an immutable input JSON
and must write findings JSON. Nothing in this module calls an LLM implicitly.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from datetime import datetime, timezone


ROLES = ("correctness", "security", "architecture")
SEVERITIES = ("critical", "high", "medium", "low")


def _execute(argv: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    if not argv or any(not isinstance(x, str) for x in argv):
        raise ValueError("command must be an argv array")
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, shell=False, check=False)
        return p.returncode, (p.stdout + "\n" + p.stderr)[-2000:]
    except (OSError, subprocess.TimeoutExpired) as e:
        return 125, str(e)


def _within_repo(repo: Path, filename: str) -> Path:
    path = (repo / filename).resolve()
    if not path.is_relative_to(repo.resolve()) or not path.is_file():
        raise ValueError("evidence file unavailable or outside repository")
    return path


def _review(role: str, argv: list[str], context: dict, repo: Path, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="axqe-review-") as directory:
        root = Path(directory)
        request, result = root / "request.json", root / "findings.json"
        request.write_text(json.dumps({"role": role, **context}, ensure_ascii=False))
        command = [part.replace("{input}", str(request)).replace("{output}", str(result))
                   for part in argv]
        start = time.monotonic()
        code, log = _execute(command, repo, timeout)
        elapsed = round(time.monotonic() - start, 3)
        if code != 0 or not result.is_file():
            return {"role": role, "status": "error", "error": log, "duration_s": elapsed,
                    "findings": []}
        try:
            payload = json.loads(result.read_text())
            findings = payload["findings"]
            if not isinstance(findings, list):
                raise ValueError("findings must be an array")
        except (ValueError, KeyError, TypeError) as e:
            return {"role": role, "status": "error", "error": str(e),
                    "duration_s": elapsed, "findings": []}
        return {"role": role, "status": "ok", "duration_s": elapsed, "findings": findings}


def _verify(finding: dict, repo: Path, timeout: int, trusted: dict) -> dict:
    output = {k: v for k, v in finding.items() if k != "reproducer"}
    output["verified"] = False
    try:
        if finding["severity"] not in SEVERITIES:
            raise ValueError("invalid severity")
        location = finding["file"]
        line = finding["line"]
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise ValueError("invalid source line")
        path = _within_repo(repo, location)
        lines = path.read_text(encoding="utf-8").splitlines()
        if line > len(lines):
            raise ValueError("source line missing")
        repro_id = finding.get("reproducer_id")
        command = trusted.get(repro_id) if isinstance(repro_id, str) else None
        if not isinstance(command, list) or not command:
            raise ValueError("no trusted reproducer ID: requires manual adjudication")
        code, log = _execute(command, repo, timeout)
        output["verification_exit_code"] = code
        output["verification_log"] = log
        output["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if code != 0:
            raise ValueError("reproducer did not confirm the finding")
        output["verified"] = True
        output["reason"] = "reproducer_passed"
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as e:
        output["reason"] = str(e)
    return output


def run(config: dict, repo: Path) -> dict:
    """Run independent adapters, independently verify findings, and fail closed."""
    repo = repo.resolve()
    if not repo.is_dir():
        raise ValueError("invalid repository")
    context = config.get("context", {})
    adapters = config.get("reviewers", {})
    timeout = int(config.get("timeout_seconds", 120))
    if not 1 <= timeout <= 600:
        raise ValueError("timeout_seconds out of range")
    if not isinstance(adapters, dict) or set(adapters) != set(ROLES):
        raise ValueError("exactly correctness/security/architecture reviewers required")
    if not isinstance(context, dict) or not context.get("requirement_id") or not context.get("diff_ref"):
        raise ValueError("requirement_id and diff_ref required")
    trusted = config.get("trusted_reproducers", {})
    if not isinstance(trusted, dict):
        raise ValueError("invalid trusted_reproducers")
    start = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ROLES)) as pool:
        futures = {role: pool.submit(_review, role, adapters[role], context, repo, timeout)
                   for role in ROLES}
        reviews = [futures[role].result() for role in ROLES]
    findings = []
    malformed_findings = 0
    dedup = set()
    for review in reviews:
        for entry in review["findings"]:
            if not isinstance(entry, dict):
                malformed_findings += 1
                continue
            tagged = dict(entry, reviewer_role=review["role"])
            signature = (tagged.get("file"), tagged.get("line"), tagged.get("title"))
            if signature in dedup:
                continue
            dedup.add(signature)
            findings.append(_verify(tagged, repo, timeout, trusted))
    reviews_ok = all(r["status"] == "ok" for r in reviews)
    blocking = [f for f in findings if f.get("severity") in ("critical", "high")]
    # The gate does not equate 'not reproduced' with 'not a real defect'.
    evidence_ok = bool(config.get("required_tests")) and True
    test_results = []
    for argv in config.get("required_tests", []):
        code, log = _execute(argv, repo, timeout)
        test_results.append({"argv": argv, "exit_code": code, "log": log})
        evidence_ok = evidence_ok and code == 0
    unresolved = [f for f in findings if not f["verified"]]
    gate = "pass" if reviews_ok and evidence_ok and not blocking and not unresolved and malformed_findings == 0 else "hold"
    return {
        "schema_version": "pilot-1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "requirement_id": context["requirement_id"],
        "diff_ref": context["diff_ref"],
        "reviews": reviews,
        "findings": findings,
        "required_test_results": test_results,
        "gate": gate,
        "reasons": {
            "reviewers_ok": reviews_ok,
            "tests_ok": evidence_ok,
            "blocking_findings": len(blocking),
            "unverified_findings": len(unresolved),
            "malformed_findings": malformed_findings,
        },
        "wall_clock_seconds": round(time.monotonic() - start, 3),
        "human_approval": "pending",
    }


def metrics(records: list[dict]) -> dict:
    """Use adjudicated truth, NOT agent agreement, for detection-rate measurement."""
    by_arm = {}
    for row in records:
        arm = row["arm"]
        d = by_arm.setdefault(arm, {"truth_positive": 0, "detected_true_positive": 0,
                                   "human_review_minutes": 0.0, "cases": 0})
        truth, found = set(row["adjudicated_defect_ids"]), set(row["detected_defect_ids"])
        if not found <= truth and not row.get("allow_false_positives", False):
            # Explicitly require false-positive reporting to avoid silent inflation.
            raise ValueError("detected ids outside adjudicated set; add allow_false_positives")
        d["truth_positive"] += len(truth)
        d["detected_true_positive"] += len(found & truth)
        d["human_review_minutes"] += float(row["human_review_minutes"])
        d["cases"] += 1
    for d in by_arm.values():
        d["defect_detection_rate"] = (d["detected_true_positive"] / d["truth_positive"]
                                      if d["truth_positive"] else None)
        d["mean_human_review_minutes"] = d["human_review_minutes"] / d["cases"]
    if "baseline" in by_arm and "pilot" in by_arm:
        a, b = by_arm["baseline"], by_arm["pilot"]
        by_arm["comparison"] = {
            "human_review_reduction_ratio": (1 - b["mean_human_review_minutes"] /
                                              a["mean_human_review_minutes"]
                                              if a["mean_human_review_minutes"] > 0 else None),
            "detection_rate_delta": (b["defect_detection_rate"] - a["defect_detection_rate"]
                                     if a["defect_detection_rate"] is not None and
                                     b["defect_detection_rate"] is not None else None),
        }
    return by_arm


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "metrics"))
    parser.add_argument("--config", required=True, help="JSON config or pilot measurement rows")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.config).read_text(encoding="utf-8"))
    result = run(data, Path(args.repo)) if args.mode == "run" else metrics(data)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": args.output, "gate": result.get("gate")}, ensure_ascii=False))
    return 2 if result.get("gate") == "hold" else 0


if __name__ == "__main__":
    raise SystemExit(main())

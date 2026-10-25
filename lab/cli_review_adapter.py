"""Operator-invoked CLI reviewer adapter (Claude / Codex / Gemini).

Usage: python -m lab.cli_review_adapter PROVIDER INPUT_JSON OUTPUT_JSON
No model command is accepted from model output. Run only in a trusted
ephemeral read-only sandbox without production secrets.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path

ROLES = {"correctness", "security", "architecture"}
PROVIDERS = {"claude", "codex", "gemini"}

def prompt_for(request: dict) -> str:
    role = request.get("role")
    if role not in ROLES:
        raise ValueError("unsupported review role")
    requirement = request.get("requirement_id", "")
    diff_ref = request.get("diff_ref", "")
    if not requirement or not diff_ref:
        raise ValueError("missing requirement/diff reference")
    return (
        "Act as an independent, read-only " + role + " code reviewer. "
        "Read the repository and the exact commit/diff; do not modify files. "
        "Never execute generated programs or secrets. Identify defects, not stylistic preferences. "
        "Return ONLY a JSON object with findings array. Each item must have "
        "title, file (repository-relative), line (positive integer), severity "
        "(critical/high/medium/low), and explanation. "
        "Optionally provide a reproducer_id ONLY if the operator has pre-registered that ID; "
        "never provide a shell command. Do not infer that a test was executed. "
        "If no findings, return {\"findings\":[]}. "
        "Requirement: " + json.dumps(str(requirement)) + ". "
        "Diff reference: " + json.dumps(str(diff_ref)) + "."
    )

def invoke(provider: str, prompt: str, cwd: Path, timeout: int) -> str:
    if provider == "claude":
        args = ["claude", "-p", "--permission-mode", "plan",
                "--max-turns", "8", prompt]
    elif provider == "codex":
        args = ["codex", "exec", "--sandbox", "read-only",
                "--ephemeral", prompt]
    elif provider == "gemini":
        # Gemini CLI sandbox policy must also be enforced by the outer OS/container.
        args = ["gemini", "-p", prompt, "--output-format", "json"]
    else:
        raise ValueError("unknown provider")
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False, shell=False)
    if result.returncode:
        raise RuntimeError("provider failed with exit " + str(result.returncode))
    if len(result.stdout) > 250_000:
        raise ValueError("oversized model response")
    if provider == "gemini":
        payload = json.loads(result.stdout)
        return payload["response"]
    return result.stdout

def parse_findings(response: str) -> dict:
    # Strict JSON only: do not scrape arbitrary text or accept markdown fences.
    output = json.loads(response.strip())
    findings = output["findings"]
    if not isinstance(findings, list) or len(findings) > 100:
        raise ValueError("invalid findings")
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("invalid finding")
        if finding.get("severity") not in {"critical", "high", "medium", "low"}:
            raise ValueError("invalid severity")
        if not isinstance(finding.get("file"), str) or not finding["file"]:
            raise ValueError("invalid file")
        if type(finding.get("line")) is not int or finding["line"] < 1:
            raise ValueError("invalid line")
        if not isinstance(finding.get("title"), str) or not finding["title"]:
            raise ValueError("invalid title")
        # The downstream verifier never executes LLM-proposed shell commands.
        finding.pop("reproducer", None)
        finding.pop("command", None)
    return {"findings": findings}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=sorted(PROVIDERS))
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 600:
        parser.error("timeout out of range")
    request = json.loads(Path(args.input).read_text(encoding="utf-8"))
    prompt = prompt_for(request)
    result = parse_findings(invoke(args.provider, prompt, Path.cwd(), args.timeout))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

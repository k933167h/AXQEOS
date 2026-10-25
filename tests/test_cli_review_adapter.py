import json
import pytest
from lab.cli_review_adapter import prompt_for, parse_findings, invoke


def test_all_roles_prompt():
    for role in ("correctness", "security", "architecture"):
        assert role in prompt_for({"role": role, "requirement_id": "R1", "diff_ref": "sha1"})


def test_strict_response_validation():
    result = parse_findings(json.dumps({"findings": [
        {"title": "example", "file": "a.py", "line": 1, "severity": "high",
         "reproducer": ["sh", "-c", "echo unsafe"]}
    ]}))
    assert "reproducer" not in result["findings"][0]


@pytest.mark.parametrize("bad", [
    "not json",
    '{"findings":{}}',
    '{"findings":[{"title":"x","file":"a","line":0,"severity":"high"}]}',
])
def test_invalid_finding_fails_closed(bad):
    with pytest.raises((ValueError, KeyError, json.JSONDecodeError)):
        parse_findings(bad)


def test_provider_argv_no_shell(monkeypatch, tmp_path):
    seen = []
    class Result:
        returncode = 0
        stdout = '{"findings":[]}'
    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        return Result()
    monkeypatch.setattr("lab.cli_review_adapter.subprocess.run", fake_run)
    for provider in ("claude", "codex"):
        assert invoke(provider, "review", tmp_path, 40) == '{"findings":[]}'
    assert seen[0][0][0] == "claude"
    assert "--permission-mode" in seen[0][0]
    assert seen[1][0][:2] == ["codex", "exec"]
    assert "read-only" in seen[1][0]
    assert all(x[1]["shell"] is False for x in seen)

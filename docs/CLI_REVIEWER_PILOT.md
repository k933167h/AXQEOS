# CLI reviewers — optional pilot

Review agents are wired by a subprocess protocol. The operator must install and authenticate the appropriate CLI and approve transmission of repository contents. The adapter **does not** provision models, credentials, sandbox images, or external services.

Example role mapping in an operator-created configuration (not recommended for untrusted PRs):
- correctness: ["python", "-m", "lab.cli_review_adapter", "claude", "{input}", "{output}"]
- security: ["python", "-m", "lab.cli_review_adapter", "codex", "{input}", "{output}"]
- architecture: ["python", "-m", "lab.cli_review_adapter", "gemini", "{input}", "{output}"]

Requirements:
1. Run in a disposable read-only container with no production secrets, restricted egress, resource limits and an explicit repository snapshot/commit.
2. The outer sandbox is mandatory: a CLI tool's own plan/read-only configuration is defense-in-depth, NOT an OS-level guarantee.
3. Only harness-owned trusted_reproducers IDs may be executed. AI-proposed command lines are discarded.
4. Manually adjudicate unresolved findings. No automated deployment authorization.
5. Validate CLI version compatibility and actual JSON output in a real integration trial before relying on this adapter. CLI syntax and provider output can change. A parsing or subprocess failure must result in HOLD.
6. The included adapter is a protocol implementation; it has not been verified against live vendor CLIs. Existing CI uses deterministic adapters only.

Progression: first prove independent CLI results and reproduce seeded findings, then collect adjudicated pilot measurements. Only then evaluate expansion to parallel root-cause exploration, Harness² and LLMWiki Gherkin.

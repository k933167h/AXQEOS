# v4.9 Orchestrator integration
The deterministic `/api/v1/e2e/runs` endpoint now delegates its tier selection to `app.orchestrator.route_assertion`, using config/routing.yaml. The explicit assertion-failure and missing-assertion precedence is preserved; complexity may escalate evaluation but never auto-accept uncertain evidence.
New optional request fields: `complexity` and `budget` in [0,1]. Defaults preserve the public request schema. `budget` is a normalized input, **not a billed-dollar enforcement mechanism**. No JEV/LLM model calls are made by this deterministic endpoint; `/api/v1/reporter` remains the separate async Judge execution path.
Tests cover critical risk, deterministic failure, missing confidence, complexity escalation and conservative acceptance.
Status: isolated algorithm wired into deterministic route only; full Orchestrator budget economics, vendor API and trace instrumentation pending.

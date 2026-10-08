# AX QE OS v4.9 Architecture Overview
Golden Dataset/Evaluation Data -> Evaluation Orchestrator (Risk x Confidence x Complexity x Cost) -> T0 Deterministic -> T1 Economical/JEV -> T2 Strong LLM -> T3 Human/SME -> Calibration/Regression/Continuous QM.
Agentic E2E Execution Plane (TesterArmy e2e): Reporter -> API -> SQLite -> Judge -> Outbox -> Plane/Kiwi/Langfuse.
Observability target: OTel Collector -> metrics/traces -> Grafana. Metrics endpoint exists; trace instrumentation remains pending.
Domains: Traditional SW -> Data -> LLM -> RAG -> Agent -> Security.
Golden candidate != Golden. Promotion requires recorded SME approval.
Deployment gates: real browser execution, Judge calibration, API integration, trace correlation, end-to-end CI and audit evidence. Not production ready.

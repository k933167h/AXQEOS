# AX QE OS v4.9 — Open-source gap / custom algorithm register
Source of truth: existing AX QE OS v4.9 Adaptive Evaluation Cascade; Golden promotion always requires SME approval.

| Gap | Existing OSS capability | AXQEOS algorithm | Validation |
|---|---|---|---|
| Cross-system execution dedup | Individual vendor run IDs | canonical_fingerprint SHA-256 of normalized evidence | deterministic unit test |
| Risk-aware routing | LLM scoring and SDK confidence | choose_tier(risk,confidence,complexity,budget) with critical-risk fail-closed | boundary tests |
| Transient upstream failures | SDK HTTP retry (vendor-specific) | retry_delay bounded exponential jitter | deterministic unit test |
| Evidence credential leakage | Vendor-side access control | redact_evidence best-effort filter | unit test; DLP still needed |
| Kiwi result association | JSON-RPC TestExecution.create/update/add_property | cross-system link graph to be implemented | NOT VERIFIED |
| Langfuse trace ingestion | native OTLP/HTTP (v4) | shared run/trace correlation and policy routing | NOT VERIFIED |
| TesterArmy execution | depends on installed browser runner | normalize actual runner events, attach evidence | NOT VERIFIED |
| OTel tracing | SDK + FastAPI/httpx instrumentation | ax.* attributes, causal correlation, evidence links | NOT VERIFIED |

Algorithms in app/integration_algorithms.py are isolated primitives; they are **not wired into production routing or worker** yet. This avoids claiming coverage of live execution. Wiring requires regression tests against existing route policies.

## Standards / API decisions
Kiwi TCMS: prefer official tcms-api client or documented JSON-RPC at /json-rpc/. Do not assume a generic REST endpoint.
Langfuse: prefer OTLP/HTTP for trace ingestion; do not implement new code against deprecated legacy trace ingestion.
OpenTelemetry: use official SDK and FastAPI/httpx instrumentation, not a custom tracing protocol.

# Trace correlation v4.9 (Phase 1)
The Reporter API accepts W3C traceparent and returns trace_id. Worker and Judge outgoing HTTP calls forward child traceparent values; this enables cross-service correlation without exposing secrets.
This implementation is trace-context propagation **only**, not OpenTelemetry SDK instrumentation, span export, or verified collector ingestion. Real OTLP spans and end-to-end sampling will be delivered in a later phase.
Reject malformed or all-zero trace identifiers by generating fresh context; do not trust incoming baggage or arbitrary trace metadata.

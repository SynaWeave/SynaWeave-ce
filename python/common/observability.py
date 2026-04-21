"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  wire the bounded OpenTelemetry trace path for the Sprint 1 API and ingest runtimes

- Later Extension Points:
    --> widen telemetry setup only when more runtimes or signal types
        become part of the governed proof path

- Role:
    --> initializes OTLP trace export when the local collector path is enabled
    --> exposes tiny propagation helpers so API and ingest share one trace continuity contract

- Exports:
    --> `current_trace_id()`
    --> `extract_trace_context()`
    --> `init_tracing()`
    --> `inject_current_trace_headers()`
    --> `flush_tracing()`

- Consumed By:
    --> API middleware ingest execution and local observability evidence scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import atexit
import os
from typing import Mapping

from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_TRACING_READY = False


# ---------- env helpers ----------
# Keep env parsing tiny so runtime setup stays predictable in tests and compose runs.
def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def tracing_enabled() -> bool:
    return _env_flag("SYNAWAVE_OTEL_ENABLED")


def _traces_endpoint() -> str:
    explicit = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
    if explicit:
        return explicit
    base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318").rstrip("/")
    return f"{base}/v1/traces"


def _batch_delay_millis() -> int:
    raw_value = os.getenv("SYNAWAVE_OTEL_BATCH_DELAY_MS", "250").strip()
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 250


# ---------- provider bootstrap ----------
# Keep one provider per process because API and ingest run as separate runtime processes.
def init_tracing(service_name: str):
    global _TRACING_READY
    if _TRACING_READY or not tracing_enabled():
        return trace.get_tracer(service_name)
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": os.getenv("SYNAWAVE_RUNTIME_ENV", "local"),
            }
        )
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=_traces_endpoint()),
            schedule_delay_millis=_batch_delay_millis(),
        )
    )
    trace.set_tracer_provider(provider)
    atexit.register(provider.shutdown)
    _TRACING_READY = True
    return trace.get_tracer(service_name)


# ---------- propagation helpers ----------
# Keep incoming and outgoing carrier handling in one shared module across runtimes.
def extract_trace_context(headers: Mapping[str, str] | None = None):
    return propagate.extract(headers or {})


def inject_current_trace_headers() -> dict[str, str]:
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier


def flush_tracing() -> None:
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if callable(force_flush):
        force_flush()


# ---------- trace identity helper ----------
# Keep trace id formatting W3C-compatible so responses scripts and docs compare the same value.
def current_trace_id() -> str:
    span_context = trace.get_current_span().get_span_context()
    if span_context.is_valid:
        return f"{span_context.trace_id:032x}"
    return "0" * 32

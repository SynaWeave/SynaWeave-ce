"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  wire the bounded OpenTelemetry trace path for the Sprint 1 API and ingest runtimes

- Later Extension Points:
    --> widen telemetry setup only when more runtimes or signal types
        become part of the governed proof path

- Role:
    --> initializes OTLP trace export when the local collector path
        is enabled and the SDK is present
    --> degrades to no-op tracing with explicit runtime compatibility
        when only the API package is installed
    --> exposes tiny propagation helpers so API and ingest share one trace continuity contract

- Exports:
    --> `current_trace_id()`
    --> `extract_trace_context()`
    --> `init_tracing()`
    --> `inject_current_trace_headers()`
    --> `flush_tracing()`
    --> `tracing_runtime_mode()`

- Consumed By:
    --> API middleware ingest execution and local observability evidence scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import atexit
import os
from typing import Mapping

from opentelemetry import propagate, trace

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ModuleNotFoundError:
    OTLPSpanExporter = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None

_tracing_ready = False
_tracing_mode = "noop"


# ---------- env helpers ----------
# Keep env parsing tiny so runtime setup stays predictable in tests and compose runs.
def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def tracing_enabled() -> bool:
    return _env_flag("TRACE_ON") or _env_flag("SYNAWAVE_OTEL_ENABLED")


def tracing_runtime_mode() -> str:
    return _tracing_mode


def _traces_endpoint() -> str:
    explicit = os.getenv("TRACE_OTLP_TRACES_URL", "").strip() or os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", ""
    ).strip()
    if explicit:
        return explicit
    base = (
        os.getenv("TRACE_OTLP_URL", "").strip()
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318")
    ).rstrip("/")
    return f"{base}/v1/traces"


def _batch_delay_millis() -> int:
    raw_value = os.getenv("TRACE_BATCH_MS", "").strip() or os.getenv(
        "SYNAWAVE_OTEL_BATCH_DELAY_MS", "250"
    ).strip()
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 250


def _sdk_available() -> bool:
    return all(
        dependency is not None
        for dependency in (
            OTLPSpanExporter,
            Resource,
            TracerProvider,
            BatchSpanProcessor,
        )
    )


# ---------- provider bootstrap ----------
# Keep one provider per process because API and ingest run as separate runtime processes.
def init_tracing(service_name: str):
    global _tracing_ready, _tracing_mode

    if _tracing_ready:
        return trace.get_tracer(service_name)

    if not tracing_enabled():
        _tracing_mode = "disabled"
        return trace.get_tracer(service_name)

    if not _sdk_available():
        _tracing_mode = "api-only-fallback"
        return trace.get_tracer(service_name)

    assert TracerProvider is not None
    assert Resource is not None
    assert BatchSpanProcessor is not None
    assert OTLPSpanExporter is not None

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": os.getenv("SW_ENV", "")
                or os.getenv("SYNAWAVE_RUNTIME_ENV", "local"),
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
    _tracing_ready = True
    _tracing_mode = "otlp"
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

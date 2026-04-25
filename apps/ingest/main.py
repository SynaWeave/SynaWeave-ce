"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the first bounded background job path for digest and evaluation output

- Later Extension Points:
    --> widen the worker only when later ingest queues or batch jobs become durable runtime concerns

- Role:
    --> executes one queued job by id against the shared runtime store
    --> keeps the first background boundary separate from the request-serving API process

- Exports:
    --> `run_job()`
    --> `main()`

- Consumed By:
    --> API job routes local operators and tests proving the first background execution path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import os

from opentelemetry import trace

from python.common.observability import (
    current_trace_id,
    extract_trace_context,
    flush_tracing,
    init_tracing,
)
from python.common.runtime_store import JobExecutionError, RuntimeStore

# ---------- worker bootstrap ----------
# Keep one shared store instance because each CLI invocation only needs bounded local work.
store = RuntimeStore()
tracer = init_tracing("sw-ingest")


# ---------- job execution ----------
# Keep the function tiny so tests and the API trigger path can both reuse the same worker logic.
def run_job(job_id: str) -> dict[str, object]:
    carrier = {
        "traceparent": os.getenv("TRACEPARENT", ""),
        "tracestate": os.getenv("TRACESTATE", ""),
    }
    with tracer.start_as_current_span(
        "workspace_digest_job",
        context=extract_trace_context(carrier),
        kind=trace.SpanKind.CONSUMER,
    ) as span:
        trace_id = current_trace_id()
        span.set_attribute("sw.job_id", job_id)
        span.set_attribute("sw.runtime", "ingest")
        store.record_backend_event(
            component="ingest",
            event="workspace_job.started",
            trace_id=trace_id,
            job_id=job_id,
            status="running",
        )
        try:
            result = store.run_job(job_id)
        except Exception as exc:
            store.record_backend_event(
                component="ingest",
                event="workspace_job.failed",
                level="error",
                trace_id=trace_id,
                job_id=job_id,
                status="error",
                detail=str(exc),
            )
            raise
        store.record_backend_event(
            component="ingest",
            event="workspace_job.succeeded",
            trace_id=trace_id,
            job_id=job_id,
            workspace_id=str(result.get("workspace_id", "")),
            user_id=str(result.get("user_id", "")),
            status=str(result.get("state", "")),
        )
        return result


# ---------- cli parsing ----------
# Keep the CLI narrow because Sprint 1 only needs one explicit job execution path.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one SynaWeave ingest job")
    parser.add_argument("--job-id", required=True, help="Queued job identifier")
    return parser.parse_args()


# ---------- process entrypoint ----------
# Print JSON so local operators and tests can inspect worker output without extra tooling.
def main() -> int:
    args = parse_args()
    try:
        print(json.dumps(run_job(args.job_id), sort_keys=True))
        return 0
    except JobExecutionError:
        print(json.dumps(store.job_view(args.job_id), sort_keys=True))
        return 1
    finally:
        flush_tracing()


if __name__ == "__main__":
    raise SystemExit(main())

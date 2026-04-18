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

from python.common.observability import extract_trace_context, init_tracing
from python.common.runtime_store import RuntimeStore

# ---------- worker bootstrap ----------
# Keep one shared store instance because each CLI invocation only needs bounded local work.
store = RuntimeStore()
tracer = init_tracing("synaweave-ingest")


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
        span.set_attribute("synaweave.job_id", job_id)
        span.set_attribute("synaweave.runtime", "ingest")
        return store.run_job(job_id)


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
    print(json.dumps(run_job(args.job_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

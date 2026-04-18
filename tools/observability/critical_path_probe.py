"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  replay the Sprint 1 critical path and confirm
collector-routed traces plus metrics evidence locally

- Later Extension Points:
    --> widen the probe only when more runtimes or stronger
        observability backends become default local proof surfaces

- Role:
    --> exercises auth workspace action and ingest job requests against a running local API
    --> checks collector-exported trace evidence and Prometheus-style
        metrics after the replay completes

- Exports:
    --> `main()`

- Consumed By:
    --> local operators and review evidence runs for Sprint 1 observability proof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import secrets
import time
from pathlib import Path

import httpx

from python.common.runtime_paths import (
    backend_log_path,
    collector_trace_export_path,
    measurements_history_path,
)


# ---------- cli parsing ----------
# Keep the probe inputs explicit so replay runs stay easy to copy into review evidence.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the Sprint 1 observability critical path")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--collector-traces", default=str(collector_trace_export_path()))
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    return parser.parse_args()


# ---------- trace helpers ----------
# Keep one generated traceparent so the replay can look for the same trace id end to end.
def make_traceparent() -> tuple[str, str]:
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    return trace_id, f"00-{trace_id}-{span_id}-01"


# ---------- collector evidence ----------
# Poll the collector output file because OTLP batching stays asynchronous
# even in the bounded local stack.
def wait_for_collector_evidence(trace_id: str, export_path: Path, timeout_seconds: float) -> str:
    started_at = time.time()
    original_text = export_path.read_text(encoding="utf-8") if export_path.exists() else ""
    while time.time() - started_at <= timeout_seconds:
        current_text = export_path.read_text(encoding="utf-8") if export_path.exists() else ""
        delta = current_text[len(original_text) :]
        if trace_id in delta and "synaweave-api" in delta and "synaweave-ingest" in delta:
            return delta
        time.sleep(0.5)
    raise RuntimeError(f"collector trace evidence for {trace_id} did not appear in {export_path}")


# ---------- runtime replay ----------
# Keep the replay to the critical path so the resulting evidence stays bounded and readable.
def main() -> int:
    args = parse_args()
    export_path = Path(args.collector_traces)
    trace_id, traceparent = make_traceparent()

    with httpx.Client(base_url=args.api_base_url, timeout=10.0) as client:
        auth = client.post(
            "/v1/auth/link",
            headers={"traceparent": traceparent},
            json={"email": "probe@example.com", "surface": "web"},
        )
        auth.raise_for_status()
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

        action = client.post(
            "/v1/workspace/action",
            headers={"Authorization": f"Bearer {token}", "traceparent": traceparent},
            json={"kind": "note", "value": "critical path probe", "source": "web"},
        )
        action.raise_for_status()

        job = client.post(
            "/v1/jobs/workspace",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": f"probe-{trace_id[:12]}",
                "traceparent": traceparent,
            },
            json={"workspaceId": workspace_id, "waitForFinish": True},
        )
        job.raise_for_status()

        metrics = client.get("/metrics")
        metrics.raise_for_status()

    collector_delta = wait_for_collector_evidence(trace_id, export_path, args.timeout_seconds)
    required_metrics = [
        "synaweave_api_latency_p95_ms",
        "synaweave_job_duration_p95_ms",
        "synaweave_ai_ready_trace_coverage",
        "synaweave_job_failure_total",
        "synaweave_runtime_ready",
    ]
    missing_metrics = [name for name in required_metrics if name not in metrics.text]
    if missing_metrics:
        raise RuntimeError(f"metrics output missed required names: {', '.join(missing_metrics)}")
    measurement_history = measurements_history_path()
    backend_logs = backend_log_path()
    if not measurement_history.exists():
        raise RuntimeError(f"metrics history file was not written to {measurement_history}")
    if not backend_logs.exists():
        raise RuntimeError(f"backend log file was not written to {backend_logs}")

    print(
        json.dumps(
            {
                "backendLogBytes": backend_logs.stat().st_size,
                "measurementHistoryBytes": measurement_history.stat().st_size,
                "traceId": trace_id,
                "traceparent": traceparent,
                "metricsChecked": required_metrics,
                "collectorEvidenceBytes": len(collector_delta.encode("utf-8")),
                "jobState": job.json()["payload"]["state"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

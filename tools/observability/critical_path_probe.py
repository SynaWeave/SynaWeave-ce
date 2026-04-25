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
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
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
@dataclass(frozen=True)
class FileEvidenceSnapshot:
    path: Path
    size_bytes: int


def snapshot_file_evidence(path: Path) -> FileEvidenceSnapshot:
    return FileEvidenceSnapshot(
        path=path,
        size_bytes=path.stat().st_size if path.exists() else 0,
    )


def wait_for_collector_evidence(trace_id: str, export_path: Path, timeout_seconds: float) -> str:
    started_at = time.time()
    original_text = export_path.read_text(encoding="utf-8") if export_path.exists() else ""
    while time.time() - started_at <= timeout_seconds:
        current_text = export_path.read_text(encoding="utf-8") if export_path.exists() else ""
        delta = current_text[len(original_text) :]
        if trace_id in delta and "sw-api" in delta and "sw-ingest" in delta:
            return delta
        time.sleep(0.5)
    raise RuntimeError(f"collector trace evidence for {trace_id} did not appear in {export_path}")


def wait_for_fresh_file_evidence(
    snapshot: FileEvidenceSnapshot,
    *,
    timeout_seconds: float,
    label: str,
) -> int:
    started_at = time.time()
    while time.time() - started_at <= timeout_seconds:
        current_size = snapshot.path.stat().st_size if snapshot.path.exists() else 0
        if current_size > snapshot.size_bytes:
            return current_size
        time.sleep(0.5)
    raise RuntimeError(
        f"{label} did not record fresh evidence in {snapshot.path} during the current replay"
    )


def wait_for_fresh_jsonl_evidence(
    snapshot: FileEvidenceSnapshot,
    *,
    timeout_seconds: float,
    label: str,
    row_matches: Callable[[dict[str, object]], bool],
) -> dict[str, object]:
    started_at = time.time()
    while time.time() - started_at <= timeout_seconds:
        delta_bytes = b""
        if snapshot.path.exists():
            current_bytes = snapshot.path.read_bytes()
            if len(current_bytes) > snapshot.size_bytes:
                delta_bytes = current_bytes[snapshot.size_bytes :]
        for line in delta_bytes.decode("utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row_matches(row):
                return row
        time.sleep(0.5)
    raise RuntimeError(
        f"{label} did not record replay-linked evidence in {snapshot.path} "
        "during the current replay"
    )


# ---------- runtime replay ----------
# Keep the replay to the critical path so the resulting evidence stays bounded and readable.
def main() -> int:
    args = parse_args()
    export_path = Path(args.collector_traces)
    requested_trace_id, traceparent = make_traceparent()
    measurement_history = measurements_history_path()
    backend_logs = backend_log_path()
    measurement_snapshot = snapshot_file_evidence(measurement_history)
    backend_log_snapshot = snapshot_file_evidence(backend_logs)

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
                "Idempotency-Key": f"probe-{requested_trace_id[:12]}",
                "traceparent": traceparent,
            },
            json={"workspaceId": workspace_id, "waitForFinish": True},
        )
        job.raise_for_status()
        job_payload = job.json()["payload"]
        job_id = job_payload["job_id"]
        observed_trace_id = job.json()["meta"]["traceId"]

        metrics = client.get("/metrics")
        metrics.raise_for_status()

    collector_delta = wait_for_collector_evidence(
        observed_trace_id,
        export_path,
        args.timeout_seconds,
    )
    required_metrics = [
        "synaweave_api_latency_p95_ms",
        "synaweave_job_duration_p95_ms",
        "synaweave_ai_ready_trace_coverage",
        "synaweave_job_failure_total",
        "synaweave_runtime_ready",
        "synaweave_trace_event_total",
    ]
    missing_metrics = [name for name in required_metrics if name not in metrics.text]
    if missing_metrics:
        raise RuntimeError(f"metrics output missed required names: {', '.join(missing_metrics)}")
    measurement_history_row = wait_for_fresh_jsonl_evidence(
        measurement_snapshot,
        timeout_seconds=args.timeout_seconds,
        label="metrics history",
        row_matches=lambda row: row.get("latest_job_id") == job_id
        and row.get("latest_job_trace_id") == f"trc_{job_id}",
    )
    backend_log_row = wait_for_fresh_jsonl_evidence(
        backend_log_snapshot,
        timeout_seconds=args.timeout_seconds,
        label="backend logs",
        row_matches=lambda row: row.get("job_id") == job_id
        and row.get("trace_id") == observed_trace_id
        and row.get("event") == "workspace_job.completed",
    )

    print(
        json.dumps(
            {
                "backendLogEvent": backend_log_row["event"],
                "measurementHistoryCapturedAt": measurement_history_row["captured_at"],
                "requestedTraceId": requested_trace_id,
                "traceId": observed_trace_id,
                "traceparent": traceparent,
                "metricsChecked": required_metrics,
                "collectorEvidenceBytes": len(collector_delta.encode("utf-8")),
                "jobId": job_id,
                "jobState": job_payload["state"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

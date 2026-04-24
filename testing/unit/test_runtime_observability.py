"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the bounded observability path for trace propagation
and critical-path metrics export

- Later Extension Points:
    --> widen runtime observability tests only when more runtimes or
        richer telemetry contracts become part of the default proof path

- Role:
    --> proves the API forwards incoming trace context into the ingest trigger path
    --> proves alert-backed metric names stay exported from the runtime store snapshot

- Exports:
    --> unittest module only

- Consumed By:
    --> local and CI test runs guarding the Sprint 1 observability slice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app
from python.common.runtime_paths import backend_log_path
from python.common.runtime_store import RuntimeStore

client = TestClient(app)


class RuntimeObservabilityTest(unittest.TestCase):
    def make_store(self) -> RuntimeStore:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return RuntimeStore(Path(temp_dir.name) / "runtime.sqlite3")

    def test_metrics_text_exports_alert_threshold_metrics(self) -> None:
        store = self.make_store()
        session = store.create_session("observability@example.com", "web")
        token = session["token"]
        workspace_id = session["workspace"]["workspace"]["workspaceId"]

        store.emit_telemetry(
            surface="web",
            name="web_workspace_bootstrap",
            status="degraded",
            duration_ms=111.0,
            trace_id="web-trace-1",
        )
        job = store.create_job(token, workspace_id, "idem-observability-metrics")
        store.run_job(job["job_id"])
        metrics_text = store.metrics_text()

        self.assertIn("synaweave_workspace_entry_timing_ms", metrics_text)
        self.assertIn("synaweave_ai_ready_trace_coverage", metrics_text)
        self.assertIn("synaweave_job_failure_total", metrics_text)
        self.assertIn("synaweave_degraded_event_total", metrics_text)
        self.assertIn("synaweave_runtime_ready", metrics_text)

    def test_job_route_forwards_traceparent_to_ingest_subprocess(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "traceproof@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]
        trace_id = "1" * 32
        traceparent = f"00-{trace_id}-{'2' * 16}-01"

        with patch("apps.api.main.subprocess.run") as run_job:
            response = client.post(
                "/v1/jobs/workspace",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "trace-continuity-proof",
                    "traceparent": traceparent,
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["meta"]["traceId"], trace_id)
        self.assertEqual(response.headers["x-trace-id"], trace_id)
        self.assertEqual(run_job.call_args.kwargs["env"]["TRACEPARENT"], traceparent)

    def test_backend_logs_capture_request_and_job_correlation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            runtime_dir = Path(temp_dir_name)
            isolated_store = RuntimeStore(runtime_dir / "runtime.sqlite3")
            with (
                patch.dict("os.environ", {"SYNAWAVE_RUNTIME_DIR": str(runtime_dir)}),
                patch("apps.api.main.store", isolated_store),
            ):
                auth = client.post(
                    "/v1/auth/link",
                    json={"email": "logproof@example.com", "surface": "web"},
                )
                token = auth.json()["payload"]["token"]
                workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

                with patch("apps.api.main.subprocess.run"):
                    response = client.post(
                        "/v1/jobs/workspace",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Idempotency-Key": "backend-log-proof",
                        },
                        json={"workspaceId": workspace_id, "waitForFinish": True},
                    )

                log_rows = [
                    json.loads(line)
                    for line in backend_log_path().read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(row["event"] == "request.completed" for row in log_rows))
        self.assertTrue(any(row["event"] == "workspace_job.queued" for row in log_rows))
        self.assertTrue(any(row["event"] == "workspace_job.completed" for row in log_rows))
        queued = next(row for row in log_rows if row["event"] == "workspace_job.queued")
        completed = next(row for row in log_rows if row["event"] == "workspace_job.completed")
        self.assertEqual(queued["request_id"], completed["request_id"])
        self.assertEqual(queued["job_id"], completed["job_id"])

    def test_job_route_returns_failed_job_payload_when_worker_subprocess_fails(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "jobfailure@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

        with patch(
            "apps.api.main.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["python", "-m", "apps.ingest.main"]),
        ):
            response = client.post(
                "/v1/jobs/workspace",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "job-failure-proof",
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["payload"]["state"], "failed")
        self.assertIn("error_detail", response.json()["payload"])

    def test_backend_logs_capture_timeout_as_retryable_degraded_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            runtime_dir = Path(temp_dir_name)
            isolated_store = RuntimeStore(runtime_dir / "runtime.sqlite3")
            with (
                patch.dict("os.environ", {"SYNAWAVE_RUNTIME_DIR": str(runtime_dir)}),
                patch("apps.api.main.store", isolated_store),
            ):
                auth = client.post(
                    "/v1/auth/link",
                    json={"email": "timeoutlog@example.com", "surface": "web"},
                )
                token = auth.json()["payload"]["token"]
                workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

                with patch(
                    "apps.api.main.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(
                        cmd=["python3", "-m", "apps.ingest.main"],
                        timeout=15,
                    ),
                ):
                    response = client.post(
                        "/v1/jobs/workspace",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Idempotency-Key": "backend-timeout-proof",
                        },
                        json={"workspaceId": workspace_id, "waitForFinish": True},
                    )

                log_rows = [
                    json.loads(line)
                    for line in backend_log_path().read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

        self.assertEqual(response.status_code, 504)
        timeout_row = next(row for row in log_rows if row["event"] == "workspace_job.timed_out")
        self.assertEqual(timeout_row["status"], "degraded")
        self.assertTrue(timeout_row["fields"]["retryable"])


if __name__ == "__main__":
    unittest.main()

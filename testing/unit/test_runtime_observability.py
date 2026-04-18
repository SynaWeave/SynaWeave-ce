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

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app
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
            status="ok",
            duration_ms=111.0,
            trace_id="web-trace-1",
        )
        job = store.create_job(token, workspace_id, "idem-observability-metrics")
        store.run_job(job["job_id"])
        metrics_text = store.metrics_text()

        self.assertIn("synaweave_workspace_entry_timing_ms", metrics_text)
        self.assertIn("synaweave_ai_ready_trace_coverage", metrics_text)

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


if __name__ == "__main__":
    unittest.main()

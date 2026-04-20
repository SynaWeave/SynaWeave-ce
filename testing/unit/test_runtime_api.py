"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the FastAPI runtime path for auth writes jobs metrics and ownership checks

- Later Extension Points:
    --> add broader API route tests only when later runtime domains join the critical path

- Role:
    --> proves the first request-serving path behaves like a real product runtime
    --> confirms readiness and ownership failures stay visible through the API boundary

- Exports:
    --> unittest module only

- Consumed By:
    --> local and CI test runs guarding the Sprint 1 API proof slice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import subprocess
import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import (
    MAX_BROWSER_TELEMETRY_DETAIL_LENGTH,
    MAX_BROWSER_TELEMETRY_DURATION_MS,
    app,
    store,
)

# ---------- api tests ----------
# Keep one shared test client because the runtime path is intentionally small in Sprint 1.
client = TestClient(app)


class RuntimeApiTest(unittest.TestCase):
    def test_auth_bootstrap_action_job_and_metrics(self) -> None:
        stamp = uuid.uuid4().hex[:8]
        auth = client.post(
            "/v1/auth/link",
            json={"email": f"api-proof-{stamp}@example.com", "surface": "web"},
        )
        self.assertEqual(auth.status_code, 200)
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]
        headers = {"Authorization": f"Bearer {token}"}

        identity = client.get("/v1/identity", headers=headers)
        self.assertEqual(identity.status_code, 200)

        action = client.post(
            "/v1/workspace/action",
            headers=headers,
            json={"kind": "note", "value": "api proof action", "source": "web"},
        )
        self.assertEqual(action.status_code, 200)

        job = client.post(
            "/v1/jobs/workspace",
            headers={**headers, "Idempotency-Key": f"api-runtime-proof-{stamp}"},
            json={"workspaceId": workspace_id, "waitForFinish": True},
        )
        self.assertEqual(job.status_code, 200)
        self.assertEqual(job.json()["status"], "ok")
        self.assertEqual(job.json()["payload"]["state"], "succeeded")

        bootstrap = client.get("/v1/workspace/bootstrap", headers=headers)
        self.assertEqual(bootstrap.status_code, 200)
        self.assertIn("lastDigest", bootstrap.json()["payload"]["workspace"])

        metrics = client.get("/metrics")
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("synaweave_auth_success_total", metrics.text)

    def test_job_route_rejects_foreign_workspace(self) -> None:
        first = client.post(
            "/v1/auth/link",
            json={"email": "owner@example.com", "surface": "web"},
        ).json()["payload"]
        second = client.post(
            "/v1/auth/link",
            json={"email": "other@example.com", "surface": "web"},
        ).json()["payload"]

        response = client.post(
            "/v1/jobs/workspace",
            headers={
                "Authorization": f"Bearer {first['token']}",
                "Idempotency-Key": "foreign-workspace-job",
            },
            json={
                "workspaceId": second["workspace"]["workspace"]["workspaceId"],
                "waitForFinish": False,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_workspace_action_rejects_source_that_does_not_match_session(self) -> None:
        token = client.post(
            "/v1/auth/link",
            json={"email": "action-surface@example.com", "surface": "web"},
        ).json()["payload"]["token"]

        response = client.post(
            "/v1/workspace/action",
            headers={"Authorization": f"Bearer {token}"},
            json={"kind": "note", "value": "spoofed extension write", "source": "extension"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "workspace action source does not match session",
        )

    def test_job_routes_report_invalid_bearer_as_unauthorized(self) -> None:
        create_response = client.post(
            "/v1/jobs/workspace",
            headers={"Authorization": "Bearer not-a-real-token"},
            json={"workspaceId": "wsp_missing", "waitForFinish": False},
        )
        read_response = client.get(
            "/v1/jobs/job_missing",
            headers={"Authorization": "Bearer not-a-real-token"},
        )

        self.assertEqual(create_response.status_code, 401)
        self.assertEqual(read_response.status_code, 401)

    def test_job_view_keeps_unknown_job_as_not_found(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "missing-job@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]

        response = client.get(
            "/v1/jobs/job_missing",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 404)

    def test_ready_reports_dependency_failures(self) -> None:
        with patch("apps.api.main.store.readiness_status") as readiness_status:
            readiness_status.return_value = {
                "dbReady": False,
                "telemetryReady": True,
                "runtimeDir": "build/runtime",
                "errors": ["db:offline"],
            }
            response = client.get("/health/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "not_ready")
        self.assertFalse(response.json()["payload"]["dbReady"])

    def test_telemetry_emit_accepts_degraded_status(self) -> None:
        token = client.post(
            "/v1/auth/link",
            json={"email": "telemetry-web@example.com", "surface": "web"},
        ).json()["payload"]["token"]
        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "surface": "web",
                "name": "web_workspace_bootstrap",
                "status": "degraded",
                "durationMs": 12.5,
                "detail": "transient:504:upstream timeout",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "accepted")
        self.assertEqual(response.json()["payload"]["status"], "degraded")
        self.assertEqual(response.json()["payload"]["surface"], "web")

    def test_telemetry_emit_requires_authenticated_session(self) -> None:
        response = client.post(
            "/v1/telemetry/emit",
            json={
                "surface": "web",
                "name": "web_workspace_bootstrap",
                "status": "ok",
                "durationMs": 12.5,
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "missing bearer token")

    def test_telemetry_emit_rejects_server_owned_surfaces(self) -> None:
        token = client.post(
            "/v1/auth/link",
            json={"email": "telemetry-api@example.com", "surface": "web"},
        ).json()["payload"]["token"]
        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "surface": "api",
                "name": "GET /v1/identity",
                "status": "ok",
                "durationMs": 12.5,
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_telemetry_emit_rejects_surface_name_mismatch(self) -> None:
        token = client.post(
            "/v1/auth/link",
            json={"email": "telemetry-mismatch@example.com", "surface": "web"},
        ).json()["payload"]["token"]
        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "surface": "web",
                "name": "extension_digest_run",
                "status": "ok",
                "durationMs": 9.5,
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "telemetry name does not match surface")

    def test_telemetry_emit_sanitizes_and_bounds_browser_inputs(self) -> None:
        long_detail = "line one\nline two\t" + ("x" * 300)
        token = client.post(
            "/v1/auth/link",
            json={"email": "telemetry-extension@example.com", "surface": "extension"},
        ).json()["payload"]["token"]
        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "surface": "extension",
                "name": "extension_workspace_bootstrap",
                "status": "degraded",
                "durationMs": MAX_BROWSER_TELEMETRY_DURATION_MS + 999.0,
                "detail": long_detail,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertEqual(payload["duration_ms"], MAX_BROWSER_TELEMETRY_DURATION_MS)
        self.assertEqual(payload["cost_micros"], 0)
        self.assertNotIn("\n", payload["detail"])
        self.assertNotIn("\t", payload["detail"])
        self.assertLessEqual(len(payload["detail"]), MAX_BROWSER_TELEMETRY_DETAIL_LENGTH)

    def test_telemetry_emit_rejects_surface_that_does_not_match_session(self) -> None:
        token = client.post(
            "/v1/auth/link",
            json={"email": "telemetry-surface@example.com", "surface": "web"},
        ).json()["payload"]["token"]
        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "surface": "extension",
                "name": "extension_workspace_bootstrap",
                "status": "ok",
                "durationMs": 9.5,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "telemetry surface does not match session")

    def test_auth_bootstrap_rejects_non_loopback_host(
        self,
    ) -> None:
        guarded_client = TestClient(app, base_url="https://api.synaweave.example")

        with patch("apps.api.main.LOCAL_PROOF_ONLY_AUTH", True):
            response = guarded_client.post(
                "/v1/auth/link",
                json={"email": "guarded@example.com", "surface": "web"},
            )

        self.assertEqual(response.status_code, 403)
        self.assertIn("loopback hosts", response.json()["detail"])

    def test_waited_job_subprocess_receives_explicit_runtime_store_handoff(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "handoff@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

        with patch("apps.api.main.subprocess.run") as subprocess_run:
            response = client.post(
                "/v1/jobs/workspace",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "api-runtime-handoff",
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 200)
        subprocess_env = subprocess_run.call_args.kwargs["env"]
        self.assertIn("SYNAWEAVE_RUNTIME_DIR", subprocess_env)
        self.assertIn("SYNAWEAVE_RUNTIME_DB_PATH", subprocess_env)
        self.assertTrue(subprocess_env["SYNAWEAVE_RUNTIME_DB_PATH"].endswith(".sqlite3"))

    def test_waited_job_returns_failed_truth_when_ingest_subprocess_fails(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "job-failure@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

        with patch(
            "apps.api.main.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["python3", "-m", "apps.ingest.main"]),
        ):
            response = client.post(
                "/v1/jobs/workspace",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "api-runtime-failure",
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["payload"]["state"], "failed")
        self.assertIn("ingest execution failed", response.json()["payload"]["summary"].lower())
        self.assertIn("CalledProcessError", response.json()["payload"]["error_detail"])

        job_id = response.json()["payload"]["job_id"]
        read_response = client.get(
            f"/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["payload"]["state"], "failed")

    def test_waited_job_keeps_durable_succeeded_truth_when_subprocess_exits_oddly(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "job-odd-exit@example.com", "surface": "web"},
        )
        token = auth.json()["payload"]["token"]
        workspace_id = auth.json()["payload"]["workspace"]["workspace"]["workspaceId"]

        def odd_exit(*args, **kwargs):
            job_id = args[0][-1]
            store.run_job(job_id)
            raise subprocess.CalledProcessError(1, ["python3", "-m", "apps.ingest.main"])

        with patch("apps.api.main.subprocess.run", side_effect=odd_exit):
            response = client.post(
                "/v1/jobs/workspace",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "api-runtime-odd-exit",
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["payload"]["state"], "succeeded")
        self.assertEqual(response.json()["payload"]["error_detail"], "")

    def test_waited_job_timeout_returns_retryable_degraded_failure(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "job-timeout@example.com", "surface": "web"},
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
                    "Idempotency-Key": "api-runtime-timeout",
                },
                json={"workspaceId": workspace_id, "waitForFinish": True},
            )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.headers["Retry-After"], "15")
        self.assertEqual(response.json()["status"], "degraded")
        self.assertTrue(response.json()["retryable"])
        self.assertEqual(response.json()["payload"]["state"], "failed")
        self.assertIn("timed out", response.json()["detail"].lower())
        self.assertIn("TimeoutExpired", response.json()["payload"]["error_detail"])


if __name__ == "__main__":
    unittest.main()

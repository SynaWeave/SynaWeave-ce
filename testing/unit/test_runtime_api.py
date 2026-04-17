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

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app

# ---------- api tests ----------
# Keep one shared test client because the runtime path is intentionally small in Sprint 1.
client = TestClient(app)


class RuntimeApiTest(unittest.TestCase):
    def test_auth_bootstrap_action_job_and_metrics(self) -> None:
        auth = client.post(
            "/v1/auth/link",
            json={"email": "api-proof@example.com", "surface": "web"},
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
            headers={**headers, "Idempotency-Key": "api-runtime-proof"},
            json={"workspaceId": workspace_id, "waitForFinish": True},
        )
        self.assertEqual(job.status_code, 200)
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


if __name__ == "__main__":
    unittest.main()

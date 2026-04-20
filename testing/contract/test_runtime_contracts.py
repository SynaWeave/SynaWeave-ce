"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  validate Sprint 1 runtime request response and extension message
            contracts against versioned schemas

- Later Extension Points:
    --> add more public serialized interfaces only when new Sprint-owned runtime
        boundaries become durable

- Role:
    --> proves live API envelopes and payloads still match the governed contract bundle
    --> keeps extension message fixtures pinned to the same shared contract home as runtime payloads

- Exports:
    --> unittest module only

- Consumed By:
    --> Python contract discovery and repository verification runs covering
        public serialized interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from apps.api.main import app
from testing.contract.schema_assertions import assert_matches_schema

client = TestClient(app)
CONTRACT_BUNDLE_PATH = Path("packages/contracts/runtime/public-interfaces.v1.json")
CONTRACT_FIXTURES_PATH = Path("testing/contract/fixtures/runtime-public-interfaces.v1.json")


class RuntimeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contracts = json.loads(
            CONTRACT_BUNDLE_PATH.read_text(encoding="utf-8")
        )["contracts"]
        cls.fixtures = json.loads(CONTRACT_FIXTURES_PATH.read_text(encoding="utf-8"))

    def assert_contract(self, name: str, payload: object) -> None:
        assert_matches_schema(payload, self.contracts[name], path=name)

    def assert_api_response(self, response, payload_contract: str) -> None:
        body = response.json()
        self.assert_contract("apiEnvelope", body)
        self.assert_contract(payload_contract, body["payload"])

    def bootstrap_session(self) -> tuple[str, dict[str, Any]]:
        request_body = self.fixtures["authLinkRequest"]
        response = client.post("/v1/auth/link", json=request_body)
        self.assertEqual(response.status_code, 200)
        self.assert_api_response(response, "authBootstrapPayload")
        payload = response.json()["payload"]
        return payload["token"], payload

    def test_auth_bootstrap_payload_contract(self) -> None:
        _, payload = self.bootstrap_session()
        self.assert_contract("identityPayload", payload["identity"])
        self.assert_contract("workspaceBootstrapPayload", payload["workspace"])

    def test_identity_payload_contract(self) -> None:
        token, _ = self.bootstrap_session()
        response = client.get("/v1/identity", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assert_api_response(response, "identityPayload")

    def test_workspace_bootstrap_payload_contract(self) -> None:
        token, _ = self.bootstrap_session()
        response = client.get(
            "/v1/workspace/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assert_api_response(response, "workspaceBootstrapPayload")

    def test_workspace_action_request_and_response_contracts(self) -> None:
        token, _ = self.bootstrap_session()
        request_body = self.fixtures["workspaceActionRequest"]
        self.assert_contract("workspaceActionRequest", request_body)

        response = client.post(
            "/v1/workspace/action",
            headers={"Authorization": f"Bearer {token}"},
            json=request_body,
        )
        self.assertEqual(response.status_code, 200)
        self.assert_api_response(response, "workspaceActionPayload")

    def test_job_create_and_view_payload_contracts(self) -> None:
        token, auth_payload = self.bootstrap_session()
        workspace_id = auth_payload["workspace"]["workspace"]["workspaceId"]

        create_response = client.post(
            "/v1/jobs/workspace",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "contract-job-create",
            },
            json={"workspaceId": workspace_id, "waitForFinish": False},
        )
        self.assertEqual(create_response.status_code, 200)
        self.assert_api_response(create_response, "jobCreatePayload")
        self.assertEqual(create_response.json()["status"], "accepted")

        job_id = create_response.json()["payload"]["job_id"]
        view_response = client.get(
            f"/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(view_response.status_code, 200)
        self.assert_api_response(view_response, "jobViewPayload")

    def test_telemetry_emit_request_and_response_contracts(self) -> None:
        token, _ = self.bootstrap_session()
        request_body = self.fixtures["telemetryEmitRequest"]
        self.assert_contract("telemetryEmitRequest", request_body)

        response = client.post(
            "/v1/telemetry/emit",
            headers={"Authorization": f"Bearer {token}"},
            json=request_body,
        )
        self.assertEqual(response.status_code, 200)
        self.assert_api_response(response, "telemetryEmitPayload")
        self.assertEqual(response.json()["status"], "accepted")

    def test_extension_selection_message_contracts(self) -> None:
        self.assert_contract(
            "extensionSelectionRequest",
            self.fixtures["extensionSelectionRequest"],
        )
        self.assert_contract(
            "extensionSelectionResponse",
            self.fixtures["extensionSelectionResponse"],
        )


if __name__ == "__main__":
    unittest.main()

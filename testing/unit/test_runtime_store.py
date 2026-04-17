"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the local runtime store for shared auth workspace jobs and baseline behavior

- Later Extension Points:
    --> add more store tests only when later runtime tables or invariants become proof needs

- Role:
    --> proves same-email identity continuity across sessions
    --> proves writes ownership checks and baseline generation against isolated sqlite state

- Exports:
    --> unittest module only

- Consumed By:
    --> local and CI test runs guarding the Sprint 1 runtime proof path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from python.common.runtime_store import RuntimeStore


# ---------- runtime store tests ----------
# Keep isolated databases per test so state leakage never hides correctness issues.
class RuntimeStoreTest(unittest.TestCase):
    def make_store(self) -> RuntimeStore:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return RuntimeStore(Path(temp_dir.name) / "runtime.sqlite3")

    def test_same_email_reuses_identity_and_workspace(self) -> None:
        store = self.make_store()
        first = store.create_session("user@example.com", "web")
        second = store.create_session("user@example.com", "extension")

        self.assertEqual(first["identity"]["email"], second["identity"]["email"])
        self.assertEqual(first["identity"]["bridgeCode"], second["identity"]["bridgeCode"])
        self.assertEqual(
            first["workspace"]["workspace"]["workspaceId"],
            second["workspace"]["workspace"]["workspaceId"],
        )

    def test_action_write_and_job_create_digest_and_eval(self) -> None:
        store = self.make_store()
        session = store.create_session("learner@example.com", "web")
        token = session["token"]
        workspace_id = session["workspace"]["workspace"]["workspaceId"]

        store.record_action(token, "note", "graph retrieval needs evidence", "web")
        store.record_action(token, "capture", "otel collector comes later", "extension")
        job = store.create_job(token, workspace_id, "idem-runtime-test")
        finished = store.run_job(job["job_id"])
        bootstrap = store.workspace_bootstrap(session["identity"]["userId"])

        self.assertEqual(finished["state"], "succeeded")
        self.assertIn("note", bootstrap["workspace"]["lastDigest"])
        self.assertIsNotNone(bootstrap["latestEval"])
        self.assertGreater(bootstrap["latestEval"]["score"], 0)

    def test_rejects_cross_workspace_job_creation(self) -> None:
        store = self.make_store()
        first = store.create_session("owner@example.com", "web")
        second = store.create_session("other@example.com", "web")

        with self.assertRaises(PermissionError):
            store.create_job(
                first["token"],
                second["workspace"]["workspace"]["workspaceId"],
                "idem-foreign-workspace",
            )

    def test_rejects_foreign_job_reads(self) -> None:
        store = self.make_store()
        owner = store.create_session("owner@example.com", "web")
        other = store.create_session("other@example.com", "web")
        workspace_id = owner["workspace"]["workspace"]["workspaceId"]
        job = store.create_job(owner["token"], workspace_id, "idem-owned-job")

        with self.assertRaises(PermissionError):
            store.job_view(job["job_id"], user_id=other["identity"]["userId"])

    def test_metrics_snapshot_counts_runtime_events(self) -> None:
        store = self.make_store()
        session = store.create_session("metrics@example.com", "web")
        token = session["token"]
        workspace_id = session["workspace"]["workspace"]["workspaceId"]

        store.emit_telemetry(
            surface="web",
            name="web_workspace_bootstrap",
            status="ok",
            duration_ms=123.0,
            trace_id="web_trace_1",
        )
        store.record_action(token, "note", "measure the first proof path", "web")
        job = store.create_job(token, workspace_id, "idem-metrics-test")
        store.run_job(job["job_id"])
        snapshot = store.metrics_snapshot()

        self.assertGreaterEqual(snapshot["auth_success_total"], 1)
        self.assertGreaterEqual(snapshot["workspace_action_total"], 1)
        self.assertGreaterEqual(snapshot["job_success_total"], 1)
        self.assertEqual(snapshot["workspace_entry_timing_ms"], 123.0)
        self.assertEqual(snapshot["ai_ready_trace_coverage"], 1.0)
        self.assertNotIn("side_panel_open_timing_ms", snapshot)


if __name__ == "__main__":
    unittest.main()

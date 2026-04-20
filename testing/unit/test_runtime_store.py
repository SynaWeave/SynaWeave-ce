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

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from python.common.runtime_paths import measurements_history_path
from python.common.runtime_store import JobExecutionError, RuntimeStore


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
        extension_session = store.create_session("learner@example.com", "extension")
        token = session["token"]
        workspace_id = session["workspace"]["workspace"]["workspaceId"]

        store.record_action(token, "note", "graph retrieval needs evidence", "web")
        store.record_action(
            extension_session["token"],
            "capture",
            "otel collector comes later",
            "extension",
        )
        job = store.create_job(token, workspace_id, "idem-runtime-test")
        finished = store.run_job(job["job_id"])
        bootstrap = store.workspace_bootstrap(session["identity"]["userId"])

        self.assertEqual(finished["state"], "succeeded")
        self.assertIn("note", bootstrap["workspace"]["lastDigest"])
        self.assertIsNotNone(bootstrap["latestEval"])
        self.assertGreater(bootstrap["latestEval"]["score"], 0)

    def test_rejects_action_source_that_does_not_match_session_surface(self) -> None:
        store = self.make_store()
        session = store.create_session("learner@example.com", "web")

        with self.assertRaises(PermissionError):
            store.record_action(session["token"], "note", "cross-surface spoof", "extension")

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
        self.assertEqual(snapshot["job_failure_total"], 0)
        self.assertEqual(snapshot["ingest_error_total"], 0)
        self.assertEqual(snapshot["degraded_event_total"], 0)
        self.assertEqual(snapshot["runtime_ready"], 1)
        self.assertEqual(snapshot["latest_job_id"], job["job_id"])
        self.assertEqual(snapshot["latest_job_trace_id"], f"trc_{job['job_id']}")
        self.assertNotIn("side_panel_open_timing_ms", snapshot)

    def test_store_recovers_from_generated_malformed_runtime_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            database_path = Path(temp_dir_name) / "runtime.sqlite3"
            database_path.write_text("not sqlite\n", encoding="utf-8")

            store = RuntimeStore(database_path)
            session = store.create_session("recover@example.com", "web")
            quarantine_dir = Path(temp_dir_name) / "quarantine"
            quarantine_paths = list(quarantine_dir.glob("runtime.sqlite3.corrupt-*"))
            recovery_rows = [
                line
                for line in (Path(temp_dir_name) / "runtime-db-recovery.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]

        self.assertEqual(session["identity"]["email"], "recover@example.com")
        self.assertTrue(quarantine_paths)
        self.assertEqual(len(recovery_rows), 1)
        self.assertIn("not a database", recovery_rows[0])

    def test_store_recreates_missing_telemetry_table_after_runtime_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            database_path = Path(temp_dir_name) / "runtime.sqlite3"
            store = RuntimeStore(database_path)

            with sqlite3.connect(database_path) as connection:
                connection.execute("drop table telemetry")

            event = store.emit_telemetry(
                surface="web",
                name="web_workspace_bootstrap",
                status="ok",
                duration_ms=12.5,
                trace_id="trace_schema_recovery",
            )

        self.assertEqual(event["surface"], "web")
        self.assertEqual(event["name"], "web_workspace_bootstrap")

    def test_job_failure_persists_error_detail_and_allows_retry(self) -> None:
        store = self.make_store()
        session = store.create_session("failure@example.com", "web")
        token = session["token"]
        workspace_id = session["workspace"]["workspace"]["workspaceId"]
        store.record_action(token, "note", "provider fallback must stay truthful", "web")
        job = store.create_job(token, workspace_id, "idem-runtime-failure")

        with patch.object(store, "_write_eval", side_effect=RuntimeError("provider offline")):
            with self.assertRaises(JobExecutionError):
                store.run_job(job["job_id"])

        failed = store.job_view(job["job_id"])
        self.assertEqual(failed["state"], "failed")
        self.assertIn("evaluation failed", failed["summary"].lower())
        self.assertIn("RuntimeError: provider offline", failed["error_detail"])
        self.assertEqual(failed["retry_count"], 0)

        retried = store.create_job(token, workspace_id, "idem-runtime-failure")
        self.assertEqual(retried["job_id"], job["job_id"])

        finished = store.run_job(job["job_id"])
        self.assertEqual(finished["state"], "succeeded")
        self.assertEqual(finished["retry_count"], 1)
        self.assertEqual(finished["error_detail"], "")

    def test_metrics_text_appends_measurement_history_with_hotspots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            runtime_dir = Path(temp_dir_name)
            with patch.dict("os.environ", {"SYNAWEAVE_RUNTIME_DIR": str(runtime_dir)}):
                store = RuntimeStore(runtime_dir / "runtime.sqlite3")
                store.emit_telemetry(
                    surface="api",
                    name="GET /v1/identity",
                    status="error",
                    duration_ms=250.0,
                    trace_id="api_trace_1",
                )
                store.emit_telemetry(
                    surface="api",
                    name="GET /v1/identity",
                    status="ok",
                    duration_ms=125.0,
                    trace_id="api_trace_2",
                )
                store.emit_telemetry(
                    surface="web",
                    name="web_workspace_bootstrap",
                    status="degraded",
                    duration_ms=90.0,
                    trace_id="web_trace_degraded",
                )

                store.metrics_text()
                store.metrics_text()
                snapshot = store.metrics_snapshot()

                measurement_rows = [
                    line
                    for line in measurements_history_path().read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

        self.assertEqual(len(measurement_rows), 2)
        self.assertIn("GET /v1/identity", measurement_rows[-1])
        self.assertEqual(snapshot["degraded_event_total"], 1)


if __name__ == "__main__":
    unittest.main()

"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the local evaluation harness exports reproducible proof artifacts

- Later Extension Points:
    --> widen harness assertions only when more eval flows become real runtime proof targets

- Role:
    --> proves the Sprint 1 eval fixture runs through the real runtime store
    --> confirms tracked proof JSON stays machine-readable and threshold-aware

- Exports:
    --> unittest module only

- Consumed By:
    --> local and CI test runs guarding the first eval and performance proof path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from python.evaluation.runtime_eval import read_runtime_baseline, run_local_eval_fixture
from python.evaluation.verify_mlflow_run import verify_latest_runtime_eval_run


class RuntimeEvalTest(unittest.TestCase):
    def test_fixture_run_generates_eval_and_performance_reports(self) -> None:
        dataset_path = Path("testing/evals/fixtures/runtime-digest-density.v1.json")

        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            eval_output = temp_dir / "eval-proof.json"
            performance_output = temp_dir / "performance-proof.json"
            mlflow_db = temp_dir / "mlflow.db"
            mlflow_tracking_uri = f"sqlite:///{mlflow_db.resolve()}"
            mlflow_experiment_name = "runtime-eval-test"

            report = run_local_eval_fixture(
                dataset_path,
                output_path=eval_output,
                performance_output_path=performance_output,
                mlflow_tracking_uri=mlflow_tracking_uri,
                mlflow_experiment_name=mlflow_experiment_name,
            )

            self.assertEqual(report["datasetVersion"], "v1")
            self.assertEqual(len(report["cases"]), 2)
            self.assertGreater(report["metricsSnapshot"]["job_success_total"], 0)
            self.assertEqual(report["metricsSnapshot"]["ai_ready_trace_coverage"], 1.0)
            self.assertTrue(report["performanceSnapshot"]["thresholdStatus"]["workspaceEntryTiming"])
            self.assertEqual(report["mlflow"]["experimentName"], mlflow_experiment_name)
            self.assertEqual(report["mlflow"]["trackingUri"], mlflow_tracking_uri)
            self.assertEqual(report["mlflow"]["runStatus"], "FINISHED")
            self.assertTrue(eval_output.exists())
            self.assertTrue(performance_output.exists())

            eval_payload = json.loads(eval_output.read_text(encoding="utf-8"))
            performance_payload = json.loads(performance_output.read_text(encoding="utf-8"))

            self.assertEqual(eval_payload["proofType"], "repo-local-runtime-eval")
            self.assertEqual(performance_payload["proofType"], "repo-local-performance-baseline")

            mlflow_summary = verify_latest_runtime_eval_run(
                tracking_uri=mlflow_tracking_uri,
                experiment_name=mlflow_experiment_name,
                run_id=report["mlflow"]["runId"],
            )
            self.assertEqual(mlflow_summary["runId"], report["mlflow"]["runId"])
            self.assertIn("runtime-eval/report.json", mlflow_summary["artifactFiles"])
            self.assertIn("score_mean", mlflow_summary["metricKeys"])

    def test_read_runtime_baseline_is_empty_without_generated_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            runtime_dir = Path(temp_dir_name)
            with patch.dict("os.environ", {"SYNAWEAVE_RUNTIME_DIR": str(runtime_dir)}):
                self.assertEqual(read_runtime_baseline(), {})
            self.assertFalse((runtime_dir / "baseline.json").exists())


if __name__ == "__main__":
    unittest.main()

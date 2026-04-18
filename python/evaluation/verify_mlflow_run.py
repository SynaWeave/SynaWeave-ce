"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  confirm the local runtime eval produced a real MLflow run

- Later Extension Points:
    --> widen artifact and metric assertions only when the runtime eval proof expands

- Role:
    --> checks the configured local MLflow experiment for one runtime-eval run
    --> proves the run includes the expected metrics and JSON artifacts

- Exports:
    --> `verify_latest_runtime_eval_run()`

- Consumed By:
    --> operator verification and unit tests for the Sprint 1 local MLflow proof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
from typing import Any

from python.evaluation.runtime_eval import (
    default_mlflow_experiment_name,
    default_mlflow_tracking_uri,
)


def verify_latest_runtime_eval_run(
    *,
    tracking_uri: str | None = None,
    experiment_name: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    from mlflow.tracking import MlflowClient

    resolved_tracking_uri = tracking_uri or default_mlflow_tracking_uri()
    resolved_experiment_name = experiment_name or default_mlflow_experiment_name()
    client = MlflowClient(tracking_uri=resolved_tracking_uri)
    experiment = client.get_experiment_by_name(resolved_experiment_name)

    if experiment is None:
        raise RuntimeError(
            "MLflow experiment "
            f"'{resolved_experiment_name}' was not found at {resolved_tracking_uri}"
        )

    if run_id is None:
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["attributes.start_time DESC"],
            max_results=1,
        )
        if not runs:
            raise RuntimeError(
                f"MLflow experiment '{resolved_experiment_name}' has no runs to verify"
            )
        run = runs[0]
    else:
        run = client.get_run(run_id)

    artifact_files = {
        artifact.path for artifact in client.list_artifacts(run.info.run_id, path="runtime-eval")
    }
    required_artifacts = {
        "runtime-eval/dataset.json",
        "runtime-eval/performance.json",
        "runtime-eval/report.json",
    }
    missing_artifacts = sorted(required_artifacts - artifact_files)
    if missing_artifacts:
        raise RuntimeError(
            "MLflow run is missing expected artifacts: " + ", ".join(missing_artifacts)
        )

    required_metrics = {
        "ai_ready_trace_coverage",
        "api_latency_p95_ms",
        "case_count",
        "job_duration_p95_ms",
        "job_success_total",
        "score_mean",
        "trace_event_total",
        "workspace_entry_timing_ms",
    }
    missing_metrics = sorted(required_metrics - set(run.data.metrics))
    if missing_metrics:
        raise RuntimeError(
            "MLflow run is missing expected metrics: " + ", ".join(missing_metrics)
        )

    return {
        "trackingUri": resolved_tracking_uri,
        "experimentName": resolved_experiment_name,
        "experimentId": experiment.experiment_id,
        "runId": run.info.run_id,
        "runName": run.data.tags.get("mlflow.runName", ""),
        "runStatus": run.info.status,
        "artifactFiles": sorted(artifact_files),
        "metricKeys": sorted(run.data.metrics),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the latest local runtime-eval MLflow run"
    )
    parser.add_argument("--tracking-uri", default=default_mlflow_tracking_uri())
    parser.add_argument("--experiment-name", default=default_mlflow_experiment_name())
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    result = verify_latest_runtime_eval_run(
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

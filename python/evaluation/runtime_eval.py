"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the first local evaluation harness and export versioned proof JSON

- Later Extension Points:
    --> swap local proof runs for Langfuse and MLflow-backed adapters when hosted infra is durable

- Role:
    --> executes a synthetic Sprint 1 runtime dataset through the real runtime store
    --> exports machine-readable local eval and performance proof from actual runtime data

- Exports:
    --> `read_runtime_baseline()`
    --> `run_local_eval_fixture()`

- Consumed By:
    --> tests operator scripts and Sprint 1 proof generation for
        `testing/evals/` and `testing/performance/`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from python.common.runtime_store import RuntimeStore
from python.common.runtime_time import utc_now_iso


# ---------- repo path helpers ----------
# Keep tracked proof paths centralized so docs and scripts reuse the same homes.
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_dataset_path() -> Path:
    return repo_root() / "testing" / "evals" / "fixtures" / "runtime-digest-density.v1.json"


def default_eval_output_path() -> Path:
    return (
        repo_root()
        / "testing"
        / "evals"
        / "artifacts"
        / "runtime-digest-density.local-proof.v1.json"
    )


def default_performance_output_path() -> Path:
    return repo_root() / "testing" / "performance" / "runtime-baseline.local-proof.v1.json"


def default_mlflow_dir() -> Path:
    return repo_root() / "build" / "mlflow"


def default_mlflow_db_path() -> Path:
    return default_mlflow_dir() / "mlflow.db"


def default_mlflow_artifact_root() -> Path:
    return default_mlflow_dir() / "artifacts"


def default_mlflow_tracking_uri() -> str:
    configured = os.environ.get("MLFLOW_TRACKING_URI", "").strip()
    if configured:
        return configured

    default_mlflow_artifact_root().mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_mlflow_db_path().resolve()}"


def default_mlflow_experiment_name() -> str:
    return os.environ.get(
        "SYNAWEAVE_MLFLOW_EXPERIMENT",
        "synaweave-sprint1-runtime-eval-local",
    )


# ---------- baseline reader ----------
# Keep the reader defensive so early tests can call it before the first baseline is written.
def read_runtime_baseline() -> dict[str, Any]:
    path = Path(os.environ.get("SYNAWEAVE_RUNTIME_DIR", "")).expanduser()
    baseline = (
        path / "baseline.json"
        if str(path)
        else repo_root() / "build" / "runtime" / "baseline.json"
    )
    if not baseline.exists():
        return {}
    return json.loads(baseline.read_text(encoding="utf-8"))


# ---------- runtime dir override ----------
# Keep proof runs isolated so tracked fixture generation does not depend on shared local state.
@contextmanager
def _runtime_dir_override(runtime_dir: Path):
    previous = os.environ.get("SYNAWEAVE_RUNTIME_DIR")
    os.environ["SYNAWEAVE_RUNTIME_DIR"] = str(runtime_dir)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SYNAWEAVE_RUNTIME_DIR", None)
        else:
            os.environ["SYNAWEAVE_RUNTIME_DIR"] = previous


# ---------- fixture loading ----------
# Keep fixture parsing explicit so failures stay readable during local proof regeneration.
def _load_fixture(dataset_path: Path) -> dict[str, Any]:
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def _mlflow_metric_name(case_id: str, field: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", case_id.lower()).strip("_")
    return f"case_{slug}_{field}"


def _mlflow_artifact_location(tracking_uri: str) -> str | None:
    if not tracking_uri.startswith("sqlite:///"):
        return None

    db_path = Path(tracking_uri.removeprefix("sqlite:///"))
    artifact_root = db_path.parent / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root.resolve().as_uri()


def _write_mlflow_run(
    dataset: dict[str, Any],
    case_results: list[dict[str, Any]],
    metrics_snapshot: dict[str, Any],
    performance_snapshot: dict[str, Any],
    report: dict[str, Any],
    *,
    tracking_uri: str | None = None,
    experiment_name: str | None = None,
) -> dict[str, Any]:
    import mlflow
    from mlflow.tracking import MlflowClient

    resolved_tracking_uri = tracking_uri or default_mlflow_tracking_uri()
    resolved_experiment_name = experiment_name or default_mlflow_experiment_name()
    run_name = f"{dataset['datasetName']}-{dataset['datasetVersion']}"

    mlflow.set_tracking_uri(resolved_tracking_uri)
    client = MlflowClient(tracking_uri=resolved_tracking_uri)

    experiment = client.get_experiment_by_name(resolved_experiment_name)
    if experiment is None:
        artifact_location = _mlflow_artifact_location(resolved_tracking_uri)
        if artifact_location is None:
            experiment_id = client.create_experiment(resolved_experiment_name)
        else:
            experiment_id = client.create_experiment(
                resolved_experiment_name,
                artifact_location=artifact_location,
            )
    else:
        experiment_id = experiment.experiment_id

    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        run_id = run.info.run_id
        mlflow.set_tags(
            {
                "proof_scope": "repo-local",
                "proof_type": report["proofType"],
                "dataset_name": dataset["datasetName"],
                "dataset_version": dataset["datasetVersion"],
                "dataset_owner": dataset.get("owner", "unknown"),
                "langfuse_proven": "false",
                "hosted_mlflow_proven": "false",
            }
        )
        mlflow.log_params(
            {
                "dataset_name": dataset["datasetName"],
                "dataset_version": dataset["datasetVersion"],
                "flow": dataset.get("flow", "unknown"),
                "case_count": len(case_results),
                "proof_type": report["proofType"],
            }
        )

        scores = [float(case["score"]) for case in case_results]
        mlflow.log_metrics(
            {
                "case_count": float(len(case_results)),
                "score_mean": sum(scores) / len(scores),
                "score_min": min(scores),
                "score_max": max(scores),
                "ai_ready_trace_coverage": float(metrics_snapshot["ai_ready_trace_coverage"]),
                "trace_event_total": float(metrics_snapshot["trace_event_total"]),
                "job_success_total": float(metrics_snapshot["job_success_total"]),
                "workspace_action_total": float(metrics_snapshot["workspace_action_total"]),
                "workspace_entry_timing_ms": float(
                    performance_snapshot["workspaceEntryTimingMs"]
                ),
                "api_latency_p95_ms": float(performance_snapshot["apiLatencyP95Ms"]),
                "job_duration_p95_ms": float(performance_snapshot["jobDurationP95Ms"]),
            }
        )

        for case in case_results:
            mlflow.log_metrics(
                {
                    _mlflow_metric_name(case["caseId"], "score"): float(case["score"]),
                    _mlflow_metric_name(case["caseId"], "cost_micros"): float(
                        case["costMicros"]
                    ),
                    _mlflow_metric_name(case["caseId"], "recent_action_count"): float(
                        case["recentActionCount"]
                    ),
                }
            )

        with tempfile.TemporaryDirectory() as artifact_dir_name:
            artifact_dir = Path(artifact_dir_name)
            for file_name, payload in {
                "dataset.json": dataset,
                "report.json": report,
                "performance.json": {
                    "artifactVersion": report["artifactVersion"],
                    "generatedAt": report["generatedAt"],
                    "sourceDataset": dataset["datasetVersion"],
                    "proofType": "repo-local-performance-baseline",
                    **performance_snapshot,
                },
            }.items():
                (artifact_dir / file_name).write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

            mlflow.log_artifacts(str(artifact_dir), artifact_path="runtime-eval")

    run_record = client.get_run(run_id)
    artifact_files = [
        artifact.path for artifact in client.list_artifacts(run_id, path="runtime-eval")
    ]

    return {
        "trackingUri": resolved_tracking_uri,
        "experimentName": resolved_experiment_name,
        "experimentId": experiment_id,
        "runId": run_id,
        "runName": run_name,
        "runStatus": run_record.info.status,
        "artifactUri": run_record.info.artifact_uri,
        "artifactFiles": artifact_files,
    }


# ---------- fixture execution ----------
# Keep the first harness narrow so Sprint 1 proves one repeatable AI-ready flow honestly.
def run_local_eval_fixture(
    dataset_path: Path | None = None,
    *,
    output_path: Path | None = None,
    performance_output_path: Path | None = None,
    mlflow_tracking_uri: str | None = None,
    mlflow_experiment_name: str | None = None,
) -> dict[str, Any]:
    dataset = _load_fixture(dataset_path or default_dataset_path())
    cases = dataset.get("cases", [])
    performance_thresholds = dataset.get("performanceThresholds", {})

    with tempfile.TemporaryDirectory() as temp_dir_name:
        runtime_dir = Path(temp_dir_name)
        with _runtime_dir_override(runtime_dir):
            store = RuntimeStore()
            case_results: list[dict[str, Any]] = []

            for index, case in enumerate(cases, start=1):
                session = store.create_session(case["email"], case["surface"])
                token = session["token"]
                tokens_by_surface = {case["surface"]: token}
                workspace_id = session["workspace"]["workspace"]["workspaceId"]

                for event in case.get("telemetry", []):
                    store.emit_telemetry(
                        surface=event["surface"],
                        name=event["name"],
                        status=event.get("status", "ok"),
                        duration_ms=float(event["durationMs"]),
                        trace_id=event["traceId"],
                        cost_micros=int(event.get("costMicros", 0)),
                        detail=event.get("detail", ""),
                    )

                for action in case.get("actions", []):
                    action_token = tokens_by_surface.get(action["source"])
                    if action_token is None:
                        action_token = store.create_session(
                            case["email"],
                            action["source"],
                        )["token"]
                        tokens_by_surface[action["source"]] = action_token
                    store.record_action(
                        action_token,
                        action["kind"],
                        action["value"],
                        action["source"],
                    )

                job = store.create_job(
                    token,
                    workspace_id,
                    f"fixture-{dataset['datasetVersion']}-{index}",
                )
                finished = store.run_job(job["job_id"])
                bootstrap = store.workspace_bootstrap(session["identity"]["userId"])
                latest_eval = bootstrap["latestEval"]

                case_results.append(
                    {
                        "caseId": case["caseId"],
                        "flow": latest_eval["flow"],
                        "label": latest_eval["label"],
                        "score": latest_eval["score"],
                        "costMicros": latest_eval["cost_micros"],
                        "jobId": finished["job_id"],
                        "jobState": finished["state"],
                        "digest": bootstrap["workspace"]["lastDigest"],
                        "recentActionCount": len(bootstrap["recentActions"]),
                    }
                )

            metrics_snapshot = store.metrics_snapshot()
            store.metrics_text()

    performance_snapshot = {
        "workspaceEntryTimingMs": metrics_snapshot["workspace_entry_timing_ms"],
        "apiLatencyP95Ms": metrics_snapshot["api_latency_p95_ms"],
        "jobDurationP95Ms": metrics_snapshot["job_duration_p95_ms"],
        "traceEventTotal": metrics_snapshot["trace_event_total"],
        "thresholds": performance_thresholds,
        "thresholdStatus": {
            "workspaceEntryTiming": metrics_snapshot["workspace_entry_timing_ms"]
            <= float(performance_thresholds.get("workspaceEntryTimingMsMax", 0) or 0),
            "apiLatencyP95": metrics_snapshot["api_latency_p95_ms"]
            <= float(performance_thresholds.get("apiLatencyP95MsMax", 0) or 0),
            "jobDurationP95": metrics_snapshot["job_duration_p95_ms"]
            <= float(performance_thresholds.get("jobDurationP95MsMax", 0) or 0),
        },
    }

    report = {
        "artifactVersion": "v1",
        "generatedAt": utc_now_iso(),
        "datasetName": dataset["datasetName"],
        "datasetVersion": dataset["datasetVersion"],
        "proofType": "repo-local-runtime-eval",
        "cases": case_results,
        "metricsSnapshot": metrics_snapshot,
        "performanceSnapshot": performance_snapshot,
        "localProof": {
            "confirmed": [
                "synthetic eval dataset is versioned under testing/evals/fixtures",
                (
                    "eval results are machine-readable and reproducible from "
                    "python -m python.evaluation.runtime_eval"
                ),
                (
                    "performance evidence is derived from runtime telemetry "
                    "emitted during the proof run"
                ),
                "AI-ready trace coverage is computed from durable runtime telemetry",
                (
                    "one repo-local MLflow experiment run is written with metrics "
                    "and eval artifacts from the same proof execution"
                ),
                (
                    "collector-routed trace export is proven separately through "
                    "the compose-backed observability path"
                ),
            ],
            "notConfirmedHere": [
                (
                    "This harness does not by itself prove collector export, because "
                    "it runs against an isolated runtime store"
                ),
                (
                    "Langfuse trace ingestion and online scores still require "
                    "a reachable Langfuse deployment and credentials"
                ),
                (
                    "This harness proves only repo-local MLflow tracking to the "
                    "configured local URI, not hosted or team-shared MLflow durability"
                ),
                (
                    "GitHub rulesets required checks and hosted scanners still "
                    "require GitHub-side confirmation"
                ),
            ],
        },
    }

    report["mlflow"] = _write_mlflow_run(
        dataset,
        case_results,
        metrics_snapshot,
        performance_snapshot,
        report,
        tracking_uri=mlflow_tracking_uri,
        experiment_name=mlflow_experiment_name,
    )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if performance_output_path is not None:
        performance_output_path.parent.mkdir(parents=True, exist_ok=True)
        performance_output_path.write_text(
            json.dumps(
                {
                    "artifactVersion": report["artifactVersion"],
                    "generatedAt": report["generatedAt"],
                    "sourceDataset": dataset["datasetVersion"],
                    "proofType": "repo-local-performance-baseline",
                    **performance_snapshot,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    return report


# ---------- cli ----------
# Keep one CLI so operators can regenerate tracked proof artifacts without custom scripts.
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate local Sprint 1 eval and performance proof"
    )
    parser.add_argument("--dataset", type=Path, default=default_dataset_path())
    parser.add_argument("--output", type=Path, default=default_eval_output_path())
    parser.add_argument(
        "--performance-output",
        type=Path,
        default=default_performance_output_path(),
    )
    parser.add_argument(
        "--mlflow-tracking-uri",
        default=default_mlflow_tracking_uri(),
    )
    parser.add_argument(
        "--mlflow-experiment-name",
        default=default_mlflow_experiment_name(),
    )
    args = parser.parse_args()
    run_local_eval_fixture(
        args.dataset,
        output_path=args.output,
        performance_output_path=args.performance_output,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
        mlflow_experiment_name=args.mlflow_experiment_name,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

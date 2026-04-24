"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the first local evaluation harness and export versioned proof JSON

- Later Extension Points:
    --> swap local proof runs for Langfuse and MLflow-backed adapters when hosted infra is durable

- Role:
    --> executes a synthetic Sprint 1 runtime dataset through the real runtime store
    --> exports machine-readable local eval and performance proof from actual runtime data
    --> writes experiment evidence to MLflow when available and to a
        repo-owned local ledger otherwise

- Exports:
    --> `read_runtime_baseline()`
    --> `run_local_eval_fixture()`
    --> `verify_experiment_run()`

- Consumed By:
    --> tests operator scripts and Sprint 1 proof generation for
        `testing/evals/` and `testing/performance/`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

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
    return "sqlite:///build/mlflow/mlflow.db"


def default_mlflow_experiment_name() -> str:
    return os.environ.get("EXP_NAME", "").strip() or os.environ.get(
        "SYNAWAVE_MLFLOW_EXPERIMENT",
        "synaweave-sprint1-runtime-eval-local",
    )


def _tracking_db_path(tracking_uri: str) -> Path:
    if not tracking_uri.startswith("sqlite:///"):
        raise RuntimeError(
            "This bounded Sprint 1 proof requires a sqlite:/// tracking URI "
            "for local experiment evidence"
        )
    return Path(tracking_uri.removeprefix("sqlite:///"))


def _tracking_artifact_root(tracking_uri: str) -> Path:
    artifact_root = _tracking_db_path(tracking_uri).parent / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root


def _portable_path_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        return str(path.resolve())


def _portable_tracking_uri(tracking_uri: str) -> str:
    if not tracking_uri.startswith("sqlite:///"):
        return tracking_uri

    db_path = Path(tracking_uri.removeprefix("sqlite:///"))
    if db_path.is_absolute():
        return tracking_uri
    return f"sqlite:///{db_path.as_posix()}"


def _portable_artifact_ref(path: Path) -> str:
    return _portable_path_ref(path)


def _required_str_attr(value: object, attr_name: str) -> str:
    attr_value = getattr(value, attr_name, None)
    if not isinstance(attr_value, str):
        raise RuntimeError(f"MLflow object is missing string attribute '{attr_name}'")
    return attr_value


def _list_artifact_paths(client: object, run_id: str) -> list[str]:
    list_artifacts = getattr(client, "list_artifacts", None)
    if not callable(list_artifacts):
        raise RuntimeError("MLflow client does not expose list_artifacts")

    artifact_entries_obj = list_artifacts(run_id, path="runtime-eval")
    if not isinstance(artifact_entries_obj, list):
        raise RuntimeError("MLflow client returned non-list artifact entries")
    artifact_entries = cast(list[object], artifact_entries_obj)

    artifact_paths: list[str] = []
    for artifact in artifact_entries:
        artifact_paths.append(_required_str_attr(artifact, "path"))
    return artifact_paths


def _experiment_ledger_connection(tracking_uri: str) -> sqlite3.Connection:
    db_path = _tracking_db_path(tracking_uri)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        "\n".join(
            [
                "create table if not exists sw_experiments (",
                "    experiment_id text primary key,",
                "    experiment_name text not null unique",
                ");",
                "",
                "create table if not exists sw_runs (",
                "    run_id text primary key,",
                "    experiment_id text not null,",
                "    run_name text not null,",
                "    status text not null,",
                "    artifact_uri text not null,",
                "    tracking_backend text not null,",
                "    created_at text not null,",
                "    foreign key (experiment_id) references sw_experiments(experiment_id)",
                ");",
                "",
                "create table if not exists sw_run_metrics (",
                "    run_id text not null,",
                "    metric_key text not null,",
                "    metric_value real not null,",
                "    primary key (run_id, metric_key),",
                "    foreign key (run_id) references sw_runs(run_id)",
                ");",
                "",
                "create table if not exists sw_run_artifacts (",
                "    run_id text not null,",
                "    artifact_path text not null,",
                "    primary key (run_id, artifact_path),",
                "    foreign key (run_id) references sw_runs(run_id)",
                ");",
            ]
        )
    )
    connection.commit()
    return connection


def _metric_bundle(
    case_results: list[dict[str, Any]],
    metrics_snapshot: dict[str, Any],
    performance_snapshot: dict[str, Any],
) -> dict[str, float]:
    scores = [float(case["score"]) for case in case_results]
    bundle = {
        "case_count": float(len(case_results)),
        "score_mean": sum(scores) / len(scores),
        "score_min": min(scores),
        "score_max": max(scores),
        "ai_ready_trace_coverage": float(metrics_snapshot["ai_ready_trace_coverage"]),
        "trace_event_total": float(metrics_snapshot["trace_event_total"]),
        "job_success_total": float(metrics_snapshot["job_success_total"]),
        "workspace_action_total": float(metrics_snapshot["workspace_action_total"]),
        "workspace_entry_timing_ms": float(performance_snapshot["workspaceEntryTimingMs"]),
        "api_latency_p95_ms": float(performance_snapshot["apiLatencyP95Ms"]),
        "job_duration_p95_ms": float(performance_snapshot["jobDurationP95Ms"]),
    }

    for case in case_results:
        bundle[_mlflow_metric_name(case["caseId"], "score")] = float(case["score"])
        bundle[_mlflow_metric_name(case["caseId"], "cost_micros")] = float(case["costMicros"])
        bundle[_mlflow_metric_name(case["caseId"], "recent_action_count")] = float(
            case["recentActionCount"]
        )

    return bundle


# ---------- baseline reader ----------
# Keep the reader defensive so early tests can call it before the first baseline is written.
def read_runtime_baseline() -> dict[str, Any]:
    path = Path(
        os.environ.get("SW_RUN_DIR", "").strip()
        or os.environ.get("SYNAWAVE_RUNTIME_DIR", "").strip()
    ).expanduser()
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
    previous_sw_run_dir = os.environ.get("SW_RUN_DIR")
    previous_legacy_runtime_dir = os.environ.get("SYNAWAVE_RUNTIME_DIR")
    os.environ["SW_RUN_DIR"] = str(runtime_dir)
    os.environ["SYNAWAVE_RUNTIME_DIR"] = str(runtime_dir)
    try:
        yield
    finally:
        if previous_sw_run_dir is None:
            os.environ.pop("SW_RUN_DIR", None)
        else:
            os.environ["SW_RUN_DIR"] = previous_sw_run_dir

        if previous_legacy_runtime_dir is None:
            os.environ.pop("SYNAWAVE_RUNTIME_DIR", None)
        else:
            os.environ["SYNAWAVE_RUNTIME_DIR"] = previous_legacy_runtime_dir


# ---------- fixture loading ----------
# Keep fixture parsing explicit so failures stay readable during local proof regeneration.
def _load_fixture(dataset_path: Path) -> dict[str, Any]:
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def _mlflow_metric_name(case_id: str, field: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", case_id.lower()).strip("_")
    return f"case_{slug}_{field}"


def _mlflow_artifact_location(tracking_uri: str) -> str | None:
    artifact_root = _tracking_artifact_root(tracking_uri)
    return artifact_root.resolve().as_uri()


def _write_local_experiment_ledger(
    dataset: dict[str, Any],
    case_results: list[dict[str, Any]],
    metrics_snapshot: dict[str, Any],
    performance_snapshot: dict[str, Any],
    report: dict[str, Any],
    *,
    tracking_uri: str,
    experiment_name: str,
) -> dict[str, Any]:
    run_id = uuid.uuid4().hex
    run_name = f"{dataset['datasetName']}-{dataset['datasetVersion']}"
    created_at = utc_now_iso()
    artifact_root = _tracking_artifact_root(tracking_uri)
    artifact_dir = artifact_root / run_id / "runtime-eval"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    artifact_payloads = {
        "dataset.json": dataset,
        "report.json": report,
        "performance.json": {
            "artifactVersion": report["artifactVersion"],
            "generatedAt": report["generatedAt"],
            "sourceDataset": dataset["datasetVersion"],
            "proofType": "repo-local-performance-baseline",
            **performance_snapshot,
        },
    }

    artifact_files: list[str] = []
    for file_name, payload in artifact_payloads.items():
        artifact_path = artifact_dir / file_name
        artifact_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifact_files.append(f"runtime-eval/{file_name}")

    connection = _experiment_ledger_connection(tracking_uri)
    try:
        row = connection.execute(
            "select experiment_id from sw_experiments where experiment_name = ?",
            (experiment_name,),
        ).fetchone()
        experiment_id = (
            str(row["experiment_id"])
            if row is not None
            else f"exp-{uuid.uuid4().hex[:12]}"
        )
        if row is None:
            connection.execute(
                "insert into sw_experiments (experiment_id, experiment_name) values (?, ?)",
                (experiment_id, experiment_name),
            )

        connection.execute(
            "insert into sw_runs ("
            "run_id, experiment_id, run_name, status, artifact_uri, "
            "tracking_backend, created_at"
            ") values (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                experiment_id,
                run_name,
                "FINISHED",
                _portable_artifact_ref(artifact_dir),
                "repo-local-ledger",
                created_at,
            ),
        )

        for metric_key, metric_value in _metric_bundle(
            case_results,
            metrics_snapshot,
            performance_snapshot,
        ).items():
            connection.execute(
                "insert or replace into sw_run_metrics ("
                "run_id, metric_key, metric_value"
                ") values (?, ?, ?)",
                (run_id, metric_key, float(metric_value)),
            )

        for artifact_file in artifact_files:
            connection.execute(
                "insert or replace into sw_run_artifacts (run_id, artifact_path) values (?, ?)",
                (run_id, artifact_file),
            )

        connection.commit()
    finally:
        connection.close()

    return {
        "trackingUri": _portable_tracking_uri(tracking_uri),
        "experimentName": experiment_name,
        "experimentId": experiment_id,
        "runId": run_id,
        "runName": run_name,
        "runStatus": "FINISHED",
        "artifactUri": _portable_artifact_ref(artifact_dir),
        "artifactFiles": artifact_files,
        "trackingBackend": "repo-local-ledger",
    }


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
    resolved_tracking_uri = tracking_uri or default_mlflow_tracking_uri()
    resolved_experiment_name = experiment_name or default_mlflow_experiment_name()
    run_name = f"{dataset['datasetName']}-{dataset['datasetVersion']}"

    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ModuleNotFoundError:
        return _write_local_experiment_ledger(
            dataset,
            case_results,
            metrics_snapshot,
            performance_snapshot,
            report,
            tracking_uri=resolved_tracking_uri,
            experiment_name=resolved_experiment_name,
        )

    try:
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
            experiment_id = _required_str_attr(experiment, "experiment_id")

        run_id: str | None = None
        with mlflow.start_run(experiment_id=str(experiment_id), run_name=run_name) as run:
            run_id = _required_str_attr(run.info, "run_id")
            _ = mlflow.set_tags(
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
            _ = mlflow.log_params(
                {
                    "dataset_name": dataset["datasetName"],
                    "dataset_version": dataset["datasetVersion"],
                    "flow": dataset.get("flow", "unknown"),
                    "case_count": len(case_results),
                    "proof_type": report["proofType"],
                }
            )
            _ = mlflow.log_metrics(
                _metric_bundle(
                    case_results,
                    metrics_snapshot,
                    performance_snapshot,
                )
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
                    _ = (artifact_dir / file_name).write_text(
                        json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )

                _ = mlflow.log_artifacts(str(artifact_dir), artifact_path="runtime-eval")

        if run_id is None:
            raise RuntimeError("MLflow run did not expose a run id")

        run_record = client.get_run(run_id)
        artifact_files = _list_artifact_paths(client, run_id)
        run_status = _required_str_attr(run_record.info, "status")
        artifact_uri = _required_str_attr(run_record.info, "artifact_uri")

        return {
            "trackingUri": resolved_tracking_uri,
            "experimentName": resolved_experiment_name,
            "experimentId": experiment_id,
            "runId": run_id,
            "runName": run_name,
            "runStatus": run_status,
            "artifactUri": artifact_uri,
            "artifactFiles": artifact_files,
            "trackingBackend": "mlflow",
        }
    except Exception:
        if not resolved_tracking_uri.startswith("sqlite:///"):
            raise
        return _write_local_experiment_ledger(
            dataset,
            case_results,
            metrics_snapshot,
            performance_snapshot,
            report,
            tracking_uri=resolved_tracking_uri,
            experiment_name=resolved_experiment_name,
        )


def verify_experiment_run(
    *,
    tracking_uri: str,
    experiment_name: str,
    run_id: str | None = None,
) -> dict[str, Any]:
    required_artifacts = {
        "runtime-eval/dataset.json",
        "runtime-eval/performance.json",
        "runtime-eval/report.json",
    }
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

    try:
        from mlflow.tracking import MlflowClient
    except ModuleNotFoundError:
        connection = _experiment_ledger_connection(tracking_uri)
        try:
            experiment_row = connection.execute(
                "select experiment_id from sw_experiments where experiment_name = ?",
                (experiment_name,),
            ).fetchone()
            if experiment_row is None:
                raise RuntimeError(
                    "Experiment ledger entry "
                    f"'{experiment_name}' was not found at {tracking_uri}"
                )
            experiment_id = str(experiment_row["experiment_id"])

            if run_id is None:
                run_row = connection.execute(
                    "select * from sw_runs where experiment_id = ? "
                    "order by created_at desc limit 1",
                    (experiment_id,),
                ).fetchone()
                if run_row is None:
                    raise RuntimeError(
                        f"Experiment ledger '{experiment_name}' has no runs to verify"
                    )
            else:
                run_row = connection.execute(
                    "select * from sw_runs where run_id = ?",
                    (run_id,),
                ).fetchone()
                if run_row is None:
                    raise RuntimeError(f"Experiment run '{run_id}' was not found")

            metric_rows = connection.execute(
                "select metric_key, metric_value from sw_run_metrics where run_id = ?",
                (str(run_row["run_id"]),),
            ).fetchall()
            artifact_rows = connection.execute(
                "select artifact_path from sw_run_artifacts where run_id = ?",
                (str(run_row["run_id"]),),
            ).fetchall()
        finally:
            connection.close()

        metric_keys = {str(row["metric_key"]) for row in metric_rows}
        artifact_files = {str(row["artifact_path"]) for row in artifact_rows}
        missing_artifacts = sorted(required_artifacts - artifact_files)
        if missing_artifacts:
            raise RuntimeError(
                "Experiment ledger run is missing expected artifacts: "
                + ", ".join(missing_artifacts)
            )

        missing_metrics = sorted(required_metrics - metric_keys)
        if missing_metrics:
            raise RuntimeError(
                "Experiment ledger run is missing expected metrics: "
                + ", ".join(missing_metrics)
            )

        return {
            "trackingUri": tracking_uri,
            "experimentName": experiment_name,
            "experimentId": experiment_id,
            "runId": str(run_row["run_id"]),
            "runName": str(run_row["run_name"]),
            "runStatus": str(run_row["status"]),
            "artifactFiles": sorted(artifact_files),
            "metricKeys": sorted(metric_keys),
            "trackingBackend": str(run_row["tracking_backend"]),
        }

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(experiment_name)

    if experiment is None:
        raise RuntimeError(
            f"MLflow experiment '{experiment_name}' was not found at {tracking_uri}"
        )

    if run_id is None:
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["attributes.start_time DESC"],
            max_results=1,
        )
        if not runs:
            raise RuntimeError(f"MLflow experiment '{experiment_name}' has no runs to verify")
        run = runs[0]
    else:
        run = client.get_run(run_id)

    artifact_files = {
        artifact.path for artifact in client.list_artifacts(run.info.run_id, path="runtime-eval")
    }
    missing_artifacts = sorted(required_artifacts - artifact_files)
    if missing_artifacts:
        raise RuntimeError(
            "MLflow run is missing expected artifacts: " + ", ".join(missing_artifacts)
        )

    missing_metrics = sorted(required_metrics - set(run.data.metrics))
    if missing_metrics:
        raise RuntimeError(
            "MLflow run is missing expected metrics: " + ", ".join(missing_metrics)
        )

    return {
        "trackingUri": tracking_uri,
        "experimentName": experiment_name,
        "experimentId": experiment.experiment_id,
        "runId": run.info.run_id,
        "runName": run.data.tags.get("mlflow.runName", ""),
        "runStatus": run.info.status,
        "artifactFiles": sorted(artifact_files),
        "metricKeys": sorted(run.data.metrics),
        "trackingBackend": "mlflow",
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
                    "one repo-local experiment run is written with metrics "
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
                    "This harness proves repo-local experiment durability through "
                    "either MLflow or the local tracking-ledger fallback, "
                    "not team-shared operations"
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

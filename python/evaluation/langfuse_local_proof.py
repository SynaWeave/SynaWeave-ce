"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  send one real Sprint 1 trace and score proof into local Langfuse

- Later Extension Points:
    --> widen this proof only when more AI-facing runtime flows become truthful targets

- Role:
    --> reuses the Sprint 1 runtime-eval fixture to derive one honest score source
    --> writes traces and scores into a reachable local Langfuse service and verifies queryability

- Exports:
    --> `run_local_langfuse_proof()`

- Consumed By:
    --> operators proving the bounded Sprint 1 D3 Langfuse trace-plus-score path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from python.common.runtime_time import utc_now_iso
from python.evaluation.runtime_eval import default_dataset_path, run_local_eval_fixture


def default_langfuse_base_url() -> str:
    return os.environ.get("LANGFUSE_BASE_URL", "http://127.0.0.1:3030")


def default_langfuse_public_key() -> str:
    return os.environ.get("LANGFUSE_PUBLIC_KEY", "synaweave-local-public-key")


def default_langfuse_secret_key() -> str:
    return os.environ.get("LANGFUSE_SECRET_KEY", "synaweave-local-secret-key")


def default_langfuse_output_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "testing"
        / "evals"
        / "artifacts"
        / "runtime-digest-density.langfuse-local-proof.v1.json"
    )


def _new_langfuse_client(*, base_url: str, public_key: str, secret_key: str):
    try:
        from langfuse import Langfuse
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Langfuse SDK is not installed. Install the runtime extras or "
            "pass a client_factory for bounded local proof runs."
        ) from exc

    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        base_url=base_url,
        environment="local",
        release="sprint-1-d3-local-proof",
    )


def _queryable_score_value(score_response: Any) -> float | str | None:
    data = getattr(score_response, "data", [])
    if not data:
        return None
    return getattr(data[0], "value", None)


def _wait_for_langfuse_auth(
    client: Any,
    *,
    base_url: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            if client.auth_check():
                return
            last_error = "auth check returned false"
        except Exception as exc:  # pragma: no cover - exercised in live verification
            last_error = str(exc)
        time.sleep(poll_interval_seconds)

    raise RuntimeError(
        (
            f"Langfuse auth check failed for {base_url}. "
            "Start the local Langfuse stack or set valid credentials."
        )
        + (f" Last error: {last_error}" if last_error else "")
    )


def _wait_for_langfuse_verification(
    client: Any,
    *,
    ingested_cases: list[dict[str, Any]],
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while time.monotonic() < deadline:
        verified_cases: list[dict[str, Any]] = []
        pending = False

        for case in ingested_cases:
            try:
                trace = client.api.trace.get(case["traceId"])
                score_response = client.api.scores.get_many(
                    trace_id=case["traceId"],
                    name=case["scoreName"],
                    observation_id=case["observationId"],
                )
            except Exception as exc:  # pragma: no cover - exercised in live verification
                last_error = str(exc)
                pending = True
                break

            score_value = _queryable_score_value(score_response)
            if score_value is None:
                pending = True
                break

            verified_cases.append(
                {
                    **case,
                    "queriedTraceName": getattr(trace, "name", ""),
                    "queriedScoreValue": score_value,
                }
            )

        if not pending and len(verified_cases) == len(ingested_cases):
            return verified_cases

        time.sleep(poll_interval_seconds)

    raise RuntimeError(
        "Timed out waiting for Langfuse to return the ingested Sprint 1 traces and scores"
        + (f": {last_error}" if last_error else "")
    )


def run_local_langfuse_proof(
    dataset_path: Path | None = None,
    *,
    base_url: str | None = None,
    public_key: str | None = None,
    secret_key: str | None = None,
    output_path: Path | None = None,
    verification_timeout_seconds: float = 45.0,
    poll_interval_seconds: float = 2.0,
    client_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    runtime_report = run_local_eval_fixture(dataset_path or default_dataset_path())
    resolved_base_url = base_url or default_langfuse_base_url()
    resolved_public_key = public_key or default_langfuse_public_key()
    resolved_secret_key = secret_key or default_langfuse_secret_key()
    proof_run_id = f"sprint1-langfuse-{uuid.uuid4().hex[:12]}"
    langfuse_client_factory = client_factory or _new_langfuse_client
    client = langfuse_client_factory(
        base_url=resolved_base_url,
        public_key=resolved_public_key,
        secret_key=resolved_secret_key,
    )

    _wait_for_langfuse_auth(
        client,
        base_url=resolved_base_url,
        timeout_seconds=verification_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )

    ingested_cases: list[dict[str, Any]] = []
    for case in runtime_report["cases"]:
        metadata = {
            "proofRunId": proof_run_id,
            "caseId": case["caseId"],
            "datasetName": runtime_report["datasetName"],
            "datasetVersion": runtime_report["datasetVersion"],
            "jobId": case["jobId"],
            "jobState": case["jobState"],
            "costMicros": case["costMicros"],
        }
        trace_id = client.create_trace_id(seed=f"{proof_run_id}-{case['caseId']}")
        event = client.create_event(
            trace_context={"trace_id": trace_id},
            name=case["flow"],
            input={
                "caseId": case["caseId"],
                "label": case["label"],
                "recentActionCount": case["recentActionCount"],
            },
            output={
                "digest": case["digest"],
                "jobId": case["jobId"],
                "jobState": case["jobState"],
            },
            metadata=metadata,
            version=runtime_report["datasetVersion"],
        )
        client.create_score(
            name=case["label"],
            value=float(case["score"]),
            trace_id=trace_id,
            observation_id=event.id,
            data_type="NUMERIC",
            comment="Sprint 1 runtime-store digest score routed through local Langfuse",
            metadata=metadata,
        )
        ingested_cases.append(
            {
                "caseId": case["caseId"],
                "traceId": trace_id,
                "observationId": event.id,
                "traceName": case["flow"],
                "scoreName": case["label"],
                "scoreValue": case["score"],
            }
        )

    client.flush()
    client.shutdown()
    verified_cases = _wait_for_langfuse_verification(
        client,
        ingested_cases=ingested_cases,
        timeout_seconds=verification_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )

    report = {
        "artifactVersion": "v1",
        "generatedAt": utc_now_iso(),
        "datasetName": runtime_report["datasetName"],
        "datasetVersion": runtime_report["datasetVersion"],
        "proofType": "local-langfuse-trace-score-proof",
        "langfuseBaseUrl": resolved_base_url,
        "proofRunId": proof_run_id,
        "traceCount": len(verified_cases),
        "scoreCount": len(verified_cases),
        "cases": verified_cases,
        "metricsSnapshot": runtime_report["metricsSnapshot"],
        "performanceSnapshot": runtime_report["performanceSnapshot"],
        "localProof": {
            "confirmed": [
                "local Langfuse authentication succeeded against a reachable service",
                "Sprint 1 runtime-eval cases created queryable Langfuse traces",
                "each ingested Sprint 1 trace has a queryable numeric score in Langfuse",
            ],
            "notConfirmedHere": [
                (
                    "this bounded proof does not instrument the live web extension "
                    "API and ingest runtimes end to end"
                ),
                (
                    "this proof does not claim hosted Langfuse durability shared-team "
                    "operations or production retention"
                ),
                "MLflow offline experiment proof still requires its own reachable tracking backend",
            ],
        },
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a bounded local Langfuse trace and score proof for Sprint 1"
    )
    parser.add_argument("--dataset", type=Path, default=default_dataset_path())
    parser.add_argument("--base-url", default=default_langfuse_base_url())
    parser.add_argument("--public-key", default=default_langfuse_public_key())
    parser.add_argument("--secret-key", default=default_langfuse_secret_key())
    parser.add_argument("--output", type=Path, default=default_langfuse_output_path())
    parser.add_argument("--verification-timeout-seconds", type=float, default=45.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    args = parser.parse_args()

    report = run_local_langfuse_proof(
        args.dataset,
        base_url=args.base_url,
        public_key=args.public_key,
        secret_key=args.secret_key,
        output_path=args.output,
        verification_timeout_seconds=args.verification_timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

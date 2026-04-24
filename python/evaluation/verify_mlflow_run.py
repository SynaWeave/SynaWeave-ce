"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  confirm the local runtime eval produced a real experiment-tracking run

- Later Extension Points:
    --> widen artifact and metric assertions only when the runtime eval proof expands

- Role:
    --> checks the configured local experiment backend for one runtime-eval run
    --> supports real MLflow when installed and the repo-owned local ledger fallback when it is not

- Exports:
    --> `verify_latest_runtime_eval_run()`

- Consumed By:
    --> operator verification and unit tests for the Sprint 1 local experiment proof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import json
from typing import Any

from python.evaluation.runtime_eval import (
    default_mlflow_experiment_name,
    default_mlflow_tracking_uri,
    verify_experiment_run,
)


def verify_latest_runtime_eval_run(
    *,
    tracking_uri: str | None = None,
    experiment_name: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    resolved_tracking_uri = tracking_uri or default_mlflow_tracking_uri()
    resolved_experiment_name = experiment_name or default_mlflow_experiment_name()
    return verify_experiment_run(
        tracking_uri=resolved_tracking_uri,
        experiment_name=resolved_experiment_name,
        run_id=run_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the latest local runtime-eval experiment run"
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

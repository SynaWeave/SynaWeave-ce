"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the bounded local Langfuse proof stays query-backed and honest

- Later Extension Points:
    --> widen assertions only when the proof writes richer Langfuse metadata on purpose

- Role:
    --> guards the local Langfuse proof report shape and auth failure behavior
    --> keeps the Sprint 1 proof path small while still testable without a live service

- Exports:
    --> unittest module only

- Consumed By:
    --> local and CI test runs covering the bounded Langfuse proof helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from python.evaluation.langfuse_local_proof import run_local_langfuse_proof


class _FakeLangfuseClient:
    def __init__(self, *, auth_ok: bool = True) -> None:
        self.auth_ok = auth_ok
        self.trace_index = 0
        self._scores: dict[tuple[str, str], float] = {}
        self._trace_names: dict[str, str] = {}
        self.api = SimpleNamespace(
            trace=SimpleNamespace(get=self._get_trace),
            scores=SimpleNamespace(get_many=self._get_scores),
        )

    def auth_check(self) -> bool:
        return self.auth_ok

    def create_trace_id(self, *, seed: str | None = None) -> str:
        self.trace_index += 1
        suffix = seed or str(self.trace_index)
        return f"trace-{suffix}"

    def create_event(self, *, trace_context: dict[str, str], name: str, **_: object):
        trace_id = trace_context["trace_id"]
        observation_id = f"obs-{self.trace_index}"
        self._trace_names[trace_id] = name
        return SimpleNamespace(id=observation_id, trace_id=trace_id)

    def create_score(self, *, trace_id: str, name: str, value: float, **_: object) -> None:
        self._scores[(trace_id, name)] = value

    def flush(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def _get_trace(self, trace_id: str):
        return SimpleNamespace(name=self._trace_names[trace_id])

    def _get_scores(self, *, trace_id: str, name: str, **_: object):
        score_value = self._scores.get((trace_id, name))
        if score_value is None:
            return SimpleNamespace(data=[])
        return SimpleNamespace(data=[SimpleNamespace(value=score_value)])


class LangfuseLocalProofTest(unittest.TestCase):
    def test_langfuse_local_proof_generates_query_backed_artifact(self) -> None:
        dataset_path = Path("testing/evals/fixtures/runtime-digest-density.v1.json")

        with tempfile.TemporaryDirectory() as temp_dir_name:
            output_path = Path(temp_dir_name) / "langfuse-proof.json"

            report = run_local_langfuse_proof(
                dataset_path,
                output_path=output_path,
                client_factory=lambda **_: _FakeLangfuseClient(),
                poll_interval_seconds=0.01,
            )

            self.assertEqual(report["proofType"], "local-langfuse-trace-score-proof")
            self.assertEqual(report["traceCount"], 2)
            self.assertEqual(report["scoreCount"], 2)
            self.assertEqual(len(report["cases"]), 2)
            self.assertTrue(output_path.exists())
            self.assertTrue(all(case["queriedTraceName"] for case in report["cases"]))

    def test_langfuse_local_proof_requires_successful_auth(self) -> None:
        dataset_path = Path("testing/evals/fixtures/runtime-digest-density.v1.json")

        with self.assertRaises(RuntimeError):
            run_local_langfuse_proof(
                dataset_path,
                client_factory=lambda **_: _FakeLangfuseClient(auth_ok=False),
                verification_timeout_seconds=0.01,
                poll_interval_seconds=0.01,
            )


if __name__ == "__main__":
    unittest.main()

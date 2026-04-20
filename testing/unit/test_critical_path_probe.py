"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the observability probe rejects stale or unrelated replay evidence

- Later Extension Points:
    --> add deeper replay assertions only when the probe owns more than freshness checks

- Role:
    --> proves the critical-path probe demands replay-linked rows from the current replay
    --> keeps stale local artifacts from satisfying Sprint 1 observability evidence checks

- Exports:
    --> unittest module only

- Consumed By:
    --> focused unit and repository verification runs guarding the probe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.observability.critical_path_probe import (
    snapshot_file_evidence,
    wait_for_fresh_jsonl_evidence,
)


class CriticalPathProbeTest(unittest.TestCase):
    def test_wait_for_fresh_jsonl_evidence_requires_matching_replay_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            evidence_path = Path(temp_dir_name) / "measurements.jsonl"
            evidence_path.write_text('{"old": true}\n', encoding="utf-8")
            snapshot = snapshot_file_evidence(evidence_path)

            evidence_path.write_text(
                '{"old": true}\n'
                '{"latest_job_id": "job_123", "latest_job_trace_id": "trc_job_123"}\n',
                encoding="utf-8",
            )

            self.assertEqual(
                wait_for_fresh_jsonl_evidence(
                    snapshot,
                    timeout_seconds=0.01,
                    label="metrics history",
                    row_matches=lambda row: row.get("latest_job_id") == "job_123"
                    and row.get("latest_job_trace_id") == "trc_job_123",
                )["latest_job_id"],
                "job_123",
            )

    def test_wait_for_fresh_jsonl_evidence_rejects_unrelated_growth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            evidence_path = Path(temp_dir_name) / "backend-logs.jsonl"
            evidence_path.write_text('{"old": true}\n', encoding="utf-8")
            snapshot = snapshot_file_evidence(evidence_path)
            evidence_path.write_text('{"old": true}\n{"job_id": "job_other"}\n', encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "replay-linked evidence"):
                wait_for_fresh_jsonl_evidence(
                    snapshot,
                    timeout_seconds=0.01,
                    label="backend logs",
                    row_matches=lambda row: row.get("job_id") == "job_123",
                )


if __name__ == "__main__":
    unittest.main()

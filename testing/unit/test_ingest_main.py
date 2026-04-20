"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the ingest entrypoint flushes tracing before exit

- Later Extension Points:
    --> widen ingest entrypoint checks only when the worker owns more runtime coordination logic

- Role:
    --> proves the short-lived ingest CLI forces a final trace flush on success and failure
    --> keeps the compose-backed collector proof from depending on batch timing luck alone

- Exports:
    --> unittest module only

- Consumed By:
    --> focused unit runs guarding Sprint 1 ingest observability behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import unittest
from unittest.mock import patch

from apps.ingest import main as ingest_main


class IngestMainTest(unittest.TestCase):
    def test_main_flushes_tracing_after_success(self) -> None:
        with (
            patch("apps.ingest.main.parse_args") as parse_args,
            patch(
                "apps.ingest.main.run_job",
                return_value={"job_id": "job_ok", "state": "succeeded"},
            ),
            patch("apps.ingest.main.flush_tracing") as flush_tracing,
            patch("builtins.print"),
        ):
            parse_args.return_value.job_id = "job_ok"

            exit_code = ingest_main.main()

        self.assertEqual(exit_code, 0)
        flush_tracing.assert_called_once_with()

    def test_main_flushes_tracing_after_job_error(self) -> None:
        from python.common.runtime_store import JobExecutionError

        with (
            patch("apps.ingest.main.parse_args") as parse_args,
            patch(
                "apps.ingest.main.run_job",
                side_effect=JobExecutionError("job_fail", "failed", "RuntimeError: odd exit"),
            ),
            patch(
                "apps.ingest.main.store.job_view",
                return_value={"job_id": "job_fail", "state": "failed"},
            ),
            patch("apps.ingest.main.flush_tracing") as flush_tracing,
            patch("builtins.print"),
        ):
            parse_args.return_value.job_id = "job_fail"

            exit_code = ingest_main.main()

        self.assertEqual(exit_code, 1)
        flush_tracing.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

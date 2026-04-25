"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  provide tiny shared time helpers for runtime rows telemetry and proof baselines

- Later Extension Points:
    --> add richer clock seams only when deterministic time injection becomes a wider shared concern

- Role:
    --> keeps runtime timestamps consistently UTC and ISO-shaped
    --> avoids repeating ad hoc time formatting logic across API ingest and test utilities

- Exports:
    --> `utc_now_iso()`
    --> `utc_now_epoch_ms()`

- Consumed By:
    --> runtime storage telemetry job logic and tests that depend on stable timestamp formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

from datetime import UTC, datetime


# ---------- utc helpers ----------
# Keep timestamp formatting centralized so rows and responses stay aligned everywhere.
def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_now_epoch_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)

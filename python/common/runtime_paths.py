"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  centralize deterministic local runtime state paths for the first proof baseline

- Later Extension Points:
    --> widen path helpers only when later runtimes gain separate state homes or artifact classes

- Role:
    --> keeps local runtime state under one ignored build directory
    --> prevents API ingest and tests from guessing at independent local storage paths

- Exports:
    --> `repo_root()`
    --> `runtime_dir()`
    --> `observability_dir()`
    --> `db_path()`
    --> `trace_path()`
    --> `metrics_path()`
    --> `baseline_path()`
    --> `collector_trace_export_path()`

- Consumed By:
    --> API ingest telemetry and runtime tests that need one deterministic local state home
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import os
from pathlib import Path


# ---------- repo path helpers ----------
# Walk back from this module so every runtime surface shares one repo-relative state location.
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ---------- runtime dir ----------
# Keep local durable state under build so tracked source paths stay clean and gitignored by default.
def runtime_dir() -> Path:
    override = os.environ.get("SYNAWEAVE_RUNTIME_DIR", "").strip()
    path = Path(override) if override else repo_root() / "build" / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------- observability dir ----------
# Keep collector-side artifacts separated from app-owned runtime state while staying repo-local.
def observability_dir() -> Path:
    path = repo_root() / "build" / "observability"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------- durable state files ----------
# Keep filenames semantic so operators can inspect the proof baseline without a legend lookup.
def db_path() -> Path:
    return runtime_dir() / "synaweave.sqlite3"


def trace_path() -> Path:
    return runtime_dir() / "traces.jsonl"


def metrics_path() -> Path:
    return runtime_dir() / "metrics.json"


def baseline_path() -> Path:
    return runtime_dir() / "baseline.json"


def collector_trace_export_path() -> Path:
    return observability_dir() / "collector-traces.json"

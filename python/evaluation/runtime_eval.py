"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  expose a tiny evaluation reader for the first AI-ready baseline snapshot

- Later Extension Points:
    --> replace the local reader with richer offline evaluation loaders when MLflow is durable

- Role:
    --> reads the current local baseline snapshot for human review and lightweight tests
    --> keeps the first AI-ready proof artifact accessible outside the API runtime itself

- Exports:
    --> `read_runtime_baseline()`

- Consumed By:
    --> tests operator scripts and future evaluation runtimes that need the local baseline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
from typing import Any

from python.common.runtime_paths import baseline_path


# ---------- baseline reader ----------
# Keep the reader defensive so early tests can call it before the first baseline is written.
def read_runtime_baseline() -> dict[str, Any]:
    path = baseline_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

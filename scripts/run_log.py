"""Append-only run log used by ingest and dbt wrappers."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import RUN_LOG_PATH, ensure_data_dirs


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def append_run_log(
    *,
    run_id: str,
    layer: str,
    model: str,
    rows_read: int,
    rows_written: int,
    duration_seconds: float,
    run_type: str,
    extra: dict[str, Any] | None = None,
) -> None:
    ensure_data_dirs()
    record = {
        "run_id": run_id,
        "layer": layer,
        "model": model,
        "rows_read": int(rows_read),
        "rows_written": int(rows_written),
        "duration_seconds": round(float(duration_seconds), 3),
        "run_type": run_type,
        "timestamp": utc_now().isoformat(),
    }
    if extra:
        record.update(extra)
    with RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")

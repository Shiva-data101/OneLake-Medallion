"""Return processed state to zero. Landing and archive/ are left alone.

Deletes bronze Delta tables, watermarks.json, run_log.jsonl, and the DuckDB
file so the next dbt build is a true full refresh (is_incremental() is false).
Safe to re-run: missing paths are skipped.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import (
    BENCHMARK_DIR,
    BRONZE_DIR,
    DUCKDB_PATH,
    RUN_LOG_PATH,
    WATERMARKS_PATH,
    ensure_data_dirs,
)


def _remove(path: Path) -> str:
    if not path.exists():
        return "absent"
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return "removed"


def reset() -> dict[str, str]:
    results = {
        "bronze": _remove(BRONZE_DIR),
        "watermarks": _remove(WATERMARKS_PATH),
        "run_log": _remove(RUN_LOG_PATH),
        "duckdb": _remove(DUCKDB_PATH),
    }
    dbt_builds = BENCHMARK_DIR / "dbt_builds.jsonl"
    replay_log = BENCHMARK_DIR / "replay_days.jsonl"
    results["dbt_builds"] = _remove(dbt_builds)
    results["replay_log"] = _remove(replay_log)
    ensure_data_dirs()
    return results


def main() -> int:
    results = reset()
    for name, status in results.items():
        print(f"{name}: {status}")
    print("Reset complete. Landing and archive/ were not touched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

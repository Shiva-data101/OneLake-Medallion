"""Run dbt build and append timing to the run log."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import BENCHMARK_DIR, BRONZE_DIR, PROJECT_ROOT, WAREHOUSE_DIR, ensure_data_dirs
from run_log import append_run_log


def run_dbt(run_type: str, extra_args: list[str]) -> dict:
    ensure_data_dirs()
    os.environ["ONELAKE_BRONZE"] = str(BRONZE_DIR).replace("\\", "/")
    os.environ["ONELAKE_DUCKDB"] = str(WAREHOUSE_DIR / "onelake.duckdb").replace("\\", "/")
    run_id = str(uuid.uuid4())
    dbt_exe = PROJECT_ROOT / ".venv" / "Scripts" / "dbt.exe"
    if not dbt_exe.exists():
        dbt_exe = Path("dbt")

    command = [
        str(dbt_exe),
        "build",
        "--project-dir",
        str(PROJECT_ROOT / "transform"),
        "--profiles-dir",
        str(PROJECT_ROOT / "transform"),
        *extra_args,
    ]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    elapsed = time.perf_counter() - started

    append_run_log(
        run_id=run_id,
        layer="dbt",
        model="build",
        rows_read=0,
        rows_written=0,
        duration_seconds=elapsed,
        run_type=run_type,
        extra={"returncode": completed.returncode, "command": command},
    )

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    bench_path = BENCHMARK_DIR / "dbt_builds.jsonl"
    with bench_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "run_id": run_id,
                    "run_type": run_type,
                    "duration_seconds": round(elapsed, 3),
                    "returncode": completed.returncode,
                }
            )
            + "\n"
        )

    print(f"dbt build ({run_type}) finished in {elapsed:.1f}s with exit {completed.returncode}")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return {"run_id": run_id, "duration_seconds": elapsed, "returncode": completed.returncode}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-type", default="incremental", choices=("full", "incremental"))
    parser.add_argument("dbt_args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    extra = [arg for arg in args.dbt_args if arg != "--"]
    run_dbt(args.run_type, extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Replay the next N landing days. ingest --once, then incremental dbt build.

Each cycle appends data/benchmark/replay_days.jsonl. Stops if ingest finds
no next folder. last_batch_date must already sit at the cutoff. Run
ingest --backfill first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest import ingest
from paths import BENCHMARK_DIR, LANDING_DIR, REPLAY_LOG_PATH, ensure_data_dirs
from run_dbt import run_dbt


def replay_days(*, landing: Path, days: int) -> list[dict]:
    ensure_data_dirs()
    records: list[dict] = []
    for index in range(1, days + 1):
        ingested = ingest(landing=landing, mode="once", run_type="incremental")
        day_batches = [name for name in ingested.get("batches", []) if name != "_reference"]
        if not day_batches:
            print(f"Replay stopped after {index - 1} day(s): no next landing folder.")
            break
        batch_id = day_batches[0]
        built = run_dbt("incremental", [])
        record = {
            "day_index": index,
            "batch_id": batch_id,
            "ingest_rows_written": ingested.get("rows_written", 0),
            "ingest_duration_seconds": round(float(ingested.get("duration_seconds", 0)), 3),
            "dbt_duration_seconds": round(float(built.get("duration_seconds", 0)), 3),
            "dbt_returncode": built.get("returncode", 1),
        }
        records.append(record)
        with REPLAY_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        print(
            f"Replay {index}/{days} {batch_id}: "
            f"{record['ingest_rows_written']} rows in {record['ingest_duration_seconds']}s, "
            f"dbt {record['dbt_duration_seconds']}s"
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing", type=Path, default=LANDING_DIR)
    parser.add_argument("--days", type=int, default=30, help="How many landing folders to replay")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    replay_days(landing=args.landing, days=args.days)
    print(f"Replay log: {REPLAY_LOG_PATH}")
    print(f"Also see {BENCHMARK_DIR / 'dbt_builds.jsonl'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

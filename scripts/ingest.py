"""Append landing parquet into bronze Delta tables.

Bronze stays raw. Source columns plus _ingested_at, _source_file, _batch_id.
last_batch_date is a folder cursor, not a row watermark. If landing/_meta.json
exists you must pass --backfill, --once, or --all. Otherwise I would ingest
the replay queue by accident.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import pandas as pd
from deltalake import write_deltalake

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import (
    ALL_TABLES,
    BRONZE_DIR,
    CONTROL_DIR,
    LANDING_DIR,
    REFERENCE_BATCH_ID,
    WATERMARKS_PATH,
    ensure_data_dirs,
    load_landing_meta,
)
from run_log import append_run_log, utc_now


def _load_watermarks() -> dict:
    if not WATERMARKS_PATH.exists():
        return {
            "reference_loaded": False,
            "last_batch_date": None,
            "processed_batches": [],
            "tables": {},
        }
    return json.loads(WATERMARKS_PATH.read_text(encoding="utf-8"))


def _save_watermarks(watermarks: dict) -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    WATERMARKS_PATH.write_text(json.dumps(watermarks, indent=2, default=str) + "\n", encoding="utf-8")


def _batch_dirs(landing: Path) -> list[Path]:
    if not landing.exists():
        return []
    days = []
    for child in landing.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        days.append(child)
    return sorted(days, key=lambda path: path.name)


def _read_parquet(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    for col in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[col]):
            frame[col] = pd.to_datetime(frame[col], utc=False)
    return frame


def _append_delta(table_name: str, frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    target = BRONZE_DIR / table_name
    write_deltalake(str(target), frame, mode="append")


def _stamp(frame: pd.DataFrame, source_file: Path, batch_id: str, ingested_at: str) -> pd.DataFrame:
    stamped = frame.copy()
    stamped["_ingested_at"] = ingested_at
    stamped["_source_file"] = str(source_file.as_posix())
    stamped["_batch_id"] = batch_id
    return stamped


def _select_pending(landing: Path, mode: str, watermarks: dict) -> list[Path]:
    pending: list[Path] = []
    ref_dir = landing / REFERENCE_BATCH_ID
    if ref_dir.exists() and not watermarks.get("reference_loaded"):
        pending.append(ref_dir)

    last = watermarks.get("last_batch_date")
    meta = load_landing_meta(landing)
    cutoff = meta["cutoff"] if meta and mode == "backfill" else None

    for day_dir in _batch_dirs(landing):
        if last and day_dir.name <= last:
            continue
        if cutoff is not None and day_dir.name > cutoff:
            continue
        pending.append(day_dir)

    if mode == "once":
        day_pending = [path for path in pending if path.name != REFERENCE_BATCH_ID]
        refs = [path for path in pending if path.name == REFERENCE_BATCH_ID]
        if day_pending:
            pending = refs + day_pending[:1]
        else:
            pending = refs
    return pending


def ingest(*, landing: Path, mode: str, run_type: str) -> dict:
    ensure_data_dirs()
    run_id = str(uuid.uuid4())
    started = time.perf_counter()
    watermarks = _load_watermarks()
    ingested_at = utc_now().isoformat()
    rows_read = 0
    rows_written = 0
    batches_done: list[str] = []

    pending = _select_pending(landing, mode, watermarks)

    if not pending:
        elapsed = time.perf_counter() - started
        append_run_log(
            run_id=run_id,
            layer="bronze",
            model="ingest",
            rows_read=0,
            rows_written=0,
            duration_seconds=elapsed,
            run_type=run_type,
            extra={"batches": []},
        )
        print("No new landing batches to ingest.")
        return {"run_id": run_id, "rows_written": 0, "batches": [], "duration_seconds": elapsed}

    table_buffers: dict[str, list[pd.DataFrame]] = {name: [] for name in ALL_TABLES}
    table_row_counts: dict[str, int] = {name: 0 for name in ALL_TABLES}

    for batch_dir in pending:
        batch_id = batch_dir.name
        for table_name in ALL_TABLES:
            parquet_path = batch_dir / f"{table_name}.parquet"
            if not parquet_path.exists():
                continue
            frame = _read_parquet(parquet_path)
            rows_read += len(frame)
            stamped = _stamp(frame, parquet_path, batch_id, ingested_at)
            table_buffers[table_name].append(stamped)
            table_row_counts[table_name] += len(stamped)
        batches_done.append(batch_id)

    for table_name, frames in table_buffers.items():
        if not frames:
            continue
        combined = pd.concat(frames, ignore_index=True)
        _append_delta(table_name, combined)
        rows_written += len(combined)
        table_meta = watermarks.setdefault("tables", {}).setdefault(table_name, {"rows": 0})
        table_meta["rows"] = int(table_meta.get("rows", 0)) + len(combined)
        if "updated_at" in combined.columns:
            table_meta["last_updated_at"] = str(pd.to_datetime(combined["updated_at"]).max())

    if any(path.name == REFERENCE_BATCH_ID for path in pending):
        watermarks["reference_loaded"] = True
    day_batches = [name for name in batches_done if name != REFERENCE_BATCH_ID]
    if day_batches:
        watermarks["last_batch_date"] = max(day_batches)
    processed = list(watermarks.get("processed_batches", []))
    processed.extend(batches_done)
    watermarks["processed_batches"] = processed
    watermarks["last_run_id"] = run_id
    _save_watermarks(watermarks)

    elapsed = time.perf_counter() - started
    append_run_log(
        run_id=run_id,
        layer="bronze",
        model="ingest",
        rows_read=rows_read,
        rows_written=rows_written,
        duration_seconds=elapsed,
        run_type=run_type,
        extra={"batches": batches_done, "tables": table_row_counts},
    )
    print(
        f"Ingested {len(batches_done)} batch(es), {rows_written:,} rows "
        f"in {elapsed:.1f}s (run_id={run_id})"
    )
    return {
        "run_id": run_id,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "batches": batches_done,
        "duration_seconds": elapsed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing", type=Path, default=LANDING_DIR)
    parser.add_argument("--backfill", action="store_true", help="Ingest reference + folders on or before cutoff")
    parser.add_argument("--once", action="store_true", help="Ingest only the next unprocessed batch")
    parser.add_argument("--all", dest="all_remaining", action="store_true", help="Ingest every remaining folder")
    parser.add_argument("--full-refresh", action="store_true", help="Drop bronze + watermarks first (prefer reset.py)")
    parser.add_argument("--run-type", default=None, choices=("full", "incremental"))
    return parser.parse_args()


def _resolve_mode(args: argparse.Namespace, landing: Path) -> str:
    selected = [name for name, flag in (("backfill", args.backfill), ("once", args.once), ("all", args.all_remaining)) if flag]
    if len(selected) > 1:
        raise SystemExit("Pass only one of --backfill, --once, or --all.")
    if selected:
        if selected[0] == "backfill" and load_landing_meta(landing) is None:
            raise SystemExit("landing/_meta.json is missing. Re-run generate_batches.py --cutoff ...")
        return selected[0]
    if load_landing_meta(landing) is not None:
        raise SystemExit("landing/_meta.json exists; pass --backfill, --once, or --all so the replay queue is not ingested.")
    return "all"


def main() -> int:
    args = parse_args()
    if args.full_refresh:
        if BRONZE_DIR.exists():
            import shutil

            shutil.rmtree(BRONZE_DIR)
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        if WATERMARKS_PATH.exists():
            WATERMARKS_PATH.unlink()
    mode = _resolve_mode(args, args.landing)
    run_type = args.run_type or ("full" if mode == "backfill" or args.full_refresh else "incremental")
    ingest(landing=args.landing, mode=mode, run_type=run_type)
    return 0


if __name__ == "__main__":
    sys.exit(main())

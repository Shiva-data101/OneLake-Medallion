"""Split Olist CSVs into daily landing parquet files.

Folder names are order_date. That is a source-arrival simulation, not a
watermark. --cutoff writes landing/_meta.json so ingest can backfill
through the cutoff and leave later folders as the replay queue.
Do not use updated_at as the dbt watermark. It is a delivery date.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import (
    ARCHIVE_DIR,
    CSV_BY_TABLE,
    DAILY_TABLES,
    DEFAULT_CUTOFF,
    LANDING_DIR,
    REFERENCE_BATCH_ID,
    REFERENCE_TABLES,
    STRING_COLUMNS,
    ensure_data_dirs,
    landing_meta_path,
)


def _read_csv(name: str) -> pd.DataFrame:
    path = ARCHIVE_DIR / CSV_BY_TABLE[name]
    dtype = {col: "string" for col in STRING_COLUMNS}
    frame = pd.read_csv(path, dtype=dtype, keep_default_na=True)
    return frame


def _row_max_timestamp(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    converted = [pd.to_datetime(frame[col], errors="coerce") for col in columns if col in frame.columns]
    stacked = pd.concat(converted, axis=1)
    return stacked.max(axis=1)


def _prepare_orders(orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    purchase = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    orders["order_date"] = purchase.dt.date
    orders["updated_at"] = _row_max_timestamp(
        orders,
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    orders["updated_at"] = orders["updated_at"].fillna(purchase)
    return orders


def _attach_order_date(child: pd.DataFrame, orders: pd.DataFrame, extra_ts: list[str]) -> pd.DataFrame:
    lookup = orders[["order_id", "order_date", "updated_at"]].rename(columns={"updated_at": "order_updated_at"})
    merged = child.merge(lookup, on="order_id", how="left")
    extra = _row_max_timestamp(merged, extra_ts) if extra_ts else pd.Series(pd.NaT, index=merged.index)
    merged["updated_at"] = extra.combine_first(merged["order_updated_at"])
    return merged.drop(columns=["order_updated_at"])


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def generate_batches(
    *,
    dest: Path,
    inject_late: bool,
    late_days: int,
    cutoff: date,
) -> dict[str, int]:
    ensure_data_dirs()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    orders = _prepare_orders(_read_csv("orders"))
    items = _attach_order_date(_read_csv("order_items"), orders, ["shipping_limit_date"])
    payments = _attach_order_date(_read_csv("order_payments"), orders, [])
    reviews = _attach_order_date(
        _read_csv("order_reviews"),
        orders,
        ["review_creation_date", "review_answer_timestamp"],
    )
    customers = _read_csv("customers").merge(
        orders[["customer_id", "order_date", "updated_at"]],
        on="customer_id",
        how="left",
    )

    daily_frames = {
        "orders": orders,
        "order_items": items,
        "order_payments": payments,
        "order_reviews": reviews,
        "customers": customers,
    }

    files_written = 0
    days_written = 0
    for day, day_orders in orders.groupby("order_date", sort=True):
        if pd.isna(day):
            continue
        day_dir = dest / str(day)
        day_ids = set(day_orders["order_id"])
        customer_ids = set(day_orders["customer_id"])
        for table in DAILY_TABLES:
            frame = daily_frames[table]
            if table == "customers":
                subset = frame[frame["customer_id"].isin(customer_ids)]
            else:
                subset = frame[frame["order_id"].isin(day_ids)]
            _write_parquet(subset, day_dir / f"{table}.parquet")
            files_written += 1
        days_written += 1

    ref_dir = dest / REFERENCE_BATCH_ID
    for table in REFERENCE_TABLES:
        frame = _read_csv(table)
        if table != "geolocation":
            frame["updated_at"] = pd.Timestamp("2016-01-01")
        else:
            frame["updated_at"] = pd.Timestamp("2016-01-01")
        _write_parquet(frame, ref_dir / f"{table}.parquet")
        files_written += 1

    if inject_late:
        last_day = max(day for day in orders["order_date"].dropna().unique())
        source_day = last_day - timedelta(days=late_days)
        candidates = orders[orders["order_date"] == source_day]
        if candidates.empty:
            candidates = orders.sort_values("order_date").head(1)
            source_day = candidates.iloc[0]["order_date"]
        sample = candidates.iloc[[0]].copy()
        landing_day = last_day + timedelta(days=1)
        new_updated = pd.Timestamp(f"{landing_day} 12:00:00")
        sample["updated_at"] = new_updated
        late_dir = dest / str(landing_day)

        order_id = sample.iloc[0]["order_id"]
        customer_id = sample.iloc[0]["customer_id"]
        _write_parquet(sample, late_dir / "orders.parquet")
        _write_parquet(items[items["order_id"] == order_id].assign(updated_at=new_updated), late_dir / "order_items.parquet")
        _write_parquet(payments[payments["order_id"] == order_id].assign(updated_at=new_updated), late_dir / "order_payments.parquet")
        _write_parquet(reviews[reviews["order_id"] == order_id].assign(updated_at=new_updated), late_dir / "order_reviews.parquet")
        _write_parquet(
            customers[customers["customer_id"] == customer_id].assign(updated_at=new_updated),
            late_dir / "customers.parquet",
        )
        files_written += 5
        days_written += 1
        print(f"Injected late-arriving order {order_id} (order_date={source_day}) into {landing_day}")

    order_days = [day for day in orders["order_date"].dropna().unique()]
    backfill_days = sum(1 for day in order_days if day <= cutoff)
    replay_days = sum(1 for day in order_days if day > cutoff)
    if inject_late:
        replay_days += 1

    meta = {
        "cutoff": cutoff.isoformat(),
        "inclusive": True,
        "backfill_days": backfill_days,
        "replay_days": replay_days,
    }
    landing_meta_path(dest).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    summary = {
        "days_written": days_written,
        "files_written": files_written,
        "orders": len(orders),
        "min_date": str(orders["order_date"].min()),
        "max_date": str(orders["order_date"].max()),
        "cutoff": cutoff.isoformat(),
        "backfill_days": backfill_days,
        "replay_days": replay_days,
    }
    print(
        f"Landing ready: {days_written} day folders, {files_written} parquet files, "
        f"{len(orders):,} orders ({summary['min_date']} to {summary['max_date']})"
    )
    print(
        f"Cutoff {cutoff.isoformat()} inclusive: {backfill_days} backfill days, "
        f"{replay_days} replay-queue days. Wrote {landing_meta_path(dest)}."
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=LANDING_DIR, help="Landing root folder")
    parser.add_argument(
        "--cutoff",
        type=date.fromisoformat,
        default=date.fromisoformat(DEFAULT_CUTOFF),
        help="Inclusive backfill end date (YYYY-MM-DD). Later folders are the replay queue.",
    )
    parser.add_argument("--inject-late", action="store_true", help="Add a late-arriving order after the last source day")
    parser.add_argument("--late-days", type=int, default=3, help="How many days back the injected order is dated")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generate_batches(
        dest=args.out,
        inject_late=args.inject_late,
        late_days=args.late_days,
        cutoff=args.cutoff,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

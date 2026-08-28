"""Sample a referentially consistent bronze slice into transform/seeds/.

CI has no archive/ and no bronze. Seeds are the fixture. Tables are not
sampled independently: start from ~2,000 orders, then take only the rows
those orders (and their items) actually reference.

Default is a dry run that prints counts and orphan checks. Pass --write
to emit CSV. Does not touch GitHub workflows.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import ALL_TABLES, BRONZE_DIR, SEEDS_DIR

# Order of operations — do not shuffle this graph.
#   1. orders          distinct order_id, deterministic, limit n
#   2. order_items     order_id in (1)
#   3. order_payments  order_id in (1)
#   4. order_reviews   order_id in (1)
#   5. customers       customer_id in (1)   — Olist reissues customer_id per order
#   6. products        product_id in (2)
#   7. sellers         seller_id in (2)
#   8. geolocation     zip in sampled customers ∪ sellers   (no relationships
#                      test, but stg_geolocation still builds in CI)
#   9. product_category_translation  category in sampled products  (left join)
DEFAULT_N_ORDERS = 2000
DEFAULT_SALT = "onelake-ci-seeds"

ORPHAN_CHECKS = (
    ("order_items.order_id", "SELECT count(*) FROM slice_order_items i LEFT JOIN slice_orders o USING (order_id) WHERE o.order_id IS NULL"),
    ("order_payments.order_id", "SELECT count(*) FROM slice_order_payments p LEFT JOIN slice_orders o USING (order_id) WHERE o.order_id IS NULL"),
    ("order_reviews.order_id", "SELECT count(*) FROM slice_order_reviews r LEFT JOIN slice_orders o USING (order_id) WHERE o.order_id IS NULL"),
    ("orders.customer_id", "SELECT count(*) FROM slice_orders o LEFT JOIN slice_customers c USING (customer_id) WHERE c.customer_id IS NULL"),
    ("order_items.product_id", "SELECT count(*) FROM slice_order_items i LEFT JOIN slice_products p USING (product_id) WHERE p.product_id IS NULL"),
    ("order_items.seller_id", "SELECT count(*) FROM slice_order_items i LEFT JOIN slice_sellers s USING (seller_id) WHERE s.seller_id IS NULL"),
)


def _bronze_glob(table_name: str) -> str:
    path = (BRONZE_DIR / table_name / "*.parquet").as_posix()
    return path


def _read_sql(table_name: str) -> str:
    return f"read_parquet('{_bronze_glob(table_name)}', union_by_name=true, hive_partitioning=0)"


def connect() -> duckdb.DuckDBPyConnection:
    missing = [name for name in ALL_TABLES if not any((BRONZE_DIR / name).glob("*.parquet"))]
    if missing:
        raise SystemExit(f"Bronze parquet missing for: {', '.join(missing)}. Ingest locally first.")
    return duckdb.connect(database=":memory:")


def build_slice(con: duckdb.DuckDBPyConnection, *, n_orders: int, salt: str) -> None:
    # 1. Parent keys. Inner-join customers so every sampled order has the
    #    per-order customer_id row dim_customer will need.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE sampled_order_ids AS
        SELECT order_id
        FROM (
            SELECT DISTINCT o.order_id
            FROM {_read_sql('orders')} AS o
            INNER JOIN {_read_sql('customers')} AS c
                ON o.customer_id = c.customer_id
            WHERE o.order_id IS NOT NULL
              AND o.customer_id IS NOT NULL
            ORDER BY md5(o.order_id || ?)
            LIMIT ?
        )
        """,
        [salt, n_orders],
    )

    # 2–5. Children of those orders.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_orders AS
        SELECT o.*
        FROM {_read_sql('orders')} AS o
        INNER JOIN sampled_order_ids k USING (order_id)
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_order_items AS
        SELECT i.*
        FROM {_read_sql('order_items')} AS i
        INNER JOIN sampled_order_ids k USING (order_id)
        WHERE i.product_id IS NOT NULL
          AND i.seller_id IS NOT NULL
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_order_payments AS
        SELECT p.*
        FROM {_read_sql('order_payments')} AS p
        INNER JOIN sampled_order_ids k USING (order_id)
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_order_reviews AS
        SELECT r.*
        FROM {_read_sql('order_reviews')} AS r
        INNER JOIN sampled_order_ids k USING (order_id)
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_customers AS
        SELECT c.*
        FROM {_read_sql('customers')} AS c
        WHERE c.customer_id IN (SELECT customer_id FROM slice_orders)
        """
    )

    # 6–7. Only products and sellers the sampled items actually reference.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_products AS
        SELECT p.*
        FROM {_read_sql('products')} AS p
        WHERE p.product_id IN (SELECT DISTINCT product_id FROM slice_order_items)
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_sellers AS
        SELECT s.*
        FROM {_read_sql('sellers')} AS s
        WHERE s.seller_id IN (SELECT DISTINCT seller_id FROM slice_order_items)
        """
    )

    # 8–9. Geo is append-only in bronze with many rows per zip (285k rows
    # for ~2k zips in a 2k-order slice). The seed keeps one row per zip,
    # same grain silver will use. No relationships test points at geo.
    # Translation is a left join; only categories the sampled products use.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_geolocation AS
        SELECT * EXCLUDE (_rn)
        FROM (
            SELECT
                g.*,
                row_number() OVER (
                    PARTITION BY g.geolocation_zip_code_prefix
                    ORDER BY g._ingested_at DESC, g.updated_at DESC
                ) AS _rn
            FROM {_read_sql('geolocation')} AS g
            WHERE g.geolocation_zip_code_prefix IN (
                SELECT customer_zip_code_prefix FROM slice_customers
                UNION
                SELECT seller_zip_code_prefix FROM slice_sellers
            )
        )
        WHERE _rn = 1
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE slice_product_category_translation AS
        SELECT t.*
        FROM {_read_sql('product_category_translation')} AS t
        WHERE t.product_category_name IN (
            SELECT DISTINCT product_category_name
            FROM slice_products
            WHERE product_category_name IS NOT NULL
        )
        """
    )


def restamp_ingested_at(con: duckdb.DuckDBPyConnection, ingested_at: str) -> None:
    for table_name in ALL_TABLES:
        con.execute(
            f"""
            UPDATE slice_{table_name}
            SET _ingested_at = ?,
                _source_file = 'ci_seed',
                _batch_id = 'ci_seed'
            """,
            [ingested_at],
        )


def slice_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    counts = {"orders_sampled": con.execute("SELECT count(*) FROM sampled_order_ids").fetchone()[0]}
    for table_name in ALL_TABLES:
        counts[table_name] = con.execute(f"SELECT count(*) FROM slice_{table_name}").fetchone()[0]
    return counts


def orphan_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {label: con.execute(sql).fetchone()[0] for label, sql in ORPHAN_CHECKS}


def extra_stats(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    return {
        "distinct_order_status": con.execute(
            "SELECT count(DISTINCT order_status) FROM slice_orders"
        ).fetchone()[0],
        "review_score_min": con.execute(
            "SELECT min(review_score) FROM slice_order_reviews"
        ).fetchone()[0],
        "review_score_max": con.execute(
            "SELECT max(review_score) FROM slice_order_reviews"
        ).fetchone()[0],
        "review_score_avg": con.execute(
            "SELECT round(avg(review_score), 4) FROM slice_order_reviews"
        ).fetchone()[0],
        "distinct_customer_state": con.execute(
            "SELECT count(DISTINCT customer_state) FROM slice_customers"
        ).fetchone()[0],
        "min_ingested_at": con.execute(
            "SELECT min(_ingested_at) FROM slice_orders"
        ).fetchone()[0],
        "max_ingested_at": con.execute(
            "SELECT max(_ingested_at) FROM slice_orders"
        ).fetchone()[0],
    }


def write_seeds(con: duckdb.DuckDBPyConnection, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for table_name in ALL_TABLES:
        out = dest / f"{table_name}_seed.csv"
        con.execute(
            f"""
            COPY slice_{table_name}
            TO '{out.as_posix()}'
            (HEADER, DELIMITER ',', QUOTE '"', ESCAPE '"', DATEFORMAT '%Y-%m-%d', TIMESTAMPFORMAT '%Y-%m-%d %H:%M:%S.%f')
            """
        )
        print(f"wrote {out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-orders", type=int, default=DEFAULT_N_ORDERS)
    parser.add_argument("--salt", default=DEFAULT_SALT, help="Salt for md5(order_id) so the sample is stable")
    parser.add_argument(
        "--restamp-ingested-at",
        action="store_true",
        help="Set every seed row's _ingested_at to now so the 7-day freshness tests still pass in CI",
    )
    parser.add_argument("--write", action="store_true", help="Write transform/seeds/*.csv (off by default)")
    parser.add_argument("--dest", type=Path, default=SEEDS_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    con = connect()
    build_slice(con, n_orders=args.n_orders, salt=args.salt)
    if args.restamp_ingested_at:
        restamp_ingested_at(con, datetime.now(timezone.utc).isoformat())

    counts = slice_counts(con)
    orphans = orphan_counts(con)
    stats = extra_stats(con)

    print("CI seed slice (not written unless --write)")
    print(f"n_orders={args.n_orders} salt={args.salt!r} restamp={args.restamp_ingested_at}")
    for key, value in counts.items():
        print(f"  {key:32} {value}")
    print("orphan checks (must be 0)")
    for label, value in orphans.items():
        print(f"  {label:32} {value}")
    print("slice stats")
    for key, value in stats.items():
        print(f"  {key:32} {value}")

    bad = {label: n for label, n in orphans.items() if n}
    if bad:
        print(f"Refusing to write: orphan rows {bad}")
        return 1

    if args.write:
        write_seeds(con, args.dest)
    else:
        print("Dry run. Pass --write to emit transform/seeds/<table>_seed.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())

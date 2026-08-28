"""Shared filesystem locations for lakehouse scripts."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = PROJECT_ROOT / "archive"
DATA_DIR = PROJECT_ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
BRONZE_DIR = DATA_DIR / "bronze"
CONTROL_DIR = DATA_DIR / "control"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
QUARANTINE_DIR = DATA_DIR / "quarantine"
BENCHMARK_DIR = DATA_DIR / "benchmark"
SODA_DIR = PROJECT_ROOT / "soda"
SODA_DS_CONFIG_PATH = SODA_DIR / "ds_config.yml"
SODA_DS_CONFIG_LOCAL_PATH = SODA_DIR / "ds_config.local.yml"
SODA_CONTRACTS_DIR = SODA_DIR / "contracts"
SODA_CI_CONTRACTS_DIR = SODA_CONTRACTS_DIR / "ci"
SEEDS_DIR = PROJECT_ROOT / "transform" / "seeds"

WATERMARKS_PATH = CONTROL_DIR / "watermarks.json"
RUN_LOG_PATH = CONTROL_DIR / "run_log.jsonl"
LANDING_META_PATH = LANDING_DIR / "_meta.json"
DUCKDB_PATH = WAREHOUSE_DIR / "onelake.duckdb"
CI_DUCKDB_PATH = WAREHOUSE_DIR / "ci.duckdb"
REPLAY_LOG_PATH = BENCHMARK_DIR / "replay_days.jsonl"

DEFAULT_CUTOFF = "2018-06-30"
REFERENCE_BATCH_ID = "_reference"

DAILY_TABLES = (
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "customers",
)
REFERENCE_TABLES = (
    "products",
    "sellers",
    "geolocation",
    "product_category_translation",
)
ALL_TABLES = DAILY_TABLES + REFERENCE_TABLES

CSV_BY_TABLE = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}

STRING_COLUMNS = {
    "customer_zip_code_prefix",
    "seller_zip_code_prefix",
    "geolocation_zip_code_prefix",
    "order_id",
    "customer_id",
    "customer_unique_id",
    "product_id",
    "seller_id",
    "review_id",
}


def landing_meta_path(landing: Path | None = None) -> Path:
    return (landing or LANDING_DIR) / "_meta.json"


def load_landing_meta(landing: Path | None = None) -> dict | None:
    path = landing_meta_path(landing)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_data_dirs() -> None:
    for path in (
        LANDING_DIR,
        BRONZE_DIR,
        CONTROL_DIR,
        WAREHOUSE_DIR,
        QUARANTINE_DIR,
        BENCHMARK_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)

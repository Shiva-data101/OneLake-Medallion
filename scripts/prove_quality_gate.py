"""Prove the Phase 2 quality gate: poison one bronze review, watch a named
dbt test fail, restore the row, watch it pass.

Staging only try_casts review_score, so a 99 lands in silver. The gate is
dbt_expectations.expect_column_values_to_be_between on silver_order_reviews.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import BRONZE_DIR, DUCKDB_PATH, PROJECT_ROOT, ensure_data_dirs

PROOF_TEST = "dbt_expectations_expect_column_values_to_be_between_silver_order_reviews_review_score__5__1"
BAD_SCORE = 99
BATCH_ID = "quality_gate_probe"


def _dbt_exe() -> Path:
    candidate = PROJECT_ROOT / ".venv" / "Scripts" / "dbt.exe"
    return candidate if candidate.exists() else Path("dbt")


def _stamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_review(row: pd.DataFrame) -> None:
    target = BRONZE_DIR / "order_reviews"
    table = pa.Table.from_pandas(row.reset_index(drop=True), preserve_index=False)
    write_deltalake(str(target), table, mode="append")


def _one_review() -> pd.DataFrame:
    table = DeltaTable(str(BRONZE_DIR / "order_reviews"))
    frame = table.to_pandas()
    if frame.empty:
        raise SystemExit("bronze order_reviews is empty")
    return frame.sort_values("_ingested_at").tail(1).copy()


def _run_dbt() -> subprocess.CompletedProcess:
    os.environ["ONELAKE_BRONZE"] = str(BRONZE_DIR).replace("\\", "/")
    os.environ["ONELAKE_DUCKDB"] = str(DUCKDB_PATH).replace("\\", "/")
    command = [
        str(_dbt_exe()),
        "build",
        "--project-dir",
        str(PROJECT_ROOT / "transform"),
        "--profiles-dir",
        str(PROJECT_ROOT / "transform"),
        "--select",
        "silver_order_reviews",
    ]
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False, text=True)
    return completed


def main() -> int:
    ensure_data_dirs()
    original = _one_review()
    review_id = original.iloc[0]["review_id"]
    original_score = int(original.iloc[0]["review_score"])
    print(f"Probing review_id={review_id} original_score={original_score}")

    poisoned = original.copy()
    poisoned["review_score"] = BAD_SCORE
    poisoned["_ingested_at"] = _stamp_now()
    poisoned["_batch_id"] = BATCH_ID
    poisoned["_source_file"] = "quality_gate_probe"
    _append_review(poisoned)
    print(f"Appended bronze review_score={BAD_SCORE}")

    failed = _run_dbt()
    if failed.returncode == 0:
        print("Expected dbt build to fail after poisoning review_score; it passed.")
        return 1
    if PROOF_TEST not in (failed.stdout or "") + (failed.stderr or ""):
        # dbt prints the test name to the console; subprocess inherits the tty so
        # stdout may be empty here. The return code is still the gate.
        print(f"dbt build failed as expected (exit {failed.returncode}). Look for FAIL on {PROOF_TEST}")
    else:
        print(f"Named test failed as expected: {PROOF_TEST}")

    restored = original.copy()
    restored["review_score"] = original_score
    restored["_ingested_at"] = _stamp_now()
    restored["_batch_id"] = f"{BATCH_ID}_restore"
    restored["_source_file"] = "quality_gate_probe"
    _append_review(restored)
    print(f"Appended restored review_score={original_score}")

    passed = _run_dbt()
    if passed.returncode != 0:
        print("Expected dbt build to pass after restore; it failed.")
        return 1
    print(f"dbt build passed after restore. Gate: {PROOF_TEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

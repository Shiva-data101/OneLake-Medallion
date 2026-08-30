"""Run Soda Core v4 contracts against the local DuckDB warehouse."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import (
    CI_DUCKDB_PATH,
    DUCKDB_PATH,
    PROJECT_ROOT,
    SODA_CI_CONTRACTS_DIR,
    SODA_CONTRACTS_DIR,
    SODA_DS_CONFIG_LOCAL_PATH,
    ensure_data_dirs,
)


def _soda_exe() -> Path:
    candidate = PROJECT_ROOT / ".venv" / "Scripts" / "soda.exe"
    return candidate if candidate.exists() else Path("soda")


def write_ds_config(database: Path) -> Path:
    ensure_data_dirs()
    path = str(database).replace("\\", "/")
    SODA_DS_CONFIG_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SODA_DS_CONFIG_LOCAL_PATH.write_text(
        f"type: duckdb\nname: onelake\nconnection:\n  database: \"{path}\"\n",
        encoding="utf-8",
    )
    return SODA_DS_CONFIG_LOCAL_PATH


def run_soda(*, ci: bool = False, database: Path | None = None) -> int:
    warehouse = database or (CI_DUCKDB_PATH if ci else DUCKDB_PATH)
    contracts_dir = SODA_CI_CONTRACTS_DIR if ci else SODA_CONTRACTS_DIR
    if not warehouse.exists():
        print(f"Warehouse not found: {warehouse}")
        return 1
    ds_config = write_ds_config(warehouse)
    contracts = sorted(path for path in contracts_dir.glob("*.yml"))
    if not contracts:
        print(f"No contracts in {contracts_dir}")
        return 1

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    failed = 0
    for contract in contracts:
        command = [
            str(_soda_exe()),
            "contract",
            "verify",
            "-ds",
            str(ds_config),
            "-c",
            str(contract),
        ]
        print(f"soda contract verify {contract.name}")
        completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False, env=env)
        if completed.returncode != 0:
            failed += 1
    if failed:
        print(f"Soda failed {failed} of {len(contracts)} contracts")
        return 1
    print(f"Soda passed {len(contracts)} contracts")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Scan the CI warehouse with gold schema contracts. Skip freshness and volume row_count.",
    )
    parser.add_argument("--database", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_soda(ci=args.ci, database=args.database)


if __name__ == "__main__":
    sys.exit(main())

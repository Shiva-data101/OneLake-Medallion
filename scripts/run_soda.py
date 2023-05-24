"""Run Soda Core v4 contracts against the local DuckDB warehouse."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import DUCKDB_PATH, PROJECT_ROOT, SODA_CONTRACTS_DIR, SODA_DS_CONFIG_LOCAL_PATH, ensure_data_dirs


def _soda_exe() -> Path:
    candidate = PROJECT_ROOT / ".venv" / "Scripts" / "soda.exe"
    return candidate if candidate.exists() else Path("soda")


def write_ds_config() -> Path:
    ensure_data_dirs()
    database = str(DUCKDB_PATH).replace("\\", "/")
    SODA_DS_CONFIG_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SODA_DS_CONFIG_LOCAL_PATH.write_text(
        f"type: duckdb\nname: onelake\nconnection:\n  database: \"{database}\"\n",
        encoding="utf-8",
    )
    return SODA_DS_CONFIG_LOCAL_PATH


def run_soda() -> int:
    if not DUCKDB_PATH.exists():
        print(f"Warehouse not found: {DUCKDB_PATH}")
        return 1
    ds_config = write_ds_config()
    contracts = sorted(SODA_CONTRACTS_DIR.glob("*.yml"))
    if not contracts:
        print(f"No contracts in {SODA_CONTRACTS_DIR}")
        return 1

    env = os.environ.copy()
    env["ONELAKE_DUCKDB"] = str(DUCKDB_PATH).replace("\\", "/")
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


def main() -> int:
    return run_soda()


if __name__ == "__main__":
    sys.exit(main())

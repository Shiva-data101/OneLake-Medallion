# OneLake Medallion

[![ci](https://github.com/Shiva-data101/OneLake-Medallion/actions/workflows/ci.yml/badge.svg)](https://github.com/Shiva-data101/OneLake-Medallion/actions/workflows/ci.yml)

An incremental analytics lakehouse on the Olist Brazilian e-commerce dataset,
built locally on DuckDB and then lifted to Microsoft Fabric. The same dbt models
build on both engines.

Reporting rebuilds everything every night, nobody is sure the numbers are right, and a
single bad SQL edit can sit unnoticed for a week. This project loads only what
changed, tests every layer, and refuses to merge a change that breaks the tests.

## What it does

A Kaggle CSV dump is static, so there is nothing to load incrementally. The first
script slices the orders into one folder per calendar day, which gives a source
that actually changes over time. From there:

```text
archive/ CSVs
  -> generate_batches.py    634 daily folders in data/landing/
  -> ingest.py              append to bronze Delta, stamp arrival metadata
  -> dbt staging            rename and cast only
  -> dbt silver             dedupe on business key, clean, quarantine bad rows
  -> dbt gold               3 dimensions, 2 facts
  -> Power BI               report on gold
```

Bronze is append-only and never cleaned. If the silver logic turns out to be
wrong, it is rebuilt from bronze instead of re-fetching from source.

## Results

Measured on Windows, Python 3.12.10, DuckDB 1.5.5. Numbers come from
data/control/run_log.jsonl and data/benchmark/replay_days.jsonl, not from
estimates.

| Step | Rows | Time |
| --- | ---: | ---: |
| Backfill through 2018-06-30 | 1,484,933 | 60.5 s |
| First full dbt build | 23 models, 61 tests | 12.3 s |
| One replay day, ingest | 467 to 1,590 | 0.37 s median |
| One replay day, dbt | 23 models, 61 tests | 8.5 s median |

A full load takes about a minute. A daily incremental load takes under nine
seconds and touches roughly 1,000 rows instead of 1.5 million.

Gold after the 30-day replay: 105,024 order items, 89,505 customers, 585 sales
days, revenue 12,691,496.09.

In Fabric the backfill produced 98,309 bronze order items, which is exactly what
the local backfill produced. Same data, same cutoff, different engine.

## Tools

Python 3.12, dbt-core with dbt-duckdb and dbt-fabric, Delta Lake, DuckDB,
dbt_expectations, Soda Core v4, sqlfluff, GitHub Actions, Microsoft Fabric
(Lakehouse, Warehouse, Data Factory pipelines), Power BI.

Stable dbt does not run on Python 3.14. Soda Core v3 pins duckdb below 1.1 and
cannot read this warehouse, so v4 is required.

## Running it yourself

Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
from Kaggle and unzip all nine CSVs into `archive/` at the repo root. The CSVs,
the landing folders, bronze and the DuckDB file are all generated or downloaded,
so none of them are in git.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\dbt.exe deps --project-dir transform --profiles-dir transform
```

Then run the full cycle from the repo root:

```powershell
.\.venv\Scripts\python.exe scripts\generate_batches.py --cutoff 2018-06-30
.\.venv\Scripts\python.exe scripts\reset.py
.\.venv\Scripts\python.exe scripts\ingest.py --backfill
.\.venv\Scripts\python.exe scripts\run_dbt.py --run-type full
.\.venv\Scripts\python.exe scripts\replay_days.py --days 30
.\.venv\Scripts\python.exe scripts\run_soda.py
```

reset.py is safe to re-run. It clears bronze, the watermarks, the run log and the
DuckDB file, and leaves landing and archive alone.

A bare ingest.py is refused once landing has been generated. You have to pass
--backfill, --once or --all. That guard exists so the replay queue cannot be
swallowed by accident.

Nothing above needs Azure, Docker or a Fabric account.

## Data quality

dbt build runs 23 models and 61 tests. It prints 84 because it counts both
together.

Every bound was queried from the warehouse first and then set with headroom. Item
price is capped at 15,000 against a measured maximum of 6,735. Review score mean
is bounded 3.5 to 4.7 against a measured 4.076. Nothing was guessed, and no test
was added that the model already filters into being unfailable.

Three layers of checking, each blind to something the others catch:

- dbt generic tests cover shape. Keys unique, foreign keys present, statuses from
  a known list.
- dbt_expectations covers values and distributions. A price of nine million
  passes not_null quite happily.
- Soda Core runs outside dbt, against the warehouse as it stands. If the pipeline
  stops entirely then dbt never runs, so no dbt test ever fails. Silence looks
  exactly like success. Soda is what notices.

Freshness checks watch arrival time, not order date. Order dates here are all
2016 to 2018, so a freshness check on order_date would report the warehouse as
years stale forever and everyone would learn to ignore it.

To see the gate actually fail:

```powershell
.\.venv\Scripts\python.exe scripts\prove_quality_gate.py
```

It copies one real bronze review with a score of 99, watches the named test fail,
appends the original score back, and watches it pass. Bronze stays append-only
throughout. The restore relies on the same delete+insert upsert the incremental
models use every day.

Per-test reasoning lives next to each test in transform/models/schema.yml.

## CI

GitHub Actions is the merge gate. main is protected, a pull request is required,
and the build has to be green before the merge button unlocks.

A CI runner has no Kaggle dump and no bronze, so there is nothing to build
against. The fix is a small committed fixture in transform/seeds: 2,000 orders
plus only the items, payments, reviews, customers, products and sellers those
orders actually reference. Sampling each table independently would have produced
a slice where nothing joins and the referential tests would fail for reasons that
have nothing to do with the code.

bronze_source() reads the seeds when ci_mode is true and bronze parquet
otherwise, so one set of model files serves both. The seeds are only enabled
under ci_mode, so a normal local build does not load fixtures into the real
warehouse.

Some checks cannot be meaningful on a 2,000-order fixture. Row-count contracts
and the review-score mean encode full-warehouse values, and freshness cannot say
anything about a static file. Those are tagged and excluded from CI rather than
having their thresholds loosened, because a widened threshold stops detecting the
thing it exists to detect. They still run at full scale locally.

The gate was proven by opening a pull request with a deliberate bug in the
gross_amount expression. The singular test failed on 2,253 rows and the merge
button went red.

## Fabric

The same models run in Microsoft Fabric. dev on DuckDB, ci on DuckDB with seeds,
and fabric on T-SQL all build from one set of files. Repointing the profile is a
config change, not a rewrite.

A Lakehouse SQL endpoint is read-only, so dbt cannot write T-SQL into one. Bronze
Delta lives in a Lakehouse and silver and gold live in a Warehouse. The Warehouse
reads bronze across the item boundary with three-part naming, so nothing is
copied twice.

Ingestion is metadata-driven. One Data Factory pipeline handles all nine source
tables by reading a control table: source path, file pattern, destination, and
how far that table has got. There are no table names anywhere in the pipeline.
Adding a tenth source is an INSERT, not a new pipeline.

Each table carries its own cursor and advances it only after its own copy
succeeds, so a single failure does not strand or duplicate the others. The loop
runs sequentially because Fabric Warehouse uses snapshot isolation and parallel
updates to the control table abort with a conflict.

Gold feeds a Power BI report: revenue trend, top categories, revenue by state,
and freight cost as a share of revenue by category. Metrics are defined once in
the semantic model rather than in the report, so a second dashboard cannot drift
from the first.

Note that dbt-fabric 1.11 bundles its own driver. The Microsoft ODBC install that
older guides warn about is no longer needed.

## Problems worth mentioning

**The first incremental run silently dropped every new row.** Each replayed day
appended to bronze, but gold stayed frozen. The watermark was on updated_at,
which is a business lifecycle timestamp. After the backfill its maximum was
already 2018-10-17 on orders and 2020-04-09 on items, so every genuinely new July
purchase looked older than the watermark and was rejected. Moving the watermark
to the arrival timestamp fixed it. That column only moves when ingest writes.

**The first Fabric backfill swallowed the replay queue.** The wildcard matched
every landing folder, so the 77 days meant to stay queued were loaded along with
the history. The local script has a guard against exactly this, which forces you
to state your intent, and that guard was not carried across. It is now split into
a backfill pipeline and a daily pipeline, so the intent is structural instead of
a flag someone can forget.

**Ingestion is at-least-once, not exactly-once.** There is a real window between
the data landing and the cursor advancing, and it failed once under a snapshot
isolation conflict. What makes that survivable is silver deduplicating on the
business key. Bronze can double-load and gold still reconciles.

## Layout

```text
scripts/     batch generation, ingest, replay, run logging, quality proof
transform/   dbt project: staging, silver, gold, tests, seeds, macros
soda/        Soda contracts, full-scale and CI
fabric/      Fabric control-table SQL and pipeline definitions
.github/     CI and main workflows
```

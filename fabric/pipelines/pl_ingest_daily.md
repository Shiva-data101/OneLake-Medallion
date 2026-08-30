# pl_ingest_daily

Copies the next unprocessed landing folder into bronze, one table at a time.
Each table's cursor moves only after that table's copy succeeds.

Same job as `python scripts/ingest.py --once` locally.

I did not use an If Condition. Fabric does not allow a ForEach inside one,
and I do not need it. When the replay queue is empty the Lookup returns
zero rows and the ForEach does nothing. No next batch is the stop signal.

## 1. Lookup: `LookupNextBatch`

Connection: `wh_onelake`. First row only: unchecked.

```sql
SELECT
    c.table_name,
    c.file_name,
    c.destination_table,
    (SELECT MIN(b.batch_date)
     FROM meta.landing_batches b
     WHERE b.batch_date > c.last_batch_date) AS batch_date
FROM meta.ingest_control c
WHERE c.is_active = 1
  AND c.load_type = 'daily'
  AND EXISTS (SELECT 1
              FROM meta.landing_batches b
              WHERE b.batch_date > c.last_batch_date);
```

Each table finds its own next batch from its own cursor. If one table's copy
fails, only that table stays behind and retries. The others are not touched.
Nothing is copied twice.

## 2. ForEach: `ForEachTable`

Connected directly to the Lookup on success.

- Items: `@activity('LookupNextBatch').output.value`
- Sequential: checked

I first left Sequential unchecked with batch count 5. Fabric Warehouse uses
snapshot isolation. Five parallel UPDATEs to `ingest_control` aborted with
an update conflict. So I changed ForEach to sequential.

## 3. Copy: `CopyBatch` (inside ForEach)

Source: `lh_bronze`, root folder `Files`, wildcard file path

- Wildcard folder path: `@{concat('landing/', formatDateTime(item().batch_date,'yyyy-MM-dd'))}`
- Wildcard file name: `@{item().file_name}`
- Format: Parquet

Additional columns:

| Name | Value |
| --- | --- |
| `_ingested_at` | `@{utcnow()}` |
| `_source_file` | `$$FILEPATH` |
| `_batch_id` | `@{formatDateTime(item().batch_date,'yyyy-MM-dd')}` |

Destination: `lh_bronze`, root folder `Tables`,
table `@{item().destination_table}`, table action Append.

## 4. Stored procedure: `AdvanceWatermark` (inside ForEach, after Copy, on success)

Connection: `wh_onelake`. Procedure: `meta.sp_update_watermark`

| Parameter | Type | Value |
| --- | --- | --- |
| `table_name` | String | `@{item().table_name}` |
| `batch_date` | String | `@{formatDateTime(item().batch_date,'yyyy-MM-dd')}` |

The cursor moves only after the copy succeeds. Same order as `ingest.py`,
where the watermark write follows the Delta append.

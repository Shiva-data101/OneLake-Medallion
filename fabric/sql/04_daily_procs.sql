-- Advance every daily table's cursor in one call, after a batch is copied.
-- Mirrors the single write to data/control/watermarks.json in ingest.py:
-- the cursor moves only once the copy has actually succeeded.

CREATE PROCEDURE meta.sp_advance_daily_watermark
    @batch_date date
AS
BEGIN
    UPDATE meta.ingest_control
    SET last_batch_date = @batch_date
    WHERE load_type = 'daily' AND is_active = 1;
END
GO

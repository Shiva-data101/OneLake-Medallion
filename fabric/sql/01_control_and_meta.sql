-- Fabric Warehouse: wh_onelake
-- Control tables for the ingest pipeline, plus a run log so I can
-- compare incremental vs full with real numbers, not claims.
--
-- Same idea as local Phase 1:
--   data/control/watermarks.json  ->  meta.ingest_control.last_batch_date
--   data/control/run_log.jsonl    ->  meta.run_log

CREATE SCHEMA meta;
GO

-- One row per source table. A tenth source is an INSERT here, not a new pipeline.
CREATE TABLE meta.ingest_control (
    table_name        varchar(64)  NOT NULL,
    load_type         varchar(16)  NOT NULL,  -- 'daily' | 'reference'
    source_path       varchar(256) NOT NULL,
    file_name         varchar(64)  NOT NULL,
    watermark_column  varchar(64)  NOT NULL,
    last_batch_date   date             NULL,  -- folder cursor. NULL for reference.
    destination_table varchar(64)  NOT NULL,
    is_active         bit          NOT NULL
);
GO

-- Every pipeline and dbt run appends here. Rows, duration, run type.
CREATE TABLE meta.run_log (
    run_id           varchar(64)  NOT NULL,
    layer            varchar(32)  NOT NULL,  -- 'bronze' | 'silver' | 'gold'
    table_name       varchar(64)      NULL,
    batch_date       date             NULL,
    rows_written     bigint           NULL,
    duration_seconds float            NULL,
    run_type         varchar(16)      NULL,  -- 'full' | 'incremental'
    started_at       datetime2(6)     NULL,
    finished_at      datetime2(6)     NULL
);
GO

-- Daily tables sit in landing/YYYY-MM-DD/ folders.
-- last_batch_date starts at the Phase 1 cutoff, so the first pipeline
-- run picks up 2018-07-01. That is the replay queue, 77 folders through 2018-10-17.
INSERT INTO meta.ingest_control
(table_name, load_type, source_path, file_name, watermark_column, last_batch_date, destination_table, is_active)
VALUES
('orders',                      'daily',     'Files/landing',            'orders.parquet',                      '_ingested_at', '2018-06-30', 'bronze_orders',                      1),
('order_items',                 'daily',     'Files/landing',            'order_items.parquet',                 '_ingested_at', '2018-06-30', 'bronze_order_items',                 1),
('order_payments',              'daily',     'Files/landing',            'order_payments.parquet',              '_ingested_at', '2018-06-30', 'bronze_order_payments',              1),
('order_reviews',               'daily',     'Files/landing',            'order_reviews.parquet',               '_ingested_at', '2018-06-30', 'bronze_order_reviews',               1),
('customers',                   'daily',     'Files/landing',            'customers.parquet',                   '_ingested_at', '2018-06-30', 'bronze_customers',                   1),
('products',                    'reference', 'Files/landing/_reference', 'products.parquet',                    '_ingested_at', NULL,         'bronze_products',                    1),
('sellers',                     'reference', 'Files/landing/_reference', 'sellers.parquet',                     '_ingested_at', NULL,         'bronze_sellers',                     1),
('geolocation',                 'reference', 'Files/landing/_reference', 'geolocation.parquet',                 '_ingested_at', NULL,         'bronze_geolocation',                 1),
('product_category_translation','reference', 'Files/landing/_reference', 'product_category_translation.parquet','_ingested_at', NULL,         'bronze_product_category_translation',1);
GO

-- Pipeline calls this after that table's folder is copied, so the cursor
-- moves only then. I first ran five of these in parallel. Fabric Warehouse
-- uses snapshot isolation, so those UPDATEs aborted with an update conflict.
-- ForEach on pl_ingest_daily is sequential now.
CREATE PROCEDURE meta.sp_update_watermark
    @table_name varchar(64),
    @batch_date date
AS
BEGIN
    UPDATE meta.ingest_control
    SET last_batch_date = @batch_date
    WHERE table_name = @table_name;
END
GO

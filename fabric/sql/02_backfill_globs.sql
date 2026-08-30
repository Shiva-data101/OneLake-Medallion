-- Backfill only through the Phase 1 cutoff (2018-06-30 inclusive).
--
-- A Copy activity wildcard cannot say "folder date <= cutoff". So I split
-- the range into folder-name patterns and stored them as data. The pipeline
-- cross-joins these against the active daily tables: 5 tables x 8 globs = 40
-- copies, plus 4 reference tables. The pipeline itself has no date logic.
--
-- Everything after the cutoff (2018-07-01 to 2018-10-17, 77 folders) stays
-- in landing. That is the replay queue. pl_ingest_daily consumes it.

CREATE TABLE meta.backfill_globs (
    folder_glob varchar(64) NOT NULL
);
GO

INSERT INTO meta.backfill_globs (folder_glob) VALUES
('landing/2016-*'),
('landing/2017-*'),
('landing/2018-01-*'),
('landing/2018-02-*'),
('landing/2018-03-*'),
('landing/2018-04-*'),
('landing/2018-05-*'),
('landing/2018-06-*');
GO

-- Put the cursor back where Phase 1 left it, after the backfill copies.
UPDATE meta.ingest_control
SET last_batch_date = '2018-06-30'
WHERE load_type = 'daily';
GO

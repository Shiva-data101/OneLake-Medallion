-- Scope the backfill to the Phase 1 cutoff (2018-06-30 inclusive).
--
-- A Copy activity wildcard cannot express "folder date <= cutoff", so the date
-- range is decomposed into folder-name patterns and stored as data. The pipeline
-- cross-joins these against the active daily tables: 5 tables x 8 globs = 40
-- copies, plus 4 reference tables. Still zero logic in the pipeline itself.
--
-- Everything after the cutoff (2018-07-01 .. 2018-10-17, 77 folders) stays in
-- landing as the replay queue, which is what pl_ingest_daily consumes.

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

-- Put the cursor back where Phase 1 left it.
UPDATE meta.ingest_control
SET last_batch_date = '2018-06-30'
WHERE load_type = 'daily';
GO

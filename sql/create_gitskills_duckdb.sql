-- GitSkills SQLite -> DuckDB import
--
-- Creates a local DuckDB copy of the MSR GitSkills dataset with:
--   * surrogate BIGINT id columns on repos, artifacts, and artifact_siblings
--   * repo_id on artifacts, populated from repos.id
--   * artifact_id on artifact_siblings, populated from artifacts.id
--   * mining_runs.run_id retained as the logical identifier
--
-- The imported tables are read-only analysis tables. Primary-key constraints
-- are intentionally not created to avoid the cost of building ART indexes.
-- The original source columns are preserved for traceability.

INSTALL sqlite;
LOAD sqlite;

SET VARIABLE sqlite_source_db = getenv('GITSKILLS_SQLITE_DB');


-- ============================================================
-- repos
-- ============================================================

CREATE TABLE repos AS
SELECT
    row_number() OVER ()::BIGINT AS id,
    r.*
FROM sqlite_scan(getvariable('sqlite_source_db'), 'repos') AS r;


-- ============================================================
-- artifacts
-- ============================================================

CREATE TABLE artifacts AS
SELECT
    row_number() OVER ()::BIGINT AS id,
    r.id AS repo_id,
    a.*
FROM sqlite_scan(getvariable('sqlite_source_db'), 'artifacts') AS a
LEFT JOIN repos AS r ON r.full_name = a.repo_full_name;


-- ============================================================
-- artifact_siblings
-- ============================================================

CREATE TABLE artifact_siblings AS
SELECT
    row_number() OVER ()::BIGINT AS id,
    a.id AS artifact_id,
    s.*
FROM sqlite_scan(getvariable('sqlite_source_db'), 'artifact_siblings') AS s
LEFT JOIN artifacts AS a ON a.repo_full_name = s.repo_full_name
AND a.path = s.artifact_path;


-- ============================================================
-- mining_runs
-- ============================================================

CREATE TABLE mining_runs AS
SELECT *
FROM sqlite_scan(getvariable('sqlite_source_db'), 'mining_runs');


-- ============================================================
-- Validation
-- ============================================================

-- These should both return 0.
SELECT COUNT(*) AS unresolved_repo_ids
FROM artifacts
WHERE repo_id IS NULL;

SELECT COUNT(*) AS unresolved_artifact_ids
FROM artifact_siblings
WHERE artifact_id IS NULL;


-- Imported row counts should match source row counts.
SELECT
    'repos' AS table_name,
    (SELECT COUNT(*) FROM sqlite_scan(getvariable('sqlite_source_db'), 'repos')) AS source_count,
    (SELECT COUNT(*) FROM repos) AS imported_count

UNION ALL

SELECT
    'artifacts',
    (SELECT COUNT(*) FROM sqlite_scan(getvariable('sqlite_source_db'), 'artifacts')),
    (SELECT COUNT(*) FROM artifacts)

UNION ALL

SELECT
    'artifact_siblings',
    (SELECT COUNT(*) FROM sqlite_scan(getvariable('sqlite_source_db'), 'artifact_siblings')),
    (SELECT COUNT(*) FROM artifact_siblings)

UNION ALL

SELECT
    'mining_runs',
    (SELECT COUNT(*) FROM sqlite_scan(getvariable('sqlite_source_db'), 'mining_runs')),
    (SELECT COUNT(*) FROM mining_runs);

CHECKPOINT;

-- Build the frozen Sprint 1 sample tables.
--
-- The sample population is defined by stable source identifiers:
--   repo_full_name + path + file_sha
--
-- Local surrogate IDs are intentionally not used to identify
-- the frozen sample across independent database builds.


-- ============================================================
-- Sample selections
-- ============================================================

DROP TABLE IF EXISTS sample_selections;

CREATE TABLE sample_selections AS
WITH manifest AS (
    SELECT *
    FROM read_csv_auto(
        'data/sample_population.csv',
        header = true
    )
)
SELECT
    m.selection_type,
    m.selection_level,

    a.id AS artifact_id,
    a.repo_id,

    g.name,
    g.normalized_description,
    g.artifact_group_size,

    a.repo_full_name,
    a.path,
    a.file_sha,
    a.content,
    a.first_commit_at,

    g.sibling_file_count,
    g.sibling_content_sha,

    m.notes

FROM manifest AS m

JOIN artifacts AS a
    ON a.repo_full_name = m.repo_full_name
   AND a.path = m.path
   AND a.file_sha = m.file_sha

JOIN artifact_groupings AS g
    ON g.artifact_id = a.id;


-- ============================================================
-- Sample siblings
-- ============================================================

DROP TABLE IF EXISTS sample_siblings;

CREATE TABLE sample_siblings AS
WITH selected_artifacts AS (
    SELECT DISTINCT
        artifact_id,
        repo_full_name,
        path,
        file_sha
    FROM sample_selections
)
SELECT
    s.repo_full_name,
    s.artifact_path,
    a.file_sha AS parent_file_sha,

    s.entry_name,
    s.entry_type,
    s.entry_size,
    s.entry_sha,
    s.content,
    s.content_fetched,
    s.skipped_reason

FROM selected_artifacts AS selected

JOIN artifacts AS a
    ON a.id = selected.artifact_id

JOIN artifact_siblings AS s
    ON s.artifact_id = a.id;


-- ============================================================
-- Sample repositories
-- ============================================================

DROP TABLE IF EXISTS sample_repos;

CREATE TABLE sample_repos AS
SELECT DISTINCT
    r.*
FROM repos AS r
JOIN (
    SELECT DISTINCT repo_id
    FROM sample_selections
) AS s
    ON s.repo_id = r.id;


-- ============================================================
-- Validation
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM sample_selections)
        AS sample_selection_rows,

    (SELECT COUNT(DISTINCT artifact_id)
     FROM sample_selections)
        AS unique_sample_artifacts,

    (SELECT COUNT(*) FROM sample_siblings)
        AS sample_sibling_rows,

    (SELECT COUNT(*) FROM sample_repos)
        AS sample_repo_rows;
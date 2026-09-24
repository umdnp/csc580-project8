-- Update derived sibling metadata for artifact_groupings.
--
-- artifact_groupings.id uses the same value as artifacts.id.
--
-- For each grouped artifact with a complete sibling composition:
--   * sibling_file_count = number of sibling entries where entry_type = 'file'
--   * sibling_content_sha = SHA-256 of the sorted multiset of sibling file entry_sha values
--
-- Directory entries are excluded.
-- Actual sibling file content is not read or hashed.
--
-- If composition was not fetched, was truncated, or any sibling file is
-- missing entry_sha, both derived columns remain NULL.
--
-- A valid artifact with zero sibling files receives:
--   sibling_file_count = 0
--   sibling_content_sha = sha256('')

BEGIN TRANSACTION;

-- Reset derived values so this script can be rerun safely.
UPDATE artifact_groupings
SET
    sibling_file_count = NULL,
    sibling_content_sha = NULL;


WITH sibling_stats AS (
    SELECT
        g.id,
        COUNT(*) FILTER (
            WHERE s.entry_type = 'file'
        ) AS sibling_file_count,
        COUNT(s.entry_sha) FILTER (
            WHERE s.entry_type = 'file'
        ) AS sibling_sha_count,
        string_agg(
            s.entry_sha,
            '|' ORDER BY s.entry_sha
        ) FILTER (
            WHERE s.entry_type = 'file'
              AND s.entry_sha IS NOT NULL
        ) AS sibling_sha_list
    FROM artifact_groupings AS g
    JOIN artifacts AS a ON a.id = g.id
    LEFT JOIN artifact_siblings AS s ON s.artifact_id = g.id
    WHERE a.composition_fetched = 1
      AND a.composition_truncated = 0
    GROUP BY g.id
)
UPDATE artifact_groupings AS g
SET
    sibling_file_count = s.sibling_file_count,
    sibling_content_sha = sha256(coalesce(s.sibling_sha_list, ''))
FROM sibling_stats AS s
WHERE s.id = g.id
  AND s.sibling_file_count = s.sibling_sha_count;

COMMIT;


-- ============================================================
-- Validation summary
-- ============================================================

SELECT
    COUNT(*) AS artifact_count,
    COUNT(*) FILTER (
        WHERE sibling_file_count IS NOT NULL
    ) AS sibling_data_populated,
    COUNT(*) FILTER (
        WHERE sibling_file_count = 0
    ) AS zero_sibling_files,
    COUNT(*) FILTER (
        WHERE sibling_file_count IS NULL
    ) AS sibling_data_unavailable
FROM artifact_groupings;

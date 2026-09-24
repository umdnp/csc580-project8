-- Analysis tables for the GitSkills project database.


-- ============================================================
-- Artifact groupings
-- ============================================================
--
-- Groups related artifacts by exact name and normalized description.
-- Only groups containing at least two artifacts are retained.
--
-- The id column uses the same value as artifacts.id, providing a
-- one-to-one relationship back to the source artifact.
--
-- Artifacts without first_commit_at are excluded because they cannot
-- participate in chronological comparison.
--
-- sibling_file_count and sibling_content_sha are initialized to NULL
-- and can be populated later from artifact_siblings.

DROP TABLE IF EXISTS artifact_groupings;

CREATE TABLE artifact_groupings AS
WITH filtered AS (
    SELECT
        a.id,
        a.repo_id,
        a.name,
        regexp_replace(
            lower(trim(a.description)),
            '\s+',
            ' ',
            'g'
        ) AS normalized_description,
        a.first_commit_at
    FROM artifacts AS a
    WHERE a.frontmatter_valid = 1
      AND a.location_class IN ('canonical', 'skills-dir')
      AND lower(a.filename) = 'skill.md'
      AND a.body_chars > 50
      AND a.content IS NOT NULL
      AND a.name IS NOT NULL
      AND a.description IS NOT NULL
      AND a.first_commit_at IS NOT NULL
),
groups AS (
    SELECT
        name,
        normalized_description,
        COUNT(*) AS artifact_group_size
    FROM filtered
    GROUP BY
        name,
        normalized_description
    HAVING COUNT(*) >= 2
)
SELECT
    f.id,
    f.repo_id,
    f.name,
    f.normalized_description,
    g.artifact_group_size,
    NULL::BIGINT AS sibling_file_count,
    NULL::VARCHAR AS sibling_content_sha
FROM filtered AS f
JOIN groups AS g
    ON g.name = f.name
   AND g.normalized_description = f.normalized_description;

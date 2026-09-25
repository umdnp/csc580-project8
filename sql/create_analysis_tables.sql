-- Analysis tables for the GitSkills project database.

-- ============================================================
-- Artifact groupings
-- ============================================================
--
-- Groups related artifacts by exact name and normalized description.
--
-- A skill name must appear in at least two qualifying artifacts to be
-- retained. Within an eligible name, each distinct name + normalized
-- description combination forms its own artifact group. This allows a
-- description variant that appears only once to remain available for
-- comparison when other artifacts share the same skill name.
--
-- The id column identifies the artifact group. Multiple rows can share
-- the same id when they have the same name and normalized description.
--
-- artifact_id links each group member back to artifacts.id.
-- repo_id links each group member back to repos.id.
--
-- sibling_file_count and sibling_content_sha are initialized to NULL
-- and can be populated later from artifact_siblings.

DROP TABLE IF EXISTS artifact_groupings;

CREATE TABLE artifact_groupings AS
WITH filtered AS (
    SELECT
        a.id AS artifact_id,
        a.repo_id,
        a.name,
        regexp_replace(
            lower(trim(a.description)),
            '\s+',
            ' ',
            'g'
        ) AS normalized_description
    FROM artifacts AS a
    WHERE a.frontmatter_valid = 1
      AND a.location_class IN ('canonical', 'skills-dir')
      AND lower(a.filename) = 'skill.md'
      AND a.body_chars > 50
      AND a.content IS NOT NULL
      AND a.name IS NOT NULL
      AND a.description IS NOT NULL
),
eligible_names AS (
    SELECT
        name
    FROM filtered
    GROUP BY name
    HAVING COUNT(*) >= 2
),
groups AS (
    SELECT
        f.name,
        f.normalized_description,
        COUNT(*) AS artifact_group_size
    FROM filtered AS f
    JOIN eligible_names AS e ON e.name = f.name
    GROUP BY
        f.name,
        f.normalized_description
),
group_ids AS (
    SELECT
        row_number() OVER ()::BIGINT AS id,
        name,
        normalized_description,
        artifact_group_size
    FROM groups
)
SELECT
    g.id,
    f.artifact_id,
    f.repo_id,
    f.name,
    f.normalized_description,
    g.artifact_group_size,
    NULL::BIGINT AS sibling_file_count,
    NULL::VARCHAR AS sibling_content_sha
FROM filtered AS f
JOIN eligible_names AS e ON e.name = f.name
JOIN group_ids AS g ON g.name = f.name
 AND g.normalized_description = f.normalized_description;

# Sample Population Queries
These queries supported selection of a small, purposeful Sprint 1 sample for validating the family-analysis and scanner workflow. They were screening heuristics, not validated risk findings or a representative sampling procedure. Candidate families were checked through the Python workflow, and selected comparisons were inspected manually in Mergely; this does not imply that every comparison was manually validated.

Here, a family consists of artifacts sharing an exact name. Some screening steps compare only artifacts within the same name-and-normalized-description group, whereas `analyze_family` loads qualifying artifacts across description groups for the exact name. SQL hit-count differences therefore identify candidates for further analysis; they do not establish relatedness, comparison direction, or increased risk.

## Query 1 - Find Potential Families
### Rationale
This query identifies manageable exact-name families containing different file versions and variation in package-installation screening counts. The displayed configuration selects families with 5–15 artifact-grouping rows, at least two distinct file hashes, and no missing hashes or content. It attempts to remove leading YAML frontmatter before counting matches for selected package-installation commands.

A family qualifies when at least one pair within the same normalized-description group has different file hashes and different screening counts. Families with a qualifying pair whose commit timestamps parse successfully and differ are ranked first, followed by smaller families. The query selects up to ten families and returns all screened members of those families, not just the qualifying pairs.

The rationale is to find compact cases that may exercise family analysis and scanner-count changes. Different hashes and dates do not establish lineage, and these package-installation patterns do not guarantee a Python scanner delta. Relatedness, supported direction, and scanner results must be assessed through the Python workflow. Earlier family-size and result-limit settings are recorded in the unchanged SQL comments.

```sql
-- Locate small families that have lineage tracing and could generate results based on scan_diff rules
-- Comments added for lines that were manipulated to alter results
WITH small_families AS (
    SELECT
        g.name,
        COUNT(*) AS artifact_count
    FROM artifact_groupings AS g
    JOIN artifacts AS a ON a.id = g.artifact_id
    GROUP BY g.name
    HAVING COUNT(*) BETWEEN 5 AND 15 --Change this to alter the artifact count. Original output was 3 AND 10
       AND COUNT(DISTINCT a.file_sha) >= 2
       AND COUNT(a.file_sha) = COUNT(*)
       AND COUNT(a.content) = COUNT(*)
),
bodies AS (
    SELECT
        g.name,
        g.normalized_description,
        a.repo_full_name,
        a.path,
        a.file_sha,
        a.first_commit_at,
        regexp_replace(
            a.content,
            '^\x{FEFF}?---[ \t]*(?:\r\n|\n|\r).*?\n---[ \t]*(?:\r\n|\n|\r|$)',
            '',
            's'
        ) AS body
    FROM artifact_groupings AS g
    JOIN small_families AS f ON f.name = g.name
    JOIN artifacts AS a ON a.id = g.artifact_id
),
screened AS (
    SELECT
        *,
        array_length(
            regexp_extract_all(
                body,
                '\b(?:pip(?:3)?[ \t]+install|npm[ \t]+install|npm[ \t]+i|(?:apt(?:-get)?|dnf|yum|brew)[ \t]+install)\b',
                0,
                'i'
            )
        ) AS package_install_hits
    FROM bodies
),
candidate_pairs AS (
    SELECT
        l.name,
        CASE
            WHEN TRY_CAST(l.first_commit_at AS TIMESTAMP)
                 <> TRY_CAST(r.first_commit_at AS TIMESTAMP)
            THEN 1 ELSE 0
        END AS has_distinct_dates
    FROM screened AS l
    JOIN screened AS r
      ON l.name = r.name
     AND l.normalized_description = r.normalized_description
     AND l.file_sha < r.file_sha
    WHERE l.package_install_hits <> r.package_install_hits
),
chosen_family AS (
    SELECT
        p.name,
        f.artifact_count,
        MAX(p.has_distinct_dates) AS has_dated_test_pair
    FROM candidate_pairs AS p
    JOIN small_families AS f ON f.name = p.name
    GROUP BY p.name, f.artifact_count
    ORDER BY
        has_dated_test_pair DESC,
        f.artifact_count ASC,
        p.name ASC
    LIMIT 10 --Change this to output more rows. Original use was 1, then upped to 5, and now 10
)
SELECT
    s.name,
    f.artifact_count,
    f.has_dated_test_pair,
    s.normalized_description,
    s.repo_full_name,
    s.path,
    s.file_sha,
    s.first_commit_at,
    s.package_install_hits
FROM screened AS s
JOIN chosen_family AS f ON f.name = s.name
ORDER BY
    s.name,
    s.normalized_description,
    s.package_install_hits,
    s.repo_full_name,
    s.path,
    s.file_sha;
```

## Query 2 - Find "declared source" samples
### Rationale
This query screens for field-like references to the supported provenance keys `derived_from`, `upstream_skill`, `source_repo`, and `upstream_source`. It searches content line by line and reports the artifact ID, matching field, line number, and full exact-name family size. Ordering by family size prioritizes smaller families for review; the limit applies to 50 matching lines, not 50 families, and there is no explicit family-size cutoff.

The rationale is to locate candidates that may exercise declared-provenance handling. This is a text search across the entire document, not a YAML frontmatter parser. The `exact_top_level_spelling` flag identifies lines beginning with the exact lowercase field spelling followed immediately by a colon; it does not establish that the field occurs in valid frontmatter or resolves to a source artifact.

Candidates require follow-up to determine whether the metadata is recognized, whether its source resolves within the loaded exact-name family, and whether a relationship is inferred. A matching declaration alone does not establish a directed relationship or prove historical copying. Unresolved declarations can also provide useful limitation cases.

```sql
-- Locate "declared source" examples to add to Sprint 1 Sample.
-- Locate field-like declarations and show full family sizes.
WITH family_sizes AS (
    SELECT name, COUNT(*) AS family_size
    FROM artifact_groupings
    GROUP BY name
),
candidate_lines AS (
    SELECT
        g.name,
        g.artifact_id,
        f.family_size,
        lines.line_number,
        regexp_extract(
            lines.line,
            '(derived_from|upstream_skill|source_repo|upstream_source)[ \t]*:',
            1,
            'i'
        ) AS matched_field,
        regexp_matches(
            lines.line,
            '^(derived_from|upstream_skill|source_repo|upstream_source):'
        ) AS exact_top_level_spelling
    FROM artifact_groupings AS g
    JOIN family_sizes AS f ON f.name = g.name
    JOIN artifacts AS a ON a.id = g.artifact_id
    CROSS JOIN UNNEST(
        string_split(
            replace(
                replace(a.content, chr(13) || chr(10), chr(10)),
                chr(13),
                chr(10)
            ),
            chr(10)
        )
    ) WITH ORDINALITY AS lines(line, line_number)
    WHERE regexp_matches(
        lines.line,
        '(derived_from|upstream_skill|source_repo|upstream_source)[ \t]*:',
        'i'
    )
)
SELECT *
FROM candidate_lines
ORDER BY
    family_size,
    name,
    artifact_id,
    line_number
LIMIT 50;
```

## Query 3 - Find samples that trigger scan_diff rules not already exercised
### Rationale
This query supports a bounded follow-up search for variation in scanner rules not yet demonstrated by the selected sample. It processes batches of up to 100 exact-name families containing 2–15 artifact-grouping rows, ordered by name. The displayed offset is 300; changing the offset selects another batch. This batching limits processing effort and is not random or exhaustive sampling.

Within each batch, the query excludes records with missing content or hashes, normalizes line endings, collapses duplicate selected records, and attempts to remove leading YAML frontmatter. Approximate screening patterns count matches by rule and file version. A name-and-description group qualifies when at least two distinct hashes are present and its minimum and maximum counts differ. Up to 25 families are then ranked by the number of target rules with variation, followed by smaller family size. Reported ranges summarize qualifying groups; they are not directed pairwise scanner deltas.

Although the retained Stage 3 comment refers to five target rules, this saved version has four active patterns: NET-002, FS-002, EXT-001, and SYS-001. FS-001 is commented out. The exclusion values in `name NOT IN (...)` have also been omitted, so this documented version requires those values to be restored before execution. Omitting them does not establish anonymity.

The rationale is to find additional validation cases efficiently, not to establish rule coverage from SQL alone. The query performs no similarity analysis or direction inference, and its patterns approximate the Python scanner. Candidate families therefore require follow-up through the Python workflow to confirm actual rule-count deltas or introduced capabilities. A count change within an existing capability is different from a newly detected capability, and neither alone establishes a change in risk. The search ended because further screening was time-consuming; it was not exhaustive or statistically optimized.

```sql
-- Stage 1: Freeze a bounded list before processing artifact content.
-- Temporary tables last only for the current database connection.

CREATE OR REPLACE TEMP TABLE rule_search_batch AS
SELECT
    name,
    COUNT(*) AS artifact_count
FROM artifact_groupings
WHERE name NOT IN (
    -- Criteria explicitly omitted to preserve data anonymity. References the artifact_id field in sample_population.csv to deduce names.
)
GROUP BY name
HAVING COUNT(*) BETWEEN 2 AND 15
ORDER BY name
LIMIT 100 OFFSET 300; --Limits runtime, original offset set to 0. Increment by 100 to choose different dataset to analyze.


-- Stage 2: Read and normalize content only for this batch.
-- Collapse repeated copies of the same version.

CREATE OR REPLACE TEMP TABLE rule_search_bodies AS
WITH normalized AS (
    SELECT DISTINCT
        g.name,
        g.normalized_description,
        a.file_sha,
        replace(
            replace(a.content, chr(13) || chr(10), chr(10)),
            chr(13),
            chr(10)
        ) AS content
    FROM artifact_groupings AS g
    JOIN rule_search_batch AS b ON b.name = g.name
    JOIN artifacts AS a ON a.id = g.artifact_id
    WHERE a.content IS NOT NULL
      AND a.file_sha IS NOT NULL
)
SELECT
    name,
    normalized_description,
    file_sha,
    regexp_replace(
        content,
        '^\x{FEFF}?---[ \t]*\n.*?\n---[ \t]*(?:\n|$)',
        '',
        's'
    ) AS body
FROM normalized;


-- Stage 3: Screen for the five target rules.
-- These patterns approximate the Python rules.
-- No edit-distance or similarity calculations are performed.

CREATE OR REPLACE TEMP TABLE rule_search_hits AS
WITH patterns(rule_id, pattern) AS (
    VALUES
        (
            'NET-002',
            '\b(curl|wget)[ \t]+[^\s`]'
            || '|\brequests\.(get|post|put|patch|delete|head)[ \t]*\('
        ),
        /*( --Commented out to search for other rules
            'FS-001',
            '\b(rm|mv|cp|mkdir|touch)[ \t]+[^\s`]'
        ),*/
        (
            'FS-002',
            '\bopen[ \t]*\([^\n]*,[ \t]*["''][^"'']*[wax+][^"'']*["'']'
            || '|\.(write_text|write_bytes|write)[ \t]*\('
        ),
        (
            'EXT-001',
            '\b(curl|wget)\b[^\n|]*\|[ \t]*(bash|sh|zsh)\b'
        ),
        (
            'SYS-001',
            '\bsudo[ \t]+[^\s`]'
            || '|\bsu[ \t]+(-|--login|\w+)'
        )
)
SELECT
    b.name,
    b.normalized_description,
    b.file_sha,
    p.rule_id,
    array_length(
        regexp_extract_all(b.body, p.pattern, 0, 'i')
    ) AS hit_count
FROM rule_search_bodies AS b
CROSS JOIN patterns AS p;


-- Stage 4: Save up to 25 promising families from this batch.
-- Require count variation within the same name-and-description group.

CREATE OR REPLACE TEMP TABLE rule_search_shortlist AS
WITH varying_groups AS (
    SELECT
        name,
        normalized_description,
        rule_id,
        MIN(hit_count) AS min_hits,
        MAX(hit_count) AS max_hits
    FROM rule_search_hits
    GROUP BY name, normalized_description, rule_id
    HAVING COUNT(DISTINCT file_sha) >= 2
       AND MIN(hit_count) < MAX(hit_count)
),
family_rules AS (
    SELECT
        name,
        rule_id,
        MIN(min_hits) AS min_hits,
        MAX(max_hits) AS max_hits
    FROM varying_groups
    GROUP BY name, rule_id
)
SELECT
    r.name,
    b.artifact_count,
    COUNT(*) AS target_rules_with_variation,
    string_agg(
        r.rule_id || ': '
        || CAST(r.min_hits AS VARCHAR) || ' to '
        || CAST(r.max_hits AS VARCHAR),
        '; ' ORDER BY r.rule_id
    ) AS screening_hit_ranges
FROM family_rules AS r
JOIN rule_search_batch AS b ON b.name = r.name
GROUP BY r.name, b.artifact_count
ORDER BY
    target_rules_with_variation DESC,
    b.artifact_count ASC,
    r.name ASC
LIMIT 25;


-- Return the candidate list, without source content.
SELECT *
FROM rule_search_shortlist
ORDER BY
    target_rules_with_variation DESC,
    artifact_count ASC,
    name ASC;
```
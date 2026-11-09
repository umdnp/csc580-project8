\clearpage


# Appendix A Dataset construction and preparation

## Candidate selection

GitSkills is imported from the released SQLite database into a separate DuckDB database. The following query from `sql/create_analysis_tables.sql` materializes the comparison candidates without changing the source `artifacts` table.

```sql
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
```

Candidates require valid frontmatter, more than 50 body characters, available content/name/description, and at least two qualifying occurrences with the same exact name. These conditions select analyzable comparison candidates; they do not establish safety, reuse, or common ancestry. Short, malformed, metadata-poor, and singleton skills are excluded.

Descriptions are lowercased, trimmed, and whitespace-normalized for subgrouping. Family analysis compares across description subgroups within the same exact name, preserving candidates whose descriptions changed. The repeated-name requirement counts occurrences, including identical copies, rather than distinct content or repositories.

## Preparation workflow

The activity diagram connects candidate preparation to the end-to-end cohort analysis. Preparation counts come from the October 15, 2026 local audit; the three Sprint 3 samples are drawn from a separately screened subset of this candidate pool.

```{#fig-preparation .plantuml source="report/diagrams/preparation-activity.puml" width="100%" .fullpage .wide caption="Candidate preparation and the end-to-end cohort analysis workflow."}
```


## Selection audit and identity

| Cumulative selection stage | Retained artifacts | Excluded at this step |
| --- | ---: | ---: |
| All source artifact occurrences | 3,797,117 | - |
| `frontmatter_valid = 1` | 1,627,753 | 2,169,364 |
| `body_chars > 50` | 1,621,757 | 5,996 |
| `content IS NOT NULL` | 1,621,757 | 0 |
| `name IS NOT NULL` | 1,621,757 | 0 |
| `description IS NOT NULL` | 1,621,757 | 0 |
| Exact name occurs in at least two qualifying rows | 943,257 | 678,500 |

: Candidate-selection audit for the prepared GitSkills snapshot {.wide}

The audit retained 943,257 occurrences in 162,995 exact-name families. These are **not** the final family-selection pool or results denominator. The Sprint 3 family picker excluded names unsuitable for one-name-per-line selection, screened distinct main-file/sibling hash states, and checked for at least one usable primary directed comparison. Its sampling reports list 162,461 candidates at the preliminary selection stage; **not all of these candidates pass relationship validation**. The final analysis covers 300 randomly selected, validated families and 6,570 loaded artifact occurrences across three non-overlapping trials.

Artifact and description-group numbers are local to the prepared database. The query assigns group numbers without an explicit ordering, so cross-build reconciliation must use the dataset snapshot, repository/path identity, and content hashes. The sibling fields begin as null placeholders; subsequent enrichment distinguishes known empty bundles from unavailable or incomplete sibling evidence. Null must not be interpreted as an empty bundle.

## Sprint 3 sample audit

The following counts come from the saved `sampling_report.json` files. A rejection means that the candidate failed the family picker's relationship validation, **not** that it contained no security-sensitive behavior. The picker replaced rejected candidates in the same stratum.

| Sample | Seed | Families selected | Candidates rejected during drawing | Previously selected families excluded |
| --- | ---: | ---: | ---: | ---: |
| Trial 1 | 5801 | 100 | 239 | 0 |
| Trial 2 | 5802 | 100 | 288 | 100 |
| Trial 3 | 5803 | 100 | 247 | 200 |

: Sprint 3 sample seeds and family-selection audit

Each trial retains the same 20/55/20/4/1 size allocation described in Section 5. The sampling reports preserve the rejection reasons, source database identity, thresholds, excluded `families.txt` paths and checksums, and exact selected names. The 162,461 preliminary candidates are **not** an eligible-population denominator for estimating risk prevalence, because a validated primary directed relationship is required to enter the study.

\clearpage

# Dataset and Data Preparation

This section describes the dataset source, study scope, data schema, sampling strategy, eligibility filters, preprocessing steps, and safety controls used to construct the analysis-ready data. The detailed algorithms and implementation pipeline are described in the Method and Implementation section.

## Dataset Source and Acquisition

The source dataset for this study is `agent_skills_release.db`, the GitSkills database provided for the MSR 2027 Mining Challenge. The source population consists of all GitSkills artifact records contained in the database.

[TODO: Add the approved dataset access instructions, release or snapshot identifier, file integrity information, and the date on which the database was obtained. Explain that the full database is not committed to the project repository and identify the expected local storage location.]

## Dataset Scope

The study distinguishes three populations:

1. **Source population:** All GitSkills artifact records in `agent_skills_release.db`.
2. **Analyzable artifact population:** Records from the source population that contain stored skill content that the static analyzer can process.
3. **Eligible comparison population:** Ordered base-derived comparisons that can be extracted from the database and satisfy the eligibility criteria defined below.

Artifacts without analyzable content or without an identifiable, ordered relationship remain part of the source population, but they are not part of the eligible comparison population. The pipeline will report the number of records and candidate relationships excluded at each stage and the reasons for exclusion.

The local selection audit below verifies 3,797,117 source occurrences and 943,257 retained candidates. Candidate membership is narrower than the population of all records with stored text. Counts of unique analyzed content SHAs, supported relationships, completed scans, and final eligible directed comparisons still require the corresponding pipeline run; they cannot be inferred from the candidate-table row count.

## Candidate-Population Reduction

### From the Source Release to Comparison Candidates

The source release contains approximately 3.8 million discovered file occurrences, often rounded to four million. These are artifact occurrences rather than four million distinct skill contents or four million eligible comparisons. The setup in `data/README.md` imports the SQLite release into a separate DuckDB database, then invokes `sql/create_analysis_tables.sql` to materialize `artifact_groupings`. The selection leaves the source `artifacts` table intact. It narrows the candidate population for reuse analysis rather than deleting source records or drawing a random sample.

The following is the executable candidate-selection statement from `sql/create_analysis_tables.sql`. The preceding `DROP TABLE IF EXISTS artifact_groupings` rebuilds only the derived table; it is not a source-data exclusion criterion.

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

### Preparation Workflow

The activity diagram summarizes the implemented candidate reduction and two separate analysis objectives. The branch represents a chosen workflow, not concurrent execution or a claim that the planned population census has been completed. Counts describe the local selection audit; the Sprint 1 path uses a purposeful subset.

```{#fig-preparation .plantuml source="report/diagrams/preparation-activity.puml" width="5.6in" caption="Activity diagram of candidate preparation and the family-review and Sprint 1 validation paths."}
```

### Content and Metadata Filters

The `filtered` common table expression (CTE) selects each artifact's identifier, repository identifier, exact name, and normalized description. A CTE names an intermediate query result so later stages can refer to the same selection logic. The `WHERE` conditions are combined with `AND`, so every condition must be satisfied; a missing value in either numeric condition does not pass the filter.

| SQL condition | What it retains | Methodological rationale and cost |
| --- | --- | --- |
| `a.frontmatter_valid = 1` | Records marked as having valid frontmatter | Provides structured skill metadata for candidate construction. It can exclude useful instructions with missing or malformed frontmatter; it is a format-quality criterion, not a security judgment. |
| `a.body_chars > 50` | Bodies with strictly more than 50 characters | Screens out very short or near-empty bodies before comparison. Fifty characters is a pragmatic screening threshold, not a validated minimum for meaningful behavior or a guarantee of enough five-token shingles. Short legitimate skills can be excluded. |
| `a.content IS NOT NULL` | Occurrences with stored text available | Similarity and static scanning require analyzable text. Missing stored content cannot be interpreted as empty or safe content; availability can reflect the dataset's representative-enrichment strategy. |
| `a.name IS NOT NULL` | Records with a parsed name | The implemented candidate loader uses exact-name families. Without a name, an artifact cannot enter that search space; related artifacts lacking metadata will be missed. |
| `a.description IS NOT NULL` | Records with a parsed description | Allows the query to construct description-based groups consistently. This is required by the current grouping design, even though exact-name family loading does not require descriptions to match. Missing descriptions can therefore exclude otherwise useful same-name candidates. |

These tests check non-nullness, not nonempty trimmed strings. The query does not explicitly reject blank names or descriptions, require a particular filename or directory, restrict natural language, require commit dates, retain only `dedup_primary` rows, or filter for security-rule matches. In particular, selecting records with valid frontmatter is different from scanning frontmatter: metadata supports candidate selection and provenance, while behavioral scans normally exclude that metadata.

### Description Normalization

`trim(a.description)` removes leading and trailing whitespace; `lower(...)` removes case distinctions; and `regexp_replace(..., '\s+', ' ', 'g')` replaces every run of whitespace with a single space. The rationale is to avoid splitting description groups because of formatting or capitalization alone. This does not remove punctuation, translate prose, or establish semantic equivalence. The name is copied unchanged: matching remains exact and case-sensitive under the query's ordinary string equality.

### Repeated Names and Description Groups

`eligible_names` groups the already-filtered rows by exact `name` and applies `HAVING COUNT(*) >= 2`. At least two qualifying occurrences are needed to form a within-name comparison candidate. The count is taken after the content and metadata filters, so a name with multiple raw occurrences can still be excluded if only one survives those conditions. The threshold counts occurrences, not distinct file SHAs, repositories, or revisions; two copies can qualify without demonstrating modification.

The `groups` CTE joins those eligible names back to the filtered rows and groups by both `f.name` and `f.normalized_description`. `COUNT(*) AS artifact_group_size` records the size of each description subgroup. There is no second minimum-size test at this level. A unique description remains eligible when its name is shared by another qualifying artifact. This preserves description changes that may accompany reuse; requiring two identical name-and-description occurrences would discard those variants prematurely. Family analysis can subsequently compare across description groups within the same exact name, as recorded in RDR-003.

### Artifact, Family, and Group Identity

The grouping design provides reproducible membership rules and explicit links between artifact occurrences, candidate families, and description subgroups. These are different identities. An artifact ID answers which collected occurrence is being analyzed; a family key answers which same-name candidate population is being searched; and a group ID answers which name-and-description subgroup contains the occurrence. None of these identifiers proves common ancestry.

| Entity | Identifier used by the current implementation | Meaning and scope |
| --- | --- | --- |
| Artifact occurrence | `artifacts.id`, copied into `artifact_groupings.artifact_id` | A surrogate integer assigned during DuckDB import; identifies one occurrence within that saved build. The original logical occurrence key is `(repo_full_name, path)` within the dataset snapshot. |
| Repository | `repos.id`, retained as `repo_id` | A local join identifier; the retained repository name provides source context. |
| Exact-name candidate family | `artifact_groupings.name` | All qualifying occurrences sharing that exact name, across description groups. The current schema does not assign a separate numeric family ID. |
| Name-and-description subgroup | `artifact_groupings.id`, called `group_id` by the Python loader | One distinct `(name, normalized_description)` combination. Its ID repeats across all member rows and is not an individual-artifact identifier. |
| Skill-content variant | `artifacts.file_sha` | A content identifier shared by byte-identical skill files; does not uniquely identify their repository occurrences or bundled resources. |

`artifact_id` is created before candidate selection. The final query copies it from `artifacts.id` rather than renumbering retained artifacts, so the same occurrence can be traced through filtering, family analysis, graph endpoints, and scanner comparisons. By contrast, `artifact_groupings.id` is assigned after grouping and intentionally appears on multiple membership rows. Identifying a group by `id` alone therefore cannot identify its individual members. The existing local audit found one distinct `artifact_id` for every retained row, but the schema does not enforce primary-key or uniqueness constraints; this property should be checked after rebuilding or changing joins.

Consider the following synthetic example; these labels and values are not dataset findings:

| Local artifact ID | Source occurrence | Exact family name | Normalized description | Local group ID | Skill SHA |
| --- | --- | --- | --- | --- | --- |
| 101 | Repository X, path P | `example-skill` | `inspect status` | 7 | H1 |
| 102 | Repository Y, path Q | `example-skill` | `inspect status` | 7 | H1 |
| 103 | Repository Z, path R | `example-skill` | `inspect and report status` | 8 | H2 |

This represents three occurrences, one exact-name family, two description groups, and two skill-content variants. Artifacts 101 and 102 remain distinct despite sharing content and a group ID. Artifact 103 remains in the family despite its different description. Later similarity and direction analysis determine whether these are useful ordered comparisons; membership alone supplies no such conclusion. A similarity cluster is also a later analysis result, not another name for the SQL group. Its membership and numbering depend on the loaded candidates and similarity policy.

### Deterministic Membership Versus Build-Local Numbers

For identical source values and fixed filtering and normalization rules, an occurrence's exact-name family and name-and-description subgroup are determined by those values. This is the reproducible part of the design. The numeric IDs have a narrower guarantee: both the import query and the grouping query use `row_number() OVER ()` without an explicit `ORDER BY`. Consequently, neither artifact IDs nor group IDs are guaranteed to receive the same values after an independent rebuild, even if observed builds have happened to agree. Persisted numbers remain usable when reopening the same unchanged database.

The team independently downloaded `agent_skills_release.db` and ran the project SQL queries on their own machines. Team members reported accurately reproducing the results across these independent local setups. This provides empirical evidence that the documented preparation and grouping workflow was repeatable in the environments exercised by the group. Observed agreement is distinct from a guarantee that unordered numeric ID assignments remain stable in every rebuild or future dataset release.

To reconcile independent builds, retain the dataset release or snapshot identity together with the original occurrence key `(repo_full_name, path)`. Use exact `name` for the candidate-family key and `(name, normalized_description)` for the subgroup key, with the normalization definition recorded. A file SHA can additionally check content identity but cannot replace occurrence identity because the same content may appear in several repositories. Across dataset releases, the same repository and path may contain different content, so the snapshot context is essential.

The current schema does not implement a persistent registry or hash-derived identifier for families and groups. Adding an explicit ordering to row numbering could make assignment repeatable for a fixed input, but additions or removals can still shift later numbers. A future persistent identity scheme would need to account for that behavior before promising stable numeric IDs across releases. For the current study, preserve the database build or retain the original logical keys and a verified mapping; do not treat an unqualified numeric ID as a global identifier.

### Final Joins and Sibling Placeholders

`group_ids` assigns a `BIGINT` identifier to each name-and-description group using `row_number() OVER ()`. The group identifier organizes related membership rows; it does not identify an individual artifact. Because this window has no `ORDER BY`, its numbering must not be assumed stable across rebuilds. Source linkage uses the retained `artifact_id`, with repository context retained through `repo_id`.

The final joins retain only eligible names and attach each filtered artifact to its matching name-and-description group. The result has one membership row per retained source artifact; grouping does not collapse occurrences to one representative or prove lineage. The stored `artifact_group_size` describes a subgroup, not the total exact-name family.

`NULL::BIGINT AS sibling_file_count` and `NULL::VARCHAR AS sibling_content_sha` create typed placeholders. They do not filter out artifacts lacking sibling data, and null does not mean no sibling files. The next setup script, `sql/update_artifact_groupings.sql`, populates these fields only when composition was fetched, was not truncated, and every sibling file has a content hash. Known empty bundles receive count zero and the fingerprint of the empty string; incomplete composition remains unknown. The fingerprint uses a sorted multiset of sibling-file hashes and ignores paths and directory entries. This enrichment distinguishes known bundle states without requiring all candidates to have complete sibling evidence.

### Selection Counts and Interpretation

A read-only audit of the prepared local DuckDB database on October 15, 2026 produced the following counts using the current selection conditions:

| Cumulative selection stage | Retained artifacts | Excluded at this step |
| --- | ---: | ---: |
| All source artifact occurrences | 3,797,117 | — |
| `frontmatter_valid = 1` | 1,627,753 | 2,169,364 |
| `body_chars > 50` | 1,621,757 | 5,996 |
| `content IS NOT NULL` | 1,621,757 | 0 |
| `name IS NOT NULL` | 1,621,757 | 0 |
| `description IS NOT NULL` | 1,621,757 | 0 |
| Exact name occurs in at least two qualifying rows | 943,257 | 678,500 |

The final selection retains **943,257 of 3,797,117 artifacts** (24.84 percent) and excludes 2,853,860 (75.16 percent). This is a reduction in the number of artifact occurrences, not a measured reduction in pairwise comparisons or a count of distinct skill contents. The materialized `artifact_groupings` table independently contains 943,257 rows and 943,257 distinct artifact IDs, organized into 162,995 exact-name families and 628,026 name-and-normalized-description groups. Its row and family totals agree with the recomputed selection totals; agreement of totals alone is not a full membership-equivalence check.

The frontmatter test removes most occurrences in the displayed sequence. The body-length condition then removes 5,996, and the repeated-name requirement removes 678,500 otherwise qualifying occurrences. The three non-null checks remove no additional rows after the preceding conditions in this local database. That observation does not establish that missing content, names, or descriptions never occur in the source; they may already have been removed by earlier conditions. Keeping these explicit checks documents and enforces the prerequisites across rebuilds and other releases.

These are current local counts, not a claim that every retained artifact has been scanned or validated. The earlier exploratory figure of 1,146,188 artifacts recorded in RDR-001 predates later selection refinements and should not replace the current query's result. A new database build or revised query requires a new audit. The source release identifier and integrity information still need to be recorded before treating these counts as a fully frozen release experiment.

Counts at each line are cumulative in the order used for explanation, not a claim about the database engine's physical evaluation order. They are also not independent exclusion totals: an artifact can fail more than one condition, and attributing exclusions to a particular step depends on the displayed order. The following read-only SQL reproduces the cumulative audit and summarizes the materialized candidate table without changing either source or analysis tables. Open the prepared database in DuckDB and execute both statements:

```shell
duckdb -readonly /c/data/duckdb/agent_skills_release.db
```

```sql
-- Read-only audit of the selection in create_analysis_tables.sql.
-- Rows are cumulative in documentation order, not SQL execution order.
-- No source or analysis tables are changed.
WITH stages AS (
    SELECT
        name,
        frontmatter_valid = 1 AS valid_frontmatter,
        body_chars > 50 AS long_enough_body,
        content IS NOT NULL AS has_content,
        name IS NOT NULL AS has_name,
        description IS NOT NULL AS has_description
    FROM artifacts
),
eligible_names AS (
    SELECT name, COUNT(*) AS artifact_count
    FROM stages
    WHERE valid_frontmatter
      AND long_enough_body
      AND has_content
      AND has_name
      AND has_description
    GROUP BY name
    HAVING COUNT(*) >= 2
),
counts AS (
    SELECT 0 AS step, 'Source artifacts' AS selection_stage,
           COUNT(*) AS retained_artifacts
    FROM stages
    UNION ALL
    SELECT 1, 'Valid frontmatter', COUNT(*)
    FROM stages WHERE valid_frontmatter
    UNION ALL
    SELECT 2, 'Body longer than 50 characters', COUNT(*)
    FROM stages WHERE valid_frontmatter AND long_enough_body
    UNION ALL
    SELECT 3, 'Stored content present', COUNT(*)
    FROM stages WHERE valid_frontmatter AND long_enough_body AND has_content
    UNION ALL
    SELECT 4, 'Name present', COUNT(*)
    FROM stages
    WHERE valid_frontmatter AND long_enough_body AND has_content AND has_name
    UNION ALL
    SELECT 5, 'Description present', COUNT(*)
    FROM stages
    WHERE valid_frontmatter AND long_enough_body AND has_content
      AND has_name AND has_description
    UNION ALL
    SELECT 6, 'Name shared by at least two qualifying artifacts',
           coalesce(SUM(artifact_count), 0)::BIGINT
    FROM eligible_names
)
SELECT
    step,
    selection_stage,
    retained_artifacts,
    lag(retained_artifacts) OVER (ORDER BY step) - retained_artifacts
        AS excluded_at_this_step
FROM counts
ORDER BY step;

-- Independent summary of the already materialized candidate table.
SELECT
    COUNT(*) AS retained_artifacts,
    COUNT(DISTINCT artifact_id) AS distinct_artifact_ids,
    COUNT(DISTINCT name) AS exact_name_families,
    COUNT(DISTINCT id) AS name_description_groups
FROM artifact_groupings;
```

This population reduction precedes shingle similarity, direction inference, and scanner comparison. It also precedes the purposeful Sprint 1 selection of 43 artifacts. The retained candidate count must not be reported as a number of proven relatives, eligible directed comparisons, security findings, or manually validated cases. Exact-name selection can miss renamed relatives, and content/metadata requirements favor better-enriched artifacts. These selection effects delimit any later population-level claims.

## Relevant Schema

The analysis uses data at four related levels: artifact, relationship, scanner profile, and ordered comparison. The field lists below describe the broader target schema, not a claim that every field is present in the current Sprint 1 reports. Exact source-table and column names will be verified against the implemented extraction pipeline and documented in `DATA_DICTIONARY.md`. Current wrapper reports record endpoint artifact IDs, relationship evidence, introduced-capability flags, total match counts, and nonzero rule-count deltas.

### Artifact Data

For both base and derived artifacts, the prepared data retains the available fields needed for identification, analysis, and traceability:

- artifact identifier;
- repository identifier;
- artifact path;
- declared skill name, when available;
- content SHA;
- stored content or a safe reference to the analyzed content; and
- available timestamp, commit, or other ordering metadata used by the relationship method.

### Relationship Data

Each candidate or eligible relationship records:

- comparison identifier;
- base artifact identifier;
- derived artifact identifier;
- relationship type;
- same-repository or cross-repository status;
- relationship-detection method;
- evidence supporting the relationship;
- evidence supporting base-derived ordering;
- relationship confidence or review status, if used by the implemented method; and
- eligibility or exclusion status and reason.

### Scanner-Profile Data

For each analyzed artifact, the prepared scanner profile contains:

- matched rule identifiers;
- matched security-relevant categories;
- match counts by rule and category;
- total matched-rule and matched-category counts;
- match locations or other evidence required for validation and safe reporting; and
- scanner and rule-catalog versions.

### Comparison Data

For each eligible ordered comparison, the prepared analysis table contains:

- introduced, removed, and retained rule identifiers;
- introduced, removed, and retained categories;
- counts of introduced rules and categories;
- indicators for at least one introduced rule and at least one introduced category; and
- the overall comparison result under the documented threat model.

Rule-level and category-level fields are both retained. A derived artifact may introduce a new rule within a category that was already present in the base artifact; that change is visible at the rule level even when the set of categories does not change.

## Unit of Analysis

The primary unit of analysis is one ordered comparison between two related, content-bearing skill artifacts:

- **Base artifact:** The inferred source endpoint, according to the supported direction evidence.
- **Derived artifact:** The inferred target endpoint being compared with the base; this designation does not prove historical descent.

The ordering is represented as:

**base artifact -> derived artifact**

One unique content SHA is the secondary processing unit. The pipeline may scan identical content once and reuse its profile, but SHA-based deduplication is only a computational optimization. Artifact occurrences, repository occurrences, and comparison relationships remain available after cached profiles are joined back to the complete extracted data.

## Inclusion and Exclusion Criteria

An ordered comparison is eligible when all of the following conditions are satisfied:

1. Both artifacts contain stored content that the scanner can analyze.
2. The extraction pipeline identifies a relationship using the project's documented relationship method.
3. Available evidence supports the base-derived ordering.
4. Both artifacts can be processed with the same scanner version and rule-catalog version.

A candidate comparison is excluded when one or more of these conditions are not satisfied. The pipeline retains the exclusion status and reason so that filtering is auditable. Uncertain or invalid relationships may be reviewed and excluded according to the documented relationship method.

[TODO: Add any implemented content-format, parsing, duplication, missing-value, or relationship-confidence filters and the exact exclusion codes used by the pipeline.]

## Data Preparation

The preparation process converts the source database into analysis-ready artifact and comparison data. It will:

1. extract artifact content and traceability metadata from the relevant source tables;
2. identify candidate relationships and retain the evidence used to establish each relationship;
3. determine base-derived ordering from the available evidence;
4. apply the documented inclusion and exclusion criteria;
5. normalize content only as required by the scanner while preserving the original content or a safe reference to it;
6. identify unique content SHAs for cached scanning without discarding artifact occurrences;
7. attach scanner profiles to artifact records; and
8. join base and derived profiles into the ordered comparison table.

[TODO: Document the implemented text decoding, line-ending normalization, parsing, missing-content handling, and any other cleaning transformations. Distinguish transformations used for matching from the original content retained for traceability.]

## Population Analysis and Sampling

### Planned Automated Census

The automated analysis will attempt a census of the eligible comparison population rather than select a statistical sample. Every eligible base-derived comparison extracted from `agent_skills_release.db` will be processed by the comparison pipeline.

Smaller reproducible datasets may be used while developing and debugging the pipeline. These development datasets are test inputs, not the research sample, and will not replace the final population-level analysis.

### Planned Manual Validation Sample

For the broader evaluation, the team plans to manually review a stratified sample of at least 100 eligible base-derived comparisons from the automated results. This future plan is separate from the 17 directed comparisons in the current Sprint 1 reports:

- at least 50 comparisons for which the scanner reports one or more newly introduced rules or categories; and
- at least 50 comparisons for which the scanner reports no newly introduced rules or categories.

Within those two groups, the sample will represent the relationship types and scanner categories present in the results. Selection will use a recorded random seed after the strata are defined. If a stratum contains fewer cases than its allocation, all cases in that stratum will be reviewed and the remaining allocation will be redistributed using a documented procedure.

The sample may be expanded if early review identifies unstable rules, poorly represented relationship types, or categories that require additional evidence. The manual-review procedure, labels, metrics, and error analysis belong in the Evaluation and Validation section.

For each sampled comparison, reviewers will record:

- whether the relationship and base-derived ordering are supported by the retained evidence;
- whether each reported match corresponds to the text identified by the scanner;
- whether the assigned categories are appropriate;
- whether a reported introduction was absent from the base and present in the derived artifact;
- whether an unflagged comparison contains a relevant introduction missed by the current rules; and
- whether the case is a true positive, false positive, false negative, true negative, or ambiguous under the documented threat model.

These records will support confirmed and rejected relationship counts, ordering disagreements, classification counts, precision and any other justified validation metrics, category- or relationship-specific breakdowns where sample size permits, and representative failure modes. The Evaluation and Validation section will define the final calculation and interpretation of those measures.

### Sprint 1 Sampling Strategy

Sprint 1 uses a small, purposeful tool-validation sample of **43 artifacts across 10 exact-name families**. The ten saved analysis reports contain **17 directed comparisons**. These totals describe the current tool output, not a representative population sample or completed manual validation of every comparison.

The earlier design combined purposeful cases with 75 random artifact seeds and family expansion, producing approximately 1,400 artifact-selection rows. It was too large for immediate manual validation. The revised selection aimed for approximately 50 artifacts or fewer and has no separate random component. The earlier sample may remain useful for later work; its reconstruction checks do not validate the revised selection.

The Evaluation and Validation section explains how these artifacts exercised candidate loading, lineage analysis, scanning, and extraction. It distinguishes the 17 selected directed family comparisons from the extraction notebook's 33 adjacent comparisons. The two counts describe different pairing procedures applied to the sample, not competing estimates of its size.

#### Selection Logic and Family Scope

Families were selected to exercise supported direction evidence, ambiguous relationships, cases without inferred relationships, and positive, negative, or unchanged scanner counts. Other cases distinguish additional matches within an existing capability from newly detected capabilities and expose scanner coverage or normalization limitations.

`artifact_groupings` groups artifacts by exact name and normalized description. The current `analyze_family` tool loads all qualifying artifacts sharing an exact name, including multiple description groups. Some screening queries compare only within a name-and-description group, so their screening scope is narrower than the family-analysis scope. Shared metadata establishes candidate context, not proven lineage.

The selection queries screened for package-installation count variation, supported provenance-field references, and variation in additional scanner rules. SQL patterns were selection heuristics rather than validated findings. Candidate families were checked through the Python workflow, and selected comparisons were inspected manually in Mergely. Searching ended because further screening was time-consuming, not because the sample was exhaustive or statistically optimized. The query rationale and RDR-006 record the selection decisions.

#### Observed Coverage and Limits

The saved Sprint 1 reports documented nonzero count deltas in 10 of the then-current 12 rules. EXT-001 and SYS-001 lacked confirmed delta examples in that historical selection. The current implementation registers 13 rules, including FS-003 for file reading; the older coverage total must not be treated as coverage of the current catalog. Rule presence, a count change, and an introduced capability are different outcomes; none alone establishes increased or decreased risk.

The Sprint 1 wrapper scanned selected directed relationships rather than every possible artifact pair and compared only `SKILL.md` content. These limits describe the saved Sprint 1 output. The current `scan_family` implementation also reviews available sibling content for applicable changes and reports incomplete coverage. Ambiguous relationships remain excluded from directional scanning; a family with no directed comparisons does not establish an absence of matches. Historical skill-only results must not be interpreted as findings about sibling safety.

Selected manual inspections exposed uneven command coverage and a line-ending sensitivity bug. The Sprint 1 wrapper was corrected to normalize line endings before scanning, and that comparison was retained for regression checking in the earlier workflow. This historical correction is not evidence that every current input path applies identical normalization. Other inspected cases illustrate limitations in declared-source resolution and exact-name candidate generation. These observations do not constitute manual validation of every comparison.

#### Sample View and Reproducibility

The revised selection uses the 43 `artifact_id` values recorded for the team's saved database build. These values identify occurrences consistently within that build; the unordered import numbering does not guarantee the same mapping in a separate build. The script `sql/create_sprint1_samples_view.sql` embeds the selected IDs, selects matching `artifact_groupings` rows, and joins them to `artifacts` and `repos` to create or replace `sample_artifacts`. The CSV at `data/sample-population/sample_population.csv` separately records selected IDs; the view does not read that file.

The view stores the selection query rather than copying artifact records into separate sample tables. Its ID list fixes the selection criteria, while returned values reflect the underlying `artifacts` table when queried. The current view exposes grouping membership, selected source fields including content and paths, and repository metadata through those joins. It is not an anonymized reporting view.

The script's final count query should return 43 if every selected occurrence remains in the candidate table and resolves through the artifact and repository joins. The saved family-report totals do not demonstrate that this query has been run successfully. Reproducibility checks should reconcile the embedded IDs with the recorded list, confirm that every ID resolves, and compare reconstructed membership in both directions. A matching row count alone is insufficient to establish identical membership.

The saved ID list supports reconstruction in the original build. Reconstructing the intended occurrences in an independent build also requires verifying the ID-to-source mapping through the original logical keys. The dataset version, database build, selection SQL, scanner rules, and normalization settings must therefore be recorded. Earlier frozen-table validation applies only to the earlier sample.

## Data Ethics and Safety

All artifact content is treated as untrusted data. The project performs static analysis only and will not execute scripts, commands, or instructions contained in the dataset.

The pipeline and reporting process will:

- avoid executing or importing untrusted artifact code;
- avoid exposing credentials, tokens, or other sensitive strings that may appear in artifact content;
- keep validation evidence local and omit source text and identifying values from exported reports under the current output constraints;
- distinguish detected risk signals from proof of malicious intent, vulnerability, exploitability, or real-world harm; and
- report aggregate findings and generalized observations without naming selected artifacts or reproducing source content.

Current orchestration reports identify endpoints by artifact ID, omit text diffs, and serialize scanner comparisons with `verbose=False`. These measures limit exported content but do not guarantee anonymity or resolve licensing questions. Artifact IDs can be linked to source records by someone with access to the dataset.

[TODO: Document the implemented redaction, access-control, retention, and safe-example-selection procedures.]

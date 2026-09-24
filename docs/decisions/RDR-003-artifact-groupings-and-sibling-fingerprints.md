# RDR-003: Artifact Groupings and Sibling Fingerprints

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-23 |
| **Type** | Research methodology, data, and implementation |
| **Related work** | Question 4, similarity analysis, Sprint 1 |
| **Evidence** | `sql/create_gitskills_duckdb.sql`, `sql/create_analysis_tables.sql`, `sql/update_artifact_groupings.sql`, DuckDB validation queries |
| **Supersedes** | None |

## Context

RDR-001 retained Question 4 by using related GitSkills artifacts as observed or inferred versions rather than requiring complete repository history.

The next problem was reducing the comparison space before similarity and security analysis. Many artifacts can be identified as exact content matches using hashes, so running similarity checks on every candidate comparison would add unnecessary work.

## Decision Drivers

- Simplify joins and later analysis.
- Reduce unnecessary similarity comparisons.
- Preserve repeated `SKILL.md` occurrences when their bundled sibling files may differ.
- Distinguish known absence of sibling files from missing or incomplete sibling data.
- Focus on security-relevant content changes rather than path or directory changes.

## Evidence

The materialized `artifact_groupings` table currently contains:

| Finding | Result |
| --- | ---: |
| Rows in `artifact_groupings` | 60,034 |
| Rows with usable sibling metadata | 59,210 |
| Rows with zero sibling files | 36,312 |
| Rows with unavailable sibling metadata | 824 |
| Rows where `dedup_primary = 0` | 162 |

The 162 non-primary rows are retained because byte-identical `SKILL.md` files can still have different bundled sibling resources.

We also checked for duplicate sibling file names within an artifact using `artifact_id` and `entry_name`; no duplicates were found.

## Decision

> **Materialize the RQ4 comparison population and compute exact sibling-content fingerprints before performing similarity or security-change analysis.**

### Analysis Identifiers and Groupings

The DuckDB analysis database adds numeric identifiers and direct relationships to simplify joins. `artifact_groupings.id` uses the same value as `artifacts.id`, so grouped rows can be joined directly back to the source artifact.

The table includes valid `SKILL.md` artifacts from the selected skill locations with usable content, metadata, and chronology, and retains only groups containing at least two artifacts.

Artifacts are placed in the same group when they share the same `name` and normalized `description`. Description normalization trims surrounding whitespace, converts text to lowercase, and collapses repeated whitespace.

This is a **blocking step only**. Matching metadata identifies artifacts worth comparing but does not establish reuse, ancestry, or lineage.

The grouping process does not filter to `dedup_primary = 1` because repeated `SKILL.md` occurrences may have different sibling resources.

### Sibling Fingerprints

For artifacts with complete sibling composition data:

- `sibling_file_count` records the number of sibling files.
- `sibling_content_sha` is a SHA-256 fingerprint of the sorted sibling file `entry_sha` values.

Directory entries are excluded. File paths and directory layout are also excluded because path-only changes are not relevant to the security-content focus of Question 4.

Duplicate file hashes are preserved, so the fingerprint represents the complete multiset of sibling file contents.

Sibling metadata is populated only when `composition_fetched = 1`, `composition_truncated = 0`, and every sibling file has an `entry_sha`.

| `sibling_file_count` | `sibling_content_sha` | Meaning |
| ---: | --- | --- |
| `NULL` | `NULL` | Sibling composition could not be characterized reliably. |
| `0` | SHA-256 of the empty string | Composition was checked and no sibling files exist. |
| Greater than `0` | SHA-256 value | Sibling file contents were successfully characterized. |

### Use During Similarity Analysis

These exact hashes provide a low-cost check before more expensive similarity and security analysis:

```text
same SKILL.md file_sha + same known sibling_content_sha
    -> no observed content change in SKILL.md or sibling file contents

same SKILL.md file_sha + different known sibling_content_sha
    -> inspect bundled sibling-resource changes

different SKILL.md file_sha
    -> perform similarity validation and security-delta analysis

unknown sibling_content_sha
    -> do not assume sibling equivalence
```

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Keep only `dedup_primary = 1` artifacts | Not selected | Exact `SKILL.md` duplicates may have different sibling resources. |
| Include sibling paths and directory layout in the fingerprint | Not selected | Path-only changes are outside the RQ4 security-content focus. |
| Treat missing sibling data as zero siblings | Not selected | This would confuse unknown composition with known absence of sibling files. |
| Run similarity analysis before exact hash checks | Not selected | Exact hashes can eliminate redundant comparisons more cheaply. |

## Consequences and Limitations

This adds a small preprocessing step but simplifies later analysis by separating exact content matches, sibling-content differences, and incomplete data before similarity scanning.

The metadata grouping remains a heuristic. Related skills with changed names or descriptions may fall into different groups, while unrelated skills with identical metadata may appear in the same group. Similarity validation is still required.

The sibling fingerprint intentionally ignores filenames, paths, and directory layout. This is acceptable for RQ4 because the analysis is concerned with introduced security-relevant content.

A changed sibling fingerprint establishes that sibling content differs, but not that the change is security-relevant. If the changed file's content is unavailable, that file may not be scannable for security-sensitive behavior.

Chronological and lineage limitations remain as documented in RDR-001.

## Follow-up Actions

- Implement similarity validation for grouped artifacts with different `file_sha` values.
- Compare sibling resources when identical `SKILL.md` files have different sibling fingerprints.
- Apply the security scanner to validated earlier/later comparisons.

## Revisit Criteria

Revisit this decision if validation shows that metadata blocking misses too many related artifacts, sibling fingerprints do not support the needed comparisons, or path changes become relevant to the research question.

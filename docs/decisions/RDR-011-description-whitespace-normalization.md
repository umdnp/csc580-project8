# RDR-011: Description Whitespace Normalization

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-10-21 |
| **Type** | Data preparation and implementation |
| **Related work** | Story 6.1 SQL preparation tests; RDR-003 |
| **Evidence** | Read-only inspection of the local DuckDB; `tests/pytests/test_data_preparation.py` |
| **Supersedes** | None; implements the existing RDR-003 normalization policy |

## Context and decision

The grouping SQL previously trimmed spaces before collapsing whitespace. A
description such as `\tBuild reports\n` therefore became ` build reports `,
while `Build reports` became `build reports`. Equivalent descriptions could
occupy separate description groups.

**Collapse whitespace, then trim the resulting spaces.**
`sql/create_analysis_tables.sql` now uses:

```sql
trim(regexp_replace(lower(a.description), '\s+', ' ', 'g'))
```

Eligibility filters and exact-name candidate-family selection remain as defined
in RDR-003. The change does not modify artifact IDs, repository IDs, source
content, file hashes, or per-artifact sibling fingerprints.

## Measured database impact

The local DuckDB was inspected read-only on October 21, 2026. These counts
describe that build, not a guarantee for every dataset release or local build.

| Measure | Count |
| --- | ---: |
| Artifact members in `artifact_groupings` | 943,257 |
| Current description groups | 628,026 |
| Artifacts with boundary spaces in normalized descriptions | 118,618 |
| Groups with affected descriptions | 82,703 |
| Sets of existing groups that would merge after trimming | 3,475 |
| Existing groups participating in those merges | 6,950 |
| Artifact members in the merging groups | 26,368 |
| Projected description groups after correction | 624,551 |

Of the 43 approved-sample artifacts, nine have affected descriptions: four in
`003-create-golang-project` and five in `databricks-upgrade-migration`, across
three description groups. None participates in a merge, even when compared
with groups outside the sample. Recomputing both normalization expressions from
all 43 source descriptions confirmed this sample impact.

## Effect on clustering and scanning

Description groups are supporting metadata. The current family loader selects
by exact `name`; family clustering uses skill-body similarity; direction uses
provenance, chronology, repository boundaries, and containment. Description
group IDs are not criteria for selecting predecessor edges. The scanner uses
those selected edges and the skill/sibling content.

Consequently, changing only description normalization and group IDs is expected
to preserve selected artifact comparisons and security findings under the
current implementation. A constructed integration test executes the corrected
SQL, merges previously split description groups, and checks that the family
scanner's complete verbose structured result is identical before and after.
This is a regression check for the scanner core used by `scan_family`.

This does **not** mean all database rows or reports are identical. Group IDs,
normalized descriptions, group sizes/counts, and within/across-group reporting
can change. A full population scanner rerun is not claimed by the SQL tests.

## Existing databases and reproducibility

Committing or pulling this change does not alter an existing database. A build
retains the old grouping until its preparation SQL is rerun. To apply the change,
use the existing commands in [data setup](../../data/README.md#3-build-the-analysis-tables):

1. Run `sql/create_analysis_tables.sql` against the intended local DuckDB.
2. Run `sql/update_artifact_groupings.sql` afterward to repopulate sibling fields.

The first script drops/recreates `artifact_groupings` and initializes sibling
fields to `NULL`, so both steps are required before comparing scan results.
The original SQLite download does not need to be reimported. Group IDs are
generated locally and are not stable cross-build identifiers; use artifact IDs,
source hashes, and dataset/repository revisions when comparing runs. Rerunning
the grouping scripts can renumber groups beyond those whose descriptions changed.

Preserve previously frozen sample/review records and analysis outputs. Record
which repository revision prepared each database; any regenerated report should
be identified as coming from that revision rather than silently replacing a
frozen baseline.

## Verification

```shell
uv run pytest tests/pytests/test_data_preparation.py -v
```

The boundary-whitespace case is a normal required regression test, not an
expected failure. Other preparation checks cover filtering, grouping membership,
source links, sibling fingerprints, missing composition, and repeatable rebuilds.
All use an isolated in-memory database; they do not modify the local dataset.

Revisit this decision if family selection or direction starts using description
group membership as a decision criterion.

# RDR-006: Sprint 1 Sample Design and Selection

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-26 |
| **Revised** | 2026-09-30 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 1, RDR-001 through RDR-005, RDR-007, `artifact_groupings` |
| **Evidence** | `notes/sample_population_query_rationale.md`, `sql/create_sprint1_samples_view.sql` |
| **Supersedes** | Earlier Sprint 1 sample-selection approach documented in this RDR |

## Context

Question 4 requires the project to compare potentially reused or modified skills and look for changes in security-sensitive behavior. A useful validation sample therefore needs multiple artifacts from the same skill family, enough variation to exercise the planned analysis methods, and a size that remains practical for manual review.

An earlier sample design combined purposeful cases with a larger random component. Expanding those selections produced far more artifacts than were practical for focused validation. The team therefore moved to a smaller, purposeful sample built around exact-name skill groups that showed useful variation during exploratory screening.

This sample is intended to support method development and validation. It is not intended to represent the full GitSkills population or support population-level risk estimates.

## Decision Drivers

- Keep the sample small enough for focused manual review.
- Include multiple artifacts within the same skill-name family.
- Include a range of security-sensitive patterns rather than concentrating on one rule or behavior.
- Preserve cases that may expose weaknesses or edge cases in the analysis methods.
- Make sample membership deterministic and easy to reconstruct from the project database.
- Keep candidate selection separate from claims about reuse, provenance, lineage, or historical copying.

## Decision

> **Use a small, purposeful Sprint 1 sample of 43 artifacts across 10 exact-name skill families. Record sample membership with deterministic `artifact_id` values and expose the selected artifacts through a DuckDB view.**

The sample was selected through iterative screening rather than random sampling. Screening focused on compact families that showed potentially useful variation for later comparison and validation.

The screening queries were used only to identify candidates. They do not establish that artifacts are related, that one artifact was derived from another, or that a security-sensitive change represents increased risk.

Detailed selection queries and their rationale are documented in [`notes/sample_population_query_rationale.md`](../../notes/sample_population_query_rationale.md).

## Selection Rationale

The selection process used three main forms of screening:

1. **Package-installation variation** — identify manageable exact-name families containing different file hashes and variation in package-installation patterns.
2. **Declared source metadata** — locate artifacts with source-related fields that may be useful when evaluating provenance and direction methods.
3. **Additional scanner-rule variation** — search bounded sets of small families for variation in security-sensitive patterns that were not already represented by selected cases.

These queries were screening heuristics, not research findings. Some SQL patterns approximate the project's Python scanner and therefore may not produce identical results. Candidate families still require follow-up analysis before they can support conclusions about relatedness, direction, or security change.

The search was intentionally bounded. Selection stopped when the team had a compact sample with enough variety to support focused validation; it was not exhaustive or statistically optimized.

## Sample Construction

The approved artifact IDs are recorded in [`sql/create_sprint1_samples_view.sql`](../../sql/create_sprint1_samples_view.sql). The script creates the `sample_artifacts` view by joining the selected grouping, artifact, and repository records required for later analysis.

Using a fixed artifact-ID list gives the project a simple, reproducible way to reconstruct the same sample from the project database. The view provides a stable interface that notebooks or scripts can use without duplicating the sample-selection logic.

The view defines sample membership only. It should not be treated as evidence of lineage, reuse, or direction between artifacts.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Continue with the much larger mixed random/purposeful sample | Not selected for Sprint 1 | Too large for focused inspection and manual validation. |
| Use a random-only sample | Not selected | A small random sample might not contain enough useful variation for method validation. |
| Select isolated artifacts | Not selected | Multiple artifacts within a family are needed to evaluate comparison methods. |
| Continue searching until every scanner rule is represented | Deferred | The search was becoming time-consuming, and complete rule coverage is not required for the initial sample. |
| Use the 43-artifact purposeful sample | **Selected** | Small, reproducible, and varied enough to support focused validation. |

## Consequences and Limitations

- Purposeful selection favors informative cases and cannot be used to estimate population-wide prevalence or risk.
- Screening may favor behavior that is easier for the current rules and queries to detect.
- Exact-name families can miss related skills that changed names, while a shared name does not prove that artifacts are related.
- SQL screening patterns are approximate candidate filters and should not be treated as scanner results.
- Sample membership is reproducible from the fixed artifact-ID list, but conclusions drawn from the sample still depend on the validity of the later comparison and scanner methods.
- The sample should be treated as a validation and exploratory sample rather than a representative population sample.

## Follow-up Actions

- Keep [`sql/create_sprint1_samples_view.sql`](../../sql/create_sprint1_samples_view.sql) as the source of truth for the approved sample.
- Keep detailed candidate-selection queries and rationale in [`notes/sample_population_query_rationale.md`](../../notes/sample_population_query_rationale.md) rather than duplicating them in this RDR.
- Use the similarity and direction methods defined in RDR-004 and RDR-007 before making claims about reuse, provenance, or introduced behavior.
- Record manual validation separately from the automated screening used to select candidates.

## Revisit Criteria

Revisit this decision when broader or population-level analysis is required, when the comparison or scanner methods change enough that the current sample no longer provides useful coverage, or when validation identifies important cases that are not represented by these ten families.

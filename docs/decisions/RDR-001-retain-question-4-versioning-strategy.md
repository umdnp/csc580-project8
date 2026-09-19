# RDR-001: Retain Research Question 4 Using Inferred Version Relationships

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-19 |
| **Type** | Research scope and methodology |
| **Related work** | Issue #29, Epic #24, Sprint 1 |
| **Evidence** | `notebooks/exploratory_analysis.ipynb` |
| **Supersedes** | None |

## Context

The team selected Question 4, **Skill security and supply-chain risk**:

> Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?

The required implementation includes a static analyzer or rule-based scanner for security-sensitive behavior and changes across skill versions.

During initial dataset review, we were concerned that GitSkills might not contain enough historical information to answer the question as written. The dataset includes fields such as `commit_count`, `first_commit_at`, and `last_commit_at`, but it does not provide a complete sequence of historical `SKILL.md` contents for every commit.

Because of this limitation, the team considered revising Question 4 to focus only on security-sensitive behavior present in the available artifact contents. The assignment permits groups to refine a proposed question or substitute an equivalent question if necessary.

## Decision Drivers

- Stay as close as practical to the original Question 4.
- Keep the analysis reproducible using the GitSkills dataset.
- Do not imply that GitSkills contains complete Git history when it does not.
- Require validation before treating similar artifacts as related or chronologically ordered.

## Evidence

Exploratory analysis of the full GitSkills database indicates that the dataset contains enough structure to continue investigating reuse and modification without revising the question yet.

| Finding | Result |
| --- | ---: |
| Filtered analysis population | 1,146,188 artifacts |
| Artifacts with commit-history metadata | 346,019 |
| Commit-history coverage | 30.19% |
| Candidate families with more than one artifact | 77,959 |
| Median candidate-family size | 2 artifacts |
| Candidate families with 10 or fewer artifacts | ~96% |
| Candidate pairs using name-only blocking | ~40.0 million |
| Candidate pairs using normalized name + description | ~2.5 million |
| Reduction in candidate comparison space | 93.72% |

Candidate families also show variation in body size and available commit timestamps. This suggests that some groups may contain modified or redistributed forms of related skills rather than only identical copies.

## Decision

> **Retain Question 4 in its current form for now.**

We will investigate version and reuse relationships using related artifacts present in GitSkills rather than requiring complete per-commit history for every `SKILL.md`.

The planned approach is to:

1. Use normalized skill metadata, such as name and description, to identify candidate families.
2. Validate candidate relationships using content similarity, file hashes, repository information, and other available metadata.
3. Where commit-history metadata is available, use fields such as `first_commit_at` to establish an **observed chronological ordering**.
4. Apply the security scanner to related artifacts and compare detected capabilities such as command execution, file-system access, network access, scripts, and credential-related instructions.
5. Identify capabilities present in a later observed artifact but absent from an earlier related artifact.
6. Report the results as observed or inferred evolution unless stronger provenance evidence supports a definitive lineage claim.

The earliest timestamp in a candidate family will be treated only as the **earliest observed artifact in the dataset**, not automatically as the original source.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Revise the question to static analysis only | Not selected | Easier to answer, but removes the reuse and change-detection aspect central to Question 4. |
| Retrieve complete repository history from GitHub | Not required | Could improve lineage evidence, but significantly expands project scope and introduces additional acquisition and reproducibility concerns. |
| Infer related artifacts from GitSkills | **Selected** | Preserves the intent of Question 4 while keeping the project grounded in the challenge dataset. |

## Consequences and Limitations

This decision preserves the reuse and security-change focus of Question 4, but the results must be interpreted cautiously:

- GitSkills does not provide complete historical content for every commit.
- Commit-history metadata is available for only part of the analysis population.
- Similar names and descriptions alone do not establish reuse, ancestry, or lineage.
- The earliest artifact observed in GitSkills may not be the true origin of a skill.
- Some candidate relationships may not contain enough temporal information to establish direction.
- A capability should be described as newly introduced only when the evidence supports a meaningful ordering between related artifacts.

These limitations should also be reflected in the project methodology and `THREATS_TO_VALIDITY.md`.

## Follow-up Actions

- Define and validate the content-similarity method used to confirm candidate families.
- Determine how `file_sha`, repository information, and other metadata contribute to relationship classification.
- Define the evidence required to label artifacts as earlier and later observations.
- Implement the security-detection rules required by Question 4.
- Manually validate a sample of inferred relationships and measure how many support chronological comparison.

## Revisit Criteria

Revisit this decision if later implementation or validation shows that:

- candidate relationships cannot be validated reliably;
- too few validated relationships have enough chronological information for change analysis; or
- the available metadata cannot support defensible earlier/later comparisons.

If that occurs, the team may refine Question 4 as permitted by the assignment.

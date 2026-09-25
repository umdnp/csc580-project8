# RDR-001: Retain Research Question 4 Using Inferred Artifact Relationships

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

The required implementation includes a static analyzer or rule-based scanner for security-sensitive behavior and changes across related skill artifacts.

During initial dataset review, we were concerned that GitSkills might not contain enough historical information to answer the question as written. The dataset includes commit-history metadata, but it does not provide a complete sequence of historical `SKILL.md` contents for every commit.

Because of this limitation, the team considered revising Question 4 to focus only on security-sensitive behavior present in the available artifact contents. The assignment permits groups to refine a proposed question or substitute an equivalent question if necessary.

## Decision Drivers

- Stay as close as practical to the original Question 4.
- Keep the analysis reproducible using the GitSkills dataset.
- Do not imply that GitSkills contains complete Git history when it does not.
- Require validation before treating similar artifacts as related or chronologically ordered.

## Evidence

Initial exploratory analysis of the GitSkills database showed enough structure to continue investigating reuse and modification without revising the question.

| Finding | Initial exploratory result |
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

These results showed that the dataset contains many repeated or potentially related artifacts, while still providing enough metadata and history to support validation and observed ordering for at least part of the population.

The exact grouping and filtering strategy has since been refined in later RDRs. The results above are retained here because they were the evidence used when this decision was made.

## Decision

> **Retain Question 4 in its current form.**

We will investigate reuse and modification using related artifacts present in GitSkills rather than requiring complete per-commit history for every `SKILL.md`.

At a high level, the approach is to:

1. Use same-name artifacts as the initial candidate population for possible reuse or modification.
2. Validate candidate relationships using content similarity and other available metadata.
3. Where sufficient history is available, establish an observed earlier/later ordering without treating it as proof of original authorship or direct lineage.
4. Compare validated artifacts for changes in security-sensitive behavior such as command execution, file-system access, network access, scripts, and credential-related instructions.
5. Report the results as observed or inferred evolution unless stronger evidence supports a more specific lineage claim.

Later RDRs define the detailed grouping, sibling-fingerprint, and similarity strategies used to support this decision.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Revise the question to static analysis only | Not selected | Easier to answer, but removes the reuse and change-detection aspect central to Question 4. |
| Retrieve complete repository history from GitHub | Not required | Could improve lineage evidence, but significantly expands project scope and introduces additional acquisition and reproducibility concerns. |
| Infer related artifacts from GitSkills | **Selected** | Preserves the intent of Question 4 while keeping the project grounded in the challenge dataset. |

## Consequences and Limitations

This decision preserves the reuse and security-change focus of Question 4, but the results must be interpreted cautiously:

- GitSkills does not provide complete historical content for every commit.
- Commit-history metadata is available for only part of the dataset.
- Similar names, descriptions, or content do not by themselves establish reuse, ancestry, or lineage.
- The earliest observed artifact may not be the true origin of a skill.
- Some related artifacts may not contain enough temporal evidence to establish direction.
- A capability should be described as newly introduced only when the evidence supports a meaningful ordering between related artifacts.

These limitations should also be reflected in the project methodology and `THREATS_TO_VALIDITY.md`.

## Follow-up Actions

- Define and validate the candidate-grouping strategy.
- Define and validate the similarity method used to confirm related artifacts.
- Define the evidence needed to support earlier/later comparisons.
- Implement and validate the security-detection rules required by Question 4.
- Manually review a sample of inferred relationships and security comparisons.

## Revisit Criteria

Revisit this decision if later validation shows that:

- candidate relationships cannot be validated reliably;
- too few validated relationships support meaningful change analysis; or
- the available metadata cannot support defensible earlier/later comparisons.

If that occurs, the team may refine Question 4 as permitted by the assignment.

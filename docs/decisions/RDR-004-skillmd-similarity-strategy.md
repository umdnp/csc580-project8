# RDR-004: SKILL.md Similarity Strategy

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-24 |
| **Type** | Research methodology |
| **Related work** | Question 4, RDR-001, RDR-002, RDR-003, Story 2.2, Sprint 1 |
| **Evidence** | `RDR-003-artifact-groupings-and-sibling-fingerprints.md`, DuckDB exploratory analysis |
| **Supersedes** | None |

## Context

RDR-003 defines a practical candidate population for comparing potentially reused or modified skills. The next problem is deciding when two candidate `SKILL.md` files are similar enough to support a meaningful security comparison.

Matching names or descriptions is useful for finding candidates, but metadata alone does not show that the skill instructions are actually related. Exact hashes solve the opposite case by showing when two files are identical, but they cannot identify modified copies.

The project therefore needs a similarity method that can recognize retained content even when a skill has been reformatted, expanded, or partially rewritten.

## Decision Drivers

- Do not treat shared metadata as proof that two skills are related.
- Recognize modified copies that preserve substantial earlier content.
- Tolerate formatting changes and inserted material.
- Preserve meaningful technical text such as commands, URLs, paths, and identifiers.
- Keep the method understandable, reproducible, and practical to validate.
- Avoid introducing more complex similarity infrastructure unless the simpler approach proves insufficient.

## Evidence

Exploratory review showed that reused skills can retain most of their original instructions while adding significant new content.

A symmetric similarity measure by itself can make this kind of expanded copy look less related than it really is. For example, if one artifact contains 100 shingles, another contains 150, and they share 85:

```text
containment = 85 / 100 = 0.85
jaccard     = 85 / 165 = 0.52
```

The containment score shows that most of the smaller artifact is still present, while the Jaccard score shows that the larger artifact also contains substantial additional material.

That distinction matters for Question 4 because newly added material may be where security-sensitive behavior is introduced.

## Decision

> **Use token-shingle similarity for candidate `SKILL.md` files, with containment as the primary measure and Jaccard similarity as supporting evidence.**

Similarity will be based on the `SKILL.md` body rather than YAML frontmatter. Frontmatter is metadata and is already handled separately under RDR-002.

Token shingles provide a middle ground between exact matching and more complex semantic methods. They preserve local textual structure while being less sensitive to formatting changes than raw-text comparison.

Containment is the primary signal because it answers the question most relevant to reuse: how much of one artifact is retained in another. Jaccard is retained as a supporting measure because it helps show how much the complete artifacts differ overall.

The initial implementation will evaluate 5-token shingles, with shingle size and similarity thresholds finalized through manual validation rather than treated as fixed assumptions.

Similarity is evaluated across the same-name candidate population defined in RDR-003, including artifacts whose descriptions differ.

When chronology is available, similarity can support an observed earlier/later comparison. Similarity itself does not prove copying, ancestry, or original authorship.

Sibling resources remain outside the `SKILL.md` similarity score and are evaluated separately using the sibling fingerprints defined in RDR-003.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Treat matching metadata as sufficient evidence of reuse | Not selected | Metadata identifies candidates but does not prove that their instructions are related. |
| Restrict similarity to exact name-and-description groups | Not selected | Reused skills may keep the same name while changing their description. |
| Use raw text or edit distance | Not selected | Formatting changes and inserted content can make related skills appear more different than they are. |
| Use Jaccard alone | Not selected | Expanded copies can have strong retained content but a lower overall overlap score. |
| Use MinHash, LSH, or embeddings initially | Not selected | The candidate population is already narrowed enough to begin with a simpler, interpretable method. |
| Use a fixed threshold without validation | Not selected | The acceptance threshold must be supported by manual review. |

## Consequences and Limitations

- Similarity provides evidence that artifacts are related, not proof of copying or lineage.
- Same-name candidate groups can still contain unrelated artifacts.
- Related skills whose names changed can still be missed before similarity analysis.
- Containment can overstate similarity when a short artifact is embedded in a much larger one; Jaccard helps reveal that case.
- The shingle size and acceptance threshold require validation before final analysis.
- Sibling-resource changes are considered separately and do not influence the `SKILL.md` similarity score.

## Follow-up Actions

- Validate the similarity approach on a manually reviewed sample.
- Compare 3-, 5-, and 7-token shingles and select an appropriate size.
- Select and document the similarity threshold.
- Record false positives, false negatives, and ambiguous matches for error analysis.
- Use validated relationships as the basis for later security-delta comparisons.

## Revisit Criteria

Revisit this decision if token-shingle similarity does not reliably separate related from unrelated artifacts, validation produces unacceptable error rates, or the candidate volume requires a more scalable similarity method.

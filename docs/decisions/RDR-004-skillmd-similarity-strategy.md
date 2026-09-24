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

Question 4 asks whether modified or reused skills introduce security-sensitive behavior that was not present in an earlier version or source artifact.

RDR-001 established that we can infer useful earlier/later relationships from the artifacts available in GitSkills without reconstructing complete repository history. RDR-003 established the candidate groups and the exact-content checks that happen before similarity analysis.

The remaining problem is deciding whether two `SKILL.md` files with different content are still similar enough to make a meaningful security comparison. Matching `name` and description is useful for finding candidates, but it does not prove that the files are related. Exact hashes tell us when files are identical, but not when one is a modified version of another.

## Decision Drivers

- Do not treat shared metadata as proof that two skills are related.
- Detect modified skills even when later versions add substantial new content.
- Keep the similarity method understandable, reproducible, and practical to validate.
- Avoid unnecessary provenance reconstruction or approximate-search complexity.
- Preserve meaningful technical content such as commands, URLs, paths, and identifiers.
- Validate the similarity rules before using them as research evidence.

## Decision

> **For candidate artifacts with different `file_sha` values, compare their `SKILL.md` bodies using token shingles. Use containment as the primary similarity measure and Jaccard as a supporting measure.**

Artifacts reaching this step have already been placed in the same candidate group by RDR-003 because they share the same `name` and normalized description. That tells us they are worth comparing, but not that they are actually related.

### Similarity Comparison

Similarity will be measured using the `SKILL.md` body rather than YAML frontmatter. The goal is to compare the skill instructions themselves, while frontmatter mainly contains metadata and configuration. In addition, `name` and description already participate in candidate grouping, so including them again would artificially increase similarity. Frontmatter is also excluded from behavioral security scanning as documented in RDR-002.

The body will be broken into tokens and then into overlapping **5-token shingles**. A shingle is simply a sequence of five consecutive tokens. This allows formatting differences to have less effect on the comparison while still preserving meaningful text and technical content.

Two similarity measures will be recorded:

- **Directional containment** asks: *How much of the earlier artifact is still present in the later artifact?*
- **Jaccard similarity** asks: *How similar are the two artifacts overall?*

Containment is the primary signal because a later artifact may keep most of an earlier skill while adding a significant amount of new content. Jaccard provides useful context by showing how much the two complete artifacts overlap.

For example, if an earlier artifact has 100 shingles, a later artifact has 150, and they share 85:

```text
containment = 85 / 100 = 0.85
jaccard     = 85 / 165 = 0.52
```

The containment score shows that 85% of the earlier content is still present. The lower Jaccard score shows that the later artifact also contains a meaningful amount of additional content.

Both measures are useful because either one can be misleading by itself. Jaccard can make a legitimate expanded copy look less similar because the added content increases the union. Containment handles that case well. On the other hand, containment can be high when a relatively short earlier artifact appears inside a much larger later artifact. Jaccard makes that size difference visible and helps identify cases that deserve closer review.

Containment will remain the main similarity signal. Jaccard will be used as supporting evidence during validation. Validation will determine whether Jaccard remains descriptive or becomes part of the final matching rules.

Five-token shingles are the starting point, not a fixed assumption. The final shingle size and similarity threshold will be selected through manual validation.

### Choosing an Earlier Comparison

`first_commit_at` will be used to determine which artifact was observed earlier in the dataset. It provides an ordering for comparison; it does not prove which artifact was the original source.

For each later artifact, we will compare its `SKILL.md` with earlier candidates in the same group. If one or more earlier artifacts pass the validated similarity rules, the one that most closely matches the later artifact will be used as the comparison baseline for security analysis.

This avoids comparing every later artifact only with the oldest member of the group. For example:

```text
A -> B -> C

A vs. B = 0.85 containment
A vs. C = 0.62 containment
B vs. C = 0.91 containment
```

If `C` were compared only with `A`, it might be rejected as unrelated. Comparing it with `B` shows a much stronger relationship and better captures gradual changes over time.

This still does not prove that `B` is the true historical parent of `C`. It only identifies the best earlier comparison available in the dataset. If two earlier artifacts are similarly good matches, the relationship may need manual review rather than a definitive lineage claim.

### Sibling Resources

Sibling resources are not included in the `SKILL.md` similarity score.

RDR-003 defines sibling-content fingerprints that tell us whether bundled resource content changed. When sibling content differs, those changes are examined separately during security analysis rather than being mixed into the `SKILL.md` similarity calculation.

## Evidence

RDR-003 already narrows the comparison problem before similarity analysis begins. Shared metadata identifies candidate groups, while exact hashes identify unchanged `SKILL.md` content and sibling-content differences.

Similarity analysis is therefore needed only when candidate artifacts have different `SKILL.md` content. For those cases, token shingles provide a direct and interpretable way to measure how much content was retained and how much the files differ overall.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Treat matching `name` and description as sufficient evidence of reuse | Not selected | Shared metadata identifies candidates but does not prove that their contents are related. |
| Compare every later artifact only with the earliest artifact in the group | Not selected | Gradual changes can leave a later artifact much closer to an intermediate version than to the oldest one. |
| Reconstruct a complete provenance or clone graph | Not selected | The dataset cannot establish complete historical lineage, and this would expand the project beyond what Question 4 requires. |
| Use approximate search such as MinHash, LSH, or embeddings | Not selected | Candidate grouping and exact hash checks already reduce the problem enough to use a simpler, exact similarity measure. |
| Use raw-text or edit-distance similarity | Not selected | Formatting changes and inserted content can make related skills appear more different than they are; token shingles tolerate those changes while preserving local content overlap. |
| Use a fixed threshold without validation | Not selected | The similarity cutoff must be supported by manual review rather than chosen arbitrarily. |

## Consequences and Limitations

- Similarity provides evidence that two artifacts are related, but it does not prove direct ancestry or copying.
- `first_commit_at` is the earliest commit found at the artifact's current path and may not represent the true origin of the content.
- Grouping by `name` and description can miss related skills whose metadata changed, and it can place unrelated skills with matching metadata in the same group.
- A later artifact may have more than one reasonable earlier match. Ambiguous cases may require manual review.
- The shingle size and similarity threshold must be validated before final analysis.
- Sibling-resource changes are evaluated separately and do not affect the `SKILL.md` similarity score.

These limitations should also be reflected in the project methodology and `THREATS_TO_VALIDITY.md`.

## Follow-up Actions

- Validate the token-shingle approach on a manually reviewed sample.
- Compare 3-, 5-, and 7-token shingles and select the size that performs best during validation.
- Select and document the similarity threshold supported by manual review.
- Record ambiguous matches, false positives, and false negatives for later error analysis.
- Apply the security scanner to validated earlier/later comparisons.

## Revisit Criteria

Revisit this decision if validation shows that:

- token-shingle similarity cannot reliably distinguish related from unrelated artifacts;
- the selected threshold produces too many false positives or false negatives;
- candidate groups contain too many ambiguous earlier matches; or
- grouping by `name` and description misses a meaningful amount of reuse.

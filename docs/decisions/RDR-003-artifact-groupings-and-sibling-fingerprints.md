# RDR-003: Artifact Groupings and Sibling Fingerprints

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-23 |
| **Type** | Research methodology, data, and implementation |
| **Related work** | Question 4, similarity analysis, Sprint 1 |
| **Evidence** | `sql/create_analysis_tables.sql`, `sql/update_artifact_groupings.sql`, DuckDB exploratory analysis |
| **Supersedes** | None |

## Context

Question 4 depends on comparing related `SKILL.md` artifacts to determine whether reused or modified skills introduce new security-sensitive behavior.

The raw GitSkills data contains many repeated and near-related artifacts spread across repositories. Comparing every artifact with every other artifact would be impractical, while grouping too narrowly could remove useful variants before similarity analysis. We also need to account for bundled files because two identical `SKILL.md` files can still be packaged with different scripts, references, or other resources.

The project therefore needs a consistent way to identify reasonable comparison candidates and a low-cost way to tell when the surrounding skill content has changed.

## Decision Drivers

- Reduce the comparison space without discarding likely reused or modified skills.
- Preserve same-name variants even when their descriptions differ.
- Keep repeated `SKILL.md` occurrences when their bundled resources may differ.
- Detect exact content differences before using more expensive similarity analysis.
- Treat content changes as more important than path or directory-layout changes.
- Distinguish known absence of sibling files from unavailable sibling data.

## Evidence

Exploratory review showed that reused skills can keep the same name while changing their description or surrounding metadata.

For example, several `busybox-on-windows` artifacts shared the same skill name but used descriptions ranging from the original description to variants such as:

```text
ALWAYS use this when the request matches Busybox ON Windows ...
busybox-on-windows workflow skill ...
```

These are useful comparison candidates even though the descriptions are not identical.

We also found that identical `SKILL.md` contents do not guarantee that the complete skill package is identical. Different occurrences can include different bundled files, so the surrounding resources need to be considered separately.

## Decision

> **Use same-name artifacts as the candidate population for comparison, retain description-based groupings as supporting metadata, and use exact content fingerprints to identify changes in bundled sibling resources.**

The grouping step is intended to narrow the search space, not to prove reuse or lineage. Artifacts sharing a skill name are considered reasonable candidates for later similarity validation. Normalized descriptions remain useful for organizing closely matching variants, but a changed description does not remove an artifact from consideration.

The project materializes this comparison population in `artifact_groupings` so later analysis can work from a consistent set of candidates without repeatedly rebuilding the same selection logic. The detailed table structure is documented in the data dictionary.

Bundled resources are handled with a content fingerprint derived from sibling file hashes. Paths and directory layout are intentionally ignored so that reorganizing files does not appear as a content change.

At a high level, the comparison flow is:

```text
same SKILL.md content + same known sibling fingerprint
    -> no observed content change

same SKILL.md content + different sibling fingerprint
    -> bundled resources changed

different SKILL.md content
    -> similarity analysis is needed

unknown sibling fingerprint
    -> do not assume the bundled resources are equivalent
```

This allows inexpensive exact checks to remove obvious non-changes before more detailed similarity and security analysis.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Require an exact name-and-description match before retaining candidates | Not selected | Reused or modified skills can keep the same name while changing their description. |
| Keep only one representative of byte-identical `SKILL.md` content | Not selected | Identical skill files can be bundled with different resources. |
| Include filenames, paths, and directory layout in the sibling fingerprint | Not selected | Layout changes are not the security-content changes Question 4 is intended to study. |
| Run similarity analysis before exact hash checks | Not selected | Exact hashes can identify unchanged content more simply and cheaply. |

## Consequences and Limitations

- Same-name candidate groups can contain unrelated artifacts, so similarity validation is still required.
- Related skills that change their name can fall outside the candidate population.
- Description groupings help organize variants but do not establish ancestry or reuse.
- A changed sibling fingerprint shows that bundled content differs, but not whether the difference is security-relevant.
- Missing sibling information remains unknown and cannot be treated as an empty or unchanged bundle.

## Follow-up Actions

- Validate same-name candidates using the similarity strategy defined in RDR-004.
- Compare bundled resources when identical `SKILL.md` contents have different sibling fingerprints.
- Apply security-delta analysis only after the relevant artifact relationship has been validated.

## Revisit Criteria

Revisit this decision if same-name grouping produces too many unrelated candidates, misses a meaningful amount of reuse, or sibling fingerprints do not provide useful separation between unchanged and changed skill packages.

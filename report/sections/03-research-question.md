# Research question and study scope

> **Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

The study operationalizes this question as a comparison of stored instructions between related artifacts. An **artifact occurrence** is one skill at a repository and path in the dataset. A **skill variant** groups identical file content, while a **bundle variant** also accounts for the known state of sibling resources. A **candidate family** contains qualifying occurrences with the same exact name. Sharing a name defines a search space; it is not evidence of reuse by itself.

The unit of directional analysis is an ordered pair of related artifacts. Its endpoints are designated **base** and **derived** according to the available direction evidence. These terms identify the comparison orientation, not proven original authorship or direct copying. Equivalent and direction-unknown relationships are retained separately rather than treated as negative security findings.

The primary reported outcome is the **proportion of sampled families** with at least one directed comparison supporting a defined risk indicator. We also report comparison-level findings, but one family can contribute many related comparisons. A risk indicator is supported by evidence of a specific change, not simply by a new keyword or more scanner matches. Section 6 explains how we make that distinction.

We expected to see both security-sensitive changes and ordinary updates. Some reported changes may be intentional features rather than unwanted exposure. Our eleven indicators define which changes we assess; they do not establish why a change was made or whether it ran in practice.

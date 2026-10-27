# Research question and study scope

> **Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

The study operationalizes this question as a comparison of stored instructions between related artifacts. An **artifact occurrence** is one skill at a repository and path in the dataset. A **skill variant** groups identical file content, while a **bundle variant** also accounts for the known state of sibling resources. A **candidate family** contains qualifying occurrences with the same exact name. Sharing a name defines a search space; it is not evidence of reuse by itself.

The unit of directional analysis is an ordered pair of related artifacts. Its endpoints are designated **base** and **derived** according to the available direction evidence. These terms identify the comparison orientation, not proven original authorship or direct copying. Equivalent and direction-unknown relationships are retained separately rather than treated as negative security findings.

The primary outcome is whether a comparison supports at least one of the eleven defined risk indicators. The indicator assesses a particular introduced or changed operation, not merely a new keyword, a larger file, or a higher count of matches. For example, changing the source of an executed remote script can matter even if both artifacts contain exactly one download-and-execute command. Replacing a package manager for an otherwise equivalent installation need not introduce a new dependency-acquisition operation.

The group's expectation is that some related artifacts will contain observable security-sensitive changes, but that many differences will reflect routine adaptation, packaging, or legitimate functionality. The competing explanation is that a reported indicator identifies an intended feature rather than unwanted exposure. The study does not measure a causal effect of reuse, execute instructions, or attempt comprehensive security detection. The eleven indicators define the scope of the assessment; behavior outside that scope is not automatically a scanner error.

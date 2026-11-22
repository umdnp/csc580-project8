# Research question and study scope {#sec-research-question}

> **Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

We investigate this question by comparing stored instructions from skills that appear related. We first group skills with the same exact name, then check whether their content is sufficiently similar for comparison. Sharing a name or similar content does **not** prove that one was copied from another.

An **artifact occurrence** is a skill found at a particular repository and file path. Occurrences with identical `SKILL.md` content form a **skill variant**; a **bundle variant** also accounts for the known contents of accompanying files, such as scripts. A **candidate family** contains qualifying occurrences sharing an exact name, including some that may ultimately prove unrelated.

The unit of directional analysis is an ordered pair of related artifacts. Its endpoints are designated **base** and **derived** according to the available direction evidence. These terms identify the comparison orientation, not proven original authorship or direct copying. Equivalent and direction-unknown relationships are retained separately rather than treated as negative security findings.

The primary reported outcome is the **proportion of sampled families** with at least one directed comparison supporting a defined risk indicator. We also report comparison-level findings, but one family can contribute many related comparisons. A risk indicator is supported by evidence of a specific change, not simply by a new keyword or more scanner matches. [Section V](#sec-method) explains how we make that distinction.

We expected to see both security-sensitive changes and ordinary updates. Some reported changes may be intentional features rather than unwanted exposure. Our eleven indicators define which changes we assess; they do not establish why a change was made or whether it ran in practice.

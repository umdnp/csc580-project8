\clearpage

# Research Question and Expectations

## Selected Topic

This project investigates Question 4, **Skill security and supply-chain risk**, from the MSR 2027 Mining Challenge-inspired project outline.

## Research Question

> **Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

## Expectations

This is an exploratory question rather than a confirmatory test of a directional hypothesis. We expect the collected artifacts to contain a mixture of security-sensitive patterns and legitimate operational instructions, and we expect some same-name candidates not to be meaningfully comparable. We also expect incomplete provenance, history, or sibling data to leave some otherwise related pairs without a reliable direction. These expectations motivate the analysis and its uncertainty handling; they are not observed findings or claims about prevalence. Results are reported only from completed, traceable analysis outputs.

## Operational Definitions

These definitions specify how the research concepts are represented and measured by the tools. Scanner rules operationalize security-relevant text patterns; relationship rules operationalize candidate relatedness and direction. Both are needed to interpret an introduced signal. The detailed algorithms and the current 13-rule catalog appear in Method and Implementation.

### Artifact Occurrence and Content Variant

An artifact is one collected skill-file occurrence at a repository and path within the dataset snapshot. The local `artifact_id` identifies that occurrence in the saved DuckDB build. Occurrences with identical skill-file hashes share a skill-content variant but remain distinct artifacts. A bundle variant additionally accounts for known sibling-file content; missing sibling information is not equivalent to an empty bundle.

### Candidate Family and Related Artifacts

A candidate family comprises qualifying occurrences with the same exact skill name, including differing description subgroups. Shared names define the search space, not verified reuse or ancestry. Distinct skill variants are considered related when they satisfy the configured shingle-similarity policy. Bundle states sharing the same skill content can also be compared for sibling changes. A connected similarity cluster can contain endpoints that do not themselves pass the direct pairwise test.

### Base Artifact

The base is the source endpoint of an ordered comparison. For a selected family relationship, it is the inferred predecessor supported by the implemented direction procedure: resolved declared provenance, observed chronology or equivalent-peer chronology, a repository-creation boundary, or asymmetric containment. The evidence basis is retained because these alternatives provide different kinds of support. A base is not necessarily the earliest published artifact or the original author's version.

For `scan_diff`, the base is simply the first input path supplied by the caller. For the extraction notebook, it is the immediately preceding occurrence within the same name group in view order. These input conventions do not independently establish lineage.

### Derived Artifact

The derived artifact is the target endpoint compared against the base. In the selected family graph, it is the inferred child according to the recorded direction evidence. In a direct file comparison, it is the second input path; in the extraction notebook, it is the next occurrence in the adjacent pair. Calling an endpoint derived does not prove direct copying, historical descent, or malicious modification. Direction-unknown relationships are retained as unresolved and excluded from directional family scans.

### Security-Relevant Instruction Pattern

A security-relevant instruction pattern is text matched by a rule in the active static-scanner catalog. The current categories are command execution, network access, file-system access, credential access, external code execution, and system modification. A rule is a specific detector within a category: for example, EXT-002 detects recognized package-installation patterns within external code execution, while NET-001 detects HTTP/HTTPS URLs within network access.

A rule match records the rule ID, assigned category, and available location or excerpt evidence. A category is present when at least one rule assigned to it matches. Skill scans normally exclude leading YAML frontmatter; sibling text is scanned without that skill-specific exclusion. Matched content is never executed by the scanner. A match can occur in legitimate instructions or documentation and does not establish that an action occurred, that a resource was sensitive, or that a vulnerability exists.

### Introduced Risk Signal

An introduced signal is measured relative to both endpoints, using the same rule definitions and a comparable scan scope. The study distinguishes:

| Measure | Operational condition | Example |
| --- | --- | --- |
| Introduced rule | A rule has zero matches in the base and at least one in the derived artifact | Package-install matches change from 0 to 1. |
| Introduced capability category | No rule in a category matches the base, while at least one matches the derived artifact | External code execution is absent from the base profile and present in the derived profile. |
| Increased existing signal | A rule already matches the base and its count increases | Package-install matches change from 1 to 3, producing a delta of +2. |

The current comparator's JSON field `introduced` records category introductions. Its `rule_deltas` field records rules with changed match counts, including increases and decreases; it is not a list limited to newly appearing rules. A new rule can appear within a category already represented in the base, so rule introduction and category introduction are separate measures. More matches for an existing rule need not introduce either.

These terms describe changes in detected text, not proven increases in harm. Family-level review can also flag matches in new or changed destination sibling content without an increased aggregate count; such findings must be labeled by scan surface and should not automatically be called introduced capabilities. Missing required content makes the relevant coverage incomplete rather than negative.

### Match Count, Delta, and Retained Signals

A rule's match count is the number of non-overlapping matches retained within that rule after its pattern matches are deduplicated. Matches across different rules remain separate, so the total is not a count of unique actions. The delta is the derived count minus the base count. Positive and negative values indicate more or fewer matches, respectively; zero indicates equal counts, not necessarily identical instructions.

A rule or category is retained when present in both endpoint profiles and removed when present only in the base. Retention concerns presence, so a retained rule can still have a positive or negative count delta. A rule omitted from `rule_deltas` can be present with equal counts on both sides. These definitions do not imply that the current output serializes separate retained and removed sets.

### Modified or Reused Skill

For this study, a potentially modified or reused skill is an occurrence connected to another through the implemented candidate and relationship procedure. Exact content identity supports an observation of shared content; qualifying similarity supports candidate relatedness; available direction evidence supports an ordered comparison. None alone proves the mechanism of transfer or authorial intent.

Modification can concern the skill body, bundled sibling content, or both. Shared content in separate occurrences does not itself demonstrate modification. The main directional analysis uses selected predecessor relationships, while equivalent and unresolved relationships remain separately reported. The notebook's adjacent comparisons serve extraction and scanner testing and must not be counted as independently verified reuse relationships.

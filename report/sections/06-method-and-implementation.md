# Method

## Establish relatedness and direction

The relationship stage first separates identical skill content from distinct variants and incorporates known sibling fingerprints into bundle states. It masks leading frontmatter, tokenizes the body, and compares sets of distinct contiguous five-token shingles. The saved policy requires maximum directional containment of at least 0.80, Jaccard overlap of at least 0.30, and at least five shared shingles. These are operational thresholds for candidate relatedness, not probabilities of copying. Identical skill text can still belong to different bundle states.

Direction is assessed only after relatedness. The evidence hierarchy prefers resolved declared provenance, followed by direct observed chronology, equivalent-peer chronology, repository-creation boundaries, and asymmetric containment. A peer date can show that an equivalent skill-and-sibling state existed earlier; it is not the selected artifact's own commit date. Repository creation is used as a boundary, not a skill timestamp. A containment difference of at least 0.10 provides the weakest ordering signal when stronger evidence is absent.

The graph retains one selected predecessor per target while avoiding cycles, and records other supported directions as additional edges. Equivalent or unresolved relationships remain separately visible. The analysis retains the direction basis throughout reporting because a structural expansion hypothesis warrants a different interpretation from dated or resolved-source evidence. Appendix B contains the rule definitions, run settings, and component diagrams.

## Extract and compare observable constructs

The static scanner has thirteen rules across command execution, network access, file-system access, credential access, external code, and system modification. It records source constructs such as commands, URLs, paths, and API calls, with locations and context. Leading skill frontmatter is masked for behavioral scanning while selected provenance fields remain available to relationship analysis. Available sibling file content is considered for applicable bundle changes; directories themselves are not executable evidence.

The comparator preserves added, removed, and retained evidence rather than relying only on match counts. Equal counts can conceal a changed script URL or destination; a larger count can simply reflect repetition. Corresponding operations are associated only when sufficiently clear. Ambiguous correspondences and partial extraction remain uncertain. Local script comparisons use available sibling hashes to distinguish a content change from an identical-content rename.

A separate assessor interprets this comparison using the eleven indicators below. Detection and assessment are intentionally separate: recognizing a package-install command can be correct even when treating the change as newly introduced acquisition is incorrect. Rule counts and capability categories remain diagnostic outputs; they are not substitutes for indicator judgments.

## Eleven risk indicators

The following table states the operational scope established in RDR-010. Each indicator requires an observable change and source context. It is a reason for review, not a confirmed vulnerability. The study is limited to these eleven definitions; it does not promise recognition of every security-relevant behavior.

| ID | Indicator | Required change |
| -------- | ------------------------ | ---------------------------------------------------- |
| RI-001 | Download and execute | Newly downloaded content passes directly to an interpreter. |
| RI-002 | Executed code source | The URL of remotely executed content changes, including its path. |
| RI-003 | Network expansion or redirection | An operation adds a hostname/domain or explicit outbound data transfer. |
| RI-004 | Weakened network security | HTTPS becomes HTTP, or certificate verification is disabled. |
| RI-005 | External code or dependency acquisition | An installation/acquisition operation is introduced, or its source/registry changes. Package-name/version edits alone do not qualify. |
| RI-006 | Destructive or privileged file operation | Destructive operations are introduced or expand in scope or privilege. |
| RI-007 | Credential access or potential exposure | A new operation accesses a recognized credential file or directly includes a recognizable credential reference in an outbound request. |
| RI-008 | System or permissions modification | An operation introduces or expands permissions, service, schedule, or system-configuration changes. |
| RI-009 | Sensitive file-system operation | A read/write operation newly targets a recognized sensitive file or directory. |
| RI-010 | Local script execution | A local invocation is introduced, its target has different known content, or an invoked sibling changes. Identical-content renames do not qualify. |
| RI-011 | External instruction dependency | The skill newly directs following external instructions, changes their source, or turns a reference into such a directive. |

Context can suppress a finding or make it uncertain. An explicit warning against an operation should not independently support an instruction to perform it. A documentation link does not establish network execution or an instruction dependency. A newly mentioned credential name does not alone satisfy RI-007. Recognized missing content remains a coverage limitation rather than a negative judgment.

## Outcomes and denominators

For each pair, the assessor reports supported and uncertain indicator IDs, supporting evidence, a policy version, and coverage information. The indicator count is the number of distinct supported categories; the finding count deduplicates supporting constructs within that comparison. One credential-file read can support RI-007 and RI-009 while representing one changed construct. Neither count is a severity score.

The main descriptive measure is the number of analyzed directed pairs with at least one supported indicator divided by all analyzed directed pairs in the selected cohort. Per-indicator frequencies use the same denominator and can overlap. The analysis also separates primary/additional edges and complete/incomplete coverage. The overall automated percentage includes incomplete pairs and is labelled accordingly; a complete-case calculation is reported as a sensitivity description, not as an accuracy correction.

Pairs can share artifacts or represent related copies of one change. The analysis does not treat these pairs as independent incidents or use a binomial confidence interval to imply population risk. Appendix B summarizes the pipeline settings; Appendix E identifies supporting documentation and result artifacts.

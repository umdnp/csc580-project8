# 1. Revised Research Question

**Which security-relevant instruction patterns occur in content-bearing GitSkills artifacts, how prevalent are those patterns, and how often does the same signal-containing content SHA occur across multiple repositories?**

Exact recurrence of individual security-relevant instructions within otherwise different artifacts may be examined if project time permits. It is an optional stretch extension and is not required to answer the revised research question.

# 2. Original Research Question

The team selected **Question 4: Skill security and supply-chain risk** from the project outline.

**Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

The project outline associates this question with a static analyzer or rule-based scanner for executable commands, URLs, scripts, file operations, credential-related instructions, and changes across skill versions.

# 3. Rationale for Revising the Question

The original question requires a comparison between an earlier or source artifact and a later, modified, or reused artifact. Answering it as written would require the team to establish a defensible relationship such as:

earlier or source artifact -> later or derived artifact

The available GitSkills data does not directly provide that relationship. Preliminary dataset investigation found that:

- The database appears to store one current artifact state per repository and path rather than the historical contents of each SKILL.md version
- Available history information summarizes repository or artifact history but does not supply the earlier file contents required for direct before-and-after comparison
- Exact content SHAs show that identical complete content occurs in multiple repositories, but they do not reveal copying direction or provenance
- The database identifies very few repositories as forks, making fork metadata insufficient for reconstructing reuse relationships
- The same declared skill name can occur with many different content SHAs, so a shared name is not reliable proof of lineage
- Content similarity can identify plausible near-duplicates, but similarity alone does not establish which artifact was the source or whether the artifacts have a parent-child relationship

The team could attempt to infer genealogy using names, content similarity, timestamps, and repository metadata. However, this would introduce substantial methodological uncertainty and computational cost. It would also shift the central project from security analysis toward designing and validating a genealogy-reconstruction method.

In contrast, the database directly supports:

- Static analysis of stored artifact content
- Measurement of defined security-relevant instruction patterns
- Prevalence calculations across content-bearing artifacts
- Grouping of complete artifacts by content SHA
- Measurement of how often the same content SHA occurs across distinct repositories

The revised question is therefore based on directly observable data. It retains the original topic's emphasis on security-relevant behavior and cross-repository distribution without claiming that the team can reconstruct historical versions, prove ancestry, identify copying direction, or determine that a behavior was newly introduced.

# 4. Definitions

## GitSkills Artifact

A GitSkills artifact is one artifact record represented in agent_skills_release.db and associated with a repository and artifact path.

## Content-Bearing Artifact

A content-bearing artifact is a GitSkills artifact for which stored textual content is available to the analysis pipeline. Records without stored content are excluded because the proposed instruction patterns cannot be measured from them.

## Security-Relevant Instruction Pattern

A security-relevant instruction pattern is a statically observable instruction or textual pattern describing behavior that could affect a system, data, credentials, or an external service if carried out by an agent.

The initial high-level categories are:

- Command execution
- File-system access or modification
- External network access
- Script creation, reference, or invocation
- Credential, secret, token, or authentication handling

## Occurrence of a Pattern

A security-relevant instruction pattern occurs when the static analyzer matches at least one documented detection rule for that category in an artifact's stored content.

An occurrence means that the pattern was detected in the text. It does not mean that the instruction was executed or that the described capability was available in a particular runtime environment.

## Signal-Containing Artifact

A signal-containing artifact is a content-bearing artifact that matches at least one documented security-relevant instruction-pattern category.

## Prevalence

Prevalence is the proportion of analyzed content-bearing artifact records that match a defined instruction-pattern category.

## Exact Recurrence of an Individual Instruction

Exact instruction recurrence is distinct from complete-artifact replication. It occurs when the same extracted security-relevant instruction appears in artifacts that may otherwise have different complete-content SHAs.

For example, the same command may occur in several different SKILL.md files even though the surrounding instructions cause those files to have different content SHAs. Studying this would require the team to define how commands or other instruction units are extracted and minimally normalized before comparison.

This analysis may be performed if time permits, but it is not a required component of the revised research question.
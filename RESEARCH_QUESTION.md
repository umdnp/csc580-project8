# Research Question

## Selected Topic

**Question 4: Skill Security and Supply-Chain Risk**

### Research Question

**Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

### Required Implementation

The project requires a static analyzer or rule-based scanner for executable commands, URLs, scripts, file operations, credential-related instructions, and changes across skill versions.

### Minimum Evidence

The project should include a threat model, detection rules, annotated examples, discussion of false positives, and a safe reporting artifact. Untrusted scripts from the dataset must not be executed.

## Our Interpretation of the Research Question

We interpret this question as asking whether reused or modified skills in the GitSkills dataset tend to introduce new behavior that could increase security risk.

The focus is not just on whether an individual skill contains commands, file operations, network access, scripts, or instructions involving credentials or secrets. We are interested in whether these kinds of behaviors appear when skills are reused or changed, even though they were not present in an earlier or source artifact.

Though not explicitly defined, we interpret **other risky behavior** to mean actions beyond command execution, file-system access, and network access that could increase security risk. This could include things such as handling credentials or secrets, creating or invoking scripts, or other instructions that could expose, alter, or misuse systems or data. This does not necessarily mean that the skill is malicious.

This can become a supply-chain concern because skills are shared and reused across repositories. If new risky behavior is introduced into a reused skill, that behavior may also be carried into other projects that adopt or copy it.

Our goal is to use the GitSkills dataset to see whether this happens in practice and, when it does, what kinds of risky behavior are being introduced.

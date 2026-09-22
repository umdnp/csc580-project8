\clearpage

# Threats to Validity

## Construct Validity

[TODO: Discuss whether the selected rules and categories accurately represent the security-relevant behaviors the project intends to measure.]

## Internal Validity

[TODO: Discuss errors in relationship identification, version ordering, content extraction, rule matching, and profile comparison.]

## External Validity

[TODO: Discuss whether findings from the selected dataset generalize to other GitSkills, repositories, agent platforms, or time periods.]

## Conclusion Validity

Observed security-relevant signals may have simpler or competing explanations that do not imply elevated risk. For example, capabilities such as shell execution, network access, file modification, or use of tools such as curl may occur frequently because they are common requirements of legitimate software-development, automation, deployment, or system-administration workflows. As a result, the presence of one or more security-relevant indicators should not be interpreted by itself as evidence that a skill is malicious or unsafe.

Other factors may also affect the strength of the study's conclusions, including small sample sizes within individual categories, sparse observations, repeated or near-duplicate content, and unstable estimates for uncommon behaviors. Where applicable, results will therefore be interpreted as evidence of patterns or associations rather than proof of security risk.

## Reproducibility Threats

[TODO: Discuss dependency versions, dataset availability, rule-catalog changes, nondeterminism, random seeds, and computational requirements.]

## Missing and Incomplete Data

[TODO: Explain how unavailable content, incomplete histories, unidentifiable relationships, and excluded records may affect the results.]

## Mitigations

[TODO: Summarize the tests, manual validation, versioning, documentation, sensitivity analyses, and reporting practices used to reduce these threats.]
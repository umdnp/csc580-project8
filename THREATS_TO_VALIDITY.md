# Threats to Validity

This document records the main threats to validity identified during Sprint 1. It will be updated as the implementation and validation continue.

## Construct Validity

### Rule-Based Security Detection

The scanner uses rule-based text patterns to identify security-sensitive behavior such as command execution, file-system access, network access, credential handling, external code execution, and system modification.

The main concerns are:

- A match may appear in documentation or an example rather than an instruction that will actually be executed.
- The scanner may miss behavior expressed in a form that the current rules do not recognize.
- A change in match count does not necessarily mean that risk increased or decreased.
- A security-sensitive capability is not necessarily malicious or unsafe.

For example, a skill may mention `curl` while explaining an API without instructing an agent to run it.

Scanner findings are therefore treated as **static risk signals, not confirmed vulnerabilities**. In Sprint 2, manual validation will be used to estimate false positives, false negatives, and important coverage gaps.

### Candidate-Family Matching and Similarity

The project first uses same-name skills to find possible comparison candidates and then uses content similarity and other available evidence to determine whether artifacts appear to be related.

The main concerns are:

- Two unrelated skills may share the same name.
- A reused skill that was renamed may be missed by the initial grouping.
- Similarity results depend on the selected method and thresholds.
- Candidate-family membership does not establish copying, authorship, or the original source.

A matching name or similarity score is therefore treated as evidence of a possible relationship, not proof of one. Similarity thresholds and representative relationships will require validation before broader conclusions are made.

See [RDR-003](docs/decisions/RDR-003-grouping-and-sibling-fingerprints.md) and [RDR-004](docs/decisions/RDR-004-skillmd-similarity-strategy.md).

### Language and Frontmatter

Behavioral scanning excludes YAML frontmatter and keeps non-English skills in the analysis population.

This creates two known limitations:

- Security-relevant information that appears only in frontmatter is outside the behavioral scan.
- Risky behavior written only in non-English prose may be missed when it does not contain recognizable technical indicators such as commands, URLs, paths, tool names, or credential references.

This tradeoff reduces false positives from descriptive metadata while preserving non-English artifacts that still contain recognizable technical behavior.

See [RDR-002](docs/decisions/RDR-002-language-and-frontmatter-scanning.md).

## Internal Validity

### Earlier/Later Ordering

Question 4 requires us to determine whether security-sensitive behavior was **introduced**, so related artifacts need a reasonable earlier/later ordering.

GitSkills does not provide complete historical file contents or commit history for every artifact.

The main concerns are:

- `first_commit_at` is the earliest commit observed for the artifact in the available GitSkills history, not guaranteed proof of when the skill was originally created or introduced.
- File moves or renames may hide earlier history.
- The earliest artifact observed in the dataset may not be the true original.
- Source information written in a skill may be incomplete or incorrect.
- Some relationships may not contain enough evidence to determine which artifact came first.

The project uses the strongest available evidence to establish direction and leaves a relationship unresolved when the evidence is not strong enough. Unresolved relationships should not be used to claim that a behavior was introduced or removed.

See [RDR-007](docs/decisions/RDR-007-effective-chronology-and-direction-evidence.md).

### Alternative Explanations

A newly introduced security-sensitive behavior does not automatically mean that reuse or modification made a skill less secure.

For example, a later skill may add a network request, package installation, or file operation because its intended functionality changed.

The analysis therefore needs to separate:

- **what changed**, which can be observed from the artifacts; from
- **what the change means**, which requires interpretation.

A security-sensitive change should not be treated as evidence of malicious intent or increased risk without supporting evidence.

### Missing and Incomplete Data

Some GitSkills records have incomplete history, metadata, or related-file information.

Missing data can:

- prevent a relationship from being established;
- leave the earlier/later direction unresolved;
- hide behavior contained in unavailable related files; or
- bias the analysis toward records that have more complete metadata and history.

Missing information should be reported as missing or unresolved rather than interpreted as evidence that a behavior or relationship is absent.

## External Validity

### Sprint 1 Sample

The Sprint 1 sample contains **43 artifacts across 10 skill families** and produces **17 directed comparisons** in the saved analysis reports.

The sample was purposefully selected to provide useful variation for developing and evaluating the analysis. It is not a random or representative sample of the full GitSkills population.

As a result:

- Sprint 1 percentages should not be used to estimate how common security-sensitive changes are across all GitSkills artifacts.
- The sample may favor cases that are easier for the current comparison or scanner methods to detect.
- Additional cases may be needed if later validation exposes behaviors that are not represented in the current sample.

See [RDR-006](docs/decisions/RDR-006-sprint1-sample-design-and-selection.md).

### Dataset Coverage

The analysis is limited to the selected GitSkills release dataset and the artifacts collected by its mining process.

The dataset should not be assumed to represent every agent skill, repository, platform, or development workflow. Results from this project therefore apply first to the data that was actually collected and analyzed.

## Conclusion Validity

Sprint 1 results are exploratory and should be interpreted cautiously.

In particular:

- Only selected comparisons have been manually inspected; automated output is not independent ground truth.
- Some directed comparisons may share artifacts or repeated content, so they are not necessarily independent observations.
- Ambiguous relationships are intentionally left without directional conclusions.
- Counts and percentages from the purposeful Sprint 1 sample should not be treated as population-wide risk estimates.

These limitations will be revisited as validation and broader analysis continue.

## Reproducibility

The analysis depends on the selected GitSkills release dataset, the project's derived analysis tables, the fixed Sprint 1 sample, and the versions of the analysis code and rules used to generate the results.

The repository documents how to acquire the data, build the analysis tables, reconstruct the sample, and run the notebooks. Results should identify the dataset release, sample, and analysis configuration used to generate them so that later changes to the data or rules can be distinguished from the original Sprint 1 results.

\clearpage

# Method and Implementation

## Method Overview

The study measures whether modified or reused GitSkills introduce security-relevant behavior that was absent from an earlier version or source artifact. For each eligible ordered comparison, the method scans the base and derived artifacts with the same versioned rule catalog, constructs a rule and category profile for each artifact, and measures which signals were introduced, removed, or retained in the derived artifact.

The threat model and rule catalog are still under development. The method therefore depends on stable rule identifiers, higher-level categories, and versioned configurations rather than on a fixed preliminary list of checks. Rules and categories may be refined without changing the overall comparison design, but a reported pipeline run must use one documented scanner and rule-catalog version.

## Analysis Algorithm

### Artifact Profiling

Let \(R(a)\) be the set of rule identifiers detected in artifact \(a\), and let \(C(a)\) be the set of security-relevant categories represented by those rules. For each artifact, the static analyzer records the matched rules, categories, counts, and match evidence required for validation.

### Base-Derived Comparison

For an eligible ordered pair with base artifact \(b\) and derived artifact \(d\), the comparison stage computes:

$$
R_{introduced} = R(d) \setminus R(b)
$$

$$
R_{removed} = R(b) \setminus R(d)
$$

$$
R_{retained} = R(b) \cap R(d)
$$

The same set operations are applied to category profiles:

$$
C_{introduced} = C(d) \setminus C(b), \quad
C_{removed} = C(b) \setminus C(d), \quad
C_{retained} = C(b) \cap C(d)
$$

A comparison has a rule-level introduction when $|R_{introduced}| > 0$, and it has a category-level introduction when $|C_{introduced}| > 0$. Both measures are retained because a new rule may appear within a category already present in the base artifact.

### Outcome Computation

The primary outcome is the proportion of eligible comparisons in which the derived artifact contains at least one detected security-relevant signal that was absent from the base:

$$
\text{Rule introduction rate} =
\frac{\text{eligible comparisons with at least one introduced rule}}
{\text{eligible comparisons analyzed}}
$$

$$
\text{Category introduction rate} =
\frac{\text{eligible comparisons with at least one introduced category}}
{\text{eligible comparisons analyzed}}
$$

Secondary outputs may include:

- the count and percentage of comparisons introducing each rule or category;
- distributions of introduced-rule and introduced-category counts;
- counts and percentages of comparisons with removed signals;
- counts and percentages with retained signals but no introduced signals;
- counts and percentages with no detected profile change;
- introduction rates by relationship type;
- introduction rates for same-repository and cross-repository comparisons; and
- the numbers of distinct artifacts, content SHAs, and repositories represented.

Every reported denominator will identify whether it represents comparison occurrences, unique artifact relationships, or unique content-SHA pairs.

## Threat Model and Rule Catalog

The static analyzer is intended to identify security-relevant instructions or behaviors such as executable commands, URLs, scripts, file operations, credential-related instructions, and other categories adopted by the final threat model. A rule match is a reviewable signal, not a conclusion that an artifact is malicious or unsafe.

Each rule in the catalog should define:

- a stable rule identifier;
- rule name and description;
- higher-level security-relevant category;
- detection logic or pattern reference;
- severity or review priority, if adopted by the threat model;
- known false-positive conditions;
- positive and negative examples; and
- rule-catalog version.

[TODO: Insert the finalized threat-model scope, category definitions, rationale for inclusion, and the path to the version-controlled rule catalog.]

## Static-Analysis Algorithm

The scanner processes artifact content as text and produces rule-level and category-level profiles without executing the content. Each match retains sufficient location or excerpt evidence for validation and safe reporting. The base and derived artifacts in one comparison are always scanned with the same scanner and rule-catalog versions.

[TODO: Describe the implemented parsing strategy, pattern or rule engine, match aggregation, overlapping-match behavior, category mapping, and error handling.]

## Relationship and Ordering Algorithm

The relationship stage identifies related artifacts, determines which artifact is the base and which is derived, and records the evidence supporting both decisions. A comparison proceeds only when the relationship and ordering satisfy the eligibility criteria in the Dataset and Data Preparation section.

[TODO: Describe the implemented relationship types, candidate-generation logic, ordering evidence, tie or ambiguity handling, confidence or review rules, and any lineage limitations.]

## Tools and Implementation Architecture

The implementation is organized around four functional components:

1. **Extractor:** Reads the relevant records and metadata from `agent_skills_release.db`.
2. **Relationship builder:** Produces candidate ordered base-derived relationships and eligibility evidence.
3. **Static analyzer:** Applies the versioned rule catalog to unique artifact content and creates rule and category profiles.
4. **Comparator and reporter:** Joins profiles to eligible relationships, computes changes and aggregate measures, and writes reproducible analysis artifacts.

[TODO: Name the implemented programming language, database/query engine, packages, command-line entry points, modules or classes, configuration files, test framework, and report-generation tools. Include exact versions or a dependency lock file where applicable.]

## End-to-End Pipeline

The intended execution path is:

1. Load the required source tables from `agent_skills_release.db`.
2. Extract analyzable artifact content and traceability metadata.
3. Identify candidate relationships and determine base-derived ordering.
4. Apply eligibility filters and record exclusions.
5. Identify unique content SHAs.
6. Scan each unique SHA with the configured scanner and rule catalog.
7. Join cached profiles back to all applicable artifact occurrences.
8. Compare base and derived profiles to calculate introduced, removed, and retained rules and categories.
9. Produce structured result tables, summary measures, validation inputs, logs, and report-ready figures or tables.

The pipeline records the scanner version, rule-catalog version, configuration, and other run metadata needed to connect every result to the implementation that produced it.

[TODO: Replace this intended flow with the final executable commands and implemented module-to-module data flow when the pipeline is complete.]

## Baselines and Test Fixtures

The earlier or source artifact serves as the within-relationship baseline for each derived artifact. This paired baseline supports a direct claim about whether a signal was detected in the derived artifact but not in its identified base; it is not a general-purpose prediction baseline.

The implementation will also use manually constructed base and derived skill pairs as deterministic test fixtures. Fixtures will cover known cases in which rules and categories are introduced, removed, retained, or unchanged. These fixtures test scanner and comparison behavior and are not empirical observations from the GitSkills population.

[TODO: Define any additional baseline rule set, heuristic, comparison method, or ablation required by the final evaluation, and explain what question that baseline answers.]

## Design Decisions

### Ordered Comparisons Rather Than Isolated Artifacts

The research question concerns behavior newly introduced through modification or reuse. An ordered base-derived pair therefore provides a more direct unit of analysis than an isolated artifact.

### Rule-Level and Category-Level Measurement

The method reports both levels because category-only comparisons can hide the introduction of a new rule inside an already-present category, while rule-only results may be too granular to summarize clearly.

### One Rule Catalog per Comparison and Run

Scanning both sides with the same version prevents rule-catalog changes from being mistaken for changes in artifact content. When rules change, the catalog version changes and affected analyses must be rerun.

### SHA-Based Caching Without Statistical Deduplication

Scanning each unique content SHA once avoids redundant computation. Cached profiles are joined back to all artifact and relationship occurrences so the optimization does not silently redefine the research population.

### Census of Eligible Comparisons

The automated pipeline attempts to analyze every eligible comparison. Development subsets are used only for testing and debugging; they do not replace the population-level run.

### Evidence Retention and Auditable Filtering

The pipeline retains evidence for relationship detection, ordering, rule matches, eligibility decisions, and exclusions. This supports later manual review and makes the construction of the analyzed population auditable.

### Static Analysis and Cautious Interpretation

The project does not execute untrusted artifact content. Detected introductions are reported as static risk signals. They do not, by themselves, prove malicious intent, vulnerability, exploitability, or real-world impact.

## Generated Outputs

The pipeline is expected to produce:

- an artifact table with traceability fields;
- a relationship table with ordering evidence and eligibility status;
- versioned scanner profiles;
- an ordered comparison table with introduced, removed, and retained signals;
- exclusion counts and reasons;
- aggregate summary tables;
- a seeded manual-validation sample;
- logs and run metadata; and
- report-ready tables and figures generated from structured results.

[TODO: Replace this expected list with the final filenames, formats, schemas, and repository paths. Identify which outputs are committed, generated on demand, or omitted because of size or sensitive content.]

## Reproducibility

A reproducible run must identify:

- the dataset release or snapshot and integrity information;
- the required environment and dependency versions;
- configuration and command-line arguments;
- scanner and rule-catalog versions;
- random seeds used for validation sampling;
- executable commands for each pipeline stage and the complete pipeline;
- output locations and expected artifacts; and
- known platform, resource, or data-availability limitations.

[TODO: Add the final setup instructions and exact clean-environment execution command after the implementation is complete.]

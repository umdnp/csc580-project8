\clearpage

# Dataset and Data Preparation

This section describes the dataset source, study scope, data schema, sampling strategy, eligibility filters, preprocessing steps, and safety controls used to construct the analysis-ready data. The detailed algorithms and implementation pipeline are described in the Method and Implementation section.

## Dataset Source and Acquisition

The source dataset for this study is `agent_skills_release.db`, the GitSkills database provided for the MSR 2027 Mining Challenge. The source population consists of all GitSkills artifact records contained in the database.

[TODO: Add the approved dataset access instructions, release or snapshot identifier, file integrity information, and the date on which the database was obtained. Explain that the full database is not committed to the project repository and identify the expected local storage location.]

## Dataset Scope

The study distinguishes three populations:

1. **Source population:** All GitSkills artifact records in `agent_skills_release.db`.
2. **Analyzable artifact population:** Records from the source population that contain stored skill content that the static analyzer can process.
3. **Eligible comparison population:** Ordered base-derived comparisons that can be extracted from the database and satisfy the eligibility criteria defined below.

Artifacts without analyzable content or without an identifiable, ordered relationship remain part of the source population, but they are not part of the eligible comparison population. The pipeline will report the number of records and candidate relationships excluded at each stage and the reasons for exclusion.

[TODO: Insert verified counts for the source population, analyzable artifacts, unique content SHAs, candidate relationships, eligible comparisons, repositories, and other scope measures produced by the final pipeline.]

## Relevant Schema

The analysis uses data at four related levels: artifact, relationship, scanner profile, and ordered comparison. The field lists below describe the broader target schema, not a claim that every field is present in the current Sprint 1 reports. Exact source-table and column names will be verified against the implemented extraction pipeline and documented in `DATA_DICTIONARY.md`. Current wrapper reports record endpoint artifact IDs, relationship evidence, introduced-capability flags, total match counts, and nonzero rule-count deltas.

### Artifact Data

For both base and derived artifacts, the prepared data retains the available fields needed for identification, analysis, and traceability:

- artifact identifier;
- repository identifier;
- artifact path;
- declared skill name, when available;
- content SHA;
- stored content or a safe reference to the analyzed content; and
- available timestamp, commit, or other ordering metadata used by the relationship method.

### Relationship Data

Each candidate or eligible relationship records:

- comparison identifier;
- base artifact identifier;
- derived artifact identifier;
- relationship type;
- same-repository or cross-repository status;
- relationship-detection method;
- evidence supporting the relationship;
- evidence supporting base-derived ordering;
- relationship confidence or review status, if used by the implemented method; and
- eligibility or exclusion status and reason.

### Scanner-Profile Data

For each analyzed artifact, the prepared scanner profile contains:

- matched rule identifiers;
- matched security-relevant categories;
- match counts by rule and category;
- total matched-rule and matched-category counts;
- match locations or other evidence required for validation and safe reporting; and
- scanner and rule-catalog versions.

### Comparison Data

For each eligible ordered comparison, the prepared analysis table contains:

- introduced, removed, and retained rule identifiers;
- introduced, removed, and retained categories;
- counts of introduced rules and categories;
- indicators for at least one introduced rule and at least one introduced category; and
- the overall comparison result under the documented threat model.

Rule-level and category-level fields are both retained. A derived artifact may introduce a new rule within a category that was already present in the base artifact; that change is visible at the rule level even when the set of categories does not change.

## Unit of Analysis

The primary unit of analysis is one ordered comparison between two related, content-bearing skill artifacts:

- **Base artifact:** The inferred source endpoint, according to the supported direction evidence.
- **Derived artifact:** The inferred target endpoint being compared with the base; this designation does not prove historical descent.

The ordering is represented as:

**base artifact -> derived artifact**

One unique content SHA is the secondary processing unit. The pipeline may scan identical content once and reuse its profile, but SHA-based deduplication is only a computational optimization. Artifact occurrences, repository occurrences, and comparison relationships remain available after cached profiles are joined back to the complete extracted data.

## Inclusion and Exclusion Criteria

An ordered comparison is eligible when all of the following conditions are satisfied:

1. Both artifacts contain stored content that the scanner can analyze.
2. The extraction pipeline identifies a relationship using the project's documented relationship method.
3. Available evidence supports the base-derived ordering.
4. Both artifacts can be processed with the same scanner version and rule-catalog version.

A candidate comparison is excluded when one or more of these conditions are not satisfied. The pipeline retains the exclusion status and reason so that filtering is auditable. Uncertain or invalid relationships may be reviewed and excluded according to the documented relationship method.

[TODO: Add any implemented content-format, parsing, duplication, missing-value, or relationship-confidence filters and the exact exclusion codes used by the pipeline.]

## Data Preparation

The preparation process converts the source database into analysis-ready artifact and comparison data. It will:

1. extract artifact content and traceability metadata from the relevant source tables;
2. identify candidate relationships and retain the evidence used to establish each relationship;
3. determine base-derived ordering from the available evidence;
4. apply the documented inclusion and exclusion criteria;
5. normalize content only as required by the scanner while preserving the original content or a safe reference to it;
6. identify unique content SHAs for cached scanning without discarding artifact occurrences;
7. attach scanner profiles to artifact records; and
8. join base and derived profiles into the ordered comparison table.

[TODO: Document the implemented text decoding, line-ending normalization, parsing, missing-content handling, and any other cleaning transformations. Distinguish transformations used for matching from the original content retained for traceability.]

## Population Analysis and Sampling

### Planned Automated Census

The automated analysis will attempt a census of the eligible comparison population rather than select a statistical sample. Every eligible base-derived comparison extracted from `agent_skills_release.db` will be processed by the comparison pipeline.

Smaller reproducible datasets may be used while developing and debugging the pipeline. These development datasets are test inputs, not the research sample, and will not replace the final population-level analysis.

### Planned Manual Validation Sample

For the broader evaluation, the team plans to manually review a stratified sample of at least 100 eligible base-derived comparisons from the automated results. This future plan is separate from the 17 directed comparisons in the current Sprint 1 reports:

- at least 50 comparisons for which the scanner reports one or more newly introduced rules or categories; and
- at least 50 comparisons for which the scanner reports no newly introduced rules or categories.

Within those two groups, the sample will represent the relationship types and scanner categories present in the results. Selection will use a recorded random seed after the strata are defined. If a stratum contains fewer cases than its allocation, all cases in that stratum will be reviewed and the remaining allocation will be redistributed using a documented procedure.

The sample may be expanded if early review identifies unstable rules, poorly represented relationship types, or categories that require additional evidence. The manual-review procedure, labels, metrics, and error analysis belong in the Evaluation and Validation section.

For each sampled comparison, reviewers will record:

- whether the relationship and base-derived ordering are supported by the retained evidence;
- whether each reported match corresponds to the text identified by the scanner;
- whether the assigned categories are appropriate;
- whether a reported introduction was absent from the base and present in the derived artifact;
- whether an unflagged comparison contains a relevant introduction missed by the current rules; and
- whether the case is a true positive, false positive, false negative, true negative, or ambiguous under the documented threat model.

These records will support confirmed and rejected relationship counts, ordering disagreements, classification counts, precision and any other justified validation metrics, category- or relationship-specific breakdowns where sample size permits, and representative failure modes. The Evaluation and Validation section will define the final calculation and interpretation of those measures.

### Sprint 1 Sampling Strategy

Sprint 1 uses a small, purposeful tool-validation sample of **43 artifacts across 10 exact-name families**. The ten saved analysis reports contain **17 directed comparisons**. These totals describe the current tool output, not a representative population sample or completed manual validation of every comparison.

The earlier design combined purposeful cases with 75 random artifact seeds and family expansion, producing approximately 1,400 artifact-selection rows. It was too large for immediate manual validation. The revised selection aimed for approximately 50 artifacts or fewer and has no separate random component. The earlier sample may remain useful for later work; its reconstruction checks do not validate the revised selection.

#### Selection Logic and Family Scope

Families were selected to exercise supported direction evidence, ambiguous relationships, cases without inferred relationships, and positive, negative, or unchanged scanner counts. Other cases distinguish additional matches within an existing capability from newly detected capabilities and expose scanner coverage or normalization limitations.

`artifact_groupings` groups artifacts by exact name and normalized description. The current `analyze_family` tool loads all qualifying artifacts sharing an exact name, including multiple description groups. Some screening queries compare only within a name-and-description group, so their screening scope is narrower than the family-analysis scope. Shared metadata establishes candidate context, not proven lineage.

The selection queries screened for package-installation count variation, supported provenance-field references, and variation in additional scanner rules. SQL patterns were selection heuristics rather than validated findings. Candidate families were checked through the Python workflow, and selected comparisons were inspected manually in Mergely. Searching ended because further screening was time-consuming, not because the sample was exhaustive or statistically optimized. The query rationale and RDR-006 record the selection decisions.

#### Observed Coverage and Limits

The saved reports demonstrate nonzero count deltas in 10 of the scanner's 12 rules. EXT-001 and SYS-001 remain without confirmed delta examples. Rule presence, a count change, and an introduced capability are different outcomes; none alone establishes increased or decreased risk.

The wrapper scans selected directed relationships rather than every possible artifact pair. Ambiguous relationships are listed without directional scanning, and a family with no directed comparisons does not establish an absence of scanner matches. Only `SKILL.md` content is scanned; sibling-file contents are not compared. Sibling-only relationships remain useful validation cases but do not establish the safety of sibling changes.

Selected manual inspections exposed uneven command coverage and a line-ending sensitivity bug. The wrapper now normalizes line endings before scanning, and the corrected comparison remains a regression case. Other inspected cases illustrate limitations in declared-source resolution and exact-name candidate generation. These observations do not constitute manual validation of every comparison.

#### Sample View and Reproducibility

The revised selection uses `artifact_id`, which the project team confirmed is deterministic for the project's dataset. The script `sql/generate_sprint1_sample.sql` embeds the 43 selected IDs and creates or replaces the `sample_artifacts` view by matching them to `artifacts.id`. The CSV at `data/sample-population/sample_population.csv` also records the selected IDs, but the view does not read that file.

The view stores the selection query rather than copying artifact records into separate sample tables. Its ID list fixes the selection criteria, while returned values reflect the underlying `artifacts` table when queried. It exposes all artifact columns locally, including content and identifying metadata; it is not an anonymized reporting view.

The script's final count query should return 43 if every selected ID exists. The saved family-report totals do not demonstrate that this query has been run successfully. Reproducibility checks should reconcile the embedded IDs with the recorded list, confirm that every ID resolves, and compare reconstructed membership in both directions. A matching row count alone is insufficient to establish identical membership.

Deterministic IDs support reconstruction for the agreed dataset; they do not guarantee unchanged membership or content in a different release. The dataset version, selection SQL, scanner rules, and normalization settings must therefore be recorded. Earlier frozen-table validation applies only to the earlier sample.

## Data Ethics and Safety

All artifact content is treated as untrusted data. The project performs static analysis only and will not execute scripts, commands, or instructions contained in the dataset.

The pipeline and reporting process will:

- avoid executing or importing untrusted artifact code;
- avoid exposing credentials, tokens, or other sensitive strings that may appear in artifact content;
- keep validation evidence local and omit source text and identifying values from exported reports under the current output constraints;
- distinguish detected risk signals from proof of malicious intent, vulnerability, exploitability, or real-world harm; and
- report aggregate findings and generalized observations without naming selected artifacts or reproducing source content.

Current orchestration reports identify endpoints by artifact ID, omit text diffs, and serialize scanner comparisons with `verbose=False`. These measures limit exported content but do not guarantee anonymity or resolve licensing questions. Artifact IDs can be linked to source records by someone with access to the dataset.

[TODO: Document the implemented redaction, access-control, retention, and safe-example-selection procedures.]

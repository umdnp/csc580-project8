# Sprint 2 Analysis Results

## Scope

This directory contains preliminary results from the Sprint 2 end-to-end GitSkills artifact comparison and security-signal analysis. The selected cohort contains **30 candidate families**. The pipeline compares direction-supported relationships using:

- Changes to `SKILL.md` body content and relevant sibling files (`artifact_siblings.entry_type = 'file'`).
- Similarity, chronology, containment, declared-source, and equivalent-peer information to assess relationships and infer direction where supported.
- Static detection rules, extracted evidence, and evidence-based risk indicators (RI-001 through RI-011).
- Stratified samples for independent validation of directed comparisons and relationship classifications.

The notebook sets `EDGES = "all"`, so the results include **primary and additional directed edges**. Relationships whose direction is unresolved are excluded from directed security comparisons but remain eligible for relationship validation. No untrusted skill scripts are executed.

The selected families are matched by exact name against `artifact_groupings.name` in the prepared GitSkills DuckDB database. The sample is **purposively selected, not random**; results describe this cohort and should not be generalized to all GitSkills artifacts. The complete family list and input provenance are recorded in `sample_manifest.json`.

**Status:** The pipeline completed successfully, but the manifest still records the sample as `provisional` with no approval reference. The annotation files contain draft entries for 21 of 30 directed cases and all 15 relationship cases. Every row remains `pending`; the notes identify AI-assisted proposals awaiting human acceptance, and adjudication has not occurred. These preliminary records do not make the automated results validated findings of malicious behavior or completed accuracy estimates.

## Artifact Coverage

### Observed results

| Metric | Count |
|---|---:|
| Artifact families | 30 |
| Artifacts loaded | 1,151 |
| Artifacts skipped | 0 |
| Directed artifact comparisons analyzed | 3,997 |
| Primary comparisons | 468 |
| Additional comparisons | 3,529 |
| Ambiguous edges excluded from directed analysis | 2,244 |
| Comparisons with incomplete sibling evidence | 117 |
| Comparisons with incomplete overall evidence coverage | 206 |
| Comparisons with evidence changes | 1,998 |
| Comparisons with sibling evidence changes | 1,199 |
| Flagged comparisons | 2,241 |
| Comparisons with supported risk indicators | 588 |
| Families containing supported indicators | 19 |

All **1,151 artifacts** were loaded, and all 30 selected families produced directed comparisons. No artifacts were skipped. The skipped-artifact audit contains only its header.

### Understanding coverage

The two incomplete-coverage measures refer to different limitations:

- **117 comparisons (2.9%)** had incomplete sibling evidence, including unavailable sibling-file content.
- **206 comparisons (5.2%)** had incomplete overall evidence coverage, including the 117 sibling-incomplete comparisons and **89 additional comparisons** with incomplete evidence extraction but no missing sibling content.

Thus, **3,791 of 3,997 comparisons (94.8%)** have complete reported evidence coverage. Of the 588 indicator-bearing comparisons, **104** have incomplete evidence coverage. A supported indicator may still have observable supporting evidence in such a comparison, but the unexamined evidence limits conclusions about what else could be present.

The coverage-limited comparisons are concentrated in a small number of families: `devcontainer-setup` (65), `seo` (49), `exploiting-oauth-misconfiguration` (49), `deepread` (17), and `neurokit2` (14). These five account for 194 of the 206 coverage-limited comparisons.

The **2,244 ambiguous edges** were excluded because a reliable base-to-derived direction was not established. They are not failed scans and should not be counted as directed comparisons.

## Artifact Comparisons

### Directed comparisons

The pair-level output is in `review/directed_pairs.csv`. It records artifact IDs, family, cluster, edge type, direction basis, change type, rule flags, supported and uncertain indicators, evidence counts, and coverage status.

| Measure | Primary | Additional | Total |
|---|---:|---:|---:|
| Directed comparisons | 468 | 3,529 | 3,997 |
| Flagged comparisons | 272 | 1,969 | 2,241 |
| Comparisons with supported indicators | 81 | 507 | 588 |
| Comparisons with incomplete evidence coverage | 41 | 165 | 206 |
| Reported supported finding instances | 591 | 4,960 | 5,551 |

**Primary** edges represent the selected predecessor relationships; **additional** edges represent other direction-supported comparisons. Multiple comparisons can share artifacts and report overlapping or identical evidence. The 5,551 finding instances and 588 indicator-bearing comparisons are **not** counts of distinct security incidents.

### Relationship validation sample

The relationship sample is in `manual-review/relationship-pairs/relationship_validation_sample.csv`. It contains **15 comparisons**, selected using seed `580`:

| Relationship stratum | Sampled |
|---|---:|
| Ambiguous direction | 5 |
| Equivalent artifacts | 5 |
| No related edge | 5 |

These cases support checking relationship classification separately from the security scanner's directed-change findings. Direction-unknown examples are not assumed to have an earlier or derived side.

### Directed-comparison validation sample

The directed sample is in `manual-review/directed-pairs/validation_sample.csv`. It contains **30 comparisons**, five from each stratum:

| Directed-comparison stratum | Sampled |
|---|---:|
| Supported indicator | 5 |
| Uncertain indicator | 5 |
| Sibling change | 5 |
| Flagged without an indicator | 5 |
| Unflagged directed comparison | 5 |
| Coverage-limited comparison | 5 |

The samples, draft annotation files, and templates are in the corresponding `manual-review/` subdirectories. The draft files currently contain 21 directed-pair entries and all 15 relationship-pair entries, but every row has review status **pending** and the notes record human acceptance as outstanding. They are not completed accuracy evaluations. Reviewers should inspect the source artifacts and sibling files, preserve independent judgments, and adjudicate disagreements without executing untrusted content. The notebook describes the optional step for incorporating completed adjudications.

## Detected Security Signals

The scanner evaluated **11 evidence-based risk indicators**. **Eight** have at least one supported observation in the current cohort; RI-002, RI-009, and RI-011 have none. An indicator signals an observable security-sensitive change, **not** a confirmed vulnerability or malicious intent.

| Category | Indicator | Directed pairs | Share of 3,997 pairs |
|---|---|---:|---:|
| Download and execution | RI-001: Download-and-execute introduced | 96 | 2.40% |
| Executed code source | RI-002: Executed code source changed | 0 | 0.00% |
| Network access | RI-003: Network access expanded or redirected | 381 | 9.53% |
| Network security | RI-004: Network security weakened | 22 | 0.55% |
| External code/dependencies | RI-005: External code or dependency acquisition changed | 179 | 4.48% |
| Destructive or privileged operations | RI-006: Destructive or privileged file operation | 41 | 1.03% |
| Credentials | RI-007: Credential access or potential exposure | 231 | 5.78% |
| System configuration | RI-008: System configuration or permissions changed | 53 | 1.33% |
| Sensitive filesystem access | RI-009: Sensitive filesystem access or modification | 0 | 0.00% |
| Local scripts | RI-010: Local script execution introduced or changed | 413 | 10.33% |
| External instructions | RI-011: External instruction dependency introduced or changed | 0 | 0.00% |

Counts represent **directed pairs containing each supported indicator**, not indicator occurrences or unique underlying changes. Categories overlap: one pair can contribute to more than one row. **Uncertain** indicators are represented separately in pair-level records and are not included in the supported-frequency counts.

The full tables are `review/indicator_frequency.csv` and `review/indicator_frequency_by_edge_type.csv`.

## Security-Sensitive Changes

### Observed patterns

The **588** indicator-bearing comparisons span several kinds of changes:

- **Download-and-execute or changed script execution:** `defi-protocol-templates` and `neurokit2` provide examples involving remote or local scripts.
- **Network and credential-bearing operations:** `seo` contains RI-003 and RI-007 evidence, including API-oriented network operations; such behavior may be legitimate.
- **Network-security weakening:** `exploiting-oauth-misconfiguration` provides RI-004 observations; its evidence extraction is incomplete in all 49 directed comparisons, making it a manual-review priority.
- **Changed sibling files:** `youtube-downloader` and `busybox-on-windows` illustrate why comparing only the main skill body would miss relevant changes.
- **Benign-looking or potentially misinterpreted commands:** `PromptInjection` includes local notification requests, and `yaml-master` provides a candidate command-extraction false positive. These are useful scanner-accuracy checks, not evidence of compromise.

These examples should be evaluated in their source context. Package installation, local network requests, credential-bearing API calls, file removal, and permission changes can all be legitimate. The scanner does not establish author intent, exploitability, or actual harm.

**Source-context caveat:** The manifest includes artifacts from benchmark or security-test repositories such as `lxyeternal/MalSkillBench` and `ISAQQSAI/SkillAttack`. Such artifacts are useful positive or adversarial controls, but should be distinguished from ordinary observed reuse when interpreting results. Their presence is not evidence of a real-world supply-chain compromise.

## Family-Level Comparison Summary

The complete per-family table is in `review/families.csv`. Examples of notably different comparison patterns include:

| Family | Directed pairs | With supported indicators | Why it is useful |
|---|---:|---:|---|
| `seo` | 1,136 | 298 | Many comparisons; network and credential-related evidence |
| `defi-protocol-templates` | 544 | 58 | Multiple security-sensitive behaviors, including benchmark-derived examples |
| `python-performance-optimization` | 460 | 9 | High-volume and uncertain-indicator validation |
| `caveman-help` | 363 | 0 | Large unflagged comparison set / negative control |
| `neurokit2` | 285 | 55 | Download-and-execute and script-related evidence |
| `azure-communication-sms-java` | 255 | 0 | Many flags without supported indicators |
| `devcontainer-setup` | 249 | 52 | Diverse behaviors and substantial incomplete sibling coverage |
| `busybox-on-windows` | 174 | 0 | Sibling-file differences and relationship-analysis examples |

`seo` alone contributes approximately **28%** of all directed comparisons and about **51%** of indicator-bearing comparisons. Results should not be interpreted as 3,997 independent observations or as a population prevalence estimate. A review sample should avoid overrepresenting near-duplicate comparisons from large families.

## Audit and Reproducibility

The processing audit is available in `audit/processing_summary.csv` and `audit/skipped_artifacts.csv`. It confirms that all 30 families were processed, **1,151 artifacts loaded**, and **none skipped**.

The run configuration is recorded in `sample_manifest.json` and the notebook `end_to_end_pipeline.ipynb`, including:

- Prepared GitSkills DuckDB input and per-family source fingerprints.
- Exact selected family names, active detection rules, scanner scope, and code revision.
- Similarity policy: shingle size `5`, minimum containment `0.8`, minimum Jaccard similarity `0.3`, minimum shared shingles `5`, and direction containment margin `0.1`.
- Edge selection `all`, review sample seed `580`, and five samples per validation stratum.
- Implementation and output fingerprints for reproducibility checks.

The notebook calls `summarize_cohort()` and may reuse compatible family scan reports in `.scans/`; missing or stale reports are regenerated. The archive contains **30 individual family scan JSON files**, corresponding to the 30 selected families. It does not depend on saved SkillTrace reports.

The manifest currently identifies this as a **provisional** cohort (`approval_reference: null`). Record the team's sample approval before presenting it as an approved Sprint 2 sample. If the sample, rules, or policy change after independent review begins, archive the earlier results and reviewer copies before regenerating samples.

## Figures

Generated figures:

- `figures/indicator_frequency.svg`
- `figures/indicators_by_edge_type.svg`
- `figures/indicators_by_family.svg`
- `figures/pair_outcomes.svg`

They summarize supported indicator frequency, edge-type and family distributions, and pair outcomes.

## Limitations and Review Status

1. **Independent validation is pending.** Automated flags and indicators have not been confirmed by independent reviewers or adjudication; scanner precision and recall are not established by these outputs alone.
2. **Evidence coverage is incomplete for 206 comparisons**, including 117 with missing sibling content. Of the indicator-bearing comparisons, 104 have incomplete coverage.
3. **2,244 ambiguous relationships** were excluded from directional analysis. Inferred direction is a reasoned classification, not proof of historical lineage or copying.
4. **Indicators and comparisons overlap.** A single change can appear in multiple directed pairs and match multiple indicators; pair-level totals do not represent independent incidents.
5. **Sample selection is purposive**, and large families contribute disproportionately many comparisons. No population-wide prevalence estimate should be inferred.
6. **Benchmark and security-test artifacts** should be labeled separately from ordinary observed artifacts in analysis and interpretation.
7. **Not all indicators were observed.** RI-002, RI-009, and RI-011 have no *supported* observations in this cohort; absence of a supported detection is not proof that the underlying behavior is absent. Uncertain observations require separate review.
8. **Security-sensitive does not mean malicious.** Findings do not establish intent, compromise, exploitability, or harm.

The consolidated research metrics are in `review/summary.json`, and the execution status is in `execution_summary.json`.

## Result Inventory

The result set includes:

- `sample_manifest.json` — selected cohort, source artifacts, scanner configuration, and provenance fingerprints.
- `execution_summary.json` — pipeline execution status and high-level counts.
- `.scans/<family>.json` — individual family scan outputs, one per selected family.
- `.scans/.metadata/scan-manifest.json` — scan-cache metadata.
- `audit/processing_summary.csv` and `audit/skipped_artifacts.csv` — input and processing audit.
- `review/summary.json` — consolidated metrics and validation-sample summary.
- `review/families.csv`, `review/edge_types.csv`, and `review/direction_basis.csv` — family and relationship summaries.
- `review/directed_pairs.csv` — pair-level changes, indicators, and coverage.
- `review/indicator_frequency.csv` and `review/indicator_frequency_by_edge_type.csv` — supported-indicator frequencies.
- `manual-review/directed-pairs/validation_sample.csv`, `annotations.csv`, and `annotations_template.csv` — 30 directed-comparison review cases, 21 pending draft annotation entries, and the annotation template.
- `manual-review/relationship-pairs/relationship_validation_sample.csv`, `annotations.csv`, and `relationship_annotations_template.csv` — 15 relationship review cases, 15 pending draft annotation entries, and the annotation template.
- Four generated SVG figures under `figures/`.

This directory contains **preliminary, reproducible pipeline outputs**. Interpretations of scanner accuracy and security significance require manual validation.

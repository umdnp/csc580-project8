# Sprint 2 Analysis Results

## Scope

This directory contains the preliminary results from the Sprint 2 end-to-end artifact comparison and security-signal analysis.

The analysis examined GitSkills artifacts across 15 families using the scanner scope:

- Skill-body changes
- Changes to relevant sibling files
- Chronology, containment, and equivalent-peer relationships
- Evidence-based security indicators
- Manual-review samples for independent validation

The results are preliminary. Independent review and adjudication are still pending.

## Artifact Coverage

### Observed results

| Metric | Count |
|---|---:|
| Artifact families | 15 |
| Artifacts loaded/analyzed | 252 |
| Artifacts skipped/excluded | 0 |
| Directed artifact comparisons analyzed | 222 |
| Primary comparisons | 45 |
| Additional comparisons | 177 |
| Ambiguous edges excluded from directed analysis | 67 |
| Comparisons with incomplete coverage | 3 |
| Comparisons with missing sibling content | 3 |
| Comparisons with evidence changes | 62 |
| Comparisons with sibling evidence changes | 34 |
| Comparisons flagged by rules | 65 |
| Comparisons with supported indicators | 8 |
| Families containing supported indicators | 5 |

No artifacts were excluded by the processing pipeline. Some ambiguous relationships were omitted from directed comparisons because their direction could not be established reliably.

### Interpretation

The dataset achieved complete artifact loading, but the comparison layer still has coverage limitations. In particular, three comparisons have incomplete evidence coverage and 67 ambiguous edges were not used for directional analysis. These limitations reduce confidence in conclusions about chronology or intent.

## Artifact Comparisons

### Directed comparisons

The directed comparison output is available in `review/directed_pairs.csv`.

It records:

- Base and derived artifact IDs
- Artifact family and cluster
- Primary versus additional edge type
- Direction basis
- Skill and sibling additions/removals
- Rule flags
- Security indicator IDs
- Evidence completeness
- Missing or unknown sibling content

The analysis produced:

- **45 primary comparisons**
  - 22 flagged
  - 5 with indicators
  - 9 total indicator findings
  - 2 with incomplete coverage
- **177 additional comparisons**
  - 43 flagged
  - 3 with indicators
  - 6 total indicator findings
  - 1 with incomplete coverage

### Relationship comparisons

The relationship comparison sample is available in `manual-review/relationship-pairs/relationship_validation_sample.csv`.

The sample contains 15 relationship comparisons:

| Relationship stratum | Sampled |
|---|---:|
| Ambiguous direction | 5 |
| Equivalent artifacts | 5 |
| No related edge | 5 |

Ambiguous relationships had high textual similarity but no reliable direction. Equivalent artifacts had matching similarity measures and were classified as equivalent-state comparisons. No-related-edge samples were included as negative relationship examples.

### Validation samples

The directed-comparison validation sample is available in `manual-review/directed-pairs/validation_sample.csv`.

It contains 21 sampled comparisons across these strata:

- Supported indicator: 5
- Sibling change: 5
- Flagged without an indicator: 5
- Unflagged directed comparison: 5
- Coverage-limited comparison: 1

The annotation files are templates and have not yet been completed. Their review status is currently pending.

## Detected Security Signals

The analysis evaluated 11 evidence-based risk indicators. These are observable change signals, not confirmed vulnerabilities or proof of malicious intent.

| Category | Indicator | Directed pairs | Percentage |
|---|---|---:|---:|
| Download and execution | RI-001: Download-and-execute introduced | 0 | 0.0% |
| Executed code source | RI-002: Executed code source changed | 0 | 0.0% |
| Network access | RI-003: Network access expanded or redirected | 1 | 0.45% |
| Network security | RI-004: Network security weakened | 0 | 0.0% |
| External code/dependencies | RI-005: External code or dependency acquisition changed | 6 | 2.703% |
| Destructive or privileged operations | RI-006: Destructive or privileged file operation | 1 | 0.45% |
| Credentials | RI-007: Credential access or potential exposure | 0 | 0.0% |
| System configuration | RI-008: System configuration or permissions changed | 1 | 0.45% |
| Sensitive filesystem access | RI-009: Sensitive filesystem access or modification | 0 | 0.0% |
| Local scripts | RI-010: Local script execution introduced or changed | 0 | 0.0% |
| External instructions | RI-011: External instruction dependency introduced or changed | 0 | 0.0% |

The complete frequency table is available in `review/indicator_frequency.csv`.

Indicator counts by edge type are available in `review/indicator_frequency_by_edge_type.csv`.

## Security-Sensitive Changes

### Observed results

Eight directed comparisons contained at least one supported security indicator, producing 15 indicator findings. Multiple indicators may describe the same comparison.

The observed supported signals were:

- **RI-005 — External code or dependency acquisition changed**
  - 6 comparisons
  - 3 primary comparisons
  - 3 additional comparisons
- **RI-003 — Network access expanded or redirected**
  - 1 primary comparison
- **RI-006 — Destructive or privileged file operation**
  - 1 primary comparison
- **RI-008 — System configuration or permissions changed**
  - 1 primary comparison

The detailed comparison records show several change patterns:

- Skill-only changes where commands or operational instructions changed
- Skill-plus-sibling changes where both skill content and related files changed
- Sibling-only changes where the security-relevant difference was outside the main skill body
- Comparisons with multiple changed commands and evidence items
- Three comparisons involving unsupported or incomplete sibling evidence

Examples of observed indicator-bearing comparisons include:

- A Golang project comparison with RI-006
- A DeFi module comparison with RI-003 and RI-008
- Dependency or external-acquisition changes involving RI-005
- A Ghostclaw comparison involving RI-005
- Capacitor comparisons involving RI-005 with incomplete sibling evidence

### Interpretation

These findings identify changes that warrant review. They do not establish that an artifact is malicious, compromised, unsafe, or intentionally harmful.

For example:

- A dependency-acquisition change may represent a legitimate upgrade or migration.
- A new network destination may be required application behavior.
- A destructive or privileged operation may be appropriate for installation or system configuration.
- A system-permission change may be expected in a setup workflow.

The analysis does not infer author intent, exploitability, or actual harm from indicator presence alone. Manual review is required to determine whether a flagged change is benign, suspicious, or incorrectly classified.

## Family-Level Comparison Summary

The per-family comparison results are available in `review/families.csv`.

Notable observed comparison volumes include:

- `busybox-on-windows`: 174 comparisons
- `cometchat-core`: 7 comparisons
- `cursor-subagent-creator`: 9 comparisons
- `legacy-migration-planner`: 9 comparisons
- `argent-react-native-app-workflow`: 4 comparisons
- `hello-world`: 4 comparisons
- Several families had few or no comparable directed pairs because of their available artifact histories or relationship structure.

The family-level file should be used when investigating specific artifact families because it includes incomplete-coverage counts, evidence-change counts, flagged comparisons, and ambiguous-edge counts.

## Audit and Processing Results

The processing audit is available in:

- `audit/processing_summary.csv`
- `audit/skipped_artifacts.csv`

The audit shows:

- All 252 artifacts loaded successfully.
- No artifacts were skipped.
- Three artifact comparisons had incomplete evidence coverage.
- Sixty-seven ambiguous edges were excluded from directed comparison analysis.
- The skipped-artifact report is empty apart from its header.

## Figures

The generated figures are:

- `figures/indicator_frequency.svg`
- `figures/indicators_by_edge_type.svg`
- `figures/indicators_by_family.svg`
- `figures/pair_outcomes.svg`

These figures visualize indicator frequency, indicator distribution by edge type and family, and comparison outcomes.

## Limitations and Review Status

The execution summary is available in `execution_summary.json`, and the consolidated review metrics are available in `review/summary.json`.

Important limitations:

1. Independent review and adjudication are still pending.
2. Three comparisons have incomplete evidence coverage.
3. Three comparisons have missing sibling content.
4. Sixty-seven ambiguous edges were excluded from directed analysis.
5. Indicator categories overlap.
6. Comparisons may reuse the same artifacts and should not be treated as independent events.
7. Rule flags and indicators are evidence-based review signals, not conclusions about maliciousness or intent.

## Result Inventory

The preliminary result set under this directory includes:

- `sample_manifest.json`
- `execution_summary.json`
- `audit/processing_summary.csv`
- `audit/skipped_artifacts.csv`
- `review/summary.json`
- `review/families.csv`
- `review/edge_types.csv`
- `review/directed_pairs.csv`
- `review/direction_basis.csv`
- `review/indicator_frequency.csv`
- `review/indicator_frequency_by_edge_type.csv`
- `manual-review/directed-pairs/validation_sample.csv`
- `manual-review/directed-pairs/annotations_template.csv`
- `manual-review/relationship-pairs/relationship_validation_sample.csv`
- `manual-review/relationship-pairs/relationship_annotations_template.csv`
- Four SVG figures under `figures/`

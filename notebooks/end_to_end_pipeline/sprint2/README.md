# Sprint 2 Cohort

Sprint 2 analyzes **30 purposively selected GitSkills families** using the [end-to-end notebook](../end_to_end_pipeline.ipynb). Family names are in [`samples/families.txt`](samples/families.txt); generated artifacts are under [`results/`](results/). The selection is not random, so the findings describe this cohort rather than the GitSkills population.

The pipeline compares direction-supported artifact relationships, scans changes to skill bodies and available sibling files, and records security-sensitive indicators. It does not execute untrusted scripts. The configured edge selection is `all` (primary and additional comparisons); ambiguous relationships are excluded from directed-change analysis but included in relationship validation sampling.

**Review status:** Automated processing is complete; independent human validation and adjudication are pending. The manifest marks the cohort `provisional` (`approval_reference: null`). Draft annotation CSVs contain pending AI-assisted proposals, not accepted reviewer judgments.

## Results at a glance

| Measure | Count |
|---|---:|
| Families | 30 |
| Artifacts loaded / skipped | 1,151 / 0 |
| Directed comparisons | 3,997 |
| Primary / additional comparisons | 468 / 3,529 |
| Ambiguous relationships excluded from directed comparisons | 2,244 |
| Flagged comparisons | 2,241 |
| Comparisons with supported indicators | 588 |
| Families with supported indicators | 19 |
| Supported indicator findings | 5,551 |
| Comparisons with evidence changes | 1,998 |
| Comparisons with sibling evidence changes | 1,199 |
| Comparisons with incomplete sibling evidence | 117 |
| Comparisons with incomplete overall coverage | 206 |

Of the 3,997 directed comparisons, **3,791 (94.8%)** have complete reported evidence coverage. The 206 coverage-limited comparisons include 117 with incomplete sibling evidence; 104 of the 588 indicator-bearing comparisons have incomplete coverage. These limitations matter when interpreting absent or incomplete detections.

Several comparisons may share artifacts or report the same underlying changes. Counts of pairs, findings, and indicators must **not** be interpreted as independent security incidents or proven copying events.

### Supported risk indicators

These counts are directed **pairs containing each indicator**, not individual matches. A pair can contribute to multiple rows. Uncertain indicators are tracked separately.

| Indicator | Description | Pairs |
|---|---|---:|
| RI-001 | Download-and-execute introduced | 96 |
| RI-002 | Executed code source changed | 0 |
| RI-003 | Network access expanded or redirected | 381 |
| RI-004 | Network security weakened | 22 |
| RI-005 | External code or dependency acquisition changed | 179 |
| RI-006 | Destructive or privileged file operation | 41 |
| RI-007 | Credential access or potential exposure | 231 |
| RI-008 | System configuration or permissions changed | 53 |
| RI-009 | Sensitive filesystem access or modification | 0 |
| RI-010 | Local script execution introduced or changed | 413 |
| RI-011 | External instruction dependency introduced or changed | 0 |

Full counts are in `results/review/indicator_frequency.csv` and `results/review/indicator_frequency_by_edge_type.csv`. A supported indicator marks observable security-sensitive evidence, **not** a confirmed vulnerability or malicious intent.

### Family-level observations

| Family | Directed pairs | Pairs with supported indicators | Useful for |
|---|---:|---:|---|
| `seo` | 1,136 | 298 | Network and credential evidence; cohort imbalance |
| `defi-protocol-templates` | 544 | 58 | Script and dependency changes |
| `python-performance-optimization` | 460 | 9 | High-volume comparison and uncertain indicators |
| `caveman-help` | 363 | 0 | Unflagged comparisons |
| `neurokit2` | 285 | 55 | Downloads and local-script changes |
| `devcontainer-setup` | 249 | 52 | Incomplete sibling evidence |
| `busybox-on-windows` | 174 | 0 | Sibling-file differences |

The `seo` family contributes about **28%** of directed comparisons and **51%** of indicator-bearing comparisons, so large families heavily influence pooled rates. Some artifacts originate from security benchmarks or adversarial test repositories; interpret those separately from ordinary reuse.

## Validation samples

The notebook selected samples with seed `580`, up to five cases per category:

| Review type | Sampled cases | Categories |
|---|---:|---|
| Directed comparisons | 30 | Supported indicator; uncertain indicator; sibling change; flagged without indicator; unflagged directed; coverage-limited |
| Relationships | 15 | Ambiguous direction; equivalent; no related edge |

Files are in `results/manual-review/directed-pairs/` and `results/manual-review/relationship-pairs/`. Each directory contains a sample CSV, an annotation template, and an `annotations.csv` with draft entries. The directed draft contains **21 pending entries**; the relationship draft contains **15 pending entries**. No completed adjudications or validated precision/recall estimates are recorded.

Follow the [pipeline README](../README.md) and the [Manual Annotation Protocol](../../../docs/instructions/manual_annotation_protocol.md) for independent review and adjudication. Review the original skill bodies and relevant siblings before accepting any finding; do not execute the stored commands or scripts.

## Files and reproducibility

| Location | Contents |
|---|---|
| `samples/families.txt` | Exact family names selected for analysis |
| `results/sample_manifest.json` | Cohort selection, source details, policy, rules, and provenance checksums |
| `results/execution_summary.json` | Execution and validation status |
| `results/audit/` | Processing statistics and skipped artifacts |
| `results/review/` | Cohort summary, family and edge tables, and directed-pair records |
| `results/manual-review/` | Validation samples, templates, and review evidence |
| `results/figures/` | `pair_outcomes.svg`, `indicators_by_family.svg`, `indicators_by_edge_type.svg`, `indicator_frequency.svg` |
| `../.scans/` | Shared scan JSON cache used by Sprint 2 and Sprint 3 |
| `../.scans/.metadata/scan-manifest.json` | Shared cache fingerprints and configuration metadata |

To reproduce the analysis, use `SPRINT = 2` in the [notebook](../end_to_end_pipeline.ipynb), the prepared GitSkills DuckDB database, and the settings recorded in `results/sample_manifest.json`. The configured similarity policy uses shingle size `5`, minimum containment `0.8`, minimum Jaccard `0.3`, minimum shared shingles `5`, and direction containment margin `0.1`.

**Interpretation limits:** Source relationships and directions are inferred, not verified ancestry; missing sibling or extracted evidence limits coverage; static indicators cannot establish intent or harm; and the purposive cohort is not representative of the full dataset. Independent review is needed to assess scanner accuracy.

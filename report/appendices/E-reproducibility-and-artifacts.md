
# Appendix E Supporting repository material

The report uses the **three saved Sprint 3 trials**, not the earlier Sprint 2 exploratory cohort. The source code revision recorded in all three manifests is `ae69732ed8988ad7066ff351848f7d2e8ad311a1`; the manifests additionally retain the implementation fingerprint, active rules, dataset identity, and selected inputs. Results are not recomputed by rebuilding the report.

| Repository resource | Purpose |
| --- | --- |
| [End-to-end notebook](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb) | Reproduces cohort processing and result tables. |
| [Pipeline README](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/README.md) | Configuration, outputs, cache, and validation instructions. |
| [Dataset preparation](https://github.com/umdnp/csc580-project8/blob/main/data/README.md) | GitSkills acquisition and DuckDB preparation. |
| [Candidate-selection SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/create_analysis_tables.sql) | Generates the comparison candidate pool (Appendix A). |
| [Sibling fingerprint SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/update_artifact_groupings.sql) | Represents known versus unknown bundled-file content. |
| [Sampling decision RDR-014](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-014-stratified-family-sampling-method.md) | Family eligibility and stratified sampling. |
| [Edge-selection decision RDR-013](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-013-sprint3-sampling-and-edge-selection.md) | Rationale for primary-only comparisons and family-level reporting. |
| [Risk indicator definitions RDR-010](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-010-evidence-based-risk-indicators.md) | Operational scope of RI-001 through RI-011. |
| [Threat model](https://github.com/umdnp/csc580-project8/blob/main/THREAT_MODEL.md) | Trust boundary, detection scope, and security interpretation limits. |
| [Annotation protocol](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/manual_annotation_protocol.md) | Independent review and adjudication guidance. |
| [Report build guide](https://github.com/umdnp/csc580-project8/blob/main/report/README.md) | Source sections, figures, and local report rendering. |

: Reproducibility and supporting repository resources {.wide}

The saved research inputs and outputs are organized as follows (each trial has the same layout):

```text
notebooks/end_to_end_pipeline/sprint3/
  samples1/families.txt
  samples1/sampling_report.json
  samples2/families.txt
  samples2/sampling_report.json
  samples3/families.txt
  samples3/sampling_report.json
  results1/
    sample_manifest.json
    execution_summary.json
    review/summary.json
    review/families.csv
    review/directed_pairs.csv
    review/indicator_frequency.csv
    review/direction_basis.csv
    manual-review/directed-pairs/
    manual-review/relationship-pairs/
  results2/                  # same structure
  results3/                  # same structure
```

The `sampling_report.json` files record sampling seeds **5801–5803**, stratum allocations, exclusions, and candidate rejections. The `sample_manifest.json` files record the selected families, policies, scanner and code identities, review sample checksums, and a source fingerprint. Research summaries and CSV files contain the automated outcome counts used in Sections IV–VI and Appendix D; audit and execution files provide coverage and processing status. The separate annotation files are reviewer-owned and remain distinct from automated predictions.

Two cross-trial charts in Section VI are generated from the saved `families.csv` and `directed_pairs.csv` files using `report/figures/generate_sprint3_figures.py`. The script does not alter trial results or select new families.

The three sample manifests currently mark their approval reference as **provisional** (`sample_status: provisional`, no approval reference). The final report should not imply formal approval has been recorded unless the manifest or repository decision history is updated. A tagged release and final manual-validation record should be linked when available.

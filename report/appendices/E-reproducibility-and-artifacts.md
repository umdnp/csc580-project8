# Appendix E Supporting repository material {#app-e}

The report uses **three saved Sprint 3 trials**; Sprint 2 was exploratory. All three trials have matching recorded scanner and cohort implementation fingerprints, active rules, similarity settings, and primary-edge selection. The original manifests preserve the recorded code and dataset identities for reproducibility. Building this report does not rerun the study. The supporting resources are linked below.

## Supporting repository resources

- **Data preparation:** [Dataset guide](https://github.com/umdnp/csc580-project8/blob/main/data/README.md), [candidate-selection SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/create_analysis_tables.sql), and [sibling-state SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/update_artifact_groupings.sql) explain how the data is prepared.
- **Sampling and comparisons:** [RDR-014](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-014-stratified-family-sampling-method.md) and [RDR-013](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-013-sprint3-sampling-and-edge-selection.md) document family selection and primary-edge comparisons.
- **Detection scope:** [RDR-010](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-010-evidence-based-risk-indicators.md) and the [threat model](https://github.com/umdnp/csc580-project8/blob/main/THREAT_MODEL.md) define the indicators and their security limits.
- **Pipeline:** [End-to-end notebook](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb) and [pipeline README](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/README.md) document execution, outputs, and caching.
- **Validation:** [Annotation protocol](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/manual_annotation_protocol.md) and [reproducibility guide](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/reproducibility.md) explain review decisions and recorded settings.
- **Report:** [Report build guide](https://github.com/umdnp/csc580-project8/blob/main/report/README.md) explains how to rebuild the paper and figures.

## Saved research and validation artifacts

Each of the three trials has matching input and result folders in the [Sprint 3 directory](https://github.com/umdnp/csc580-project8/tree/main/notebooks/end_to_end_pipeline/sprint3). The input folders (`samples1`–`samples3`) hold family lists and sampling reports. The result folders (`results1`–`results3`) hold run manifests, execution records, tables, figures, and manual-review files.

The original independent reviews remain under `manual-review/` in the `directed-pairs/` and `relationship-pairs/` folders. Each `adjudicated/` folder contains the team's final `directed.csv`, `relationships.csv`, and `adjudication.txt`. Final validation metrics are in `review/summary.json`, with the pre-adjudication summary preserved alongside them.

## Reproducing the published results

1. Obtain GitSkills v1.0.0 and prepare the DuckDB tables using the [dataset guide](https://github.com/umdnp/csc580-project8/blob/main/data/README.md).
2. Install dependencies with `uv sync` and configure `GITSKILLS_DB`. Reuse the saved family lists; do not select new samples.
3. Run the [end-to-end notebook](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb) with `SPRINT = 3`, processing `SAMPLE = 1`, `2`, then `3`, and `EDGES = "primary"`. Use the saved random seeds and historical code settings in the [reproducibility guide](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/reproducibility.md); do not silently substitute a newer scanner.
4. Compare regenerated outputs against each trial's saved manifest and automated tables. Adjudication metrics can be recalculated separately from the saved samples and team judgments without rescanning skills; this alone does **not** verify a complete clean-environment reproduction of the three trials.

The sampling reports preserve seeds **5801–5803**, size strata, exclusions, and rejected candidates. The manifests record the dataset and code identities, rules, policies, selected inputs, and checksums. Automated review tables support the counts in Sections [IV](#sec-dataset)–[VI](#sec-results) and [Appendix D](#app-d); separate human annotations and summaries document validation without changing those counts. The cross-trial figures were generated from saved tables with the [chart-generation script](https://github.com/umdnp/csc580-project8/blob/main/report/figures/generate_sprint3_figures.py).

The original manifests' **provisional** status concerns sample-selection approval metadata, not the later human review. The team's approval of adjudicated judgments is documented separately in each trial's adjudication notes. The Sprint 3 research snapshot is tagged **`sprint3`**, and later review artifacts are preserved separately.

\clearpage

# Appendix E Supporting repository material

The following repository material supports the analysis without being reproduced in the report. Links identify resource locations; the saved run's manifest, rather than the evolving main branch, identifies the analysis inputs and implementation.

| Resource | Relevance |
| --- | --- |
| [End-to-end notebook](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb) | Executable cohort analysis and generation of result tables. |
| [Pipeline README](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/README.md) | Current setup, configuration, output layout, and validation instructions. |
| [Dataset setup](https://github.com/umdnp/csc580-project8/blob/main/data/README.md) | Source-data acquisition and preparation of the local DuckDB database. |
| [Candidate-selection SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/create_analysis_tables.sql) | Executable selection query reproduced in Appendix A. |
| [Sibling enrichment SQL](https://github.com/umdnp/csc580-project8/blob/main/sql/update_artifact_groupings.sql) | Known and unknown sibling-state preparation. |
| [Risk indicator definitions](https://github.com/umdnp/csc580-project8/blob/main/docs/decisions/RDR-010-evidence-based-risk-indicators.md) | Operational definitions and scope of RI-001 through RI-011. |
| [Annotation protocol](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/manual_annotation_protocol.md) | Detailed review fields and adjudication instructions. |
| [Threat model](https://github.com/umdnp/csc580-project8/blob/main/THREAT_MODEL.md) | Scope and interpretation limits of static security evidence. |
| [Report build guide](https://github.com/umdnp/csc580-project8/blob/main/report/README.md) | Report sources, appendix ordering, and local rendering instructions. |

The saved outputs are under `notebooks/end_to_end_pipeline/results/sprint2/`. The sample manifest records source identities, configuration, and sample checksums. Within `review/`, the summary, directed-pair, family, indicator-frequency, and direction-basis files supply the main results and Appendix D tables. The execution summary and audit files record processing status and coverage. Annotation files remain separate from automated predictions.

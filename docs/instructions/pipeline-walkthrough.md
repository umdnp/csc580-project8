# Pipeline Walkthrough

The current pipeline takes GitSkills data through relationship analysis, security comparison, and human validation. The [end-to-end notebook](../../notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb) runs the automated stages directly; individual family-analysis and scanning commands are not prerequisites.

## 1. Prepare the Database

Follow the [data setup guide](../../data/README.md#local-duckdb-development-setup) to import SQLite into DuckDB, create the analysis tables, populate artifact groupings, and set `GITSKILLS_DB`.

Candidate families group qualifying artifacts by exact skill name. A shared name identifies candidates for comparison; it does not establish copying or ancestry.

## 2. Configure and Run the Notebook

From the repository root:

```bash
uv run --with jupyterlab jupyter lab
```

Open `notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb` using the project environment. Review the candidate-family list, relationship policy, edge selection, sampling settings, and `RUN_LABEL`, then run through **Findings for manual review**. Record team approval before treating the provisional family list as an approved sample.

The notebook calls `summarize_cohort()` to:

1. Compare skill content and known sibling states within each family.
2. Infer relatedness and direction from similarity, source declarations, chronology, repository boundaries, and containment evidence.
3. Scan direction-supported pairs, compare skill-body and relevant sibling evidence, and assess eleven defined risk indicators.
4. Save research summaries, figures, provenance, coverage records, and stratified review samples.

The default `EDGES = "all"` includes primary and additional directed edges. Equivalent and direction-unknown relationships remain separate from directed security comparisons. `PER_STRATUM` controls the human-review sample size, not the scope of the automated analysis.

For configuration and output details, see the [Pipeline README](../../notebooks/end_to_end_pipeline/README.md).

## 3. Inspect the Results

Outputs are saved under `notebooks/end_to_end_pipeline/results/<RUN_LABEL>/`:

| Location | Contents |
| --- | --- |
| `review/` | Research summaries and comparison tables |
| `figures/` | Generated research figures |
| `manual-review/` | Directed-pair and relationship-pair samples and annotation templates |
| `sample_manifest.json` | Input provenance, configuration, and sample checksums |
| `execution_summary.json` | Processing and validation status |

Use [SkillTrace](../../apps/skilltrace/README.md) to inspect stored content, relationships, and diffs. It uses separate `analyze_family` reports and supports focused scans; the notebook performs the broader cohort analysis.

## 4. Review and Adjudicate

Give reviewers separate copies of the annotation templates. Inspect the original skill bodies, relevant siblings, relationship evidence, and all eleven risk indicators. Record uncertainty and missing coverage explicitly, then resolve disagreements into final team annotations using the [Manual Annotation Protocol](manual_annotation_protocol.md).

Once both adjudicated CSVs exist, run the notebook's final **Independent review and adjudication** cell with the same inputs and configuration. Compatible saved outputs can be reused to add validation metrics. Preserve reviewed runs under their existing labels before generating a changed cohort or sample.

## 5. Interpret the Findings

Risk indicators are static review signals, not confirmed vulnerabilities or proof of malicious intent. Inferred direction does not prove historical copying, incomplete evidence is not a negative finding, and shared artifacts make comparison counts dependent. Human-review samples do not establish population prevalence.

See [Threats to Validity](../../THREATS_TO_VALIDITY.md) and the [saved results guide](../../notebooks/end_to_end_pipeline/results/sprint2/README.md) for limitations and current validation status. Dataset instructions and scripts are inspected as text, not executed.

## Original Sprint 1 Workflow

The [original extraction notebook](../../notebooks/extraction_pipeline/README.md) uses the fixed `sample_artifacts` view and compares adjacent artifacts within each name group. It is a separate exploratory workflow; its comparisons and rule-count results should not be pooled with the current pipeline's relationship-supported indicator results. See the [Sprint 1 setup note](../../data/README.md#original-sprint-1-notebook) to reproduce it.

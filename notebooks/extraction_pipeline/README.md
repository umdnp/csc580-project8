# Sample Extraction and Exploration

## Overview

This notebook provides the extraction and exploratory analysis pipeline for the approved GitSkills sample. It reads the `sample_artifacts` view from the project DuckDB database, compares adjacent artifacts within each skill-name group, runs the GitSkills static scanner, and generates the analysis dataset and figures.

Artifact content is treated only as text. The notebook does not execute commands, scripts, or other instructions contained in the dataset.

## Data Setup

The GitSkills DuckDB database must already be available before running the notebook. See [`data/README.md`](../../data/README.md) for database setup and dataset-loading instructions.

The analysis also requires the `sample_artifacts` view. From the repository root, run [`sql/create_sprint1_samples_view.sql`](../../sql/create_sprint1_samples_view.sql) against the GitSkills DuckDB database before starting the notebook. The view selects the approved sample and joins the artifact and repository fields used by the analysis.

The notebook processes artifacts in the order returned by this view; it does not apply a separate ordering step in Pandas.

Set `GITSKILLS_DB` to the database path before starting the notebook:

```bash
export GITSKILLS_DB=/path/to/agent_skills_release.db
```

If the variable is not set, the notebook uses the default path defined near the top of the notebook.

## How the Pipeline Works

The notebook:

1. Connects to DuckDB in read-only mode and inspects the approved sample.
2. Loads all rows from `sample_artifacts` and groups them by `name` while preserving view order.
3. Compares each artifact with the immediately preceding artifact in the same group.
4. Runs the GitSkills scanner on the base and derived content and records positive rule deltas.
5. Saves the extracted dataset to Parquet, reloads it, and generates pair-, rule-, and category-level summaries and figures.

The first artifact in each name group has no scanner result because there is no earlier artifact in that group to compare against.

## Scanner Overview

The notebook uses the local `gitskills` package for static analysis. The scanner applies regex-based rules grouped into security-sensitive categories including command execution, network access, file-system access, credential access, external code execution, and system modification.

For each base/derived pair, the scanner analyzes both artifacts independently and compares their rule match counts. A rule is flagged when its match count increases in the derived artifact. The notebook stores the number of flagged rules in `rules_flagged` and the full comparison result in `scanner_json`.

The rule catalog is read directly from `gitskills`, so the notebook stays aligned with the current scanner definitions without duplicating them.

## Generated Outputs

The extracted analysis dataset is written to:

```text
notebooks/extraction_pipeline/results/sample_artifacts_scanner_results.parquet
```

The Parquet file contains the original `sample_artifacts` fields plus:

- `rules_flagged` — number of distinct scanner rules with a positive match-count delta
- `scanner_json` — complete base-versus-derived scanner comparison output

The generated visualizations are written to:

```text
notebooks/extraction_pipeline/figures/pair_scan_outcomes.png
notebooks/extraction_pipeline/figures/flagged_rules.png
notebooks/extraction_pipeline/figures/flagged_risk_categories.png
```

These outputs are regenerated when the notebook is run from beginning to end.

## Current Sample Results

The current sample contains **43 artifacts across 10 skill-name groups**, producing **33 adjacent base-versus-derived comparisons**. All 33 comparisons were scanned successfully.

Of those comparisons, **13 (39.4%)** had at least one rule with a positive match-count delta. Across those pairs, the scanner recorded **35 rule-level positive-delta events** representing **77 additional matches** in the derived artifacts.

`command_execution` was the most frequently flagged risk category, followed by `network_access` and `external_code_execution`. These are static-analysis signals: they identify changes in matched content and do not establish that an artifact is malicious or that any detected instruction was executed.

## Reproducing the Results

From a configured project environment with `duckdb`, `pandas`, `matplotlib`, and the local `gitskills` package available:

1. Prepare the GitSkills DuckDB database as described in [`data/README.md`](../../data/README.md).
2. From the repository root, run [`sql/create_sprint1_samples_view.sql`](../../sql/create_sprint1_samples_view.sql) against the database.
3. Set `GITSKILLS_DB` to the database path.
4. Open [`notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb`](../../notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb) with the working directory set to [`notebooks/extraction_pipeline`](../../notebooks/extraction_pipeline).
5. Run all cells from top to bottom.
6. Confirm that [`results/sample_artifacts_scanner_results.parquet`](../../results/sample_artifacts_scanner_results.parquet) and the three files under [`figures/`](../../figures/) are regenerated.
7. Review the notebook tables and figures to confirm the sample and detection counts.

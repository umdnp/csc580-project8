# Notebooks

Jupyter notebooks for the GitSkills project:

- [`exploratory_analysis.ipynb`](exploratory_analysis.ipynb) — dataset exploration.
- [`extraction_pipeline/`](extraction_pipeline/) — sample extraction and scanner exploration; see its [README](extraction_pipeline/README.md).
- [`end_to_end_pipeline/`](end_to_end_pipeline/) — cohort analysis, security-indicator summaries, and manual-validation samples for Sprints 2 and 3; see its [README](end_to_end_pipeline/README.md).

## Database setup

Notebooks requiring GitSkills data use the prepared DuckDB database. Set `GITSKILLS_DB` to its location in the environment running Jupyter:

```bash
export GITSKILLS_DB=/path/to/agent_skills_release.db
```

Some notebooks provide a local Windows fallback (`C:\data\duckdb\agent_skills_release.db`). See [data/README.md](../data/README.md) for dataset preparation and configuration.

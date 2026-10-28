# Data

The project imports the [GitSkills SQLite release](https://zenodo.org/records/21875637) into a separate **DuckDB database** for local analysis. See the [Data Dictionary](../DATA_DICTIONARY.md) for table and column descriptions.

## Local DuckDB Development Setup

Install the DuckDB CLI and project dependencies using the [root README](../README.md#getting-started). Run the commands below from the repository root.

### 1. Download and import the dataset

Download [agent_skills_release.db](https://zenodo.org/records/21875637/files/agent_skills_release.db?download=1) to the SQLite source location:

```text
C:/data/sqlite/agent_skills_release.db    # Downloaded SQLite source
C:/data/duckdb/agent_skills_release.db    # Separate DuckDB output
```

The import script defaults to Git Bash paths (`/c/data/...`). For WSL, use `/mnt/c/...`; for other locations, update `SQLITE_DB` and `DB_DIR` in [`bin/create_gitskills_db.sh`](../bin/create_gitskills_db.sh) and adjust the commands below.

```bash
bash bin/create_gitskills_db.sh
```

The script imports the source tables, adds local identifiers and relationships, and stops if the DuckDB output already exists. Keep the source and output files separate.

### 2. Prepare the analysis tables

Run these scripts in order:

```bash
duckdb -bail /c/data/duckdb/agent_skills_release.db < sql/create_analysis_tables.sql
duckdb -bail /c/data/duckdb/agent_skills_release.db < sql/update_artifact_groupings.sql
```

For an existing database, rerun both scripts to apply the description-normalization correction in [RDR-011](../docs/decisions/RDR-011-description-whitespace-normalization.md). Rebuilt group IDs can differ.

### 3. Configure the database path

Set `GITSKILLS_DB` to the generated DuckDB file before starting notebooks or SkillTrace. For Git Bash with Windows Python:

```bash
export GITSKILLS_DB="C:/data/duckdb/agent_skills_release.db"
```

For WSL Python, use `/mnt/c/data/duckdb/agent_skills_release.db`.

The database is now ready for the [current end-to-end pipeline](../notebooks/end_to_end_pipeline/README.md). See the [Manual Annotation Protocol](../docs/instructions/manual_annotation_protocol.md) for validation instructions.

## Original Sprint 1 Notebook

To reproduce the original sample extraction notebook, create its 43-artifact `sample_artifacts` view after the setup above:

```bash
duckdb -bail /c/data/duckdb/agent_skills_release.db < sql/create_sprint1_samples_view.sql
```

Then follow the [original notebook README](../notebooks/extraction_pipeline/README.md). This view is only needed for that notebook. Historical review material is retained under [`validation/archive/`](validation/archive/).

## License and Data Use

GitSkills metadata and aggregation are released under CC BY 4.0; collected source content remains subject to its original repository license. See the [dataset record](https://zenodo.org/records/21875637) and `repos.license` before redistributing source content.

Keep databases and extracted raw source content out of Git. Project code, notebooks, queries, aggregate statistics, and analysis results may be committed when consistent with the applicable licenses.

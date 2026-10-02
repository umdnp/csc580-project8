# CSC 580 Group Project - Mining AI-Native Software Engineering

This group project investigates AI-native software engineering using datasets and research directions inspired
by the [MSR 2027 Mining Challenge](https://2027.msrconf.org/track/msr-2027-mining-challenge). Our team will define
a focused research question, build a reproducible data-mining and analysis pipeline using the GitSkills, SpecMine,
or related datasets, and use the results to identify meaningful patterns in areas such as artifact reuse, quality,
maintenance, security, specification-to-code relationships, or human–AI collaboration. The project will be developed
iteratively using Scrum and will include tested code, documented methods, reproducible results, validation,
analysis of limitations, and a final research report and presentation.

More information about the research question selected by the team is available in the [Research Question](RESEARCH_QUESTION.md) document.

## Team and Roles

- Kyle Cantrell (Scrum Master)
- Christian Heiney (Researcher/Developer)
- Vaisnavii Mohanraj (Researcher/Developer)
- Jim Prantzalos (Product Owner)

## Getting Started

The steps below set up the project source code, Python environment, project dependencies, and the local DuckDB database used for analysis.

### 1. Clone the repository

Clone the project and change into the repository directory:

```bash
git clone https://github.com/umdnp/csc580-project8.git
cd csc580-project8
```

### 2. Install `uv`

We recommend using [`uv`](https://docs.astral.sh/uv/) to manage the Python virtual environment and project dependencies.

If `uv` is not already installed, follow the [official `uv` installation instructions](https://docs.astral.sh/uv/getting-started/installation).

### 3. Create the Python virtual environment

From the repository root, create a virtual environment with:

```bash
uv venv
```

### 4. Install project dependencies

Application and test dependencies are defined in `pyproject.toml`. Install the project's configured dependencies with:

```bash
uv sync
```

### 5. Download the GitSkills dataset

This project uses the GitSkills database as the source dataset. Download the original database from the [GitSkills dataset on Zenodo](https://zenodo.org/records/21875637).

The project imports the original SQLite database into DuckDB and applies a small set of project-specific changes needed for the analysis.

### 6. Build the local DuckDB database

Run the database creation script from the repository root:

```bash
bash bin/create_gitskills_db.sh
```

Then create the analysis tables and update the artifact groupings:

```bash
duckdb /c/data/duckdb/agent_skills_release.db < sql/create_analysis_tables.sql
duckdb /c/data/duckdb/agent_skills_release.db < sql/update_artifact_groupings.sql
```

For additional details about the local DuckDB setup, see the [data setup documentation](data/README.md#local-duckdb-development-setup).

The [Data Dictionary](DATA_DICTIONARY.md) documents the database structure, including the fields used by the project and modifications made by the team for the analysis.

## Running the Project

### Reproduce the Sprint 1 notebook output

Use [Sample Extraction and Exploration](notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb) to regenerate the sample analysis, Parquet results, and figures. The [notebook README](notebooks/extraction_pipeline/README.md) explains the analysis and how to interpret its results.

#### 1. Prepare the environment and database

Complete the [Getting Started](#getting-started) steps above, using Python 3.12 or newer within the project's supported range. Run `uv sync` from the repository root to install the project package and dependencies into `.venv`.

Follow the [data setup instructions](data/README.md#local-duckdb-development-setup) to install the DuckDB CLI, acquire the source SQLite database, create the separate DuckDB database, and build the analysis tables and artifact groupings in order. If those steps are already complete, reuse the prepared DuckDB database.

The setup scripts use `/c/data/...` paths for Git Bash on Windows. In WSL, Windows drive C is normally mounted at `/mnt/c`; adjust the configuration paths in `bin/create_gitskills_db.sh` and the paths in SQL commands to match your environment. Keep the source SQLite database and generated DuckDB database in separate locations.

#### 2. Create the Sprint 1 sample view

From the repository root, run the sample-view script against the prepared DuckDB database. For Git Bash with the default Windows storage location:

```bash
duckdb -bail /c/data/duckdb/agent_skills_release.db < sql/create_sprint1_samples_view.sql
```

For WSL, use `/mnt/c/data/duckdb/agent_skills_release.db` instead. The script should report **43 artifacts**. The fixed artifact-ID list and selection rationale are documented in [RDR-006](docs/decisions/RDR-006-sprint1-sample-design-and-selection.md).

#### 3. Configure the notebook's database path

Set `GITSKILLS_DB` before launching the notebook environment. Use a path that the selected Python interpreter can read. For the Windows `.venv` interpreter launched from Git Bash:

```bash
export GITSKILLS_DB="C:/data/duckdb/agent_skills_release.db"
```

For a Linux Python interpreter in WSL:

```bash
export GITSKILLS_DB="/mnt/c/data/duckdb/agent_skills_release.db"
```

If your database is elsewhere, substitute its actual path. The notebook requires the prepared **DuckDB** database, not the downloaded SQLite database.

#### 4. Open the notebook and run all cells

In your notebook editor, open `notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb`, select the project `.venv` Python interpreter as the kernel, and set the kernel's working directory to `notebooks/extraction_pipeline`. On Windows, the interpreter is `.venv/Scripts/python.exe`; on Linux or WSL, it is `.venv/bin/python`.

Alternatively, launch JupyterLab from the repository root with:

```bash
uv run --with jupyterlab jupyter lab --notebook-dir=notebooks/extraction_pipeline
```

This command supplies JupyterLab for the run and uses the project environment. Open `samples_extraction_and_exploration.ipynb` in the file browser and select its Python kernel.

Restart the kernel and run all cells from top to bottom. In the **Set Variables** output, confirm that the notebook directory is `notebooks/extraction_pipeline`, the Parquet output is under its `results/` directory, and the figures directory is its `figures/` directory. If these paths differ, correct the kernel's working directory before continuing. The notebook reads artifact content as text and does not execute dataset instructions.

#### 5. Check the regenerated results

Confirm that all cells finish without errors and that these files are regenerated:

```text
notebooks/extraction_pipeline/results/sample_artifacts_scanner_results.parquet
notebooks/extraction_pipeline/figures/pair_scan_outcomes.png
notebooks/extraction_pipeline/figures/flagged_rules.png
notebooks/extraction_pipeline/figures/flagged_risk_categories.png
```

Check the notebook's tables against the saved Sprint 1 exploratory baseline:

| Measure | Saved baseline |
| --- | --- |
| Sample artifacts | 43 |
| Skill-name groups | 10 |
| Adjacent comparisons scanned | 33 |
| Comparisons skipped | 0 |
| Comparisons with a positive rule delta | 13 |
| Positive rule-delta events | 35 |
| Additional rule matches | 77 |

These are adjacent-comparison notebook results, distinct from the 17 directed comparisons in the family reports. Scanner-rule or dataset changes can change the detection totals; record and explain differences instead of silently replacing the baseline. The persistent manual-review section contains the two completed annotations and the corrected derived SHA for the first example; the automatically generated candidate table may still show its original SHA and `TODO` fields.

To complete the story's reproducibility check, record the repository commit, dataset used, execution date, environment, observed counts, and regenerated output paths in the story issue after successfully following these instructions.

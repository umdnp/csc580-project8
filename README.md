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

TODO: Document how to run the project code.

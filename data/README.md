# Data

This directory contains information and setup instructions for the datasets used by the project.

## GitSkills Database

The GitSkills dataset is available from Zenodo:

[GitSkills: A Dataset of Agent Skills on GitHub](https://zenodo.org/records/21875637)

Direct database download:

[agent_skills_release.db](https://zenodo.org/records/21875637/files/agent_skills_release.db?download=1)

The downloaded `agent_skills_release.db` file is a **SQLite database**.

For local project development, we create a separate **DuckDB database** and import the SQLite tables into it. DuckDB is well suited for analytical SQL workloads and includes a convenient browser-based notebook UI through the DuckDB CLI.

The original SQLite database and the generated DuckDB database are separate files, even though they use the same filename.

For example:

```text
C:\data
├── sqlite
│   └── agent_skills_release.db    <-- original SQLite database downloaded from Zenodo
└── duckdb
    └── agent_skills_release.db    <-- DuckDB database created locally
```

> **Note:** The downloaded SQLite database and the locally generated DuckDB database are local development artifacts and should not be committed to this repository.

Do not overwrite or open the downloaded SQLite file as though it were already a DuckDB database.

## License and Data Use

The GitSkills dataset's collected metadata and aggregation are released under the
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

The dataset also contains source content collected from public GitHub repositories.
That content remains subject to the license of the original repository. Before
reproducing or redistributing specific `SKILL.md` files, sibling files, or other
source content, review the corresponding repository license in `repos.license`
and the original repository.

Do not commit the GitSkills SQLite database, the locally generated DuckDB database,
or extracted raw source content from the dataset into this repository. These files
are intended for local analysis only.

Project code, notebooks, queries, aggregate statistics, and analysis results may be
committed normally, provided they do not reproduce source content in a way that
conflicts with its original license.

For complete dataset licensing and reuse information, see the
[GitSkills dataset record on Zenodo](https://zenodo.org/records/21875637)
and the
[GitSkills dataset documentation on Hugging Face](https://huggingface.co/datasets/mvaccargiu/gitskills).

## Local DuckDB Development Setup

The project uses the GitSkills SQLite release as the source dataset and builds a separate DuckDB database for local analysis.

The setup scripts currently expect:

```text
/c/data/sqlite/agent_skills_release.db    # downloaded SQLite source
/c/data/duckdb/agent_skills_release.db    # generated DuckDB database
```

If you use different locations, update the configuration values at the top of `bin/create_gitskills_db.sh`.

Run the following commands from the repository root.

### 1. Install the DuckDB CLI

In Linux or WSL:

```bash
curl https://install.duckdb.org | bash
export PATH="$HOME/.duckdb/cli/latest:$PATH"
```

Confirm that the CLI is available:

```bash
duckdb --version
```

### 2. Build the DuckDB Database

Download the GitSkills SQLite database and place it at:

```text
/c/data/sqlite/agent_skills_release.db
```

Then run:

```bash
bash bin/create_gitskills_db.sh
```

The script creates:

```text
/c/data/duckdb/agent_skills_release.db
```

It imports the GitSkills source tables into DuckDB and adds the local identifiers and relationships used by the project.

The script will stop if the DuckDB database already exists. Remove the existing DuckDB file first if you intentionally want to rebuild it.

### 3. Build the Analysis Tables

After the database import completes, create the project analysis tables:

```bash
duckdb -bail /c/data/duckdb/agent_skills_release.db     < sql/create_analysis_tables.sql
```

Then populate the derived artifact-grouping fields:

```bash
duckdb -bail /c/data/duckdb/agent_skills_release.db     < sql/update_artifact_groupings.sql
```

Run these scripts in this order. The update script prints a validation summary when it completes.

At this point the local DuckDB database is ready for project notebooks and analysis.

## Configure the Local Database Path

Project code can use the `GITSKILLS_DB` environment variable to locate the generated DuckDB database.

For the default WSL setup:

```bash
export GITSKILLS_DB="/c/data/duckdb/agent_skills_release.db"
```

Verify the value:

```bash
echo "$GITSKILLS_DB"
```

If the database is stored somewhere else, set `GITSKILLS_DB` to that path before starting the notebook or development environment.

## Data Dictionary

For descriptions of the GitSkills tables and columns, see the project [Data Dictionary](../DATA_DICTIONARY.md).
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

### 1. Install DuckDB

Download the DuckDB CLI from:

[DuckDB Installation](https://duckdb.org/install)

DuckDB is distributed as a single executable. Place it in a directory already included in your system `PATH`, or add the directory containing the executable to your `PATH`.

Confirm that DuckDB is available:

```text
duckdb --version
```

### 2. Create a Separate Directory for the DuckDB Database

Assume the downloaded SQLite database is stored here:

```text
C:\data\sqlite\agent_skills_release.db
```

The SQLite file should remain in that directory.

Create a different directory for the DuckDB database:

```cmd
mkdir C:\data\duckdb
```

Then change into the new directory:

```cmd
cd /d C:\data\duckdb
```

At this point, the source SQLite database is still located at:

```text
C:\data\sqlite\agent_skills_release.db
```

and the new DuckDB database will be created separately under:

```text
C:\data\duckdb
```

### 3. Create and Start the DuckDB Database

From inside `C:\data\duckdb`, run:

```text
duckdb -ui agent_skills_release.db
```

This creates a new DuckDB database at:

```text
C:\data\duckdb\agent_skills_release.db
```

The new database will initially be empty. The command also opens DuckDB's browser-based notebook UI, where the remaining SQL commands can be run.

Do **not** run this command against:

```text
C:\data\sqlite\agent_skills_release.db
```

That file is the original SQLite database and is only used as the source for the import.

### 4. Enable DuckDB's SQLite Extension

In the DuckDB UI, run:

```sql
INSTALL sqlite;
LOAD sqlite;
```

Confirm that the SQLite extension is available:

```sql
SELECT *
FROM duckdb_functions()
WHERE function_name LIKE '%sqlite%';
```

### 5. Import the SQLite Tables into DuckDB

Use `sqlite_scan` to read the original SQLite database and create native DuckDB tables.

If your SQLite database is stored somewhere other than `C:/data/sqlite/agent_skills_release.db`, update the path in these commands.

```sql
CREATE TABLE artifacts AS
SELECT *
FROM sqlite_scan('C:/data/sqlite/agent_skills_release.db', 'artifacts');

CREATE TABLE repos AS
SELECT *
FROM sqlite_scan('C:/data/sqlite/agent_skills_release.db', 'repos');

CREATE TABLE mining_runs AS
SELECT *
FROM sqlite_scan('C:/data/sqlite/agent_skills_release.db', 'mining_runs');

CREATE TABLE artifact_siblings AS
SELECT *
FROM sqlite_scan('C:/data/sqlite/agent_skills_release.db', 'artifact_siblings');
```

Verify that the import completed successfully:

```sql
SELECT COUNT(*) FROM artifacts;
```

The DuckDB database is now ready for use by the project notebooks.

## Configure the Local Database Path

Project notebooks look for the DuckDB database at this default location:

```text
C:\data\duckdb\agent_skills_release.db
```

If your DuckDB database is stored somewhere else, set the `GITSKILLS_DB` environment variable to the full path of your DuckDB database.

### Windows

From Command Prompt:

```cmd
set GITSKILLS_DB=D:\data\duckdb\agent_skills_release.db
```

Verify the value:

```cmd
echo %GITSKILLS_DB%
```

Start Jupyter, VS Code, or your notebook environment from the same command session so it inherits the environment variable.

### Linux / WSL

```bash
export GITSKILLS_DB="/path/to/agent_skills_release.db"
```

Verify the value:

```bash
echo "$GITSKILLS_DB"
```

If `GITSKILLS_DB` is not defined, project notebooks fall back to the default path shown above.

## Data Dictionary

For descriptions of the GitSkills tables and columns, see the project [Data Dictionary](../DATA_DICTIONARY.md).
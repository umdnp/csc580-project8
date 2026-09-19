# Notebooks

This directory contains the Jupyter notebooks used for project exploration, analysis, validation, and visualization.

All project notebooks should be stored here so that notebook-based work remains organized in one location.

## Accessing the GitSkills Database

Project notebooks that use the GitSkills dataset should connect to the DuckDB version of the database.

Notebooks that require database access should begin with setup code similar to the following:

```python
import os
from pathlib import Path

import duckdb

DEFAULT_DB_PATH = Path(r"C:\data\duckdb\agent_skills_release.db")

DB_PATH = Path(
    os.environ.get("GITSKILLS_DB", DEFAULT_DB_PATH)
)

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

conn = duckdb.connect(database=str(DB_PATH), read_only=True)
```

The `GITSKILLS_DB` environment variable allows each developer to keep the DuckDB database in a different local directory without changing notebook code. If the variable is not defined, the notebook uses the default path:

```text
C:\data\duckdb\agent_skills_release.db
```

For instructions on downloading the GitSkills dataset, creating the DuckDB database, and configuring `GITSKILLS_DB`, see the [data directory README](../data/README.md).

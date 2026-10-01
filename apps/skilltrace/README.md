# SkillTrace – GitSkills Similarity & Security Analyzer

SkillTrace is a local web application for exploring similarity, inferred lineage, sibling files, and security-sensitive changes across GitSkills artifacts.

It visualizes reports produced by `analyze_family` and uses the local GitSkills DuckDB database for artifact metadata, file contents, sibling files, diffs, search, and on-demand security scans.

## Prerequisites

Before starting SkillTrace, you need:

- the project environment installed;
- a local GitSkills **DuckDB** database; and
- at least one `analyze_family` report in `apps/skilltrace/reports/`.

The downloaded GitSkills database is SQLite. The project creates a separate DuckDB database for local analysis and builds the additional analysis tables used by SkillTrace.

See [`data/README.md`](../../data/README.md) for database setup instructions.

## Configure the Database

SkillTrace chooses the DuckDB path in this order:

1. `GITSKILLS_DB`
2. `--db PATH`
3. `C:/data/duckdb/agent_skills_release.db`

`GITSKILLS_DB` has priority over both `--db` and the default path.

For the default WSL setup:

```sh
export GITSKILLS_DB="/c/data/duckdb/agent_skills_release.db"
```

Verify it with:

```sh
echo "$GITSKILLS_DB"
```

If `GITSKILLS_DB` is set, passing a different `--db` value will not override it.

## Generate a Report

SkillTrace does not calculate family relationships itself. It visualizes JSON reports produced by `analyze_family`.

Run `analyze_family` for the skill family you want to explore and write the report to `apps/skilltrace/reports/`:

```sh
python -m gitskills.tools.analyze_family \
  --db C:/data/duckdb/agent_skills_release.db \
  cometchat-core \
  --output apps/skilltrace/reports
```

If `GITSKILLS_DB` is already set, `--db` can be omitted:

```sh
python -m gitskills.tools.analyze_family \
  cometchat-core \
  --output apps/skilltrace/reports
```

SkillTrace loads valid current `analyze_family` JSON reports from that directory. Reports from `scan_family`, malformed JSON, and older unsupported report formats are ignored.

For `analyze_family` options and similarity-policy details, see [`TOOLS.md`](../../TOOLS.md).

## Start SkillTrace

Run from the repository root.

### Option 1: Start script

```sh
sh bin/start_skilltrace_server.sh
```

### Option 2: Python module

```sh
python -m apps.skilltrace \
  --db /c/data/duckdb/agent_skills_release.db \
  --host 127.0.0.1 \
  --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

If `GITSKILLS_DB` is set, it takes priority over the `--db` value shown above.

Stop the server with `Ctrl+C`.

## What SkillTrace Shows

Choose an `analyze_family` report from the **Report** dropdown. SkillTrace displays the report's inferred family structure as an interactive graph.

The graph supports:

- directed parent/derived relationships;
- equivalent and direction-unknown peer relationships;
- direct or direct-and-indirect relationship views;
- root candidates and inferred lineage;
- artifact selection, focus, and viewport controls; and
- artifact search by ID or, when DuckDB is available, by name, repository, path, filename, or SHA.

The footer shows the similarity policy stored in the selected report, including the containment threshold, similarity threshold, shared-shingle requirement, and shingle size.

## Artifact Inspection

Selecting an artifact opens controls for the selected skill, related artifacts, and content-bearing sibling files.

You can:

- view raw `SKILL.md` contents;
- copy raw contents directly from DuckDB;
- inspect artifact metadata and chronology evidence;
- compare a selected artifact with its parent or related peers;
- view side-by-side skill diffs;
- view and copy sibling-file contents;
- compare sibling files across related artifacts; and
- inspect added, removed, or changed files.

Diff panes contain alignment rows for side-by-side display. Use **Copy Contents** when you need the original database text; it copies the raw content rather than the rendered diff pane.

## Security Scanning

For a directed parent-to-derived relationship, **Run scan** performs the project's static security comparison on demand.

The scan reports changes in security-sensitive behavior such as:

- command execution;
- network access;
- file-system operations;
- credential or secret references;
- external package or script execution; and
- other configured security-rule matches.

SkillTrace scans stored text only. It does not execute artifact or sibling content.

A scan finding identifies behavior that warrants review; it does not establish malicious intent.

## DuckDB Availability

DuckDB is opened read-only. The active database path and connection status are shown at the bottom of the page.

The relationship graph comes from the selected JSON report and remains available if DuckDB becomes unavailable. Database-backed features such as metadata, content, sibling inspection, search, diffs, and scans require a working database connection.

SkillTrace periodically checks database health and reports when the configured database cannot be accessed.

## Reports Directory

SkillTrace reads reports only from:

```text
apps/skilltrace/reports/
```

The last selected valid report is remembered in browser local storage and restored on refresh when it is still available.

## Tests

Run the SkillTrace tests from the repository root:

```sh
python -m unittest apps.skilltrace.test_app
```

## Notes

- SkillTrace is intended for local use and defaults to `127.0.0.1`.
- DuckDB is opened read-only.
- Artifact and sibling contents are displayed and statically scanned, never executed.
- The graph represents inferred relationships from `analyze_family`; it is not proof of repository ancestry or original authorship.
- Local API documentation is available at `/docs` while the server is running.

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

## Evidence and Risk-Indicator Inspection

The **Selected Artifact** panel offers **Inspect evidence** to statically scan the
stored `SKILL.md`. The **Artifact Siblings** panel offers **Inspect evidence**
for the selected content-bearing sibling file. The sibling dropdown includes paths
from **both** selected and compared artifacts, so you can investigate evidence
removed from an earlier sibling as well as evidence added to a later one.
Paths present only in the compared artifact are labeled accordingly. Inspection displays:

- Rule matches and detected capabilities;
- **all** extracted evidence records, including unchanged observations;
- Complete, partial, and unsupported extraction counts;
- Source filename, available sibling ID, offsets, line numbers, rule IDs,
  Markdown/code context and a redacted source excerpt; and
- A **Partial / unsupported only** filter for investigating extraction gaps.

The **Compare To → Run scan** action compares directed `SKILL.md` artifacts.
The **Artifact Siblings → Run scan** action compares the selected sibling file
at the same path across a directed pair. Both comparisons focus on changes:

- Original capability and rule-count changes;
- Evidence added and removed, even where rule counts are unchanged;
- Supported and uncertain RDR-010 risk indicators with supporting evidence;
- Indicator and distinct-finding counts; and
- Coverage and extraction counts.

**Inspect evidence** in **Compare To** or **Artifact Siblings** opens the full
base and derived evidence records and rule occurrences for the directed pair,
including unchanged records and partial extractions. Paired inspection
uses **Base** and **Derived** columns within each expandable evidence type or
rule ID, so opening a group reveals both sides together. Matching visible
records are aligned regardless of line-number shifts; unpaired records show an
explicit blank counterpart and can be isolated with **Unmatched only**. The
evidence groups also have a **Partial / unsupported only** filter. Alignment is
for reviewing source observations and does not replace the scanner's evidence
comparison or establish that behavior was introduced. In particular, redacted
excerpts are never assumed identical.

The **Selected Artifact → Inspect evidence** action still inspects just the
selected `SKILL.md`. For a sibling without a directed comparison, **Inspect
evidence** inspects one available file. Where only one sibling's content is
available for a directed comparison, the other side remains visibly unavailable;
this is not treated as a proven addition or deletion. Evidence is extracted
during scanning; the separate UI actions make detailed records optional rather
than duplicating them in the scan report.

Scans remain limited to directed parent/derived relationships recorded by
`analyze_family`. An ambiguous peer pair cannot support an introduction claim,
so **Run scan** is disabled for those pairs. Artifact scans analyze `SKILL.md`
only; sibling scans analyze the selected sibling file only. These on-demand
scans do **not** reproduce the full family-level sibling change assessment in
`scan_family`, including its RI-010 invocation/hash correlation.

If a sibling is present in the available content rows on only one side,
SkillTrace displays the available source evidence and **incomplete coverage**;
it does not treat the missing row as proof that the file was newly introduced.
Sibling inspection and sibling comparisons use the content-bearing files
available in DuckDB, not a complete inventory of unavailable sibling text.

**Copy report JSON** copies the current evidence inspection or comparison as
structured JSON, including extraction status and nearby source context, so
partial examples can be reviewed independently. These reports use best-effort
secret redaction; **review copied excerpts before sharing them**. The raw
file-content viewer and its **Copy Contents** action remain intentionally
unredacted.

These are static observations and indicators for manual review, not proof of
malicious behavior or of complete security coverage. SkillTrace never executes,
downloads, or fetches any stored skill or sibling script.

### On-demand API endpoints

- `GET /api/reports/{filename}/artifacts/{id}/evidence`
- `GET /api/reports/{filename}/artifacts/{id}/siblings/evidence?entry_name=...`
- `POST /api/reports/{filename}/scan/{base_id}/{derived_id}`
- `POST /api/reports/{filename}/sibling-scan/{base_id}/{derived_id}?entry_name=...`

All endpoints require the selected artifact(s) to belong to the current
`analyze_family` report. The sibling pair scan requires a directed edge.

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

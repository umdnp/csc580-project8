# Local skill relationship explorer

The viewer reads candidate-family reports only from `visualization/reports/`.
There is no report-directory environment variable. Only valid current
`analyze_family` JSON reports are listed in the report dropdown.

## Start the viewer

Dependencies are managed by the repository-level `pyproject.toml`. From the
repository root, using the project environment:

```sh
uv sync --group dev
python -m uvicorn visualization.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Stop the server with Ctrl+C.

Run the command from the repository root. If your shell is already inside the
`visualization` directory, the equivalent import path is `app:app` rather than
`visualization.app:app`.

## Reports

The report dropdown reads JSON files directly from `visualization/reports/`, but it
remembers the last selected valid report in browser local storage, so a normal refresh
restores the same report when it is still available. It
only lists files that match the current `analyze_family` JSON format and can be
loaded successfully. Malformed JSON, `scan_family` output, older prototype formats,
and unrelated JSON files are ignored.

`analyze_family` reports contain the family clusters, directed evolution edges,
peer relationships, and root candidates used by the graph. The default JSON omits
the full pairwise similarity matrix to keep visualization reports smaller; pass
`--verbose` only when that diagnostic detail is needed. For example:

```sh
analyze_family busybox-on-windows --json --output visualization/reports
```

The graph is built from the selected report. The viewer does not recalculate family
ancestry from DuckDB.

## DuckDB access

The viewer uses this database by default:

```text
C:/data/duckdb/agent_skills_release.db
```

If `GITSKILLS_DB` is set, its value overrides the default. DuckDB is opened read-only.
The active database path and health are shown at the bottom of the viewer.

The browser polls `/api/health` every 30 seconds. The health check opens DuckDB
read-only and verifies that the `artifacts`, `artifact_siblings`, and `repos` tables are
accessible. If access is lost, the viewer opens a compact centered warning dialog.
If the user closes that dialog while DuckDB is still unavailable, the next 30-second
health check opens it again. The dialog closes automatically if a later health check
succeeds. The report-based graph continues to work while database-backed features
are unavailable.

DuckDB is queried lazily for:

- artifact metadata such as name, description, repository/path, and commit dates;
- artifact search by name, repository, path, filename, or SHA;
- selected SKILL.md contents;
- content-bearing file siblings from `artifact_siblings`;
- side-by-side artifact and sibling-file diffs; and
- on-demand static `scan_diff` using the existing `gitskills` analyzer.

Artifact sibling lists include only rows where `entry_type = 'file'` and `content IS
NOT NULL`. Directory entries and files whose content was not stored are excluded.

## Graph behavior

Directed ancestry edges are always shown for the current view. Peer relationships are
contextual: only peers connected to the selected artifact are shown. Related peers
with unknown direction use a gray dotted line; equivalent peers are identified by
node color without an additional line. Selecting another node updates those peer
relationships.

The **View** dropdown uses **Direct relationships** for the selected artifact's
immediate relationships and **Direct and indirect relationships** for the broader
lineage view. The selected artifact, its direct parent(s), direct child(ren), and
ambiguous peers are visually distinguished. `Fit visible family` resets the viewport;
`Focus selected` centers the selected artifact without changing the current graph mode.

The search box accepts an artifact ID without needing DuckDB. Text searches use
DuckDB and can match artifact name, repository, path, filename, or SHA.

## Artifact details and actions

Selecting an artifact opens a three-panel action area:

- **Selected Artifact** shows the artifact ID, repository, and full path on separate
  lines and provides **View content**. The candidate-family name is not repeated here
  because it is already shown in the report summary above the graph.
- **Compare To** lists directed parent artifact(s) first and labels them `(parent)`.
  Peer comparisons are listed afterward as `(equivalent)` or `(related)`. A peer
  that already has a directed lineage relationship to the selected artifact is not
  repeated.
- **Artifact Siblings** lists the selected artifact's content-bearing file siblings by
  `entry_name`. Database IDs are not displayed. **View content** opens the
  selected sibling file even when there is no comparison target. If none exist, the
  dropdown shows `NONE` and no sibling actions are shown.

The previous parent/child/ambiguous/sibling-count/role summary cards were removed;
that relationship structure is already visible in the graph and does not need to be
repeated in the detail area.

`View content` opens the selected skill itself. `View diff` compares the
selected artifact with the current **Compare To** artifact. For parent comparisons,
the parent is the Base and the selected node is the Derived artifact. Ambiguous
comparisons are displayed as a neutral side-by-side comparison because lineage
direction is unresolved.

`Run scan` is available only for a directed parent comparison because the static
scanner requires an explicit Base -> Derived direction.

`View content` opens the selected artifact's sibling file directly. **View diff** compares that sibling `entry_name` across the current comparison artifact and the selected artifact. If one side does not contain that
file, its pane says `No such file for this artifact.` while the existing side shows
its contents and the addition/removal highlighting.

The metadata display uses **Artifact Sibling Count**, computed from the same filtered
`artifact_siblings` rows used by the sibling dropdown. When direction relies on an
equivalent peer's observed chronology, the relationship panel also shows the
effective chronology, its `equivalent-peer` basis, and the artifact that supplied
that date. Comparison panels always show
**Repo created**, **Commit history**, **First commit**, **Last commit**, and **Commit count**;
missing values are displayed as `Unknown` instead of being hidden. `Repo created` comes from
the `repos` table, and **Commit history** reports whether artifact history was fetched. Dates
are displayed as `YYYY-MM-DD`. Relationship panels surface the relationship type, basis, and
direction evidence recorded by `analyze_family`. Normalized description is omitted from
artifact comparison metadata because the human-readable description is already shown, and
filename is omitted because the full path already includes it. The older `Has scripts` and
`Has references` fields are not displayed.

Useful artifact identifiers and Base -> Derived IDs have copy buttons. Long metadata
values are constrained to scrollable areas so they do not overwhelm the detail panel.
Opening and closing dialogs does not change the current graph selection or viewport.

This is a local application without authentication. Keep the default loopback host;
do not expose it publicly without a separate deployment review. Artifact and sibling
content are displayed and statically scanned only; they are never executed.

API documentation is available locally at `/docs`.

## Tests

Run from the repository root:

```sh
python -m unittest visualization.test_app
```

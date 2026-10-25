"""Run the current notebook from source records to saved research outputs."""

import ast
from hashlib import sha1, sha256
import json
from pathlib import Path

import duckdb
import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb"
BODY = "Read and document the available source project configuration. " * 18


def assignment_cell(cells, name):
    matches = [(index, node) for index, source in enumerate(cells)
               for node in ast.parse(source).body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == name
                       for target in node.targets)]
    assert len(matches) == 1, f"Expected one notebook assignment for {name}"
    return matches[0]


@pytest.fixture
def notebook_workspace(tmp_path, monkeypatch):
    # Notebook output paths are derived from PROJECT_ROOT. Run in a synthetic
    # project so not even a default output can touch the real research reports.
    project = tmp_path / "project"
    notebook_directory = project / "notebooks" / "end_to_end_pipeline"
    notebook_directory.mkdir(parents=True)
    (project / "pyproject.toml").write_text('[project]\nname = "notebook-test"\n', encoding="utf-8")
    cells = ["".join(cell["source"]) for cell in json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
             if cell["cell_type"] == "code"]
    # Use the actual default cohort rather than replacing the notebook's setup.
    _, assignment = assignment_cell(cells, "candidate_families")
    names = ast.literal_eval(assignment.value)
    assert len(names) >= 3, "Fixture needs positive, negative, and direction-unknown families"
    database = tmp_path / "source.duckdb"
    monkeypatch.setenv("GITSKILLS_DB", str(database))
    monkeypatch.chdir(notebook_directory)
    displayed = []
    namespace = {"display": displayed.append}
    try:
        yield project, database, cells, names, namespace, displayed
    finally:
        # The current notebook also retains an interactive read-only connection.
        if "conn" in namespace:
            namespace["conn"].close()


def run_cell(cells, index, namespace):
    # These are trusted project notebook cells, never code from dataset records.
    exec(compile(cells[index], f"{NOTEBOOK}:code-cell-{index}", "exec"), namespace)


def prepare_source(database, names, missing_sibling_content):
    expected_ids = set()
    with duckdb.connect(str(database)) as connection:
        connection.execute("""
            CREATE TABLE artifacts (
                id BIGINT, repo_id BIGINT, name VARCHAR, description VARCHAR,
                frontmatter_valid BIGINT, body_chars BIGINT, content VARCHAR,
                composition_fetched BIGINT, composition_truncated BIGINT,
                file_sha VARCHAR, repo_full_name VARCHAR, path VARCHAR,
                first_commit_at VARCHAR
            );
            CREATE TABLE repos (id BIGINT, created_at VARCHAR);
            CREATE TABLE artifact_siblings (
                id BIGINT, artifact_id BIGINT, entry_name VARCHAR,
                entry_type VARCHAR, entry_sha VARCHAR, content VARCHAR,
                skipped_reason VARCHAR
            );
        """)
        for index, name in enumerate(names):
            for endpoint in (1, 2):
                artifact_id = 100 * (index + 1) + endpoint
                expected_ids.add(artifact_id)
                content = BODY
                if index == 0 and endpoint == 2:
                    content += "\nSee https://example.test/data\n"
                elif index == 2:
                    content += "\nSee https://example.test/" + ("old" if endpoint == 1 else "new")
                elif endpoint == 2:
                    content += "\nDocument findings."
                date = None if index == 2 else f"2026-01-{endpoint:02d}"
                connection.execute("INSERT INTO artifacts VALUES (?, ?, ?, ?, 1, ?, ?, 1, 0, ?, ?, ?, ?)", [
                    artifact_id, artifact_id, name, "Build project reports",
                    len(content), content, sha1(content.encode()).hexdigest(),
                    f"test/repo-{artifact_id}", "skills/demo/SKILL.md", date,
                ])
                connection.execute("INSERT INTO repos VALUES (?, '2025-01-01')", [artifact_id])
        # The actual preparation scripts must exclude invalid content and a
        # singleton name, rather than treating either as an analyzed negative.
        connection.execute("""
            INSERT INTO artifacts VALUES
                (9001, 9001, ?, 'invalid', 1, 100, NULL, 1, 0, 'missing', 'test/invalid', 'SKILL.md', NULL),
                (9002, 9002, 'excluded-singleton', 'only member', 1, 100, ?, 1, 0, 'single', 'test/single', 'SKILL.md', NULL)
        """, [names[0], BODY])
        script = "rm -rf /tmp/cache"
        connection.executemany("INSERT INTO artifact_siblings VALUES (?, 102, ?, 'file', ?, ?, ?)", [
            (20, "scripts/cleanup.sh", sha1(script.encode()).hexdigest(), script, None),
            (21, "notes.txt", "notes-hash", None if missing_sibling_content else "Project notes.",
             "not-fetched" if missing_sibling_content else None),
        ])
        for script_name in ("create_analysis_tables.sql", "update_artifact_groupings.sql"):
            connection.execute((ROOT / "sql" / script_name).read_text(encoding="utf-8"))
        assert {row[0] for row in connection.execute("SELECT artifact_id FROM artifact_groupings").fetchall()} == expected_ids
    return expected_ids


@pytest.mark.parametrize("missing_sibling_content", [False, True], ids=["complete-inputs", "missing-sibling-content"])
def test_notebook_runs_preparation_to_reproducible_research_outputs(notebook_workspace, missing_sibling_content, capsys):
    project, database, cells, names, namespace, displayed = notebook_workspace
    expected_ids = prepare_source(database, names, missing_sibling_content)
    source_hash = sha256(database.read_bytes()).hexdigest()

    # Run every production code cell, including the optional-review check.
    for index in range(len(cells)):
        run_cell(cells, index, namespace)
    execution = namespace["execution"]
    results = project / "notebooks/end_to_end_pipeline/results/sprint2"
    from gitskills.reporting.files import report_stem
    scans_dir = results / ".scans"
    assert namespace["PROJECT_ROOT"] == project
    assert namespace["RESULT_DIR"] == results
    assert "SKILLTRACE_REPORTS" not in namespace
    assert namespace["candidate_families"] == names
    assert namespace["EDGES"] == "all"
    assert execution["status"] == "complete"
    assert execution["family_count"] == len(names)
    assert execution["artifacts_loaded"] == len(expected_ids)
    assert execution["artifacts_skipped"] == 0
    assert execution["directed_pairs_analyzed"] == len(names) - 1
    assert execution["pairs_incomplete"] == int(missing_sibling_content)
    assert displayed, "Notebook should display its run and summary tables"
    assert "Manual review is pending" in capsys.readouterr().out
    assert json.loads((results / "execution_summary.json").read_text()) == execution
    manifest = json.loads((results / "sample_manifest.json").read_text())
    assert manifest["family_names"] == names
    assert {artifact["artifact_id"] for family in manifest["families"] for artifact in family["artifacts"]} == expected_ids
    assert (results / "audit/processing_summary.csv").is_file()
    assert (results / "review/summary.json").is_file()

    positive = json.loads((scans_dir / f"{report_stem(names[0])}.json").read_text())
    assert positive["summary"]["pairs_flagged"] == 1
    pair, = positive["clusters"][0]["flagged_pairs"]
    assert (pair["source_artifact_id"], pair["destination_artifact_id"]) == (101, 102)
    assert {(item["rule_id"], item["surface"]) for item in pair["flagged_rules"]} == {
        ("NET-001", "skill"), ("FS-001", "sibling"),
    }
    assert pair["sibling_scan"]["incomplete"] == missing_sibling_content
    negative = json.loads((scans_dir / f"{report_stem(names[1])}.json").read_text())
    assert negative["summary"]["pairs_analyzed"] == 1
    assert negative["summary"]["pairs_flagged"] == 0
    unknown = json.loads((scans_dir / f"{report_stem(names[2])}.json").read_text())
    assert unknown["summary"]["pairs_analyzed"] == 0
    assert unknown["summary"]["ambiguous_edges_skipped"] == 1

    templates = [
        results / "manual-review/directed-pairs/validation_annotations_template.csv",
        results / "manual-review/relationship-pairs/relationship_validation_annotations_template.csv",
    ]
    template_bytes = {path: path.read_bytes() for path in templates}
    scan_bytes = {path: path.read_bytes() for path in scans_dir.glob("*.json")}
    # Reuse the same notebook namespace just as a user rerunning the analysis and
    # summary cells would; the same seed and cohort must preserve these outputs.
    run_cell(cells, assignment_cell(cells, "execution")[0], namespace)
    run_cell(cells, assignment_cell(cells, "runs")[0], namespace)
    assert {path: path.read_bytes() for path in templates} == template_bytes
    assert {path: path.read_bytes() for path in scan_bytes} == scan_bytes
    assert sha256(database.read_bytes()).hexdigest() == source_hash


def test_notebook_rejects_unprepared_database_before_writing_reports(notebook_workspace):
    project, database, cells, _, namespace, _ = notebook_workspace
    with duckdb.connect(str(database)):
        pass
    with pytest.raises(RuntimeError, match="missing tables"):
        for index in range(len(cells)):
            run_cell(cells, index, namespace)
    assert not (project / "apps/skilltrace/reports").exists()
    assert not (project / "notebooks/end_to_end_pipeline/results").exists()

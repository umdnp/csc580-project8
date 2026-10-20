"""Recoverable content failures must remain visible in family scan output."""

import json

import duckdb
import pytest

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.data.siblings import DuckDBSiblingRepository
from gitskills.tools.scan_family import main


BASE = "Review the project configuration and summarize the current status."


def make_database(tmp_path, records):
    database = tmp_path / "inputs.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute("""
            CREATE TABLE artifacts (
                id INTEGER, file_sha VARCHAR, content VARCHAR,
                repo_full_name VARCHAR, path VARCHAR, first_commit_at VARCHAR
            );
            CREATE TABLE artifact_groupings (
                id INTEGER, artifact_id INTEGER, repo_id INTEGER, name VARCHAR,
                normalized_description VARCHAR, sibling_file_count INTEGER,
                sibling_content_sha VARCHAR
            );
            CREATE TABLE repos (id INTEGER, created_at VARCHAR);
            CREATE TABLE artifact_siblings (
                id INTEGER, artifact_id INTEGER, entry_name VARCHAR,
                entry_sha VARCHAR, content VARCHAR, skipped_reason VARCHAR,
                entry_type VARCHAR
            );
        """)
        for artifact_id, sha, content in records:
            connection.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, 'team/repo', 'SKILL.md', ?)",
                [artifact_id, sha, content, f"2026-01-{artifact_id:02d}"],
            )
            connection.execute(
                "INSERT INTO artifact_groupings VALUES (?, ?, 1, 'example', '', 0, 'same')",
                [artifact_id, artifact_id],
            )
    return database


def test_mixed_inputs_continue_and_preserve_findings(tmp_path, capsys):
    database = make_database(tmp_path, [
        (1, "base", BASE),
        (2, "derived", BASE + " Read https://example.com/report."),
        (3, "missing", None),
        (4, "empty", " \n\t"),
        (5, None, BASE),
    ])
    assert main(["example", "--db", str(database), "--json", "--verbose"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["input_summary"] == {
        "artifacts_loaded": 2, "artifacts_skipped": 3, "incomplete": True,
    }
    assert [(item["artifact_id"], item["reason"]) for item in result["skipped_artifacts"]] == [
        (3, "missing_content"), (4, "empty_content"), (5, "missing_file_sha"),
    ]
    assert result["skipped_artifacts"][0]["path"] == "SKILL.md"
    assert result["summary"]["pairs_analyzed"] == 1
    assert result["summary"]["pairs_flagged"] == 1
    rules = result["clusters"][0]["flagged_pairs"][0]["flagged_rules"]
    assert any(rule["rule_id"] == "NET-001" for rule in rules)


def test_all_unavailable_is_incomplete_not_family_not_found(tmp_path, capsys):
    database = make_database(tmp_path, [(1, "sha", None)])
    assert main(["example", "--db", str(database), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["input_summary"]["incomplete"] is True
    assert result["input_summary"]["artifacts_loaded"] == 0
    assert result["summary"]["pairs_analyzed"] == 0
    assert result["skipped_artifacts"][0]["reason"] == "missing_content"


def test_missing_family_still_fails(tmp_path, capsys):
    database = make_database(tmp_path, [])
    assert main(["example", "--db", str(database), "--json"]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert "not found" in captured.err


def test_text_report_explains_skipped_inputs(tmp_path, capsys):
    database = make_database(tmp_path, [(1, "sha", None)])
    assert main(["example", "--db", str(database)]) == 0
    output = capsys.readouterr().out
    assert "Skipped artifact 1: missing_content" in output
    assert "Input coverage incomplete" in output


def test_missing_changed_sibling_is_reported_as_incomplete(tmp_path, capsys):
    database = make_database(tmp_path, [(1, "base", BASE), (2, "derived", BASE)])
    with duckdb.connect(str(database)) as connection:
        connection.execute("""
            UPDATE artifact_groupings SET sibling_file_count = 1,
                sibling_content_sha = 'changed' WHERE artifact_id = 2;
            INSERT INTO artifact_siblings VALUES
                (20, 2, 'setup.py', 'sibling-sha', NULL, 'unavailable', 'file');
        """)
    assert main(["example", "--db", str(database), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["summary"]["pairs_analyzed"] == 1
    assert result["summary"]["pairs_incomplete"] == 1
    coverage = result["clusters"][0]["incomplete_pairs"][0]["sibling_scan"]
    assert coverage["unavailable_destination_ids"] == [20]
    assert coverage["incomplete"] is True


def test_saved_report_preserves_skipped_input_diagnostics(tmp_path, capsys):
    database = make_database(tmp_path, [(1, "sha", None)])
    output = tmp_path / "reports"
    assert main(["example", "--db", str(database), "--json", "--output", str(output)]) == 0
    printed = json.loads(capsys.readouterr().out)
    saved = json.loads((output / "example.json").read_text(encoding="utf-8"))
    assert saved == printed
    assert saved["input_summary"]["incomplete"] is True


def test_binary_skill_content_is_not_coerced_to_text(tmp_path):
    database = make_database(tmp_path, [(1, "sha", BASE)])
    with duckdb.connect(str(database)) as connection:
        connection.execute("ALTER TABLE artifacts ALTER content TYPE BLOB")
    loaded = DuckDBFamilyRepository(database).load_available("example")
    assert not loaded.artifacts
    assert loaded.skipped_artifacts[0].reason == "non_text_content"


@pytest.mark.parametrize("content", [None, b"curl https://example.com"])
def test_unavailable_sibling_content_is_not_scanned_as_text(content):
    sibling = DuckDBSiblingRepository._row_to_sibling(
        (1, 2, "script", "sha", content, None)
    )
    assert not sibling.content_available
    if content is not None:
        assert sibling.skipped_reason == "non_text_content"


@pytest.mark.parametrize("prefix", ["---\nname: broken\n", "---\nname: [broken\n---\n"])
def test_malformed_frontmatter_does_not_prevent_body_scan(prefix):
    result = SkillAnalyzer().scan(prefix + "Read https://example.com/report.")
    matches = [match for match in result.rule_matches if match.rule_id == "NET-001"]
    assert matches
    assert matches[0].line_number == prefix.count("\n") + 1


def test_empty_text_is_a_valid_empty_scan():
    assert SkillAnalyzer().scan("").rule_matches == ()

"""Run the production grouping SQL on constructed records (Story 6.1/RDR-003)."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import duckdb
import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.analysis.family_risk import FamilyRiskAnalyzer


SQL_DIRECTORY = Path(__file__).resolve().parents[2] / "sql"
HASH_A = "a" * 40
HASH_B = "b" * 40


@pytest.fixture
def database():
    # An isolated in-memory database prevents any access to the local dataset.
    with duckdb.connect(":memory:") as connection:
        connection.execute("""
            CREATE TABLE artifacts (
                id BIGINT PRIMARY KEY, repo_id BIGINT, name VARCHAR,
                description VARCHAR, frontmatter_valid BIGINT, body_chars BIGINT,
                content VARCHAR, composition_fetched BIGINT,
                composition_truncated BIGINT, path VARCHAR, file_sha VARCHAR
            );
            CREATE TABLE artifact_siblings (
                id BIGINT PRIMARY KEY, artifact_id BIGINT, entry_name VARCHAR,
                entry_type VARCHAR, entry_sha VARCHAR, content VARCHAR
            );
        """)
        yield connection


def add_artifact(database, artifact_id, **overrides):
    record = {
        "id": artifact_id, "repo_id": 100 + artifact_id,
        "name": "example", "description": "Build project reports",
        "frontmatter_valid": 1, "body_chars": 100, "content": "x" * 100,
        "composition_fetched": 1, "composition_truncated": 0,
        "path": f"skills/example-{artifact_id}/SKILL.md", "file_sha": HASH_A,
    }
    record.update(overrides)
    columns = ", ".join(record)
    placeholders = ", ".join("?" for _ in record)
    database.execute(f"INSERT INTO artifacts ({columns}) VALUES ({placeholders})", list(record.values()))


def add_sibling(database, sibling_id, artifact_id, entry_sha, *, name="script.py", entry_type="file", content=None):
    database.execute(
        "INSERT INTO artifact_siblings VALUES (?, ?, ?, ?, ?, ?)",
        [sibling_id, artifact_id, name, entry_type, entry_sha, content],
    )


def run_sql(database, filename):
    # Execute the actual script, including transactions/reset logic and summary.
    return database.execute((SQL_DIRECTORY / filename).read_text(encoding="utf-8"))


def create_pair(database, **first_overrides):
    add_artifact(database, 1, **first_overrides)
    add_artifact(database, 2)
    run_sql(database, "create_analysis_tables.sql")


def sibling_state(database, artifact_id=1):
    return database.execute(
        "SELECT sibling_file_count, sibling_content_sha FROM artifact_groupings WHERE artifact_id = ?",
        [artifact_id],
    ).fetchone()


@pytest.mark.parametrize("description", [
    "  BUILD project reports  ",
    "Build\tPROJECT\nreports",
    "\tBUILD  project reports\r\n",
])
def test_description_normalization_groups_equivalent_whitespace_and_case(database, description):
    create_pair(database, description=description)
    rows = database.execute(
        "SELECT id, artifact_id, normalized_description, artifact_group_size FROM artifact_groupings ORDER BY artifact_id"
    ).fetchall()
    assert [row[2] for row in rows] == ["build project reports", "build project reports"]
    assert rows[0][0] == rows[1][0]
    assert [row[3] for row in rows] == [2, 2]


def test_description_variants_are_retained_within_an_eligible_name(database):
    add_artifact(database, 1)
    add_artifact(database, 2, description="Different instructions")
    add_artifact(database, 3, name="other", description="Build project reports")
    add_artifact(database, 4, name="other", description="Build project reports")
    add_artifact(database, 5, name="singleton")
    run_sql(database, "create_analysis_tables.sql")
    rows = database.execute(
        "SELECT artifact_id, id, artifact_group_size FROM artifact_groupings ORDER BY artifact_id"
    ).fetchall()
    assert [row[0] for row in rows] == [1, 2, 3, 4]
    assert [row[2] for row in rows] == [1, 1, 2, 2]
    assert rows[0][1] != rows[1][1]
    assert rows[0][1] != rows[2][1]  # Same description, different name.
    assert rows[2][1] == rows[3][1]


def test_description_group_merge_preserves_family_scanner_results(database):
    body = "Review the project configuration and summarize the current status before generating a detailed report."
    add_artifact(database, 1, description="\tBuild project reports\n", content=body)
    add_artifact(database, 2, content=body + " Read https://example.com/report.", file_sha=HASH_B)
    run_sql(database, "create_analysis_tables.sql")
    run_sql(database, "update_artifact_groupings.sql")
    rows = database.execute("""
        SELECT g.id, g.artifact_id, g.repo_id, g.name, g.normalized_description,
               g.sibling_file_count, g.sibling_content_sha, a.file_sha, a.content, a.path
        FROM artifact_groupings g JOIN artifacts a ON a.id = g.artifact_id
        ORDER BY g.artifact_id
    """).fetchall()
    assert rows[0][0] == rows[1][0]
    merged = [
        Artifact(
            group_id=row[0], artifact_id=row[1], repo_id=row[2], name=row[3],
            normalized_description=row[4], sibling_file_count=row[5],
            sibling_content_sha=row[6], file_sha=row[7], content=row[8], path=row[9],
            first_commit_at=f"2026-01-{row[1]:02d}", repo_created_at=None,
        )
        for row in rows
    ]
    # Previously the same descriptions occupied separate groups; only their
    # grouping metadata changes here, not scanner inputs or direction evidence.
    split = [
        replace(merged[0], group_id=1001, normalized_description=" build project reports "),
        replace(merged[1], group_id=1002),
    ]
    analyzer = FamilyRiskAnalyzer()
    before = analyzer.analyze(split)
    after = analyzer.analyze(merged)
    assert after.pairs_analyzed == 1
    assert after.pairs_flagged == 1
    assert after.to_dict(verbose=True) == before.to_dict(verbose=True)


@pytest.mark.parametrize("invalid_fields", [
    {"frontmatter_valid": 0}, {"frontmatter_valid": None},
    {"body_chars": 50, "content": "x" * 50}, {"body_chars": None},
    {"content": None}, {"name": None}, {"description": None},
], ids=["invalid-frontmatter", "unknown-frontmatter", "body-at-50-character-boundary", "unknown-body-size", "missing-content", "missing-name", "missing-description"])
def test_nonqualifying_artifacts_are_excluded_without_losing_valid_members(database, invalid_fields):
    add_artifact(database, 1)
    add_artifact(database, 2)
    add_artifact(database, 3, **invalid_fields)
    run_sql(database, "create_analysis_tables.sql")
    assert database.execute("SELECT artifact_id FROM artifact_groupings ORDER BY artifact_id").fetchall() == [(1,), (2,)]


def test_eligibility_is_counted_after_filters_and_names_are_exact(database):
    add_artifact(database, 1, name="singleton-after-filtering")
    add_artifact(database, 2, name="singleton-after-filtering", frontmatter_valid=0)
    add_artifact(database, 3, name="Example")
    add_artifact(database, 4, name="example")
    run_sql(database, "create_analysis_tables.sql")
    # None has two qualifying occurrences of its exact name.
    assert database.execute("SELECT COUNT(*) FROM artifact_groupings").fetchone() == (0,)


def test_51_character_body_qualifies_and_source_records_remain_traceable(database):
    create_pair(database, body_chars=51, content="x" * 51)
    assert database.execute("""
        SELECT g.artifact_id, g.repo_id, a.path, a.file_sha, a.content
        FROM artifact_groupings g JOIN artifacts a ON a.id = g.artifact_id
        WHERE g.artifact_id = 1
    """).fetchone() == (1, 101, "skills/example-1/SKILL.md", HASH_A, "x" * 51)
    # Byte-identical artifacts in distinct repositories are separate members.
    assert database.execute("SELECT COUNT(DISTINCT artifact_id), COUNT(DISTINCT repo_id) FROM artifact_groupings").fetchone() == (2, 2)
    assert sibling_state(database) == (None, None)


def test_rebuilding_groupings_replaces_stale_members_without_duplicate_rows(database):
    create_pair(database)
    add_artifact(database, 3, description="A new description")
    run_sql(database, "create_analysis_tables.sql")
    assert database.execute("SELECT artifact_id FROM artifact_groupings ORDER BY artifact_id").fetchall() == [(1,), (2,), (3,)]
    database.execute("UPDATE artifacts SET frontmatter_valid = 0 WHERE id IN (2, 3)")
    run_sql(database, "create_analysis_tables.sql")
    assert database.execute("SELECT COUNT(*) FROM artifact_groupings").fetchone() == (0,)


@pytest.mark.parametrize("directory_only", [False, True])
def test_known_empty_sibling_composition_has_empty_hash_not_unknown(database, directory_only):
    create_pair(database)
    if directory_only:
        add_sibling(database, 10, 1, None, name="scripts", entry_type="dir")
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database) == (0, sha256(b"").hexdigest())


def test_fingerprint_ignores_order_paths_directories_and_content_availability(database):
    create_pair(database)
    add_sibling(database, 10, 1, HASH_B, name="old/b.py")
    add_sibling(database, 11, 1, HASH_A, name="old/a.py", content="Original text")
    add_sibling(database, 12, 1, None, name="old", entry_type="dir")
    add_sibling(database, 20, 2, HASH_A, name="renamed/a.txt")
    add_sibling(database, 21, 2, HASH_B, name="renamed/b.txt")
    run_sql(database, "update_artifact_groupings.sql")
    expected = (2, sha256(f"{HASH_A}|{HASH_B}".encode()).hexdigest())
    assert sibling_state(database, 1) == expected
    assert sibling_state(database, 2) == expected


def test_duplicate_file_hashes_are_counted_as_a_multiset_and_changes_alter_fingerprint(database):
    create_pair(database)
    add_sibling(database, 10, 1, HASH_A, name="first.py")
    add_sibling(database, 11, 1, HASH_A, name="copy.py")
    add_sibling(database, 20, 2, HASH_A)
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database, 1) == (2, sha256(f"{HASH_A}|{HASH_A}".encode()).hexdigest())
    assert sibling_state(database, 2) == (1, sha256(HASH_A.encode()).hexdigest())
    database.execute("UPDATE artifact_siblings SET entry_sha = ? WHERE id = 20", [HASH_B])
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database, 2) == (1, sha256(HASH_B.encode()).hexdigest())


@pytest.mark.parametrize("flags", [
    {"composition_fetched": 0}, {"composition_fetched": None},
    {"composition_truncated": 1}, {"composition_truncated": None},
])
def test_incomplete_or_unknown_composition_cannot_be_treated_as_empty(database, flags):
    create_pair(database, **flags)
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database, 1) == (None, None)
    assert sibling_state(database, 2) == (0, sha256(b"").hexdigest())


def test_one_missing_file_hash_makes_the_entire_fingerprint_unknown(database):
    create_pair(database)
    add_sibling(database, 10, 1, HASH_A)
    add_sibling(database, 11, 1, None, name="unresolved.py")
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database, 1) == (None, None)


@pytest.mark.parametrize("invalidate", ["not-fetched", "truncated", "missing-file-hash"])
def test_rerunning_update_clears_stale_fingerprints_when_coverage_is_lost(database, invalidate):
    create_pair(database)
    add_sibling(database, 10, 1, HASH_A)
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database) == (1, sha256(HASH_A.encode()).hexdigest())
    if invalidate == "not-fetched":
        database.execute("UPDATE artifacts SET composition_fetched = 0 WHERE id = 1")
    elif invalidate == "truncated":
        database.execute("UPDATE artifacts SET composition_truncated = 1 WHERE id = 1")
    else:
        database.execute("UPDATE artifact_siblings SET entry_sha = NULL WHERE id = 10")
    run_sql(database, "update_artifact_groupings.sql")
    assert sibling_state(database) == (None, None)


def test_update_is_repeatable_and_summary_agrees_with_rows(database):
    create_pair(database, composition_fetched=0)
    add_artifact(database, 3)
    run_sql(database, "create_analysis_tables.sql")
    add_sibling(database, 30, 3, HASH_A)
    summary = run_sql(database, "update_artifact_groupings.sql").fetchone()
    # Total artifacts, groups, known compositions, known empty, unknown.
    assert summary == (3, 1, 2, 1, 1)
    before = database.execute("SELECT * FROM artifact_groupings ORDER BY artifact_id").fetchall()
    assert run_sql(database, "update_artifact_groupings.sql").fetchone() == summary
    assert database.execute("SELECT * FROM artifact_groupings ORDER BY artifact_id").fetchall() == before


def test_both_scripts_accept_an_empty_source_database(database):
    run_sql(database, "create_analysis_tables.sql")
    assert run_sql(database, "update_artifact_groupings.sql").fetchone() == (0, 0, 0, 0, 0)

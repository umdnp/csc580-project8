"""Family loading retains complete rows while filtering artifact content early."""

import sqlite3
import sys
from types import SimpleNamespace

from gitskills.data.families import DuckDBFamilyRepository


def _database(tmp_path, monkeypatch):
    path = tmp_path / "families.db"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE artifacts (
                id INTEGER, file_sha TEXT, content BLOB, repo_full_name TEXT,
                path TEXT, first_commit_at TEXT
            );
            CREATE TABLE artifact_groupings (
                id INTEGER, artifact_id INTEGER, repo_id INTEGER, name TEXT,
                normalized_description TEXT, sibling_file_count INTEGER,
                sibling_content_sha TEXT
            );
            CREATE TABLE repos (id INTEGER, created_at TEXT);
        """)
        connection.executemany(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?)",
            [
                (10, "sha-10", "Review the code.", "team/one", "a/SKILL.md", "2026-01-01"),
                (20, "sha-20", " \n ", "team/two", "b/SKILL.md", "2026-01-02"),
                (30, "sha-30", None, "team/three", "c/SKILL.md", "2026-01-03"),
                (40, "sha-40", "Read the docs.", "team/other", "d/SKILL.md", "2026-01-04"),
            ],
        )
        connection.executemany(
            "INSERT INTO artifact_groupings VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (20, 20, 2, "alpha", "alpha", 0, "hash-20"),
                (10, 10, 1, "alpha", "alpha", 1, "hash-10"),
                (30, 30, 3, "alpha", "alpha", 0, "hash-30"),
                (15, 10, 1, "alpha", "alpha", 1, "hash-10"),
                (40, 40, 4, "other", "other", 0, None),
                (50, 999, 5, "alpha", "alpha", 0, None),
                (60, None, 6, "alpha", "alpha", 0, None),
            ],
        )
        connection.executemany(
            "INSERT INTO repos VALUES (?, ?)",
            [(1, "2025-01-01"), (2, "2025-02-01")],
        )

    calls = []
    connections = []

    class Connection:
        def __init__(self):
            self.connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            self.closed = False
            connections.append(self)

        def execute(self, query, parameters):
            calls.append((query, parameters))
            if "SELECT DISTINCT artifact_id" in query:
                assert len(parameters) == 1
                return self.connection.execute(query, parameters)

            assert "list_contains(CAST($ids AS BIGINT[]), a.id)" in query
            assert "WHERE g.name = $name" in query
            assert set(parameters) == {"name", "ids"}
            ids = parameters["ids"]
            assert ids == sorted(set(ids))
            placeholders = ", ".join("?" for _ in ids)
            translated = query.replace(
                "list_contains(CAST($ids AS BIGINT[]), a.id)",
                f"a.id IN ({placeholders})",
            ).replace("g.name = $name", "g.name = ?")
            return self.connection.execute(
                translated, [parameters["name"], *ids]
            )

        def close(self):
            self.connection.close()
            self.closed = True

    def connect(database, *, read_only):
        assert database == str(path)
        assert read_only is True
        return Connection()

    monkeypatch.setitem(sys.modules, "duckdb", SimpleNamespace(connect=connect))
    return path, calls, connections


def test_id_filtered_family_load_preserves_rows_and_skips(tmp_path, monkeypatch):
    path, calls, connections = _database(tmp_path, monkeypatch)

    loaded = DuckDBFamilyRepository(path).load_available("alpha")

    assert [(row.group_id, row.artifact_id) for row in loaded.artifacts] == [
        (10, 10), (15, 10)
    ]
    assert loaded.artifacts[0].content == "Review the code."
    assert loaded.artifacts[0].repo_created_at == "2025-01-01"
    assert loaded.artifacts[0].sibling_file_count == 1
    assert [(row.artifact_id, row.reason) for row in loaded.skipped_artifacts] == [
        (20, "empty_content"), (30, "missing_content")
    ]
    assert [(row.repo_full_name, row.path) for row in loaded.skipped_artifacts] == [
        ("team/two", "b/SKILL.md"), ("team/three", "c/SKILL.md")
    ]
    assert len(calls) == 2
    assert calls[1][1] == {"name": "alpha", "ids": [10, 20, 30, 999]}
    assert all(con.closed for con in connections)


def test_load_retains_name_filter_and_missing_family_skips_content_query(
    tmp_path, monkeypatch
):
    path, calls, connections = _database(tmp_path, monkeypatch)
    repo = DuckDBFamilyRepository(path)

    artifacts = repo.load("other")
    assert [(row.group_id, row.artifact_id, row.name) for row in artifacts] == [
        (40, 40, "other")
    ]
    assert calls[1][1] == {"name": "other", "ids": [40]}
    assert repo.load_available("missing").artifacts == ()
    assert repo.load_available("missing").skipped_artifacts == ()
    assert len(calls) == 4  # One ID lookup + content query, then two ID lookups.
    assert all(con.closed for con in connections)

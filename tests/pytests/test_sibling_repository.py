"""Sibling loading fetches metadata before content without changing results."""

import sqlite3
import sys
from types import SimpleNamespace

from gitskills.analysis.family_risk_models import SiblingFile
from gitskills.data.siblings import DuckDBSiblingRepository


def _database(tmp_path, monkeypatch):
    path = tmp_path / "siblings.db"
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE artifact_siblings (
                id INTEGER PRIMARY KEY, artifact_id INTEGER, entry_name TEXT,
                entry_sha TEXT, content BLOB, skipped_reason TEXT,
                entry_type TEXT
            )
        """)
        connection.executemany(
            "INSERT INTO artifact_siblings VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (25, 2, "missing.md", None, None, "not_fetched", "file"),
                (11, 1, "code.sh", "sha-11", "curl https://example.com", None, "file"),
                (12, 1, "binary.dat", "sha-12", b"\x00\xff", None, "file"),
                (5, 1, "folder", None, None, None, "dir"),
                (20, 2, "notes.txt", "sha-20", "Read the docs", None, "file"),
                (31, 3, "other.md", "sha-31", "Not requested", None, "file"),
            ],
        )

    queries = []

    class Connection:
        def __init__(self):
            self.connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

        def execute(self, query, parameters):
            queries.append((query, parameters))
            return self.connection.execute(query, parameters)

        def close(self):
            self.connection.close()

    def connect(database, *, read_only):
        assert database == str(path)
        assert read_only is True
        return Connection()

    monkeypatch.setitem(sys.modules, "duckdb", SimpleNamespace(connect=connect))
    return path, queries


def test_two_stage_sibling_loading_preserves_rows_and_order(tmp_path, monkeypatch):
    path, queries = _database(tmp_path, monkeypatch)

    siblings = DuckDBSiblingRepository(path).load([2, 1, 2])

    assert siblings == (
        SiblingFile(11, 1, "code.sh", "sha-11", "curl https://example.com"),
        SiblingFile(12, 1, "binary.dat", "sha-12", None, "non_text_content"),
        SiblingFile(20, 2, "notes.txt", "sha-20", "Read the docs"),
        SiblingFile(25, 2, "missing.md", None, None, "not_fetched"),
    )
    assert len(queries) == 2
    metadata_sql, _ = queries[0]
    content_sql, _ = queries[1]
    assert "content" not in metadata_sql.lower()
    assert "WHERE id IN" in content_sql
    assert "artifact_id" not in content_sql


def test_no_matching_siblings_skips_content_query(tmp_path, monkeypatch):
    path, queries = _database(tmp_path, monkeypatch)

    assert DuckDBSiblingRepository(path).load([999]) == ()
    assert len(queries) == 1


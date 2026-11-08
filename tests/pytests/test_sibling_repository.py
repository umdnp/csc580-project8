"""Sibling loading preserves content, coverage, and stable ordering."""

import sqlite3
import sys
from types import SimpleNamespace

import pytest

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

        def execute(self, query, parameters=None):
            queries.append((query, parameters))
            assert "list_contains(CAST($ids AS BIGINT[]), artifact_id)" in query
            assert "entry_type = 'file'" in query
            assert set(parameters) == {"ids"}
            ids = parameters["ids"]
            placeholders = ", ".join("?" for _ in ids)
            return self.connection.execute(
                query.replace(
                    "list_contains(CAST($ids AS BIGINT[]), artifact_id)",
                    f"artifact_id IN ({placeholders})",
                ),
                ids,
            )

        def close(self):
            self.connection.close()

    def connect(database, *, read_only):
        assert database == str(path)
        assert read_only is True
        return Connection()

    monkeypatch.setitem(sys.modules, "duckdb", SimpleNamespace(connect=connect))
    return path, queries


def test_parameterized_list_sibling_loading_preserves_rows_and_order(tmp_path, monkeypatch):
    path, queries = _database(tmp_path, monkeypatch)

    siblings = DuckDBSiblingRepository(path).load([2, 1, 2])

    assert siblings == (
        SiblingFile(11, 1, "code.sh", "sha-11", "curl https://example.com"),
        SiblingFile(12, 1, "binary.dat", "sha-12", None, "non_text_content"),
        SiblingFile(20, 2, "notes.txt", "sha-20", "Read the docs"),
        SiblingFile(25, 2, "missing.md", None, None, "not_fetched"),
    )
    assert len(queries) == 1
    query, parameters = queries[0]
    assert "content" in query.lower()
    assert "entry_type = 'file'" in query
    assert "list_contains(CAST($ids AS BIGINT[]), artifact_id)" in query
    assert parameters == {"ids": [1, 2]}


def test_no_matching_siblings_returns_empty_after_parameterized_query(tmp_path, monkeypatch):
    path, queries = _database(tmp_path, monkeypatch)

    assert DuckDBSiblingRepository(path).load([999]) == ()
    assert len(queries) == 1
    assert queries[0][1] == {"ids": [999]}


def test_empty_artifact_ids_skip_database_access(tmp_path, monkeypatch):
    path, queries = _database(tmp_path, monkeypatch)

    assert DuckDBSiblingRepository(path).load([]) == ()
    assert queries == []


def test_parameterized_list_contains_works_in_duckdb(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    path = tmp_path / "sample.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("""
            CREATE TABLE artifact_siblings (
                id BIGINT, artifact_id BIGINT, entry_name VARCHAR,
                entry_sha VARCHAR, content VARCHAR, skipped_reason VARCHAR,
                entry_type VARCHAR
            )
        """)
        connection.executemany(
            "INSERT INTO artifact_siblings VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (7, 2, "notes.txt", "sha-seven", "review", None, "file"),
                (3, 1, "script.sh", "sha-three", None, "not_fetched", "file"),
                (6, 1, "assets", None, None, None, "dir"),
                (9, 3, "ignored.md", "sha-nine", "ignore", None, "file"),
            ],
        )

    assert DuckDBSiblingRepository(path).load([2, 1, 2]) == (
        SiblingFile(3, 1, "script.sh", "sha-three", None, "not_fetched"),
        SiblingFile(7, 2, "notes.txt", "sha-seven", "review"),
    )

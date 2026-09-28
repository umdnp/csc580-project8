"""Synthetic API tests; no project database is required."""

import importlib
import json
import os
import tempfile
import unittest
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

server = importlib.import_module("apps.visualization.app")


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.old_directory = server.REPORT_DIR
        self.old_db = os.environ.get(server.DB_ENV)
        self.old_db_override = server._database_path_override
        server.configure_database_path(None)
        server.REPORT_DIR = self.directory
        server._cached_key = server._cached_report = None
        self.client = TestClient(server.app)
        self.raw = self.family_report()
        self.write("example.json", self.raw)

    def tearDown(self):
        self.client.close()
        server.REPORT_DIR = self.old_directory
        server._cached_key = server._cached_report = None
        if self.old_db is None:
            os.environ.pop(server.DB_ENV, None)
        else:
            os.environ[server.DB_ENV] = self.old_db
        server._database_path_override = self.old_db_override
        self.temp.cleanup()

    @staticmethod
    def family_report():
        return {
            "name": "example-family",
            "policy": {
                "shingle_size": 5,
                "min_containment": 0.8,
                "min_jaccard": 0.3,
                "min_shared_shingles": 5,
                "direction_containment_margin": 0.1,
            },
            "summary": {
                "artifact_count": 4,
                "cluster_count": 1,
                "directed_edge_count": 2,
                "ambiguous_edge_count": 1,
            },
            "family": {
                "artifact_ids": [10, 20, 30, 40],
                "clusters": [
                    {
                        "cluster": 1,
                        "artifact_ids": [10, 20, 30, 40],
                        "evolution": {
                            "root_candidate_artifact_ids": [10, 30],
                            "directed_edges": [
                                {
                                    "source_artifact_id": 10,
                                    "target_artifact_id": 20,
                                    "basis": "containment",
                                    "containment": 0.91,
                                    "jaccard": 0.73,
                                    "shared_shingles": 42,
                                    "change_type": "skill-only",
                                    "evidence": [],
                                    "shared_group_ids": [7],
                                    "same_artifact_group": True,
                                },
                                {
                                    "source_artifact_id": 20,
                                    "target_artifact_id": 40,
                                    "basis": "equivalent-peer-chronology",
                                    "containment": 0.88,
                                    "jaccard": 0.61,
                                    "shared_shingles": 31,
                                    "change_type": "skill+siblings",
                                    "evidence": ["first_commit_at", "equivalent-peer"],
                                    "shared_group_ids": [],
                                    "same_artifact_group": False,
                                    "chronology": {
                                        "target": {
                                            "effective_chronology": "2026-03-01",
                                            "chronology_basis": "equivalent-peer",
                                            "chronology_source_artifact_id": 30,
                                        }
                                    },
                                },
                            ],
                            "ambiguous_edges": [
                                {
                                    "left_artifact_id": 20,
                                    "right_artifact_id": 30,
                                    "basis": "similarity-only",
                                    "containment_left_to_right": 0.95,
                                    "containment_right_to_left": 0.94,
                                    "jaccard": 0.90,
                                    "shared_shingles": 39,
                                    "change_type": "equivalent",
                                    "evidence": [],
                                    "shared_group_ids": [],
                                    "same_artifact_group": False,
                                }
                            ],
                            "related_edges": [
                                {
                                    "source_artifact_id": 30,
                                    "target_artifact_id": 40,
                                    "basis": "containment",
                                    "containment": 0.86,
                                    "jaccard": 0.58,
                                    "shared_shingles": 29,
                                    "change_type": "skill-only",
                                    "evidence": [],
                                    "shared_group_ids": [],
                                    "same_artifact_group": False,
                                }
                            ],
                        },
                    }
                ],
            },
            "groups": [
                {
                    "group_id": 7,
                    "normalized_description": "example description",
                    "artifact_ids": [10, 20],
                    "skill_variant_count": 2,
                    "bundle_variant_count": 2,
                    "family_cluster_numbers": [1],
                }
            ],
            "skill_variants": [
                {"file_sha": "aaa", "artifact_ids": [10], "representative_artifact_id": 10, "earliest_observed_at": "2026-01-01"},
                {"file_sha": "bbb", "artifact_ids": [20], "representative_artifact_id": 20, "earliest_observed_at": "2026-02-01"},
            ],
            "bundle_variants": [
                {"file_sha": "aaa", "sibling_content_sha": "s1", "sibling_state_known": True, "artifact_ids": [10], "representative_artifact_id": 10, "earliest_observed_at": "2026-01-01"},
                {"file_sha": "bbb", "sibling_content_sha": "s2", "sibling_state_known": True, "artifact_ids": [20], "representative_artifact_id": 20, "earliest_observed_at": "2026-02-01"},
            ],
            "provenance": [],
        }

    @staticmethod
    def healthy_status():
        return {
            "path": "/tmp/test.db",
            "source": "default",
            "exists": True,
            "available": True,
            "error": None,
        }

    def write(self, name, payload):
        path = self.directory / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")

    def test_family_graph_includes_all_nodes_and_ambiguous_edges(self):
        summary = self.client.get("/api/reports/example.json/summary").json()
        self.assertEqual(summary["name"], "example-family")
        self.assertEqual((summary["total"], summary["referenced"], summary["directed"], summary["ambiguous"]), (4, 4, 2, 1))

        graph = self.client.get("/api/reports/example.json/clusters/1").json()
        self.assertEqual({node["id"] for node in graph["nodes"]}, {10, 20, 30, 40})
        self.assertEqual((graph["edges"][0]["source"], graph["edges"][0]["target"]), (10, 20))
        chronology_edge = next(edge for edge in graph["edges"] if edge["target"] == 40)
        self.assertEqual(chronology_edge["basis"], "equivalent-peer-chronology")
        self.assertEqual(
            chronology_edge["chronology"]["target"]["chronology_source_artifact_id"],
            30,
        )
        self.assertEqual((graph["ambiguous"][0]["left"], graph["ambiguous"][0]["right"]), (20, 30))
        self.assertEqual((graph["related"][0]["source"], graph["related"][0]["target"]), (30, 40))
        self.assertEqual(graph["roots"], [10, 30])

    def test_compare_to_lists_parent_first_then_ambiguous_peer(self):
        records = {
            10: {"id": 10, "name": "base", "description": "base desc"},
            20: {"id": 20, "name": "derived", "description": "derived desc"},
        }

        def siblings(artifact_id, **_kwargs):
            if artifact_id == 20:
                return [{"artifact_id": 20, "entry_name": "scripts/install.sh", "entry_type": "file", "entry_sha": "s501"}]
            return []

        with (
            patch.object(server, "fetch_artifact_records", return_value=records),
            patch.object(server, "fetch_sibling_records", side_effect=siblings),
            patch.object(server, "database_health", return_value=self.healthy_status()),
        ):
            result = self.client.get("/api/reports/example.json/artifacts/20/details").json()

        self.assertEqual([item["id"] for item in result["comparisons"]], [10, 30])
        self.assertEqual([item["kind"] for item in result["comparisons"]], ["parent", "ambiguous"])
        self.assertEqual(result["comparisons"][0]["label"], "Artifact 10 (parent)")
        self.assertEqual(result["comparisons"][1]["label"], "Artifact 30 (equivalent)")
        self.assertEqual(result["comparison"]["id"], 10)
        self.assertEqual(result["relationship"]["basis"], "containment")
        self.assertEqual(result["artifact"]["artifact_sibling_count"], 1)
        self.assertEqual(result["compare_artifact"]["artifact_sibling_count"], 0)

    def test_related_peer_remains_available_when_also_in_directed_lineage_component(self):
        _, cluster = server._cluster_for_artifact(server.load_report("example.json"), 20)
        cluster["edges"].append(
            {
                "source": 10,
                "target": 30,
                "basis": "containment",
                "containment": 0.89,
                "jaccard": 0.70,
                "shared_shingles": 38,
                "change_type": "skill-only",
                "evidence": [],
                "shared_group_ids": [],
                "same_artifact_group": False,
            }
        )

        candidates = server._comparison_candidates(cluster, 20)

        self.assertEqual([item["id"] for item in candidates], [10, 30])
        self.assertEqual([item["kind"] for item in candidates], ["parent", "ambiguous"])
        self.assertEqual(candidates[1]["label"], "Artifact 30 (equivalent)")

    def test_unselected_related_edge_is_available_for_comparison(self):
        records = {
            30: {"id": 30, "name": "related"},
            40: {"id": 40, "name": "selected"},
        }
        with (
            patch.object(server, "fetch_artifact_records", return_value=records),
            patch.object(server, "fetch_sibling_records", return_value=[]),
            patch.object(server, "database_health", return_value=self.healthy_status()),
        ):
            result = self.client.get(
                "/api/reports/example.json/artifacts/40/details",
                params={"compare_id": 30},
            ).json()

        self.assertEqual(result["comparison"]["id"], 30)
        self.assertEqual(result["comparison"]["kind"], "related")
        self.assertIsNone(result["relationship"])
        self.assertIsNone(result["ambiguous_relationship"])
        self.assertEqual(result["related_relationship"]["source"], 30)
        self.assertEqual(result["related_relationship"]["target"], 40)

    def test_ambiguous_root_can_be_selected_as_compare_target(self):
        records = {
            20: {"id": 20, "name": "peer"},
            30: {"id": 30, "name": "ambiguous-root"},
        }
        with (
            patch.object(server, "fetch_artifact_records", return_value=records),
            patch.object(server, "fetch_sibling_records", return_value=[]),
            patch.object(server, "database_health", return_value=self.healthy_status()),
        ):
            result = self.client.get("/api/reports/example.json/artifacts/30/details").json()

        self.assertTrue(result["root"])
        self.assertEqual(result["comparison"]["id"], 20)
        self.assertEqual(result["comparison"]["kind"], "ambiguous")
        self.assertIsNone(result["relationship"])
        self.assertIsNotNone(result["ambiguous_relationship"])

    def test_artifact_with_no_parent_or_ambiguous_peer_has_no_compare_target(self):
        with (
            patch.object(server, "fetch_artifact_records", return_value={10: {"id": 10, "name": "root"}}),
            patch.object(server, "fetch_sibling_records", return_value=[]),
            patch.object(server, "database_health", return_value=self.healthy_status()),
        ):
            result = self.client.get("/api/reports/example.json/artifacts/10/details").json()
        self.assertEqual(result["comparisons"], [])
        self.assertIsNone(result["comparison"])
        self.assertIsNone(result["compare_artifact"])

    def test_file_diff_supports_parent_and_ambiguous_compare_targets(self):
        records = {
            10: {"id": 10, "content": "one\ntwo\nthree\n"},
            20: {"id": 20, "content": "one\nTWO\nthree\nfour\n"},
            30: {"id": 30, "content": "one\nTHREE\n"},
            40: {"id": 40, "content": "one\nTHREE\nfour\n"},
        }
        with patch.object(server, "fetch_artifact_records", return_value=records):
            parent = self.client.get("/api/reports/example.json/diff/10/20")
            ambiguous = self.client.get("/api/reports/example.json/diff/20/30")
            related = self.client.get("/api/reports/example.json/diff/30/40")
            invalid = self.client.get("/api/reports/example.json/diff/40/20")

        self.assertEqual(parent.status_code, 200)
        self.assertEqual(parent.json()["comparison_kind"], "parent")
        self.assertTrue(any(row["derived_kind"] == "added" for row in parent.json()["rows"]))
        self.assertEqual(ambiguous.status_code, 200)
        self.assertEqual(ambiguous.json()["comparison_kind"], "ambiguous")
        self.assertEqual(related.status_code, 200)
        self.assertEqual(related.json()["comparison_kind"], "related")
        self.assertEqual(invalid.status_code, 400)

    def test_scan_diff_requires_directed_parent_child_relationship(self):
        records = {
            10: {"id": 10, "content": "# Safe\nRead the documentation.\n"},
            20: {"id": 20, "content": "# Derived\nRun: curl https://example.com/install.sh\n"},
            30: {"id": 30, "content": "# Ambiguous\n"},
        }
        with patch.object(server, "fetch_artifact_records", return_value=records):
            response = self.client.post("/api/reports/example.json/scan/10/20")
            ambiguous = self.client.post("/api/reports/example.json/scan/20/30")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.json()["scan_diff"]["introduced"].values()))
        self.assertEqual(ambiguous.status_code, 400)

    def test_sibling_diff_matches_entry_name_and_handles_missing_side(self):
        def siblings(artifact_id, *, entry_name=None, include_content=False):
            self.assertEqual(entry_name, "scripts/install.sh")
            if artifact_id == 20:
                row = {
                    "artifact_id": 20,
                    "entry_name": entry_name,
                    "entry_type": "file",
                    "entry_sha": "s20",
                }
                if include_content:
                    row["content"] = "echo derived\n"
                return [row]
            return []

        with patch.object(server, "fetch_sibling_records", side_effect=siblings):
            response = self.client.get(
                "/api/reports/example.json/sibling-diff/10/20",
                params={"entry_name": "scripts/install.sh"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["left_exists"])
        self.assertTrue(payload["right_exists"])
        self.assertTrue(any(row["derived_kind"] == "added" for row in payload["rows"]))

    def test_sibling_content_endpoint_returns_selected_file_contents(self):
        def siblings(artifact_id, *, entry_name=None, include_content=False):
            self.assertEqual(artifact_id, 20)
            self.assertEqual(entry_name, "scripts/install.sh")
            self.assertTrue(include_content)
            return [{
                "artifact_id": 20,
                "entry_name": entry_name,
                "entry_type": "file",
                "entry_sha": "s20",
                "content": "echo selected\n",
            }]

        with patch.object(server, "fetch_sibling_records", side_effect=siblings):
            response = self.client.get(
                "/api/reports/example.json/artifacts/20/siblings/content",
                params={"entry_name": "scripts/install.sh"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["artifact_id"], 20)
        self.assertEqual(payload["sibling"]["entry_name"], "scripts/install.sh")
        self.assertNotIn("content", payload["sibling"])
        self.assertEqual(payload["content"], "echo selected\n")

    def test_fetch_siblings_only_returns_content_bearing_files(self):
        db_path = self.directory / "siblings.db"
        db_path.touch()

        class FakeConnection:
            def __init__(self):
                self.description = [
                    ("artifact_id",),
                    ("entry_name",),
                    ("entry_type",),
                    ("entry_sha",),
                    ("content",),
                ]
                self.sql = None
                self.parameters = None

            def execute(self, sql, parameters=None):
                self.sql = sql
                self.parameters = parameters
                return self

            def fetchall(self):
                return [(20, "scripts/install.sh", "file", "a")]

            def close(self):
                pass

        connection = FakeConnection()
        fake_duckdb = SimpleNamespace(connect=lambda *_args, **_kwargs: connection)
        with (
            patch.object(server, "database_path", return_value=db_path),
            patch.dict(sys.modules, {"duckdb": fake_duckdb}),
        ):
            rows = server.fetch_sibling_records(20)

        self.assertEqual([row["entry_name"] for row in rows], ["scripts/install.sh"])
        self.assertIn("entry_type = 'file'", connection.sql)
        self.assertIn("content IS NOT NULL", connection.sql)
        self.assertEqual(connection.parameters, [20])


    def test_fetch_artifact_records_adds_history_and_repo_created_metadata(self):
        db_path = self.directory / "artifacts.db"
        db_path.touch()

        class FakeConnection:
            def __init__(self):
                self.description = []
                self.rows = []

            def execute(self, sql, parameters=None):
                if sql == "SELECT * FROM artifacts LIMIT 0":
                    self.description = [
                        ("id",),
                        ("repo_id",),
                        ("name",),
                        ("history_fetched",),
                        ("first_commit_at",),
                        ("last_commit_at",),
                        ("commit_count",),
                    ]
                    self.rows = []
                elif "FROM artifacts WHERE id IN" in sql:
                    self.rows = [(20, 7, "derived", 0, None, None, None)]
                elif sql == "SELECT * FROM repos LIMIT 0":
                    self.description = [("id",), ("created_at",)]
                    self.rows = []
                elif "SELECT id, created_at FROM repos WHERE id IN" in sql:
                    self.rows = [(7, "2024-11-18 13:14:15")]
                else:
                    raise AssertionError(f"Unexpected SQL: {sql}")
                return self

            def fetchall(self):
                return self.rows

            def close(self):
                pass

        connection = FakeConnection()
        fake_duckdb = SimpleNamespace(connect=lambda *_args, **_kwargs: connection)
        with (
            patch.object(server, "database_path", return_value=db_path),
            patch.dict(sys.modules, {"duckdb": fake_duckdb}),
        ):
            records = server.fetch_artifact_records([20])

        self.assertEqual(records[20]["history_fetched"], 0)
        self.assertIsNone(records[20]["first_commit_at"])
        self.assertIsNone(records[20]["last_commit_at"])
        self.assertIsNone(records[20]["commit_count"])
        self.assertEqual(records[20]["repo_created_at"], "2024-11-18 13:14:15")

    def test_artifact_content_endpoint(self):
        artifact_record = {
            20: {
                "id": 20,
                "name": "derived",
                "repo_full_name": "owner/repo",
                "path": ".github/skills/demo/SKILL.md",
                "content": "# Derived\nHello\n",
            }
        }
        with patch.object(server, "fetch_artifact_records", return_value=artifact_record):
            artifact = self.client.get("/api/reports/example.json/artifacts/20/content")
        self.assertEqual(artifact.status_code, 200)
        self.assertEqual(artifact.json()["content"], "# Derived\nHello\n")

    def test_compact_analyze_family_report_is_listed_and_loads_proxy_chronology(self):
        payload = self.family_report()
        for key in ("groups", "skill_variants", "bundle_variants", "provenance"):
            payload.pop(key, None)
        payload["family"].pop("artifact_ids", None)
        payload["chronology_proxies"] = [
            {
                "artifact_id": 20,
                "effective_chronology": "2026-01-15T09:30:00+00:00",
                "chronology_basis": "equivalent-peer",
                "chronology_source_artifact_id": 10,
            }
        ]
        self.write("compact.json", payload)

        listing = self.client.get("/api/reports").json()["reports"]
        self.assertIn("compact.json", listing)

        index = server.build_index(payload)
        proxy = index["artifact_meta"][20]
        self.assertEqual(proxy["effective_chronology"], "2026-01-15T09:30:00+00:00")
        self.assertEqual(proxy["chronology_basis"], "equivalent-peer")
        self.assertEqual(proxy["chronology_source_artifact_id"], 10)

    def test_non_analyze_family_reports_are_rejected_and_hidden_from_listing(self):
        legacy = {"name": "legacy", "artifact_count": 2, "cluster_count": 1, "comparisons": []}
        scan_report = {"candidate_family": "example", "active_rules": [], "summary": {"pairs_analyzed": 1}}
        self.write("legacy.json", legacy)
        self.write("scan.json", scan_report)
        server._cached_key = server._cached_report = None

        self.assertEqual(self.client.get("/api/reports/legacy.json/summary").status_code, 422)
        self.assertEqual(self.client.get("/api/reports/scan.json/summary").status_code, 422)
        self.assertEqual(self.client.get("/api/reports").json()["reports"], ["example.json"])

    def test_search_endpoint_returns_report_scoped_matches(self):
        matches = [{"id": 20, "name": "derived", "repo_full_name": "owner/repo", "path": "skills/demo/SKILL.md", "cluster": 1}]
        with patch.object(server, "search_artifact_records", return_value=matches) as search_records:
            response = self.client.get("/api/reports/example.json/search?q=derived")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["matches"], matches)
        search_records.assert_called_once()

    def test_status_and_health_report_database_availability(self):
        health = {**self.healthy_status(), "path": "C:/data/test.db"}
        with patch.object(server, "database_health", return_value=health):
            status = self.client.get("/api/status")
            check = self.client.get("/api/health")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["database"], health)
        self.assertEqual(check.json()["database"], health)

    def test_database_health_opens_required_tables(self):
        db_path = self.directory / "health.db"
        db_path.touch()

        class FakeConnection:
            def __init__(self):
                self.queries = []

            def execute(self, sql):
                self.queries.append(sql)
                return self

            def fetchone(self):
                return (1,)

            def close(self):
                pass

        connection = FakeConnection()
        fake_duckdb = SimpleNamespace(connect=lambda *_args, **_kwargs: connection)
        with (
            patch.object(server, "database_path", return_value=db_path),
            patch.dict(sys.modules, {"duckdb": fake_duckdb}),
        ):
            result = server.database_health()

        self.assertTrue(result["available"])
        self.assertIsNone(result["error"])
        self.assertEqual(
            connection.queries,
            [
                "SELECT 1 FROM artifacts LIMIT 1",
                "SELECT 1 FROM artifact_siblings LIMIT 1",
                "SELECT 1 FROM repos LIMIT 1",
            ],
        )

    def test_database_path_precedence_is_environment_then_cli_then_default(self):
        os.environ.pop(server.DB_ENV, None)
        server.configure_database_path(None)
        self.assertEqual(str(server.database_path()), server.DEFAULT_DB_PATH)
        self.assertEqual(server.database_source(), "default")

        server.configure_database_path("/tmp/command-line.db")
        self.assertEqual(server.database_path(), Path("/tmp/command-line.db"))
        self.assertEqual(server.database_source(), "--db")

        os.environ[server.DB_ENV] = "/tmp/environment.db"
        self.assertEqual(server.database_path(), Path("/tmp/environment.db"))
        self.assertEqual(server.database_source(), server.DB_ENV)

        server.configure_database_path(None)
        self.assertEqual(server.database_path(), Path("/tmp/environment.db"))

    def test_main_accepts_db_host_and_port_arguments(self):
        fake_uvicorn = SimpleNamespace(run=Mock())
        with (
            patch.dict(os.environ, {}, clear=False),
            patch.dict(sys.modules, {"uvicorn": fake_uvicorn}),
        ):
            os.environ.pop(server.DB_ENV, None)
            server.main(["--db", "/tmp/cli.db", "--host", "127.0.0.2", "--port", "8123"])
            self.assertEqual(server.database_path(), Path("/tmp/cli.db"))

        fake_uvicorn.run.assert_called_once_with(server.app, host="127.0.0.2", port=8123)

    def test_environment_overrides_main_db_argument(self):
        fake_uvicorn = SimpleNamespace(run=Mock())
        with (
            patch.dict(os.environ, {server.DB_ENV: "/tmp/environment.db"}),
            patch.dict(sys.modules, {"uvicorn": fake_uvicorn}),
        ):
            server.main(["--db", "/tmp/cli.db"])
            self.assertEqual(server.database_path(), Path("/tmp/environment.db"))
            self.assertEqual(server.database_source(), server.DB_ENV)

        fake_uvicorn.run.assert_called_once_with(server.app, host="127.0.0.1", port=8000)

    def test_package_exports_fastapi_app(self):
        package = importlib.import_module("apps.visualization")
        self.assertIs(package.app, server.app)

    def test_cache_file_change_path_restrictions_and_home(self):
        server.load_report("example.json")
        with patch.object(server.json, "load", side_effect=AssertionError("reparsed")):
            server.load_report("example.json")

        self.raw["summary"]["artifact_count"] = 10000
        self.write("example.json", self.raw)
        self.assertEqual(server.load_report("example.json")["summary"]["total"], 10000)

        for filename in ["../example.json", "..\\example.json", "example.txt", "C:\\secret.json"]:
            with self.assertRaises(server.HTTPException):
                server.report_path(filename)

        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/api/reports/missing.json/summary").status_code, 404)
        self.assertEqual(self.client.get("/api/reports/example.json/clusters/99").status_code, 404)


if __name__ == "__main__":
    unittest.main()

"""Synthetic API tests; no project database or source content is required."""
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

server = importlib.import_module("visualization.app")


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.old_directory = server.REPORT_DIR
        server.REPORT_DIR = self.directory
        server._cached_key = server._cached_report = None
        self.client = TestClient(server.app)
        self.raw = {
            "artifact_count": 4, "cluster_count": 2,
            "comparisons": [{"cluster": 1, "base": {"artifact_id": 10},
                "derived": {"artifact_id": 20},
                "relationship": {"basis": "chronology", "jaccard": .8},
                "scan_diff": {"rule_match_count": {"delta": 2},
                              "introduced": {"network_access": True}}}],
            "ambiguous_relationships": [{"cluster": 1,
                "left": {"artifact_id": 20}, "right": {"artifact_id": 30}}],
        }
        self.write()

    def tearDown(self):
        self.client.close()
        server.REPORT_DIR = self.old_directory
        server._cached_key = server._cached_report = None
        self.temp.cleanup()

    def write(self):
        (self.directory / "example.json").write_text(json.dumps(self.raw), encoding="utf-8")

    def test_graph_direction_and_ambiguous_counts(self):
        summary = self.client.get("/api/reports/example.json/summary").json()
        self.assertEqual((summary["total"], summary["referenced"], summary["directed"], summary["ambiguous"]), (4, 3, 1, 1))
        graph = self.client.get("/api/reports/example.json/clusters/1").json()
        self.assertEqual(graph["edges"][0][:3], [10, 20, "chronology"])
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual({n["id"]: n["amb"] for n in graph["nodes"]}, {10: 0, 20: 1, 30: 1})
        self.assertEqual(self.client.get("/api/reports/example.json/artifacts/30").json()["c"], 1)
        self.assertEqual(self.client.get("/api/reports/example.json/artifacts/40").status_code, 404)

    def test_cache_and_file_change(self):
        server.load_report("example.json")
        with patch.object(server.json, "load", side_effect=AssertionError("reparsed")):
            server.load_report("example.json")
        self.raw["artifact_count"] = 10000
        self.write()
        self.assertEqual(server.load_report("example.json")["summary"]["total"], 10000)

    def test_invalid_reports_and_missing_files(self):
        for raw in ["{broken", "{}", "[]", '{"artifact_count":0,"cluster_count":0,"comparisons":null,"ambiguous_relationships":[]}']:
            (self.directory / "bad.json").write_text(raw)
            self.assertEqual(self.client.get("/api/reports/bad.json/summary").status_code, 422)
        self.assertEqual(self.client.get("/api/reports/missing.json/summary").status_code, 404)
        self.assertEqual(self.client.get("/api/reports/example.json/clusters/99").status_code, 404)

    def test_path_restrictions(self):
        for filename in ["../example.json", "..\\example.json", "example.txt", "C:\\secret.json"]:
            with self.assertRaises(server.HTTPException):
                server.report_path(filename)

    def test_empty_report_and_home(self):
        self.raw = {"artifact_count": 2, "cluster_count": 2, "comparisons": [], "ambiguous_relationships": []}
        self.write()
        self.assertEqual(self.client.get("/api/reports/example.json/summary").json()["clusters"], [])
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/api/reports").json(), {"reports": ["example.json"]})


if __name__ == "__main__":
    unittest.main()

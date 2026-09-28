"""Local explorer for analyze_family_diffs JSON reports.

From the repository root:
    python -m uvicorn visualization.app:app --host 127.0.0.1 --port 8000

GITSKILLS_REPORT_DIR overrides the default repository work/ directory.
Only compact relationship data is returned; report files are not served directly.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

HERE = Path(__file__).resolve().parent
REPORT_DIR = Path(os.environ.get("GITSKILLS_REPORT_DIR", HERE.parent / "work")).resolve()
app = FastAPI(title="Skill relationship explorer", version="0.1.0")
_lock = Lock()
_cached_key = None
_cached_report = None


def report_path(filename: str) -> Path:
    """Restrict requests to JSON files directly inside the configured directory."""
    if Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Use a report filename, not a path.")
    path = (REPORT_DIR / filename).resolve()
    if path.parent != REPORT_DIR or path.suffix.lower() != ".json":
        raise HTTPException(400, "Only JSON reports in the report directory are allowed.")
    if not path.is_file():
        raise HTTPException(404, "Report not found.")
    return path


def build_index(raw: dict) -> dict:
    """Discard verbose fields and aggregate ambiguous links without inventing direction."""
    if not isinstance(raw, dict) or not all(k in raw for k in (
        "artifact_count", "cluster_count", "comparisons", "ambiguous_relationships"
    )):
        raise ValueError("Expected an analyze_family_diffs report.")
    nodes = {}
    clusters = defaultdict(lambda: {"nodes": {}, "edges": [], "ambiguous": 0})

    def add_node(artifact_id, cluster_id):
        artifact_id, cluster_id = int(artifact_id), int(cluster_id)
        if artifact_id in nodes and nodes[artifact_id]["c"] != cluster_id:
            raise ValueError("An artifact occurs in multiple clusters.")
        node = nodes.setdefault(artifact_id, {"id": artifact_id, "c": cluster_id, "amb": 0})
        clusters[cluster_id]["nodes"][artifact_id] = node
        return node

    for comparison in raw["comparisons"]:
        cluster_id = int(comparison["cluster"])
        source = int(comparison["base"]["artifact_id"])
        target = int(comparison["derived"]["artifact_id"])
        add_node(source, cluster_id)
        add_node(target, cluster_id)
        relationship = comparison["relationship"]
        scan = comparison.get("scan_diff", {})
        clusters[cluster_id]["edges"].append([
            source, target, relationship["basis"],
            relationship.get("jaccard"),
            scan.get("rule_match_count", {}).get("delta"),
            relationship.get("change_type", "unknown"),
            [key for key, value in scan.get("introduced", {}).items() if value],
        ])
    for relationship in raw["ambiguous_relationships"]:
        cluster_id = int(relationship["cluster"])
        add_node(relationship["left"]["artifact_id"], cluster_id)["amb"] += 1
        add_node(relationship["right"]["artifact_id"], cluster_id)["amb"] += 1
        clusters[cluster_id]["ambiguous"] += 1

    summary = {
        "total": int(raw["artifact_count"]),
        "clustersTotal": int(raw["cluster_count"]),
        "directed": len(raw["comparisons"]),
        "ambiguous": len(raw["ambiguous_relationships"]),
        "referenced": len(nodes),
        "clusters": [
            {"id": cid, "n": len(c["nodes"]), "e": len(c["edges"]), "a": c["ambiguous"]}
            for cid, c in sorted(clusters.items(), key=lambda item: (-len(item[1]["edges"]), item[0]))
        ],
    }
    return {"summary": summary, "nodes": nodes, "clusters": dict(clusters)}


def load_report(filename: str) -> dict:
    """One-report cache, refreshed when the file changes; parsing runs off the event loop."""
    global _cached_key, _cached_report
    path = report_path(filename)
    with _lock:
        stat = path.stat()
        key = (path, stat.st_mtime_ns, stat.st_size)
        if key == _cached_key:
            return _cached_report
        try:
            with path.open(encoding="utf-8-sig") as stream:
                result = build_index(json.load(stream))
            after = path.stat()
            if (after.st_mtime_ns, after.st_size) != (stat.st_mtime_ns, stat.st_size):
                raise HTTPException(409, "Report changed while loading. Wait for generation to finish and retry.")
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise HTTPException(422, "Invalid or incomplete family report. Generate it again and retry.") from exc
        except OSError as exc:
            raise HTTPException(503, "Report could not be read. Try again after generation finishes.") from exc
        _cached_key, _cached_report = key, result
        return result


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(HERE / "index.html")


@app.get("/api/reports")
def reports():
    if not REPORT_DIR.is_dir():
        return {"reports": []}
    return {"reports": [p.name for p in sorted(REPORT_DIR.glob("*.json"))
                        if p.is_file() and p.resolve().parent == REPORT_DIR]}


@app.get("/api/reports/{filename}/summary")
def summary(filename: str):
    return load_report(filename)["summary"]


@app.get("/api/reports/{filename}/clusters/{cluster_id}")
def cluster(filename: str, cluster_id: int):
    item = load_report(filename)["clusters"].get(cluster_id)
    if item is None:
        raise HTTPException(404, "Cluster has no listed relationships in this report.")
    return {"nodes": list(item["nodes"].values()), "edges": item["edges"], "ambiguous": item["ambiguous"]}


@app.get("/api/reports/{filename}/artifacts/{artifact_id}")
def artifact(filename: str, artifact_id: int):
    item = load_report(filename)["nodes"].get(artifact_id)
    if item is None:
        raise HTTPException(404, "Artifact ID is not listed in this report's relationships.")
    return item

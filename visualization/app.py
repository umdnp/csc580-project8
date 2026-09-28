"""Local explorer for analyze_family candidate-family JSON reports.

From the repository root:
    python -m uvicorn visualization.app:app --host 127.0.0.1 --port 8000

Reports are always read from visualization/reports. Artifact metadata and content
come from $GITSKILLS_DB when it is set, otherwise from the default project DB.
The application opens DuckDB read-only and never executes artifact content.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from threading import Lock
from typing import Iterable

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gitskills import RiskCategory, SkillAnalyzer, compare_results  # noqa: E402

REPORT_DIR = (HERE / "reports").resolve()
DEFAULT_DB_PATH = r"C:/data/duckdb/agent_skills_release.db"
DB_ENV = "GITSKILLS_DB"

app = FastAPI(title="Skill relationship explorer", version="0.5.0")
_lock = Lock()
_cached_key: tuple[Path, int, int] | None = None
_cached_report: dict | None = None


class DatabaseAccessError(RuntimeError):
    """Raised when artifact data cannot be read from DuckDB."""


def database_path() -> Path:
    """Return the configured GitSkills DuckDB path."""

    value = os.getenv(DB_ENV)
    return Path(value).expanduser() if value else Path(DEFAULT_DB_PATH)


def database_status() -> dict:
    """Describe the configured database path without opening it."""

    path = database_path()
    return {
        "path": str(path),
        "source": DB_ENV if os.getenv(DB_ENV) else "default",
        "exists": path.exists(),
    }


def database_health() -> dict:
    """Return whether the configured DuckDB can serve the viewer's required tables."""

    status = database_status()
    if not status["exists"]:
        return {**status, "available": False, "error": "Database file was not found."}

    try:
        import duckdb
    except ImportError:
        return {**status, "available": False, "error": "duckdb is not installed."}

    connection = None
    try:
        connection = duckdb.connect(str(database_path()), read_only=True)
        connection.execute("SELECT 1 FROM artifacts LIMIT 1").fetchone()
        connection.execute("SELECT 1 FROM artifact_siblings LIMIT 1").fetchone()
        connection.execute("SELECT 1 FROM repos LIMIT 1").fetchone()
    except Exception as exc:  # pragma: no cover - depends on external DB state
        return {**status, "available": False, "error": str(exc)}
    finally:
        if connection is not None:
            connection.close()

    return {**status, "available": True, "error": None}


def report_path(filename: str) -> Path:
    """Restrict requests to JSON files directly inside visualization/reports."""

    if Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Use a report filename, not a path.")
    path = (REPORT_DIR / filename).resolve()
    if path.parent != REPORT_DIR or path.suffix.lower() != ".json":
        raise HTTPException(400, "Only JSON reports in visualization/reports are allowed.")
    if not path.is_file():
        raise HTTPException(404, "Report not found.")
    return path


def build_index(raw: dict) -> dict:
    """Normalize one analyze_family JSON report for the viewer."""

    if not _is_analyze_family_report(raw):
        raise ValueError(
            "Unsupported report format. Expected JSON output from analyze_family."
        )
    return _build_family_index(raw)


def _is_analyze_family_report(raw: object) -> bool:
    """Return whether the object has the analyze_family report structure."""

    if not isinstance(raw, dict):
        return False

    if not isinstance(raw.get("name"), str) or not raw["name"].strip():
        return False
    if not isinstance(raw.get("policy"), dict) or not isinstance(raw.get("summary"), dict):
        return False
    for key in ("groups", "skill_variants", "bundle_variants", "provenance", "chronology_proxies"):
        if key in raw and not isinstance(raw.get(key), list):
            return False

    summary = raw["summary"]
    for key in ("artifact_count", "cluster_count", "directed_edge_count", "ambiguous_edge_count"):
        if key not in summary:
            return False

    family = raw.get("family")
    if not isinstance(family, dict):
        return False
    if not isinstance(family.get("clusters"), list):
        return False
    if "artifact_ids" in family and not isinstance(family.get("artifact_ids"), list):
        return False

    for cluster in family["clusters"]:
        if not isinstance(cluster, dict):
            return False
        if "cluster" not in cluster or not isinstance(cluster.get("artifact_ids"), list):
            return False
        evolution = cluster.get("evolution")
        if not isinstance(evolution, dict):
            return False
        for key in ("root_candidate_artifact_ids", "directed_edges", "ambiguous_edges"):
            if not isinstance(evolution.get(key), list):
                return False

    return True


def _empty_cluster() -> dict:
    return {"nodes": {}, "edges": [], "ambiguous": [], "roots": set()}


def _add_node(nodes: dict[int, dict], clusters: dict[int, dict], artifact_id: object, cluster_id: object) -> dict:
    artifact_id, cluster_id = int(artifact_id), int(cluster_id)
    if artifact_id in nodes and nodes[artifact_id]["c"] != cluster_id:
        raise ValueError(f"Artifact {artifact_id} occurs in multiple family clusters.")
    node = nodes.setdefault(
        artifact_id,
        {"id": artifact_id, "c": cluster_id, "amb": 0, "root": False},
    )
    clusters[cluster_id]["nodes"][artifact_id] = node
    return node


def _normalize_directed_edge(edge: dict) -> dict:
    return {
        "source": int(edge["source_artifact_id"]),
        "target": int(edge["target_artifact_id"]),
        "basis": edge.get("basis", "unknown"),
        "containment": edge.get("containment"),
        "jaccard": edge.get("jaccard"),
        "shared_shingles": edge.get("shared_shingles"),
        "change_type": edge.get("change_type", "unknown"),
        "evidence": list(edge.get("evidence") or []),
        "shared_group_ids": list(edge.get("shared_group_ids") or []),
        "same_artifact_group": bool(edge.get("same_artifact_group", False)),
        "chronology": edge.get("chronology") or None,
    }


def _normalize_ambiguous_edge(edge: dict) -> dict:
    return {
        "left": int(edge["left_artifact_id"]),
        "right": int(edge["right_artifact_id"]),
        "basis": edge.get("basis", "similarity-only"),
        "containment_left_to_right": edge.get("containment_left_to_right"),
        "containment_right_to_left": edge.get("containment_right_to_left"),
        "jaccard": edge.get("jaccard"),
        "shared_shingles": edge.get("shared_shingles"),
        "change_type": edge.get("change_type", "unknown"),
        "evidence": list(edge.get("evidence") or []),
        "shared_group_ids": list(edge.get("shared_group_ids") or []),
        "same_artifact_group": bool(edge.get("same_artifact_group", False)),
    }


def _family_artifact_metadata(raw: dict) -> dict[int, dict]:
    metadata: dict[int, dict] = defaultdict(dict)

    for group in raw.get("groups") or []:
        for artifact_id in group.get("artifact_ids") or []:
            metadata[int(artifact_id)].update(
                {
                    "group_id": group.get("group_id"),
                    "normalized_description": group.get("normalized_description"),
                }
            )

    for variant in raw.get("skill_variants") or []:
        for artifact_id in variant.get("artifact_ids") or []:
            metadata[int(artifact_id)].update(
                {
                    "file_sha": variant.get("file_sha"),
                    "skill_variant_earliest_observed_at": variant.get("earliest_observed_at"),
                    "skill_variant_representative": (
                        int(artifact_id) == variant.get("representative_artifact_id")
                    ),
                }
            )

    for variant in raw.get("bundle_variants") or []:
        for artifact_id in variant.get("artifact_ids") or []:
            metadata[int(artifact_id)].update(
                {
                    "sibling_content_sha": variant.get("sibling_content_sha"),
                    "sibling_state_known": variant.get("sibling_state_known"),
                    "bundle_variant_earliest_observed_at": variant.get("earliest_observed_at"),
                    "bundle_variant_representative": (
                        int(artifact_id) == variant.get("representative_artifact_id")
                    ),
                }
            )

    for provenance in raw.get("provenance") or []:
        artifact_id = provenance.get("artifact_id")
        if artifact_id is not None:
            metadata[int(artifact_id)]["declared_provenance"] = {
                key: value for key, value in provenance.items() if key != "artifact_id"
            }

    for proxy in raw.get("chronology_proxies") or []:
        artifact_id = proxy.get("artifact_id")
        if artifact_id is not None:
            metadata[int(artifact_id)].update(
                {
                    "effective_chronology": proxy.get("effective_chronology"),
                    "chronology_basis": proxy.get("chronology_basis"),
                    "chronology_source_artifact_id": proxy.get(
                        "chronology_source_artifact_id"
                    ),
                }
            )

    for artifact in raw.get("artifacts") or []:
        artifact_id = artifact.get("artifact_id")
        if artifact_id is not None:
            metadata[int(artifact_id)].update(
                {key: value for key, value in artifact.items() if key != "artifact_id"}
            )

    return dict(metadata)


def _build_family_index(raw: dict) -> dict:
    nodes: dict[int, dict] = {}
    clusters: dict[int, dict] = defaultdict(_empty_cluster)
    artifact_meta = _family_artifact_metadata(raw)

    for cluster in raw["family"]["clusters"]:
        cluster_id = int(cluster["cluster"])
        for artifact_id in cluster.get("artifact_ids") or []:
            _add_node(nodes, clusters, artifact_id, cluster_id)

        evolution = cluster.get("evolution") or {}
        for root_id in evolution.get("root_candidate_artifact_ids") or []:
            node = _add_node(nodes, clusters, root_id, cluster_id)
            node["root"] = True
            clusters[cluster_id]["roots"].add(int(root_id))

        for edge in evolution.get("directed_edges") or []:
            normalized = _normalize_directed_edge(edge)
            _add_node(nodes, clusters, normalized["source"], cluster_id)
            _add_node(nodes, clusters, normalized["target"], cluster_id)
            clusters[cluster_id]["edges"].append(normalized)

        for edge in evolution.get("ambiguous_edges") or []:
            normalized = _normalize_ambiguous_edge(edge)
            _add_node(nodes, clusters, normalized["left"], cluster_id)["amb"] += 1
            _add_node(nodes, clusters, normalized["right"], cluster_id)["amb"] += 1
            clusters[cluster_id]["ambiguous"].append(normalized)

    report_summary = raw.get("summary") or {}
    total = int(report_summary.get("artifact_count", len(nodes)))
    cluster_total = int(report_summary.get("cluster_count", len(clusters)))
    directed = int(report_summary.get("directed_edge_count", sum(len(c["edges"]) for c in clusters.values())))
    ambiguous = int(report_summary.get("ambiguous_edge_count", sum(len(c["ambiguous"]) for c in clusters.values())))
    summary = _summary(
        raw.get("name") or "candidate family",
        total,
        cluster_total,
        directed,
        ambiguous,
        nodes,
        clusters,
        raw.get("policy"),
    )
    return {
        "summary": summary,
        "nodes": nodes,
        "clusters": dict(clusters),
        "artifact_meta": artifact_meta,
    }


def _summary(
    name: str,
    total: int,
    cluster_total: int,
    directed: int,
    ambiguous: int,
    nodes: dict[int, dict],
    clusters: dict[int, dict],
    policy: dict | None,
) -> dict:
    return {
        "name": name,
        "reportType": "analyze_family",
        "total": total,
        "clustersTotal": cluster_total,
        "directed": directed,
        "ambiguous": ambiguous,
        "referenced": len(nodes),
        "policy": policy or {},
        "clusters": [
            {
                "id": cluster_id,
                "n": len(cluster["nodes"]),
                "e": len(cluster["edges"]),
                "a": len(cluster["ambiguous"]),
                "r": len(cluster["roots"]),
            }
            for cluster_id, cluster in sorted(
                clusters.items(),
                key=lambda item: (-len(item[1]["edges"]), item[0]),
            )
        ],
    }


def _is_valid_report_file(path: Path) -> bool:
    """Return whether a JSON file is a loadable analyze_family report."""

    try:
        with path.open(encoding="utf-8-sig") as stream:
            build_index(json.load(stream))
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
    ):
        return False
    return True


def load_report(filename: str) -> dict:
    """Load and cache one normalized report, refreshing when the file changes."""

    global _cached_key, _cached_report
    path = report_path(filename)
    with _lock:
        stat = path.stat()
        key = (path, stat.st_mtime_ns, stat.st_size)
        if key == _cached_key and _cached_report is not None:
            return _cached_report
        try:
            with path.open(encoding="utf-8-sig") as stream:
                result = build_index(json.load(stream))
            after = path.stat()
            if (after.st_mtime_ns, after.st_size) != (stat.st_mtime_ns, stat.st_size):
                raise HTTPException(
                    409,
                    "Report changed while loading. Wait for generation to finish and retry.",
                )
        except json.JSONDecodeError as exc:
            raise HTTPException(422, "Report is not valid JSON.") from exc
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise HTTPException(422, str(exc)) from exc
        except OSError as exc:
            raise HTTPException(503, "Report could not be read. Try again after generation finishes.") from exc
        _cached_key, _cached_report = key, result
        return result


def _artifact_columns(connection) -> set[str]:
    try:
        cursor = connection.execute("SELECT * FROM artifacts LIMIT 0")
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Unable to inspect artifacts table: {exc}") from exc
    return {column[0] for column in cursor.description}


_ARTIFACT_FIELDS = (
    "id",
    "repo_id",
    "repo_full_name",
    "path",
    "filename",
    "location_class",
    "file_sha",
    "discovered_at",
    "content_fetched",
    "frontmatter_valid",
    "name",
    "description",
    "body_chars",
    "dedup_primary",
    "history_fetched",
    "first_commit_at",
    "last_commit_at",
    "commit_count",
    "content_sha_ok",
    "composition_truncated",
    "first_commit_author",
    "first_commit_type",
    "first_commit_message",
    "last_commit_author",
    "last_commit_type",
    "last_commit_message",
)


def fetch_artifact_records(
    artifact_ids: Iterable[int],
    *,
    include_content: bool = False,
) -> dict[int, dict]:
    """Read selected artifact rows from DuckDB without mutating the database."""

    ids = tuple(sorted({int(value) for value in artifact_ids}))
    if not ids:
        return {}

    database = database_path()
    if not database.exists():
        source = f"${DB_ENV}" if os.getenv(DB_ENV) else "default path"
        raise DatabaseAccessError(f"DuckDB database not found at {database} ({source}).")

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment failure
        raise DatabaseAccessError("duckdb is not installed for the visualization app.") from exc

    try:
        connection = duckdb.connect(str(database), read_only=True)
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Failed to open DuckDB database {database}: {exc}") from exc

    try:
        available = _artifact_columns(connection)
        fields = [field for field in _ARTIFACT_FIELDS if field in available]
        if include_content and "content" in available:
            fields.append("content")
        if "id" not in fields:
            raise DatabaseAccessError("The artifacts table does not contain the expected id column.")
        if include_content and "content" not in fields:
            raise DatabaseAccessError("The artifacts table does not contain artifact content.")

        quoted = ", ".join(f'"{field}"' for field in fields)
        placeholders = ", ".join("?" for _ in ids)
        query = f"SELECT {quoted} FROM artifacts WHERE id IN ({placeholders})"
        rows = connection.execute(query, list(ids)).fetchall()

        records = {}
        for row in rows:
            record = {field: _json_value(value) for field, value in zip(fields, row)}
            records[int(record["id"])] = record

        # Repository creation time is useful context for ancestry, but it is
        # repository-level metadata rather than an artifact field. Treat it as
        # optional so older/incomplete databases still return artifact details.
        repo_ids = sorted(
            {
                int(record["repo_id"])
                for record in records.values()
                if record.get("repo_id") is not None
            }
        )
        if repo_ids:
            try:
                repo_cursor = connection.execute("SELECT * FROM repos LIMIT 0")
                repo_columns = {column[0] for column in repo_cursor.description}
                if {"id", "created_at"}.issubset(repo_columns):
                    repo_placeholders = ", ".join("?" for _ in repo_ids)
                    repo_rows = connection.execute(
                        f"SELECT id, created_at FROM repos WHERE id IN ({repo_placeholders})",
                        repo_ids,
                    ).fetchall()
                    repo_created = {
                        int(repo_id): _json_value(created_at)
                        for repo_id, created_at in repo_rows
                    }
                    for record in records.values():
                        repo_id = record.get("repo_id")
                        if repo_id is not None:
                            record["repo_created_at"] = repo_created.get(int(repo_id))
            except Exception:
                # Keep artifact metadata usable even when repository metadata is
                # unavailable. The UI will display Repo created as Unknown.
                pass

        # Grouping metadata is stored separately from artifacts. Load it lazily
        # so compact analyze_family reports do not need to repeat this data.
        try:
            grouping_cursor = connection.execute(
                "SELECT * FROM artifact_groupings LIMIT 0"
            )
            grouping_columns = {column[0] for column in grouping_cursor.description}
            grouping_fields = [
                field
                for field in (
                    "id",
                    "artifact_id",
                    "sibling_file_count",
                    "sibling_content_sha",
                )
                if field in grouping_columns
            ]
            if {"id", "artifact_id"}.issubset(grouping_fields):
                grouping_quoted = ", ".join(f'"{field}"' for field in grouping_fields)
                grouping_placeholders = ", ".join("?" for _ in ids)
                grouping_rows = connection.execute(
                    f"SELECT {grouping_quoted} FROM artifact_groupings "
                    f"WHERE artifact_id IN ({grouping_placeholders})",
                    list(ids),
                ).fetchall()
                for row in grouping_rows:
                    grouping = {
                        field: _json_value(value)
                        for field, value in zip(grouping_fields, row)
                    }
                    artifact_id = int(grouping["artifact_id"])
                    record = records.get(artifact_id)
                    if record is None:
                        continue
                    record["group_id"] = grouping.get("id")
                    if "sibling_file_count" in grouping:
                        record["sibling_file_count"] = grouping.get(
                            "sibling_file_count"
                        )
                    if "sibling_content_sha" in grouping:
                        record["sibling_content_sha"] = grouping.get(
                            "sibling_content_sha"
                        )
        except Exception:
            # Older databases may not contain the project-derived grouping table.
            pass

        return records
    except DatabaseAccessError:
        raise
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Unable to query artifacts table: {exc}") from exc
    finally:
        connection.close()


def fetch_sibling_records(
    artifact_id: int,
    *,
    entry_name: str | None = None,
    include_content: bool = False,
) -> list[dict]:
    """Read content-bearing file siblings for one artifact from DuckDB."""

    database = database_path()
    if not database.exists():
        source = f"${DB_ENV}" if os.getenv(DB_ENV) else "default path"
        raise DatabaseAccessError(f"DuckDB database not found at {database} ({source}).")

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment failure
        raise DatabaseAccessError("duckdb is not installed for the visualization app.") from exc

    try:
        connection = duckdb.connect(str(database), read_only=True)
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Failed to open DuckDB database {database}: {exc}") from exc

    try:
        cursor = connection.execute("SELECT * FROM artifact_siblings LIMIT 0")
        available = {column[0] for column in cursor.description}
        required = {"artifact_id", "entry_name", "entry_type", "content"}
        if not required.issubset(available):
            missing = ", ".join(sorted(required - available))
            raise DatabaseAccessError(
                f"The artifact_siblings table is missing expected columns: {missing}."
            )

        candidate_fields = [
            "artifact_id",
            "entry_name",
            "entry_type",
            "entry_sha",
        ]
        fields = [field for field in candidate_fields if field in available]
        if include_content:
            fields.append("content")

        selections = [f'"{field}"' for field in fields]
        conditions = ["artifact_id = ?", "entry_type = 'file'", "content IS NOT NULL"]
        parameters: list[object] = [int(artifact_id)]
        if entry_name is not None:
            conditions.append("entry_name = ?")
            parameters.append(entry_name)

        query = (
            f"SELECT {', '.join(selections)} FROM artifact_siblings "
            f"WHERE {' AND '.join(conditions)} ORDER BY entry_name"
        )
        rows = connection.execute(query, parameters).fetchall()
    except DatabaseAccessError:
        raise
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Unable to query artifact_siblings table: {exc}") from exc
    finally:
        connection.close()

    return [
        {field: _json_value(value) for field, value in zip(fields, row)}
        for row in rows
    ]


def search_artifact_records(report: dict, query_text: str, limit: int = 25) -> list[dict]:
    """Search report artifacts by ID, name, repository, path, filename, or SHA."""

    artifact_ids = tuple(sorted(report["nodes"]))
    if not artifact_ids:
        return []

    database = database_path()
    if not database.exists():
        source = f"${DB_ENV}" if os.getenv(DB_ENV) else "default path"
        raise DatabaseAccessError(f"DuckDB database not found at {database} ({source}).")

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment failure
        raise DatabaseAccessError("duckdb is not installed for the visualization app.") from exc

    try:
        connection = duckdb.connect(str(database), read_only=True)
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Failed to open DuckDB database {database}: {exc}") from exc

    try:
        available = _artifact_columns(connection)
        result_fields = [
            field
            for field in ("id", "name", "repo_full_name", "path", "filename", "file_sha", "last_commit_at")
            if field in available
        ]
        if "id" not in result_fields:
            raise DatabaseAccessError("The artifacts table does not contain the expected id column.")

        searchable = [
            field
            for field in ("name", "repo_full_name", "path", "filename", "file_sha")
            if field in available
        ]
        terms = []
        parameters: list[object] = list(artifact_ids)
        text = query_text.strip()
        if text.isdigit():
            terms.append("id = ?")
            parameters.append(int(text))
        lowered = f"%{text.lower()}%"
        for field in searchable:
            terms.append(f"lower(coalesce(CAST(\"{field}\" AS VARCHAR), '')) LIKE ?")
            parameters.append(lowered)
        if not terms:
            return []

        id_placeholders = ", ".join("?" for _ in artifact_ids)
        quoted = ", ".join(f'"{field}"' for field in result_fields)
        order_fields = [
            field for field in ("name", "repo_full_name", "path", "id") if field in available
        ]
        order_by = ", ".join(
            f'"{field}" NULLS LAST' if field != "id" else '"id"'
            for field in order_fields
        )
        sql = (
            f"SELECT {quoted} FROM artifacts "
            f"WHERE id IN ({id_placeholders}) AND ({' OR '.join(terms)}) "
            f"ORDER BY {order_by} LIMIT ?"
        )
        parameters.append(max(1, min(int(limit), 100)))
        rows = connection.execute(sql, parameters).fetchall()
    except DatabaseAccessError:
        raise
    except Exception as exc:  # pragma: no cover - depends on external DB state
        raise DatabaseAccessError(f"Unable to search artifacts table: {exc}") from exc
    finally:
        connection.close()

    results = []
    for row in rows:
        record = {field: _json_value(value) for field, value in zip(result_fields, row)}
        artifact_id = int(record["id"])
        node = report["nodes"][artifact_id]
        record["cluster"] = node["c"]
        results.append(record)
    return results


def _json_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _merge_artifact_metadata(report: dict, artifact_id: int, database: dict | None) -> dict:
    merged = {"id": artifact_id}
    merged.update(report.get("artifact_meta", {}).get(artifact_id, {}))
    if database:
        merged.update(database)
    merged.pop("content", None)
    return {key: _json_value(value) for key, value in merged.items()}


def _cluster_for_artifact(report: dict, artifact_id: int) -> tuple[dict, dict]:
    node = report["nodes"].get(artifact_id)
    if node is None:
        raise HTTPException(404, "Artifact ID is not listed in this report.")
    return node, report["clusters"][node["c"]]


def _parents(cluster: dict, artifact_id: int) -> list[dict]:
    return sorted(
        (edge for edge in cluster["edges"] if edge["target"] == artifact_id),
        key=lambda edge: (edge["source"], edge["basis"]),
    )


def _children(cluster: dict, artifact_id: int) -> list[dict]:
    return sorted(
        (edge for edge in cluster["edges"] if edge["source"] == artifact_id),
        key=lambda edge: (edge["target"], edge["basis"]),
    )


def _ambiguous_for(cluster: dict, artifact_id: int) -> list[dict]:
    return sorted(
        (
            edge
            for edge in cluster["ambiguous"]
            if artifact_id in (edge["left"], edge["right"])
        ),
        key=lambda edge: (edge["left"], edge["right"]),
    )


def _comparison_candidates(cluster: dict, artifact_id: int) -> list[dict]:
    """Return parent comparisons first, then undirected peer relationships."""

    parents = _parents(cluster, artifact_id)

    lineage_peers: set[int] = set()
    queue = [artifact_id]
    while queue:
        current = queue.pop()
        for edge in _parents(cluster, current):
            peer = edge["source"]
            if peer not in lineage_peers and peer != artifact_id:
                lineage_peers.add(peer)
                queue.append(peer)
        for edge in _children(cluster, current):
            peer = edge["target"]
            if peer not in lineage_peers and peer != artifact_id:
                lineage_peers.add(peer)
                queue.append(peer)

    candidates = [
        {
            "id": edge["source"],
            "kind": "parent",
            "label": f"Artifact {edge['source']} (parent)",
            "relationship": edge,
        }
        for edge in parents
    ]
    for edge in _ambiguous_for(cluster, artifact_id):
        peer = edge["right"] if edge["left"] == artifact_id else edge["left"]
        if peer in lineage_peers:
            continue
        peer_type = (
            "equivalent"
            if edge.get("change_type") == "equivalent"
            else "related"
        )
        candidates.append(
            {
                "id": peer,
                "kind": "ambiguous",
                "label": f"Artifact {peer} ({peer_type})",
                "relationship": edge,
            }
        )
    return candidates


def _comparison_for(report: dict, compare_id: int, selected_id: int) -> dict:
    _, cluster = _cluster_for_artifact(report, selected_id)
    for candidate in _comparison_candidates(cluster, selected_id):
        if candidate["id"] == compare_id:
            return candidate
    raise HTTPException(400, "The selected artifact is not an available comparison target.")


def _directed_relationship(report: dict, source: int, target: int) -> dict:
    target_node, cluster = _cluster_for_artifact(report, target)
    source_node = report["nodes"].get(source)
    if source_node is None or source_node["c"] != target_node["c"]:
        raise HTTPException(400, "Base and derived artifacts are not in the same report cluster.")
    for edge in cluster["edges"]:
        if edge["source"] == source and edge["target"] == target:
            return edge
    raise HTTPException(
        400,
        "The selected pair is not a directed parent-child relationship in this report. "
        "Peer relationships cannot be scanned without a direction.",
    )


def _require_contents(source: int, target: int) -> tuple[str, str, dict[int, dict]]:
    try:
        records = fetch_artifact_records((source, target), include_content=True)
    except DatabaseAccessError as exc:
        raise HTTPException(503, str(exc)) from exc
    missing = [artifact_id for artifact_id in (source, target) if artifact_id not in records]
    if missing:
        raise HTTPException(404, f"Artifact IDs not found in DuckDB: {', '.join(map(str, missing))}")
    base_content = records[source].get("content")
    derived_content = records[target].get("content")
    if not isinstance(base_content, str) or not isinstance(derived_content, str):
        raise HTTPException(422, "Artifact content is unavailable for the selected pair.")
    return base_content, derived_content, records


def build_side_by_side_diff(base_text: str, derived_text: str) -> list[dict]:
    """Create aligned, line-level diff rows for two artifact bodies."""

    base_lines = base_text.splitlines()
    derived_lines = derived_text.splitlines()
    matcher = SequenceMatcher(a=base_lines, b=derived_lines, autojunk=False)
    rows: list[dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        left = base_lines[i1:i2]
        right = derived_lines[j1:j2]
        width = max(len(left), len(right))
        for offset in range(width):
            left_present = offset < len(left)
            right_present = offset < len(right)
            if tag == "equal":
                base_kind = derived_kind = "equal"
            elif tag == "delete":
                base_kind, derived_kind = "removed", "empty"
            elif tag == "insert":
                base_kind, derived_kind = "empty", "added"
            else:
                base_kind = "changed" if left_present else "empty"
                derived_kind = "changed" if right_present else "empty"

            rows.append(
                {
                    "base_line": i1 + offset + 1 if left_present else None,
                    "base_text": left[offset] if left_present else "",
                    "base_kind": base_kind,
                    "derived_line": j1 + offset + 1 if right_present else None,
                    "derived_text": right[offset] if right_present else "",
                    "derived_kind": derived_kind,
                }
            )

    return rows


def _safe_rule_match(rule_match) -> dict:
    text = rule_match.matched_text or ""
    if rule_match.category is RiskCategory.CREDENTIAL_ACCESS:
        text = "[credential-related content redacted]"
    else:
        text = " ".join(text.split())
        if len(text) > 180:
            text = f"{text[:177]}..."
    return {
        "rule_id": rule_match.rule_id,
        "category": rule_match.category.value,
        "description": rule_match.message,
        "line_number": rule_match.line_number,
        "matched_text": text,
    }


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(HERE / "index.html")


@app.get("/api/status")
def status():
    return {"database": database_health(), "report_directory": str(REPORT_DIR)}


@app.get("/api/health")
def health():
    return {"database": database_health()}


@app.get("/api/reports")
def reports():
    if not REPORT_DIR.is_dir():
        return {"reports": []}

    valid_reports = []
    for path in sorted(REPORT_DIR.glob("*.json")):
        if (
            path.is_file()
            and path.resolve().parent == REPORT_DIR
            and _is_valid_report_file(path)
        ):
            valid_reports.append(path.name)
    return {"reports": valid_reports}


@app.get("/api/reports/{filename}/summary")
def summary(filename: str):
    return load_report(filename)["summary"]


@app.get("/api/reports/{filename}/clusters/{cluster_id}")
def cluster(filename: str, cluster_id: int):
    item = load_report(filename)["clusters"].get(cluster_id)
    if item is None:
        raise HTTPException(404, "Cluster not found in this report.")
    return {
        "nodes": list(item["nodes"].values()),
        "edges": item["edges"],
        "ambiguous": item["ambiguous"],
        "roots": sorted(item["roots"]),
    }


@app.get("/api/reports/{filename}/artifacts/{artifact_id}")
def artifact(filename: str, artifact_id: int):
    item = load_report(filename)["nodes"].get(artifact_id)
    if item is None:
        raise HTTPException(404, "Artifact ID is not listed in this report.")
    return item


@app.get("/api/reports/{filename}/artifacts/{artifact_id}/details")
def artifact_details(
    filename: str,
    artifact_id: int,
    compare_id: int | None = Query(default=None),
):
    report = load_report(filename)
    node, cluster_item = _cluster_for_artifact(report, artifact_id)
    parents = _parents(cluster_item, artifact_id)
    children = _children(cluster_item, artifact_id)
    ambiguous = _ambiguous_for(cluster_item, artifact_id)
    comparisons = _comparison_candidates(cluster_item, artifact_id)

    selected_comparison = None
    if comparisons:
        if compare_id is None:
            selected_comparison = comparisons[0]
        else:
            selected_comparison = next(
                (item for item in comparisons if item["id"] == compare_id),
                None,
            )
            if selected_comparison is None:
                raise HTTPException(400, "Selected artifact is not available in Compare To.")
    elif compare_id is not None:
        raise HTTPException(400, "This artifact has no available comparison target.")

    ids = [artifact_id]
    if selected_comparison is not None:
        ids.append(selected_comparison["id"])

    database_errors = []
    try:
        records = fetch_artifact_records(ids)
    except DatabaseAccessError as exc:
        records = {}
        database_errors.append(str(exc))

    siblings = []
    siblings_error = None
    try:
        siblings = fetch_sibling_records(artifact_id)
    except DatabaseAccessError as exc:
        siblings_error = str(exc)
        database_errors.append(siblings_error)

    compare_siblings = []
    if selected_comparison is not None:
        try:
            compare_siblings = fetch_sibling_records(selected_comparison["id"])
        except DatabaseAccessError as exc:
            database_errors.append(str(exc))

    artifact_record = _merge_artifact_metadata(report, artifact_id, records.get(artifact_id))
    artifact_record["artifact_sibling_count"] = len(siblings)

    compare_record = None
    if selected_comparison is not None:
        compare_artifact_id = selected_comparison["id"]
        compare_record = _merge_artifact_metadata(
            report, compare_artifact_id, records.get(compare_artifact_id)
        )
        compare_record["artifact_sibling_count"] = len(compare_siblings)

    directed_relationship = (
        selected_comparison["relationship"]
        if selected_comparison is not None and selected_comparison["kind"] == "parent"
        else None
    )
    ambiguous_relationship = (
        selected_comparison["relationship"]
        if selected_comparison is not None and selected_comparison["kind"] == "ambiguous"
        else None
    )

    health = (
        {**database_status(), "available": True, "error": None}
        if not database_errors
        else {
            **database_status(),
            "available": False,
            "error": " | ".join(dict.fromkeys(database_errors)),
        }
    )

    return {
        "artifact": artifact_record,
        "compare_artifact": compare_record,
        "comparison": selected_comparison,
        "relationship": directed_relationship,
        "ambiguous_relationship": ambiguous_relationship,
        "parents": parents,
        "children": children,
        "ambiguous": ambiguous,
        "comparisons": comparisons,
        "siblings": siblings,
        "siblings_error": siblings_error,
        "root": bool(node.get("root")),
        "counts": {
            "parents": len(parents),
            "children": len(children),
            "ambiguous": len(ambiguous),
            "siblings": len(siblings),
        },
        "database": health,
    }


@app.get("/api/reports/{filename}/artifacts/{artifact_id}/content")
def artifact_content(filename: str, artifact_id: int):
    report = load_report(filename)
    _cluster_for_artifact(report, artifact_id)
    try:
        records = fetch_artifact_records((artifact_id,), include_content=True)
    except DatabaseAccessError as exc:
        raise HTTPException(503, str(exc)) from exc
    record = records.get(artifact_id)
    if record is None:
        raise HTTPException(404, f"Artifact ID {artifact_id} was not found in DuckDB.")
    content = record.get("content")
    if not isinstance(content, str):
        raise HTTPException(422, "Artifact content is unavailable for the selected artifact.")
    return {
        "artifact": _merge_artifact_metadata(report, artifact_id, record),
        "content": content,
    }


@app.get("/api/reports/{filename}/artifacts/{artifact_id}/siblings/content")
def sibling_content(
    filename: str,
    artifact_id: int,
    entry_name: str = Query(min_length=1),
):
    report = load_report(filename)
    _cluster_for_artifact(report, artifact_id)
    try:
        rows = fetch_sibling_records(
            artifact_id, entry_name=entry_name, include_content=True
        )
    except DatabaseAccessError as exc:
        raise HTTPException(503, str(exc)) from exc

    if not rows:
        raise HTTPException(404, f"Sibling file {entry_name!r} was not found for artifact {artifact_id}.")

    sibling = rows[0]
    content = sibling.get("content")
    if not isinstance(content, str):
        raise HTTPException(422, "Sibling file content is unavailable.")

    return {
        "artifact_id": artifact_id,
        "sibling": {key: value for key, value in sibling.items() if key != "content"},
        "content": content,
    }


@app.get("/api/reports/{filename}/search")
def search(filename: str, q: str = Query(min_length=1), limit: int = Query(default=25, ge=1, le=100)):
    report = load_report(filename)
    try:
        matches = search_artifact_records(report, q, limit)
    except DatabaseAccessError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"matches": matches}


@app.get("/api/reports/{filename}/diff/{compare_id}/{selected_id}")
def artifact_diff(filename: str, compare_id: int, selected_id: int):
    report = load_report(filename)
    comparison = _comparison_for(report, compare_id, selected_id)
    left_text, right_text, _ = _require_contents(compare_id, selected_id)
    return {
        "left_id": compare_id,
        "right_id": selected_id,
        "comparison_kind": comparison["kind"],
        "relationship": comparison["relationship"],
        "rows": build_side_by_side_diff(left_text, right_text),
    }


@app.get("/api/reports/{filename}/sibling-diff/{compare_id}/{selected_id}")
def sibling_diff(
    filename: str,
    compare_id: int,
    selected_id: int,
    entry_name: str = Query(min_length=1),
):
    report = load_report(filename)
    comparison = _comparison_for(report, compare_id, selected_id)

    try:
        left_rows = fetch_sibling_records(compare_id, entry_name=entry_name, include_content=True)
        right_rows = fetch_sibling_records(selected_id, entry_name=entry_name, include_content=True)
    except DatabaseAccessError as exc:
        raise HTTPException(503, str(exc)) from exc

    left_sibling = left_rows[0] if left_rows else None
    right_sibling = right_rows[0] if right_rows else None
    left_content = left_sibling.get("content") if left_sibling else None
    right_content = right_sibling.get("content") if right_sibling else None

    if left_content is not None and not isinstance(left_content, str):
        left_content = str(left_content)
    if right_content is not None and not isinstance(right_content, str):
        right_content = str(right_content)

    return {
        "entry_name": entry_name,
        "left_id": compare_id,
        "right_id": selected_id,
        "comparison_kind": comparison["kind"],
        "left_exists": left_sibling is not None,
        "right_exists": right_sibling is not None,
        "left_sibling": {k: v for k, v in (left_sibling or {}).items() if k != "content"} or None,
        "right_sibling": {k: v for k, v in (right_sibling or {}).items() if k != "content"} or None,
        "rows": build_side_by_side_diff(left_content or "", right_content or ""),
    }


@app.post("/api/reports/{filename}/scan/{base_id}/{derived_id}")
def scan_diff(filename: str, base_id: int, derived_id: int):
    report = load_report(filename)
    relationship = _directed_relationship(report, base_id, derived_id)
    base_text, derived_text, _ = _require_contents(base_id, derived_id)

    analyzer = SkillAnalyzer()
    base_result = analyzer.scan(base_text)
    derived_result = analyzer.scan(derived_text)
    comparison = compare_results(base_result, derived_result)
    payload = comparison.to_dict(verbose=True)
    payload["base"]["matches"] = [_safe_rule_match(match) for match in base_result.rule_matches]
    payload["derived"]["matches"] = [_safe_rule_match(match) for match in derived_result.rule_matches]

    return {
        "base_id": base_id,
        "derived_id": derived_id,
        "relationship": relationship,
        "scan_diff": payload,
    }

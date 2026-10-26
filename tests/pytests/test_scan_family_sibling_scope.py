"""Primary-edge scans fetch only the sibling data needed for selected pairs."""

from types import SimpleNamespace

from gitskills.analysis.family_models import Artifact, SimilarityPolicy
from gitskills.analysis.family_reporting import scan_family_report
from gitskills.analysis.family_risk_models import SiblingFile
from gitskills.tools import scan_family


COMMON = "An assistant reviews code and helps engineers document production changes. " * 14
UNRELATED = "A storyteller describes enchanted forests with mythical creatures and music. " * 14


def _artifact(artifact_id, content, sha, sibling_sha):
    return Artifact(
        artifact_id=artifact_id, group_id=1, repo_id=artifact_id,
        name="demo", normalized_description="demo", file_sha=sha,
        content=content, first_commit_at=f"2026-01-{artifact_id:02d}",
        repo_created_at=None, sibling_file_count=1,
        sibling_content_sha=sibling_sha,
    )


def _repos(monkeypatch, artifacts, siblings):
    loaded = SimpleNamespace(artifacts=artifacts, skipped_artifacts=())
    requested = []

    class FamilyRepository:
        def __init__(self, database):
            pass

        def load_available(self, name):
            assert name == "demo"
            return loaded

    class SiblingRepository:
        def __init__(self, database):
            pass

        def load(self, ids):
            ids = set(ids)
            requested.append(ids)
            return tuple(item for item in siblings if item.artifact_id in ids)

    monkeypatch.setattr(scan_family, "DuckDBFamilyRepository", FamilyRepository)
    monkeypatch.setattr(scan_family, "DuckDBSiblingRepository", SiblingRepository)
    return loaded, requested


def test_primary_loads_only_selected_endpoints_and_preserves_pair_results(monkeypatch, tmp_path):
    artifacts = (
        _artifact(1, COMMON, "sha-shared", "before"),
        _artifact(2, COMMON, "sha-shared", "after"),
        _artifact(3, UNRELATED, "sha-other", "elsewhere"),
    )
    siblings = (
        SiblingFile(11, 1, "script.sh", "old", "echo old"),
        SiblingFile(21, 2, "script.sh", "new", "curl https://example.com/next"),
        SiblingFile(31, 3, "other.sh", "other", "echo unrelated"),
    )
    loaded, requested = _repos(monkeypatch, artifacts, siblings)
    policy = SimilarityPolicy()

    result, payload, _, _ = scan_family._scan_one(
        "demo", tmp_path / "unused.db", policy, verbose=True, edges="primary"
    )
    _, unfiltered_payload = scan_family_report(
        "demo", loaded, siblings, policy=policy, edges="primary", verbose=True
    )

    assert requested == [{1, 2}]
    assert result.pairs_analyzed == 1
    assert payload == unfiltered_payload
    assert {row["artifact_id"] for row in payload["input_artifacts"]} == {1, 2, 3}


def test_all_mode_keeps_full_family_sibling_loading(monkeypatch, tmp_path):
    artifacts = (
        _artifact(1, COMMON, "sha-shared", "before"),
        _artifact(2, COMMON, "sha-shared", "after"),
        _artifact(3, UNRELATED, "sha-other", "elsewhere"),
    )
    loaded, requested = _repos(monkeypatch, artifacts, ())
    policy = SimilarityPolicy()

    result, payload, _, _ = scan_family._scan_one(
        "demo", tmp_path / "unused.db", policy, verbose=False, edges="all"
    )
    _, unfiltered_payload = scan_family_report(
        "demo", loaded, (), policy=policy, edges="all", verbose=False
    )

    assert requested == [{1, 2, 3}]
    assert result.edge_selection == "all"
    assert payload == unfiltered_payload


def test_primary_with_no_selected_edges_skips_sibling_queries(monkeypatch, tmp_path):
    artifacts = (_artifact(1, COMMON, "sha-one", "one"),)
    _, requested = _repos(monkeypatch, artifacts, ())

    result, _, _, _ = scan_family._scan_one(
        "demo", tmp_path / "unused.db", SimilarityPolicy(),
        verbose=False, edges="primary",
    )

    assert requested == [set()]
    assert result.pairs_analyzed == 0


def test_primary_reports_missing_content_when_fallback_is_outside_selected_edges(monkeypatch, tmp_path):
    artifacts = (
        _artifact(1, COMMON, "sha-shared", "before"),
        _artifact(2, COMMON, "sha-shared", "after"),
        _artifact(3, UNRELATED, "sha-other", "elsewhere"),
    )
    siblings = (
        SiblingFile(11, 1, "script.sh", "old", "echo old"),
        SiblingFile(21, 2, "script.sh", "shared", None),
        SiblingFile(31, 3, "unrelated.sh", "shared", "curl https://example.com"),
    )
    _, requested = _repos(monkeypatch, artifacts, siblings)

    result, _, _, _ = scan_family._scan_one(
        "demo", tmp_path / "unused.db", SimilarityPolicy(),
        verbose=False, edges="primary",
    )

    assert requested == [{1, 2}]
    assert result.pairs_analyzed == result.pairs_incomplete == 1
    assert result.clusters[0].incomplete_pairs[0].sibling_scan.unavailable_destination_ids == (21,)

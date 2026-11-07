"""Check that primary cohort scans can reuse compatible all-edge evidence."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gitskills.analysis.family_models import ChangeType, SimilarityPolicy
from gitskills.analysis.family_risk_models import (
    ClusterRiskAnalysis, FamilyRiskAnalysis, PairObservation,
)
from gitskills.pipelines import cohort
from gitskills.reporting.cohort_records import validated_pair_rows


def _observation(edge_type: str, source: int, target: int) -> PairObservation:
    return PairObservation(
        edge_type=edge_type, source_artifact_id=source, destination_artifact_id=target,
        direction_basis="chronology", change_type=ChangeType.SKILL_ONLY,
        flagged=False, rule_flagged=False, skill_evidence_added=0,
        skill_evidence_removed=0, sibling_evidence_added=0, sibling_evidence_removed=0,
        indicator_ids=(), uncertain_indicator_ids=(), finding_count=0,
        coverage="complete", evidence_complete=0, evidence_partial=0,
        evidence_unsupported=0, missing_sibling_content=0, unknown_sibling_hashes=0,
        sibling_listing_incomplete=False,
    )


def _report(*, edges: str) -> dict:
    first = [_observation("primary", 1, 2)]
    second = [_observation("additional", 1, 3)] if edges == "all" else []
    clusters = [ClusterRiskAnalysis(
        cluster_number=1, pairs_analyzed=len(first) + len(second),
        flagged_pairs=(), pair_observations=tuple(first + second),
        direction_basis_counts=(("chronology", len(first) + len(second)),),
    )]
    if edges == "all":
        clusters.append(ClusterRiskAnalysis(
            cluster_number=2, pairs_analyzed=1, flagged_pairs=(),
            pair_observations=(_observation("additional", 3, 4),),
            direction_basis_counts=(("chronology", 1),),
        ))
    scan = FamilyRiskAnalysis(
        name="example", similarity_policy=SimilarityPolicy(), active_rules=(),
        clusters=tuple(clusters), ambiguous_edges_skipped=2,
        edge_selection=edges,
    ).to_dict()
    scan.update({"input_artifacts": [], "skipped_artifacts": [],
                 "input_summary": {"artifacts_loaded": 0, "artifacts_skipped": 0,
                                   "incomplete": False}})
    return scan


def test_primary_projection_matches_native_report():
    all_scan = _report(edges="all")
    before = json.dumps(all_scan, sort_keys=True)
    primary = cohort._primary_from_all(all_scan)
    assert primary == _report(edges="primary")
    assert len(validated_pair_rows(primary)) == 1
    assert json.dumps(all_scan, sort_keys=True) == before


@pytest.mark.parametrize("versioned_all", [False, True])
def test_primary_cohort_derives_from_compatible_all_scan(tmp_path, monkeypatch, versioned_all):
    database = tmp_path / "test.db"
    database.write_bytes(b"fake-database-file")
    cache = tmp_path / ".scans"
    cache.mkdir()
    results = tmp_path / "results"
    all_scan = _report(edges="all")
    all_scan["input_artifacts"] = [
        {"artifact_id": i, "group_id": i, "repo_full_name": "org/repo",
         "path": "SKILL.md", "file_sha": str(i), "sibling_file_count": 0,
         "sibling_content_sha": str(i)}
        for i in range(1, 5)
    ]
    records = all_scan["input_artifacts"]
    artifacts = [SimpleNamespace(**row) for row in records]
    loaded = SimpleNamespace(artifacts=artifacts, skipped_artifacts=[])
    stamp = cohort._database_stamp(database)
    all_fingerprint = cohort.fingerprint({
        "name": "example", "source": cohort.fingerprint(records),
        "skipped": cohort.fingerprint([]), "database": stamp,
        "implementation": "impl-1", "policy": SimilarityPolicy().to_dict(),
        "edges": "all", "active_rules": [],
    })
    source_key = f"example::{all_fingerprint[:20]}" if versioned_all else "example"
    name_hash = hashlib.sha256(b"example").hexdigest()[:8]
    source_name = (f"example--{name_hash}-{all_fingerprint[:16]}.json"
                   if versioned_all else "example.json")
    scan_file = cache / source_name
    cohort._atomic_json(scan_file, all_scan)
    entry = cohort._entry(scan_file, records, [], stamp, "impl-1",
                          SimilarityPolicy(), "all", [])
    cohort._atomic_json(cache / ".metadata" / "scan-manifest.json",
                        {"version": cohort._CACHE_VERSION, "families": {source_key: entry}})

    class FakeFamilyRepo:
        def __init__(self, database):
            pass
        def load_available(self, name):
            return loaded

    class FakeRiskAnalyzer:
        def __init__(self, **kwargs):
            self.active_rules = []

    monkeypatch.setattr(cohort, "DuckDBFamilyRepository", FakeFamilyRepo)
    monkeypatch.setattr(cohort, "FamilyRiskAnalyzer", FakeRiskAnalyzer)
    monkeypatch.setattr(cohort, "implementation_fingerprint", lambda: "impl-1")
    monkeypatch.setattr(cohort, "scan_family_report", lambda *a, **kw: (_ for _ in ()).throw(
        AssertionError("security scanner must not run")))
    monkeypatch.setattr(cohort, "FamilyAnalyzer", lambda *a, **kw: (_ for _ in ()).throw(
        AssertionError("family similarity must not run without sampling")))
    monkeypatch.setattr(cohort, "protect_snapshot", lambda *a: None)
    monkeypatch.setattr(cohort, "write_audit", lambda *a: None)
    monkeypatch.setattr(cohort, "cohort_manifest", lambda *a: {})
    scans = []

    def fake_summarize(scans_arg, *args, **kwargs):
        scans.extend(scans_arg)
        return {"directed_pairs_analyzed": scans_arg[0]["summary"]["pairs_analyzed"]}

    monkeypatch.setattr(cohort, "summarize", fake_summarize)
    events = []
    cohort.summarize_cohort(
        ["example"], database=database, results=results,
        scan_cache=cache, per_stratum=None, edges="primary", progress=events.append,
    )
    assert len(scans) == 1
    assert scans[0]["edge_selection"] == "primary"
    assert scans[0]["summary"]["pairs_analyzed"] == 1
    assert any("deriving primary scan" in event for event in events)
    derived = [path for path in cache.glob("example--*.json")
               if json.loads(path.read_text())["edge_selection"] == "primary"]
    assert len(derived) == 1
    assert json.loads(derived[0].read_text()) == scans[0]
    manifest = json.loads((cache / ".metadata" / "scan-manifest.json").read_text())
    assert len(manifest["families"]) == 2
    assert scan_file.read_text() == json.dumps(all_scan, indent=2) + "\n"

    events.clear()
    cohort.summarize_cohort(
        ["example"], database=database, results=results,
        scan_cache=cache, per_stratum=None, edges="primary", progress=events.append,
    )
    assert any("reusing compatible scan" in event for event in events)

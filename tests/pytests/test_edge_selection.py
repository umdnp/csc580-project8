"""Research scope for primary and additional direction-supported edges."""

import csv
import json
from dataclasses import replace

import pytest

from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_models import Artifact
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.tools.summarize_scans import ResearchInputError, summarize

PREFIX = "The agent skill performs safe and documented analysis of software artifacts and security patterns. " * 15 + "\n"


def family_artifacts():
    suffixes = (
        "Prepare the project.",
        "Prepare the project.\nmkdir cache",
        "Prepare the project.\nmkdir cache\nrm -rf cache",
        "Prepare the project.\nmkdir cache\nrm -rf cache\ncat ~/.ssh/id_rsa",
    )
    return tuple(Artifact(
        artifact_id=i, group_id=1, repo_id=i, name="edge-selection-test",
        normalized_description="demo", file_sha=f"sha-{i}", content=PREFIX + suffix,
        first_commit_at=f"2026-01-{i:02d}", repo_created_at=None,
        sibling_file_count=0, sibling_content_sha="empty",
    ) for i, suffix in enumerate(suffixes, 1))


def observations(report):
    return [item for cluster in report["clusters"] for item in cluster["pair_observations"]]


def test_primary_is_default_and_all_adds_related_edges():
    artifacts = family_artifacts()
    primary = FamilyRiskAnalyzer().analyze(artifacts).to_dict()
    everything = FamilyRiskAnalyzer(edges="all").analyze(artifacts).to_dict()
    primary_pairs = {(p["source_artifact_id"], p["destination_artifact_id"])
                     for p in observations(primary)}
    all_pairs = {(p["source_artifact_id"], p["destination_artifact_id"])
                 for p in observations(everything)}
    assert primary["edge_selection"] == "primary"
    assert everything["edge_selection"] == "all"
    assert primary["summary"]["edge_type_counts"] == {"primary": 3}
    assert everything["summary"]["edge_type_counts"] == {"primary": 3, "additional": 3}
    assert primary_pairs == {(1, 2), (2, 3), (3, 4)}
    assert all_pairs == primary_pairs | {(1, 3), (1, 4), (2, 4)}
    assert all(p["edge_type"] == "primary" for p in observations(primary))
    assert {(p["source_artifact_id"], p["destination_artifact_id"]): p["edge_type"]
            for p in observations(everything)}[(1, 4)] == "additional"
    assert all(pair["edge_type"] in ("primary", "additional")
               for cluster in everything["clusters"] for pair in cluster["flagged_pairs"])
    with pytest.raises(ValueError, match="edges must be"):
        FamilyRiskAnalyzer(edges="ambiguous")


def test_duplicate_related_edge_is_scanned_once_and_remains_primary():
    artifacts = family_artifacts()
    analyzer = FamilyAnalyzer()
    original = analyzer.analyze(artifacts)
    cluster = original.family.clusters[0]
    evolution = cluster.evolution
    duplicate = replace(evolution, related_edges=evolution.related_edges + (evolution.directed_edges[0],))
    revised = replace(original, family=replace(original.family, clusters=(
        replace(cluster, evolution=duplicate),
    )))

    class StubFamilyAnalyzer:
        policy = analyzer.policy

        def analyze(self, unused):
            return revised

    result = FamilyRiskAnalyzer(family_analyzer=StubFamilyAnalyzer(), edges="all").analyze(artifacts).to_dict()
    assert result["summary"]["pairs_analyzed"] == 6
    assert result["summary"]["edge_type_counts"] == {"primary": 3, "additional": 3}
    keys = [(p["source_artifact_id"], p["destination_artifact_id"])
            for p in observations(result)]
    assert len(keys) == len(set(keys))


def test_summary_reports_overall_and_by_edge_type(tmp_path):
    report = FamilyRiskAnalyzer(edges="all").analyze(family_artifacts()).to_dict()
    source = tmp_path / "family.json"
    source.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "research"
    summary = summarize([source], output, per_stratum=2, seed=580)
    assert summary["edge_selection"] == "all"
    assert summary["directed_pairs_analyzed"] == 6
    assert sum(block["pairs_analyzed"] for block in summary["edge_type_breakdown"].values()) == 6
    assert summary["edge_type_breakdown"]["additional"]["pairs_analyzed"] == 3
    assert summary["edge_type_breakdown"]["primary"]["pairs_analyzed"] == 3
    assert len(list(csv.DictReader((output / "directed_pairs.csv").open()))) == 6
    counts = list(csv.DictReader((output / "edge_types.csv").open()))
    assert [(row["edge_type"], row["pairs_analyzed"]) for row in counts] == [
        ("primary", "3"), ("additional", "3")]
    frequencies = list(csv.DictReader((output / "indicator_frequency_by_edge_type.csv").open()))
    assert len(frequencies) == 22
    assert {int(row["directed_pairs"]) for row in frequencies} == {3}
    families = list(csv.DictReader((output / "families.csv").open()))
    assert (families[0]["primary_pairs"], families[0]["additional_pairs"]) == ("3", "3")
    assert all(p["edge_type"] in ("primary", "additional") for p in
               csv.DictReader((output / "validation_sample.csv").open()))


def test_mixed_scanning_policies_are_rejected(tmp_path):
    artifacts = family_artifacts()
    sources = []
    for name, kind in (("alpha", "primary"), ("beta", "all")):
        result = FamilyRiskAnalyzer(edges=kind).analyze(artifacts).to_dict()
        result["candidate_family"] = name
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        sources.append(path)
    with pytest.raises(ResearchInputError, match="edge selections"):
        summarize(sources, tmp_path / "output")


def test_edge_count_disagreement_is_rejected(tmp_path):
    report = FamilyRiskAnalyzer(edges="all").analyze(family_artifacts()).to_dict()
    report["clusters"][0]["edge_type_counts"]["primary"] += 1
    path = tmp_path / "wrong.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="edge types mismatch"):
        summarize([path], tmp_path / "out")


def test_unknown_sibling_state_is_not_sampled_as_confirmed_sibling_change():
    from gitskills.tools.summarize_scans import _sample
    row = {"family": "f", "cluster": 1, "base_artifact_id": 1, "derived_artifact_id": 2,
           "indicator_ids": "", "uncertain_indicator_ids": "", "coverage_status": "complete",
           "change_type": "unknown", "flagged": 1}
    selected = _sample([row], 5, 580)
    assert selected[0]["sampling_stratum"] == "flagged-no-indicator"

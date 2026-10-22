"""Constructed families verify relatedness and RDR-007 direction evidence."""

from dataclasses import replace
from hashlib import sha1

import pytest

from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_models import Artifact, ChangeType, SimilarityPolicy
from gitskills.analysis.provenance import extract_declared_provenance


# Sixteen unique tokens yield twelve 5-token shingles. Appending four tokens
# yields sixteen shingles: containment is 1 versus 0.75 and Jaccard is 0.75.
BODY = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa"
EXPANDED = BODY + " quebec romeo sierra tango"
LEFT = BODY + " red"
RIGHT = BODY + " blue"


def artifact(artifact_id, content=BODY, *, date=None, repo_date=None, sibling_sha="same", repo=None):
    return Artifact(
        artifact_id=artifact_id, group_id=artifact_id, repo_id=artifact_id,
        name="constructed-family", normalized_description=f"description {artifact_id}",
        file_sha=sha1(content.encode("utf-8")).hexdigest(), content=content,
        first_commit_at=date, repo_created_at=repo_date,
        sibling_file_count=0 if sibling_sha is not None else None,
        sibling_content_sha=sibling_sha,
        repo_full_name=repo or f"team/repo-{artifact_id}",
        path="skills/constructed-family/SKILL.md",
        provenance=extract_declared_provenance(content),
    )


def graph_for(*artifacts, policy=None):
    result = FamilyAnalyzer(policy).analyze(artifacts)
    assert len(result.family.clusters) == 1
    return result.family.clusters[0].evolution


def test_identical_artifacts_share_a_state_without_inventing_ancestry():
    result = FamilyAnalyzer().analyze([
        artifact(900, date="2026-01-01"), artifact(10, date="2026-03-01"),
    ])
    assert result.family.artifact_ids == (10, 900)
    assert len(result.family.clusters) == 1
    variant, = result.skill_variants
    assert set(variant.artifact_ids) == {10, 900}
    assert variant.representative_artifact_id == 900
    assert result.family.bundle_variant_count == 1
    assert result.family.directed_edge_count == 0


def test_frontmatter_and_formatting_changes_are_equivalent_peers_despite_dates():
    first = artifact(10, "---\nname: first\n---\n" + BODY, date="2026-01-01")
    second = artifact(20, "---\nname: second\n---\n" + BODY.upper().replace(" ", "\n"), date="2026-03-01")
    graph = graph_for(first, second)
    assert not graph.directed_edges
    peer, = graph.equivalent_edges
    assert {peer.left_artifact_id, peer.right_artifact_id} == {10, 20}
    assert peer.relationship_status == "equivalent"


def test_shared_name_description_and_provenance_do_not_make_unrelated_bodies_comparable():
    source = artifact(10)
    unrelated = artifact(20, "---\nsource_repo: team/repo-10\n---\n" + " ".join(f"unrelated{i}" for i in range(20)))
    unrelated = replace(unrelated, group_id=source.group_id, normalized_description=source.normalized_description)
    result = FamilyAnalyzer().analyze([source, unrelated])
    assert {cluster.artifact_ids for cluster in result.family.clusters} == {(10,), (20,)}
    assert not result.related_similarities
    assert result.family.directed_edge_count == 0


def test_expanded_body_can_match_across_description_groups_and_keeps_source_ids():
    source, target = artifact(900), artifact(10, EXPANDED)
    result = FamilyAnalyzer().analyze([target, source])
    edge, = result.family.clusters[0].evolution.directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (900, 10)
    assert edge.basis == "containment"
    assert edge.containment == 1
    assert edge.jaccard == pytest.approx(0.75)
    assert edge.shared_shingles == 12
    assert not edge.same_artifact_group
    payload = result.to_dict(verbose=True)
    by_id = {item["artifact_id"]: item for item in payload["artifacts"]}
    for original in (source, target):
        saved = by_id[original.artifact_id]
        assert saved["repo_full_name"] == original.repo_full_name
        assert saved["path"] == original.path
        assert saved["file_sha"] == original.file_sha
    comparison, = payload["similarities"]
    assert set(comparison["left_artifact_ids"] + comparison["right_artifact_ids"]) == {10, 900}


@pytest.mark.parametrize("margin,directed", [(0.25, True), (0.250001, False)])
def test_containment_direction_requires_the_configured_margin(margin, directed):
    graph = graph_for(artifact(10), artifact(20, EXPANDED), policy=SimilarityPolicy(direction_containment_margin=margin))
    assert len(graph.directed_edges) == int(directed)
    assert len(graph.unresolved_edges) == int(not directed)


def test_direct_chronology_overrides_opposing_containment_and_artifact_id_order():
    graph = graph_for(artifact(10, date="2026-03-01"), artifact(900, EXPANDED, date="2026-01-01"))
    edge, = graph.directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (900, 10)
    assert edge.basis == "chronology"
    assert edge.evidence == ("first_commit_at",)


def test_declared_source_overrides_opposing_commit_dates():
    source = artifact(900, date="2026-03-01")
    target = artifact(10, "---\nsource_repo: team/repo-900\n---\n" + EXPANDED, date="2026-01-01")
    edge, = graph_for(source, target).directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (900, 10)
    assert edge.basis == "declared-source"
    assert edge.evidence == ("source_repo",)


def test_mutual_source_declarations_remain_a_conflict_despite_dates_and_containment():
    first = artifact(10, "---\nsource_repo: team/repo-20\n---\n" + BODY, date="2026-01-01")
    second = artifact(20, "---\nsource_repo: team/repo-10\n---\n" + EXPANDED, date="2026-03-01")
    graph = graph_for(first, second)
    assert not graph.directed_edges
    conflict, = graph.unresolved_edges
    assert conflict.basis == "provenance-conflict"
    assert conflict.relationship_status == "direction-conflict"
    assert conflict.evidence == ("source_repo",)


def test_repository_hint_disambiguates_a_declared_source_path():
    first = replace(artifact(10, LEFT), path="skills/original/SKILL.md")
    second = replace(artifact(20, RIGHT), path="skills/original/SKILL.md")
    target = artifact(30, "---\nderived_from: skills/original\nsource_repo: team/repo-20\n---\n" + BODY + " green")
    graph = graph_for(first, second, target)
    edge, = graph.directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (20, 30)
    assert edge.basis == "declared-source"
    assert edge.evidence == ("derived_from", "source_repo")


def test_ambiguous_source_path_without_repository_hint_does_not_choose_a_source():
    first = replace(artifact(10, LEFT), path="skills/original/SKILL.md")
    second = replace(artifact(20, RIGHT), path="skills/original/SKILL.md")
    target = artifact(30, "---\nderived_from: skills/original\n---\n" + BODY + " green")
    graph = graph_for(first, second, target)
    assert not graph.directed_edges
    assert len(graph.unresolved_edges) == 3
    assert all(edge.basis == "similarity-only" for edge in graph.unresolved_edges)


@pytest.mark.parametrize("date", [None, "not-a-date", "2026-02-30", "2026-01-01"])
def test_symmetric_similarity_with_missing_invalid_or_equal_dates_stays_unresolved(date):
    graph = graph_for(artifact(10, LEFT, date=date), artifact(20, RIGHT, date=date))
    assert not graph.directed_edges
    unresolved, = graph.unresolved_edges
    assert unresolved.basis == "similarity-only"
    assert unresolved.relationship_status == "direction-unknown"


def test_unresolvable_provenance_does_not_supply_a_direction():
    first = artifact(10, LEFT)
    second = artifact(20, "---\nsource_repo: missing/repository\n---\n" + RIGHT)
    graph = graph_for(first, second)
    assert not graph.directed_edges
    assert graph.unresolved_edges[0].basis == "similarity-only"


def test_commit_dates_are_compared_as_instants_not_lexical_strings():
    graph = graph_for(
        artifact(10, LEFT, date="2026-01-01T23:00:00-02:00"),
        artifact(20, RIGHT, date="2026-01-02T00:30:00Z"),
    )
    edge, = graph.directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (20, 10)
    assert edge.basis == "chronology"


def test_repository_age_alone_does_not_establish_skill_order():
    graph = graph_for(
        artifact(10, LEFT, repo_date="2020-01-01"),
        artifact(20, RIGHT, repo_date="2026-01-01"),
    )
    assert not graph.directed_edges
    assert len(graph.unresolved_edges) == 1


def test_observed_state_before_other_repository_creation_supports_boundary_direction():
    edge, = graph_for(
        artifact(900, LEFT, date="2026-01-01"),
        artifact(10, RIGHT, repo_date="2026-02-01"),
    ).directed_edges
    assert (edge.source_artifact_id, edge.target_artifact_id) == (900, 10)
    assert edge.basis == "repo-created-boundary"
    assert set(edge.evidence) == {"first_commit_at", "repo_created_at"}


@pytest.mark.parametrize("peer_siblings", ["same", "different", None])
def test_peer_chronology_requires_equivalent_body_and_known_matching_siblings(peer_siblings):
    undated = artifact(10, LEFT)
    peer = artifact(20, "---\nname: equivalent-peer\n---\n" + LEFT, date="2026-01-01", sibling_sha=peer_siblings)
    changed = artifact(30, RIGHT, date="2026-03-01")
    result = FamilyAnalyzer().analyze([undated, peer, changed])
    proxies = {proxy.artifact_id: proxy for proxy in result.chronology_proxies}
    if peer_siblings == "same":
        assert proxies[10].chronology_source_artifact_id == 20
        graph = result.family.clusters[0].evolution
        edge = next(edge for edge in (*graph.directed_edges, *graph.related_edges) if (edge.source_artifact_id, edge.target_artifact_id) == (10, 30))
        assert edge.basis == "equivalent-peer-chronology"
        assert edge.source_chronology.chronology_source_artifact_id == 20
        assert result.artifacts[0].first_commit_at is None
    else:
        assert 10 not in proxies
        graph = result.family.clusters[0].evolution
        assert any({edge.left_artifact_id, edge.right_artifact_id} == {10, 30} for edge in graph.unresolved_edges)


def test_missing_sibling_state_stays_unknown_rather_than_equivalent():
    first, second = artifact(10, sibling_sha=None), artifact(20, sibling_sha=None)
    result = FamilyAnalyzer().analyze([first, second])
    assert result.family.bundle_variant_count == 2
    edge, = result.family.clusters[0].evolution.unresolved_edges
    assert edge.change_type == ChangeType.UNKNOWN
    assert edge.basis == "same-content-direction-unknown"


@pytest.mark.parametrize("first,second", [("", " \n"), ("one two", "three four")])
def test_insufficient_body_content_does_not_manufacture_a_relationship(first, second):
    result = FamilyAnalyzer().analyze([artifact(10, first), artifact(20, second)])
    assert len(result.family.clusters) == 2
    assert not result.related_similarities
    assert result.family.directed_edge_count == 0


def test_selected_predecessors_do_not_form_a_cycle_and_results_ignore_input_order():
    artifacts = [
        artifact(10, "---\nsource_repo: team/repo-30\n---\n" + BODY + " red"),
        artifact(20, "---\nsource_repo: team/repo-10\n---\n" + BODY + " blue"),
        artifact(30, "---\nsource_repo: team/repo-20\n---\n" + BODY + " green"),
    ]
    analyzer = FamilyAnalyzer()
    result = analyzer.analyze(artifacts)
    graph = result.family.clusters[0].evolution
    assert len(graph.directed_edges) == 2
    assert len(graph.related_edges) == 1  # Unselected candidate remains traceable.
    parents = {edge.target_artifact_id: edge.source_artifact_id for edge in graph.directed_edges}
    assert len(parents) == len(graph.directed_edges)
    for artifact_id in (10, 20, 30):
        visited = set()
        while artifact_id in parents:
            assert artifact_id not in visited
            visited.add(artifact_id)
            artifact_id = parents[artifact_id]
    assert analyzer.analyze(reversed(artifacts)).to_dict(verbose=True) == result.to_dict(verbose=True)


def test_family_analysis_rejects_empty_input_and_mixed_names_with_clear_errors():
    with pytest.raises(ValueError, match="contains no artifacts"):
        FamilyAnalyzer().analyze([])
    with pytest.raises(ValueError, match="exactly one skill name"):
        FamilyAnalyzer().analyze([artifact(10), replace(artifact(20), name="different-family")])

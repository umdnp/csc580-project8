"""Candidate-family similarity, clustering, and evolution analysis."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from typing import Iterable

from .family_models import (
    AmbiguousRelationship,
    Artifact,
    ArtifactGroupAnalysis,
    BundleKey,
    BundleVariant,
    ChangeType,
    ClusterAnalysis,
    EvolutionEdge,
    EvolutionGraph,
    FamilyAnalysis,
    ScopeAnalysis,
    SimilarityPolicy,
    SimilarityResult,
    SkillVariant,
)
from .provenance import (
    PROVENANCE_FIELDS,
    normalize_repo_reference,
    skill_path_matches,
)
from .similarity import compare_skill_variants


class FamilyAnalyzer:
    """Analyze related artifacts within one same-name candidate family."""

    def __init__(self, policy: SimilarityPolicy | None = None) -> None:
        self._policy = policy or SimilarityPolicy()

    @property
    def policy(self) -> SimilarityPolicy:
        return self._policy

    def analyze(self, artifacts: Iterable[Artifact]) -> FamilyAnalysis:
        """Analyze one candidate family loaded from artifact_groupings."""

        artifact_tuple = tuple(sorted(artifacts, key=lambda item: item.artifact_id))
        if not artifact_tuple:
            raise ValueError("Candidate family contains no artifacts")

        names = {artifact.name for artifact in artifact_tuple}
        if len(names) != 1:
            raise ValueError("Candidate family must contain exactly one skill name")

        skill_variants = _build_skill_variants(artifact_tuple)
        bundle_variants = _build_bundle_variants(artifact_tuple)
        declared_sources = _build_declared_source_index(
            artifact_tuple,
            bundle_variants,
        )
        similarities = compare_skill_variants(
            skill_variants,
            shingle_size=self._policy.shingle_size,
        )
        similarity_index = _SimilarityIndex(similarities)

        family_scope = self._analyze_family_scope(
            artifact_tuple,
            similarity_index,
            skill_variants,
            bundle_variants,
            declared_sources,
        )
        group_analyses = _build_group_analyses(
            artifact_tuple,
            skill_variants,
            bundle_variants,
            family_scope.clusters,
        )

        return FamilyAnalysis(
            name=artifact_tuple[0].name,
            policy=self._policy,
            family=family_scope,
            groups=group_analyses,
            similarities=similarities,
            skill_variants=skill_variants,
            bundle_variants=bundle_variants,
            artifacts=artifact_tuple,
        )

    def _analyze_family_scope(
        self,
        artifacts: tuple[Artifact, ...],
        similarity_index: "_SimilarityIndex",
        skill_variants: tuple[SkillVariant, ...],
        bundle_variants: tuple[BundleVariant, ...],
        declared_sources: "_DeclaredSourceIndex",
    ) -> ScopeAnalysis:
        """Build family-wide clusters and evolution graphs once."""

        components = _skill_variant_components(
            skill_variants,
            similarity_index,
            self._policy,
        )

        cluster_inputs = []
        for file_shas in components:
            cluster_artifacts = tuple(
                artifact
                for artifact in artifacts
                if artifact.file_sha in file_shas
            )
            cluster_bundles = tuple(
                bundle
                for bundle in bundle_variants
                if bundle.file_sha in file_shas
            )
            cluster_inputs.append((file_shas, cluster_artifacts, cluster_bundles))

        cluster_inputs.sort(key=_cluster_sort_key)

        clusters = tuple(
            ClusterAnalysis(
                number=index,
                file_shas=tuple(sorted(file_shas)),
                artifact_ids=tuple(
                    sorted(artifact.artifact_id for artifact in cluster_artifacts)
                ),
                bundle_variant_count=len(cluster_bundles),
                evolution=_build_evolution_graph(
                    cluster_bundles,
                    similarity_index,
                    self._policy,
                    declared_sources,
                ),
            )
            for index, (file_shas, cluster_artifacts, cluster_bundles) in enumerate(
                cluster_inputs,
                start=1,
            )
        )

        return ScopeAnalysis(
            artifact_ids=tuple(sorted(artifact.artifact_id for artifact in artifacts)),
            skill_variant_count=len(skill_variants),
            bundle_variant_count=len(bundle_variants),
            clusters=clusters,
        )


@dataclass(frozen=True, slots=True)
class _DirectedCandidate:
    source: BundleVariant
    target: BundleVariant
    basis: str
    containment: float
    jaccard: float
    shared_shingles: int
    change_type: ChangeType
    shared_group_ids: tuple[int, ...]
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _DeclaredSourceDecision:
    source: BundleVariant | None
    target: BundleVariant | None
    evidence: tuple[str, ...]
    conflict: bool = False


class _DeclaredSourceIndex:
    def __init__(
        self,
        links: dict[BundleKey, dict[BundleKey, tuple[str, ...]]],
    ) -> None:
        self._links = links

    def sources_for(self, target: BundleKey) -> dict[BundleKey, tuple[str, ...]]:
        return self._links.get(target, {})

    def evidence(self, source: BundleKey, target: BundleKey) -> tuple[str, ...]:
        return self._links.get(target, {}).get(source, ())


class _SimilarityIndex:
    def __init__(self, results: Iterable[SimilarityResult]) -> None:
        self._results = {
            frozenset((result.left_file_sha, result.right_file_sha)): result
            for result in results
        }

    def get(self, left_file_sha: str, right_file_sha: str) -> SimilarityResult | None:
        if left_file_sha == right_file_sha:
            return None
        return self._results.get(frozenset((left_file_sha, right_file_sha)))


def _build_group_analyses(
    artifacts: tuple[Artifact, ...],
    skill_variants: tuple[SkillVariant, ...],
    bundle_variants: tuple[BundleVariant, ...],
    clusters: tuple[ClusterAnalysis, ...],
) -> tuple[ArtifactGroupAnalysis, ...]:
    """Summarize database artifact groups without reclustering them."""

    by_group: dict[int, list[Artifact]] = defaultdict(list)
    for artifact in artifacts:
        by_group[artifact.group_id].append(artifact)

    cluster_by_artifact = {
        artifact_id: cluster.number
        for cluster in clusters
        for artifact_id in cluster.artifact_ids
    }

    summaries = []
    for group_id in sorted(by_group):
        members = tuple(sorted(by_group[group_id], key=lambda item: item.artifact_id))
        artifact_ids = {member.artifact_id for member in members}
        file_shas = {member.file_sha for member in members}

        group_bundle_count = sum(
            bool(artifact_ids & set(bundle.artifact_ids))
            for bundle in bundle_variants
        )
        family_cluster_numbers = tuple(
            sorted({cluster_by_artifact[artifact_id] for artifact_id in artifact_ids})
        )

        summaries.append(
            ArtifactGroupAnalysis(
                group_id=group_id,
                normalized_description=members[0].normalized_description,
                artifact_ids=tuple(sorted(artifact_ids)),
                skill_variant_count=sum(
                    variant.file_sha in file_shas
                    for variant in skill_variants
                ),
                bundle_variant_count=group_bundle_count,
                family_cluster_numbers=family_cluster_numbers,
            )
        )

    return tuple(summaries)



def _build_declared_source_index(
    artifacts: tuple[Artifact, ...],
    bundles: tuple[BundleVariant, ...],
) -> _DeclaredSourceIndex:
    """Resolve conservative frontmatter source declarations within the family."""

    artifact_to_bundle = {
        artifact_id: bundle.key
        for bundle in bundles
        for artifact_id in bundle.artifact_ids
    }
    links: dict[BundleKey, dict[BundleKey, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )

    for target in artifacts:
        target_bundle = artifact_to_bundle[target.artifact_id]
        resolutions = _resolve_artifact_declared_sources(target, artifacts)
        for source_artifact_id, evidence in resolutions.items():
            source_bundle = artifact_to_bundle[source_artifact_id]
            if source_bundle == target_bundle:
                continue
            links[target_bundle][source_bundle].update(evidence)

    normalized = {
        target: {
            source: _ordered_evidence(evidence)
            for source, evidence in sources.items()
        }
        for target, sources in links.items()
    }
    return _DeclaredSourceIndex(normalized)


def _resolve_artifact_declared_sources(
    target: Artifact,
    artifacts: tuple[Artifact, ...],
) -> dict[int, set[str]]:
    provenance = target.provenance
    candidates = tuple(
        artifact
        for artifact in artifacts
        if artifact.artifact_id != target.artifact_id
    )
    resolved: dict[int, set[str]] = defaultdict(set)

    repo_fields = {
        "source_repo": normalize_repo_reference(provenance.source_repo),
        "upstream_source": normalize_repo_reference(provenance.upstream_source),
    }
    repo_hints = {value for value in repo_fields.values() if value is not None}

    for field_name in ("derived_from", "upstream_skill"):
        value = getattr(provenance, field_name)
        if not value:
            continue

        source = _resolve_declared_skill_path(
            target,
            value,
            candidates,
            repo_hints,
        )
        if source is None:
            continue

        resolved[source.artifact_id].add(field_name)
        for repo_field, repo_name in repo_fields.items():
            if (
                repo_name is not None
                and repo_name == normalize_repo_reference(source.repo_full_name)
            ):
                resolved[source.artifact_id].add(repo_field)

    for field_name, repo_name in repo_fields.items():
        if (
            repo_name is None
            or repo_name == normalize_repo_reference(target.repo_full_name)
        ):
            continue

        repo_candidates = tuple(
            artifact
            for artifact in candidates
            if normalize_repo_reference(artifact.repo_full_name) == repo_name
        )
        if len(repo_candidates) == 1:
            resolved[repo_candidates[0].artifact_id].add(field_name)

    return dict(resolved)


def _resolve_declared_skill_path(
    target: Artifact,
    declared_path: str,
    candidates: tuple[Artifact, ...],
    repo_hints: set[str],
) -> Artifact | None:
    matches = tuple(
        artifact
        for artifact in candidates
        if skill_path_matches(declared_path, artifact.path)
    )
    if not matches:
        return None

    hinted = tuple(
        artifact
        for artifact in matches
        if normalize_repo_reference(artifact.repo_full_name) in repo_hints
    )
    if len(hinted) == 1:
        return hinted[0]

    same_repo = tuple(
        artifact
        for artifact in matches
        if target.repo_full_name is not None
        and normalize_repo_reference(artifact.repo_full_name)
        == normalize_repo_reference(target.repo_full_name)
    )
    if len(same_repo) == 1:
        return same_repo[0]

    if len(matches) == 1:
        return matches[0]

    return None


def _ordered_evidence(values: Iterable[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(field for field in PROVENANCE_FIELDS if field in present)

def _build_skill_variants(artifacts: tuple[Artifact, ...]) -> tuple[SkillVariant, ...]:
    by_sha: dict[str, list[Artifact]] = defaultdict(list)
    for artifact in artifacts:
        by_sha[artifact.file_sha].append(artifact)

    variants = []
    for file_sha, members in sorted(by_sha.items()):
        members.sort(key=lambda artifact: artifact.artifact_id)
        content = members[0].content

        if any(member.content != content for member in members[1:]):
            raise ValueError(
                f"Artifacts sharing file_sha {file_sha} do not share identical content"
            )

        representative = _representative_artifact(members)
        variants.append(
            SkillVariant(
                file_sha=file_sha,
                content=content,
                artifact_ids=tuple(member.artifact_id for member in members),
                group_ids=tuple(sorted({member.group_id for member in members})),
                representative_artifact_id=representative.artifact_id,
                earliest_observed_at=representative.first_commit_at,
            )
        )

    return tuple(variants)


def _build_bundle_variants(artifacts: tuple[Artifact, ...]) -> tuple[BundleVariant, ...]:
    by_key: dict[BundleKey, list[Artifact]] = defaultdict(list)

    for artifact in artifacts:
        if artifact.sibling_content_sha is None:
            key = BundleKey(
                file_sha=artifact.file_sha,
                sibling_content_sha=None,
                unknown_artifact_id=artifact.artifact_id,
            )
        else:
            key = BundleKey(
                file_sha=artifact.file_sha,
                sibling_content_sha=artifact.sibling_content_sha,
            )
        by_key[key].append(artifact)

    variants = []
    for key, members in sorted(
        by_key.items(),
        key=lambda item: (
            item[0].file_sha,
            item[0].sibling_content_sha or "",
            item[0].unknown_artifact_id or -1,
        ),
    ):
        members.sort(key=lambda artifact: artifact.artifact_id)
        representative = _representative_artifact(members)
        variants.append(
            BundleVariant(
                key=key,
                artifact_ids=tuple(member.artifact_id for member in members),
                group_ids=tuple(sorted({member.group_id for member in members})),
                representative_artifact_id=representative.artifact_id,
                earliest_observed_at=representative.first_commit_at,
            )
        )

    return tuple(variants)


def _representative_artifact(artifacts: Iterable[Artifact]) -> Artifact:
    members = tuple(artifacts)
    observed = [
        artifact
        for artifact in members
        if _parse_timestamp(artifact.first_commit_at) is not None
    ]

    if observed:
        return min(
            observed,
            key=lambda artifact: (
                _parse_timestamp(artifact.first_commit_at),
                artifact.artifact_id,
            ),
        )

    return min(members, key=lambda artifact: artifact.artifact_id)


def _skill_variant_components(
    variants: tuple[SkillVariant, ...],
    similarity_index: _SimilarityIndex,
    policy: SimilarityPolicy,
) -> tuple[frozenset[str], ...]:
    adjacency = {variant.file_sha: set() for variant in variants}

    for left, right in combinations(variants, 2):
        result = similarity_index.get(left.file_sha, right.file_sha)
        if result is not None and policy.relates(result):
            adjacency[left.file_sha].add(right.file_sha)
            adjacency[right.file_sha].add(left.file_sha)

    components = []
    unseen = set(adjacency)

    while unseen:
        start = min(unseen)
        stack = [start]
        component: set[str] = set()

        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            unseen.discard(current)
            stack.extend(sorted(adjacency[current] - component, reverse=True))

        components.append(frozenset(component))

    return tuple(components)


def _cluster_sort_key(
    item: tuple[frozenset[str], tuple[Artifact, ...], tuple[BundleVariant, ...]],
) -> tuple[object, ...]:
    _, artifacts, _ = item
    observed_dates = [
        parsed
        for artifact in artifacts
        if (parsed := _parse_timestamp(artifact.first_commit_at)) is not None
    ]
    earliest = min(observed_dates) if observed_dates else datetime.max.replace(tzinfo=timezone.utc)
    min_artifact_id = min(artifact.artifact_id for artifact in artifacts)
    return (-len(artifacts), earliest, min_artifact_id)


def _build_evolution_graph(
    bundles: tuple[BundleVariant, ...],
    similarity_index: _SimilarityIndex,
    policy: SimilarityPolicy,
    declared_sources: _DeclaredSourceIndex,
) -> EvolutionGraph:
    if not bundles:
        return EvolutionGraph(
            bundle_keys=(),
            directed_edges=(),
            ambiguous_edges=(),
            root_candidate_artifact_ids=(),
        )

    directed_candidates: list[_DirectedCandidate] = []
    ambiguous: list[AmbiguousRelationship] = []
    cluster_bundle_keys = frozenset(bundle.key for bundle in bundles)

    for left, right in combinations(bundles, 2):
        relation = _bundle_relationship(
            left,
            right,
            similarity_index,
            policy,
            declared_sources,
            cluster_bundle_keys,
        )
        if relation is None:
            continue

        if isinstance(relation, _DirectedCandidate):
            directed_candidates.append(relation)
        else:
            ambiguous.append(relation)

    selected = _select_predecessor_edges(directed_candidates)
    incoming = {edge.target.key for edge in selected}
    roots = tuple(
        sorted(
            (
                bundle
                for bundle in bundles
                if bundle.key not in incoming
            ),
            key=lambda bundle: bundle.representative_artifact_id,
        )
    )

    return EvolutionGraph(
        bundle_keys=tuple(bundle.key for bundle in bundles),
        directed_edges=tuple(
            EvolutionEdge(
                source=edge.source.key,
                target=edge.target.key,
                source_artifact_id=edge.source.representative_artifact_id,
                target_artifact_id=edge.target.representative_artifact_id,
                basis=edge.basis,
                containment=edge.containment,
                jaccard=edge.jaccard,
                shared_shingles=edge.shared_shingles,
                change_type=edge.change_type,
                shared_group_ids=edge.shared_group_ids,
                evidence=edge.evidence,
            )
            for edge in sorted(
                selected,
                key=lambda edge: (
                    edge.source.representative_artifact_id,
                    edge.target.representative_artifact_id,
                ),
            )
        ),
        ambiguous_edges=tuple(
            sorted(
                ambiguous,
                key=lambda relationship: (
                    relationship.left_artifact_id,
                    relationship.right_artifact_id,
                ),
            )
        ),
        root_candidate_artifact_ids=tuple(
            bundle.representative_artifact_id for bundle in roots
        ),
    )


def _bundle_relationship(
    left: BundleVariant,
    right: BundleVariant,
    similarity_index: _SimilarityIndex,
    policy: SimilarityPolicy,
    declared_sources: _DeclaredSourceIndex,
    cluster_bundle_keys: frozenset[BundleKey],
) -> _DirectedCandidate | AmbiguousRelationship | None:
    sibling_changed = _sibling_changed(left, right)
    shared_group_ids = tuple(sorted(set(left.group_ids) & set(right.group_ids)))

    if left.file_sha == right.file_sha:
        provenance = _infer_declared_source_direction(
            left,
            right,
            declared_sources,
            cluster_bundle_keys,
        )
        if provenance is not None and not provenance.conflict:
            assert provenance.source is not None and provenance.target is not None
            return _DirectedCandidate(
                source=provenance.source,
                target=provenance.target,
                basis="declared-source",
                containment=1.0,
                jaccard=1.0,
                shared_shingles=0,
                change_type=_classify_change(
                    provenance.source,
                    provenance.target,
                    result=None,
                    sibling_changed=sibling_changed,
                ),
                shared_group_ids=shared_group_ids,
                evidence=provenance.evidence,
            )

        return AmbiguousRelationship(
            left=left.key,
            right=right.key,
            left_artifact_id=left.representative_artifact_id,
            right_artifact_id=right.representative_artifact_id,
            basis=(
                "provenance-conflict"
                if provenance is not None and provenance.conflict
                else "similarity-only"
            ),
            containment_left_to_right=1.0,
            containment_right_to_left=1.0,
            jaccard=1.0,
            shared_shingles=None,
            change_type=_classify_change(
                left,
                right,
                result=None,
                sibling_changed=sibling_changed,
            ),
            shared_group_ids=shared_group_ids,
            evidence=provenance.evidence if provenance is not None else (),
        )

    result = similarity_index.get(left.file_sha, right.file_sha)
    if result is None or not policy.relates(result):
        return None

    provenance = _infer_declared_source_direction(
        left,
        right,
        declared_sources,
        cluster_bundle_keys,
    )
    if provenance is not None and provenance.conflict:
        return AmbiguousRelationship(
            left=left.key,
            right=right.key,
            left_artifact_id=left.representative_artifact_id,
            right_artifact_id=right.representative_artifact_id,
            basis="provenance-conflict",
            containment_left_to_right=result.containment(
                left.file_sha,
                right.file_sha,
            ),
            containment_right_to_left=result.containment(
                right.file_sha,
                left.file_sha,
            ),
            jaccard=result.jaccard,
            shared_shingles=result.shared_shingles,
            change_type=_classify_change(
                left,
                right,
                result=result,
                sibling_changed=sibling_changed,
            ),
            shared_group_ids=shared_group_ids,
            evidence=provenance.evidence,
        )

    if provenance is not None:
        assert provenance.source is not None and provenance.target is not None
        direction = (provenance.source, provenance.target, "declared-source")
        evidence = provenance.evidence
    else:
        direction = _infer_direction(left, right, result, policy)
        evidence = ()

    if direction is None:
        return AmbiguousRelationship(
            left=left.key,
            right=right.key,
            left_artifact_id=left.representative_artifact_id,
            right_artifact_id=right.representative_artifact_id,
            basis="similarity-only",
            containment_left_to_right=result.containment(
                left.file_sha,
                right.file_sha,
            ),
            containment_right_to_left=result.containment(
                right.file_sha,
                left.file_sha,
            ),
            jaccard=result.jaccard,
            shared_shingles=result.shared_shingles,
            change_type=_classify_change(
                left,
                right,
                result=result,
                sibling_changed=sibling_changed,
            ),
            shared_group_ids=shared_group_ids,
        )

    source, target, basis = direction
    return _DirectedCandidate(
        source=source,
        target=target,
        basis=basis,
        containment=result.containment(source.file_sha, target.file_sha),
        jaccard=result.jaccard,
        shared_shingles=result.shared_shingles,
        change_type=_classify_change(
            source,
            target,
            result=result,
            sibling_changed=sibling_changed,
        ),
        shared_group_ids=shared_group_ids,
        evidence=evidence,
    )


def _infer_declared_source_direction(
    left: BundleVariant,
    right: BundleVariant,
    declared_sources: _DeclaredSourceIndex,
    cluster_bundle_keys: frozenset[BundleKey],
) -> _DeclaredSourceDecision | None:
    left_sources = {
        key: evidence
        for key, evidence in declared_sources.sources_for(left.key).items()
        if key in cluster_bundle_keys
    }
    right_sources = {
        key: evidence
        for key, evidence in declared_sources.sources_for(right.key).items()
        if key in cluster_bundle_keys
    }

    left_declares_right = right.key in left_sources
    right_declares_left = left.key in right_sources

    left_conflict = left_declares_right and len(left_sources) > 1
    right_conflict = right_declares_left and len(right_sources) > 1

    if (left_declares_right and right_declares_left) or left_conflict or right_conflict:
        evidence = _ordered_evidence(
            (*left_sources.get(right.key, ()), *right_sources.get(left.key, ()))
        )
        return _DeclaredSourceDecision(
            source=None,
            target=None,
            evidence=evidence,
            conflict=True,
        )

    if right_declares_left:
        return _DeclaredSourceDecision(
            source=left,
            target=right,
            evidence=right_sources[left.key],
        )

    if left_declares_right:
        return _DeclaredSourceDecision(
            source=right,
            target=left,
            evidence=left_sources[right.key],
        )

    return None

def _classify_change(
    left: BundleVariant,
    right: BundleVariant,
    *,
    result: SimilarityResult | None,
    sibling_changed: bool | None,
) -> ChangeType:
    """Classify how two related bundle variants differ."""

    if sibling_changed is None:
        return ChangeType.UNKNOWN

    skill_equivalent = (
        left.file_sha == right.file_sha
        or (result is not None and result.equivalent)
    )

    if skill_equivalent:
        return (
            ChangeType.SIBLINGS_ONLY
            if sibling_changed
            else ChangeType.EQUIVALENT
        )

    return (
        ChangeType.SKILL_AND_SIBLINGS
        if sibling_changed
        else ChangeType.SKILL_ONLY
    )


def _infer_direction(
    left: BundleVariant,
    right: BundleVariant,
    result: SimilarityResult,
    policy: SimilarityPolicy,
) -> tuple[BundleVariant, BundleVariant, str] | None:
    left_date = _parse_timestamp(left.earliest_observed_at)
    right_date = _parse_timestamp(right.earliest_observed_at)

    if left_date is not None and right_date is not None and left_date != right_date:
        if left_date < right_date:
            return left, right, "chronology"
        return right, left, "chronology"

    left_to_right = result.containment(left.file_sha, right.file_sha)
    right_to_left = result.containment(right.file_sha, left.file_sha)
    difference = left_to_right - right_to_left

    if abs(difference) < policy.direction_containment_margin:
        return None

    if difference > 0:
        return left, right, "containment"
    return right, left, "containment"


def _sibling_changed(
    left: BundleVariant,
    right: BundleVariant,
) -> bool | None:
    if not left.sibling_state_known or not right.sibling_state_known:
        return None
    return left.sibling_content_sha != right.sibling_content_sha


def _select_predecessor_edges(
    candidates: list[_DirectedCandidate],
) -> tuple[_DirectedCandidate, ...]:
    by_target: dict[BundleKey, list[_DirectedCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_target[candidate.target.key].append(candidate)

    selected: list[_DirectedCandidate] = []

    targets = sorted(
        by_target,
        key=lambda key: min(
            candidate.target.representative_artifact_id
            for candidate in by_target[key]
        ),
    )

    for target in targets:
        ordered = sorted(
            by_target[target],
            key=_candidate_sort_key,
        )
        for candidate in ordered:
            if not _would_create_cycle(selected, candidate):
                selected.append(candidate)
                break

    return tuple(selected)


def _candidate_sort_key(candidate: _DirectedCandidate) -> tuple[object, ...]:
    """Prefer chronology-supported and temporally closest predecessors."""

    source_date = _parse_timestamp(candidate.source.earliest_observed_at)
    target_date = _parse_timestamp(candidate.target.earliest_observed_at)

    basis_rank = {
        "declared-source": 0,
        "chronology": 1,
        "containment": 2,
    }.get(candidate.basis, 3)
    if (
        candidate.basis == "chronology"
        and source_date is not None
        and target_date is not None
    ):
        time_gap = (target_date - source_date).total_seconds()
    else:
        time_gap = float("inf")

    return (
        basis_rank,
        -len(candidate.evidence),
        time_gap,
        -candidate.containment,
        -candidate.jaccard,
        -candidate.shared_shingles,
        candidate.source.representative_artifact_id,
    )


def _would_create_cycle(
    selected: list[_DirectedCandidate],
    candidate: _DirectedCandidate,
) -> bool:
    adjacency: dict[BundleKey, set[BundleKey]] = defaultdict(set)
    for edge in selected:
        adjacency[edge.source.key].add(edge.target.key)
    adjacency[candidate.source.key].add(candidate.target.key)

    target = candidate.source.key
    stack = [candidate.target.key]
    visited: set[BundleKey] = set()

    while stack:
        current = stack.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(adjacency[current] - visited)

    return False


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

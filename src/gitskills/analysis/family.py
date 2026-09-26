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

        family_variants = _build_skill_variants(artifact_tuple)
        family_bundles = _build_bundle_variants(artifact_tuple)
        similarities = compare_skill_variants(
            family_variants,
            shingle_size=self._policy.shingle_size,
        )
        similarity_index = _SimilarityIndex(similarities)

        family_scope = self._analyze_scope(
            artifact_tuple,
            similarity_index,
            skill_variants=family_variants,
            bundle_variants=family_bundles,
        )

        group_analyses = []
        by_group: dict[int, list[Artifact]] = defaultdict(list)
        for artifact in artifact_tuple:
            by_group[artifact.group_id].append(artifact)

        for group_id in sorted(by_group):
            group_artifacts = tuple(by_group[group_id])
            group_analyses.append(
                ArtifactGroupAnalysis(
                    group_id=group_id,
                    normalized_description=group_artifacts[0].normalized_description,
                    analysis=self._analyze_scope(
                        group_artifacts,
                        similarity_index,
                    ),
                )
            )

        return FamilyAnalysis(
            name=artifact_tuple[0].name,
            policy=self._policy,
            family=family_scope,
            groups=tuple(group_analyses),
            similarities=similarities,
            skill_variants=family_variants,
            bundle_variants=family_bundles,
            artifacts=artifact_tuple,
        )

    def _analyze_scope(
        self,
        artifacts: tuple[Artifact, ...],
        similarity_index: "_SimilarityIndex",
        *,
        skill_variants: tuple[SkillVariant, ...] | None = None,
        bundle_variants: tuple[BundleVariant, ...] | None = None,
    ) -> ScopeAnalysis:
        skill_variants = skill_variants or _build_skill_variants(artifacts)
        bundle_variants = bundle_variants or _build_bundle_variants(artifacts)

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
            cluster_inputs.append(
                (
                    file_shas,
                    cluster_artifacts,
                    cluster_bundles,
                )
            )

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
    for key, members in sorted(by_key.items(), key=lambda item: item[0]):
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
) -> EvolutionGraph:
    if not bundles:
        return EvolutionGraph(
            bundle_keys=(),
            edges=(),
            ambiguous_relationships=(),
            base_candidate_artifact_ids=(),
        )

    directed_candidates: list[_DirectedCandidate] = []
    ambiguous: list[AmbiguousRelationship] = []

    for left, right in combinations(bundles, 2):
        relation = _bundle_relationship(
            left,
            right,
            similarity_index,
            policy,
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
        edges=tuple(
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
            )
            for edge in sorted(
                selected,
                key=lambda edge: (
                    edge.source.representative_artifact_id,
                    edge.target.representative_artifact_id,
                ),
            )
        ),
        ambiguous_relationships=tuple(
            sorted(
                ambiguous,
                key=lambda relationship: (
                    relationship.left_artifact_id,
                    relationship.right_artifact_id,
                ),
            )
        ),
        base_candidate_artifact_ids=tuple(
            bundle.representative_artifact_id for bundle in roots
        ),
    )


def _bundle_relationship(
    left: BundleVariant,
    right: BundleVariant,
    similarity_index: _SimilarityIndex,
    policy: SimilarityPolicy,
) -> _DirectedCandidate | AmbiguousRelationship | None:
    sibling_changed = _sibling_changed(left, right)

    if left.file_sha == right.file_sha:
        return AmbiguousRelationship(
            left=left.key,
            right=right.key,
            left_artifact_id=left.representative_artifact_id,
            right_artifact_id=right.representative_artifact_id,
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
        )

    result = similarity_index.get(left.file_sha, right.file_sha)
    if result is None or not policy.relates(result):
        return None

    direction = _infer_direction(left, right, result, policy)
    if direction is None:
        return AmbiguousRelationship(
            left=left.key,
            right=right.key,
            left_artifact_id=left.representative_artifact_id,
            right_artifact_id=right.representative_artifact_id,
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
    )


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
    source_date = _parse_timestamp(candidate.source.earliest_observed_at)
    source_recency = (
        -source_date.timestamp()
        if source_date is not None
        else float("inf")
    )
    return (
        -candidate.containment,
        -candidate.jaccard,
        -candidate.shared_shingles,
        source_recency,
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

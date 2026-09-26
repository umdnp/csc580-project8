"""Domain models for candidate-family similarity analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChangeType(str, Enum):
    """How the endpoints of an inferred relationship differ."""

    SKILL_ONLY = "skill-only"
    SIBLINGS_ONLY = "siblings-only"
    SKILL_AND_SIBLINGS = "skill+siblings"
    EQUIVALENT = "equivalent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Artifact:
    """One artifact in an artifact_groupings candidate family."""

    artifact_id: int
    group_id: int
    repo_id: int | None
    name: str
    normalized_description: str
    file_sha: str
    content: str
    first_commit_at: str | None
    repo_created_at: str | None
    sibling_file_count: int | None
    sibling_content_sha: str | None


@dataclass(frozen=True, slots=True)
class BundleKey:
    """Internal identity for a bundle variant.

    Known sibling state is keyed by file SHA plus sibling-content SHA. When the
    sibling state is unknown, the artifact ID keeps that occurrence separate.
    """

    file_sha: str
    sibling_content_sha: str | None
    unknown_artifact_id: int | None = None


@dataclass(frozen=True, slots=True)
class SkillVariant:
    """One distinct SKILL.md content variant, identified by file_sha."""

    file_sha: str
    content: str
    artifact_ids: tuple[int, ...]
    group_ids: tuple[int, ...]
    representative_artifact_id: int
    earliest_observed_at: str | None


@dataclass(frozen=True, slots=True)
class BundleVariant:
    """One distinct known or conservatively separated skill bundle variant."""

    key: BundleKey
    artifact_ids: tuple[int, ...]
    group_ids: tuple[int, ...]
    representative_artifact_id: int
    earliest_observed_at: str | None

    @property
    def file_sha(self) -> str:
        return self.key.file_sha

    @property
    def sibling_content_sha(self) -> str | None:
        return self.key.sibling_content_sha

    @property
    def sibling_state_known(self) -> bool:
        return self.key.sibling_content_sha is not None


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """Exact 5-token-shingle similarity between two skill variants."""

    left_file_sha: str
    right_file_sha: str
    left_to_right_containment: float
    right_to_left_containment: float
    jaccard: float
    shared_shingles: int
    left_shingles: int
    right_shingles: int

    @property
    def max_containment(self) -> float:
        return max(
            self.left_to_right_containment,
            self.right_to_left_containment,
        )

    @property
    def equivalent(self) -> bool:
        """Return whether both variants have the same shingle-set representation."""

        return (
            self.left_to_right_containment == 1.0
            and self.right_to_left_containment == 1.0
            and self.jaccard == 1.0
        )

    def containment(self, source_file_sha: str, target_file_sha: str) -> float:
        """Return directional containment from source to target."""

        if (
            source_file_sha == self.left_file_sha
            and target_file_sha == self.right_file_sha
        ):
            return self.left_to_right_containment

        if (
            source_file_sha == self.right_file_sha
            and target_file_sha == self.left_file_sha
        ):
            return self.right_to_left_containment

        raise ValueError("Similarity result does not contain the requested pair")

    def to_dict(self) -> dict[str, object]:
        return {
            "left_file_sha": self.left_file_sha,
            "right_file_sha": self.right_file_sha,
            "left_to_right_containment": self.left_to_right_containment,
            "right_to_left_containment": self.right_to_left_containment,
            "jaccard": self.jaccard,
            "shared_shingles": self.shared_shingles,
            "left_shingles": self.left_shingles,
            "right_shingles": self.right_shingles,
        }


@dataclass(frozen=True, slots=True)
class SimilarityPolicy:
    """Configurable exploratory policy for deciding related skill variants.

    RDR-004 requires final thresholds to be selected through validation. These
    defaults make the exploratory CLI useful now, while keeping every threshold
    explicit and replaceable.
    """

    shingle_size: int = 5
    min_containment: float = 0.80
    min_jaccard: float = 0.30
    min_shared_shingles: int = 5
    direction_containment_margin: float = 0.10

    def __post_init__(self) -> None:
        if self.shingle_size < 1:
            raise ValueError("shingle_size must be at least 1")

        for name, value in (
            ("min_containment", self.min_containment),
            ("min_jaccard", self.min_jaccard),
            ("direction_containment_margin", self.direction_containment_margin),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        if self.min_shared_shingles < 1:
            raise ValueError("min_shared_shingles must be at least 1")

    def relates(self, result: SimilarityResult) -> bool:
        """Return whether a pair meets the current relationship policy."""

        return (
            result.max_containment >= self.min_containment
            and result.jaccard >= self.min_jaccard
            and result.shared_shingles >= self.min_shared_shingles
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "shingle_size": self.shingle_size,
            "min_containment": self.min_containment,
            "min_jaccard": self.min_jaccard,
            "min_shared_shingles": self.min_shared_shingles,
            "direction_containment_margin": self.direction_containment_margin,
        }


@dataclass(frozen=True, slots=True)
class EvolutionEdge:
    """One inferred directional relationship between bundle variants."""

    source: BundleKey
    target: BundleKey
    source_artifact_id: int
    target_artifact_id: int
    basis: str
    containment: float
    jaccard: float
    shared_shingles: int
    change_type: ChangeType
    shared_group_ids: tuple[int, ...]

    @property
    def same_artifact_group(self) -> bool:
        return bool(self.shared_group_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_artifact_id": self.source_artifact_id,
            "target_artifact_id": self.target_artifact_id,
            "basis": self.basis,
            "containment": self.containment,
            "jaccard": self.jaccard,
            "shared_shingles": self.shared_shingles,
            "change_type": self.change_type.value,
            "shared_group_ids": list(self.shared_group_ids),
            "same_artifact_group": self.same_artifact_group,
        }


@dataclass(frozen=True, slots=True)
class AmbiguousRelationship:
    """A related pair whose direction cannot be inferred defensibly."""

    left: BundleKey
    right: BundleKey
    left_artifact_id: int
    right_artifact_id: int
    basis: str
    containment_left_to_right: float
    containment_right_to_left: float
    jaccard: float
    shared_shingles: int | None
    change_type: ChangeType
    shared_group_ids: tuple[int, ...]

    @property
    def same_artifact_group(self) -> bool:
        return bool(self.shared_group_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "left_artifact_id": self.left_artifact_id,
            "right_artifact_id": self.right_artifact_id,
            "basis": self.basis,
            "containment_left_to_right": self.containment_left_to_right,
            "containment_right_to_left": self.containment_right_to_left,
            "jaccard": self.jaccard,
            "shared_shingles": self.shared_shingles,
            "change_type": self.change_type.value,
            "shared_group_ids": list(self.shared_group_ids),
            "same_artifact_group": self.same_artifact_group,
        }


@dataclass(frozen=True, slots=True)
class EvolutionGraph:
    """Reduced inferred evolution graph for one similarity cluster."""

    bundle_keys: tuple[BundleKey, ...]
    directed_edges: tuple[EvolutionEdge, ...]
    ambiguous_edges: tuple[AmbiguousRelationship, ...]
    root_candidate_artifact_ids: tuple[int, ...]

    @property
    def has_single_root(self) -> bool:
        return len(self.root_candidate_artifact_ids) == 1

    @property
    def change_counts(self) -> dict[ChangeType, int]:
        """Count directed edges by change type."""

        counts = {change_type: 0 for change_type in ChangeType}
        for edge in self.directed_edges:
            counts[edge.change_type] += 1
        return counts

    @property
    def within_group_directed_edge_count(self) -> int:
        return sum(edge.same_artifact_group for edge in self.directed_edges)

    @property
    def across_group_directed_edge_count(self) -> int:
        return len(self.directed_edges) - self.within_group_directed_edge_count

    @property
    def within_group_ambiguous_edge_count(self) -> int:
        return sum(edge.same_artifact_group for edge in self.ambiguous_edges)

    @property
    def across_group_ambiguous_edge_count(self) -> int:
        return len(self.ambiguous_edges) - self.within_group_ambiguous_edge_count

    # Compatibility aliases for notebooks or code written against the earlier model.
    @property
    def edges(self) -> tuple[EvolutionEdge, ...]:
        return self.directed_edges

    @property
    def ambiguous_relationships(self) -> tuple[AmbiguousRelationship, ...]:
        return self.ambiguous_edges

    @property
    def base_candidate_artifact_ids(self) -> tuple[int, ...]:
        return self.root_candidate_artifact_ids

    @property
    def has_single_base(self) -> bool:
        return self.has_single_root

    @property
    def within_group_edge_count(self) -> int:
        return self.within_group_directed_edge_count

    @property
    def across_group_edge_count(self) -> int:
        return self.across_group_directed_edge_count

    @property
    def within_group_ambiguous_count(self) -> int:
        return self.within_group_ambiguous_edge_count

    @property
    def across_group_ambiguous_count(self) -> int:
        return self.across_group_ambiguous_edge_count

    def to_dict(self) -> dict[str, object]:
        return {
            "root_candidate_artifact_ids": list(self.root_candidate_artifact_ids),
            "directed_edge_count": len(self.directed_edges),
            "within_group_directed_edge_count": (
                self.within_group_directed_edge_count
            ),
            "across_group_directed_edge_count": (
                self.across_group_directed_edge_count
            ),
            "ambiguous_edge_count": len(self.ambiguous_edges),
            "within_group_ambiguous_edge_count": (
                self.within_group_ambiguous_edge_count
            ),
            "across_group_ambiguous_edge_count": (
                self.across_group_ambiguous_edge_count
            ),
            "change_counts": {
                change_type.value: count
                for change_type, count in self.change_counts.items()
            },
            "directed_edges": [edge.to_dict() for edge in self.directed_edges],
            "ambiguous_edges": [edge.to_dict() for edge in self.ambiguous_edges],
        }


@dataclass(frozen=True, slots=True)
class ClusterAnalysis:
    """Similarity-derived grouping of related skill variants."""

    number: int
    file_shas: tuple[str, ...]
    artifact_ids: tuple[int, ...]
    bundle_variant_count: int
    evolution: EvolutionGraph

    @property
    def skill_variant_count(self) -> int:
        return len(self.file_shas)

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.number,
            "artifact_ids": list(self.artifact_ids),
            "skill_variant_count": self.skill_variant_count,
            "bundle_variant_count": self.bundle_variant_count,
            "file_shas": list(self.file_shas),
            "evolution": self.evolution.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ScopeAnalysis:
    """Family-wide clustering and inferred evolution analysis."""

    artifact_ids: tuple[int, ...]
    skill_variant_count: int
    bundle_variant_count: int
    clusters: tuple[ClusterAnalysis, ...]

    @property
    def directed_edge_count(self) -> int:
        return sum(len(cluster.evolution.directed_edges) for cluster in self.clusters)

    @property
    def ambiguous_edge_count(self) -> int:
        return sum(len(cluster.evolution.ambiguous_edges) for cluster in self.clusters)

    @property
    def within_group_directed_edge_count(self) -> int:
        return sum(
            cluster.evolution.within_group_directed_edge_count
            for cluster in self.clusters
        )

    @property
    def across_group_directed_edge_count(self) -> int:
        return self.directed_edge_count - self.within_group_directed_edge_count

    @property
    def within_group_ambiguous_edge_count(self) -> int:
        return sum(
            cluster.evolution.within_group_ambiguous_edge_count
            for cluster in self.clusters
        )

    @property
    def across_group_ambiguous_edge_count(self) -> int:
        return self.ambiguous_edge_count - self.within_group_ambiguous_edge_count

    @property
    def change_counts(self) -> dict[ChangeType, int]:
        counts = {change_type: 0 for change_type in ChangeType}
        for cluster in self.clusters:
            for change_type, count in cluster.evolution.change_counts.items():
                counts[change_type] += count
        return counts

    # Compatibility aliases for code written against the earlier terminology.
    @property
    def base_candidate_artifact_ids(self) -> tuple[int, ...]:
        if len(self.clusters) != 1:
            return ()
        return self.clusters[0].evolution.root_candidate_artifact_ids

    @property
    def has_single_base(self) -> bool:
        return len(self.base_candidate_artifact_ids) == 1

    @property
    def evolution_relationship_count(self) -> int:
        return self.directed_edge_count

    @property
    def ambiguous_relationship_count(self) -> int:
        return self.ambiguous_edge_count

    @property
    def within_group_evolution_count(self) -> int:
        return self.within_group_directed_edge_count

    @property
    def across_group_evolution_count(self) -> int:
        return self.across_group_directed_edge_count

    @property
    def within_group_ambiguous_count(self) -> int:
        return self.within_group_ambiguous_edge_count

    @property
    def across_group_ambiguous_count(self) -> int:
        return self.across_group_ambiguous_edge_count

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_ids": list(self.artifact_ids),
            "skill_variant_count": self.skill_variant_count,
            "bundle_variant_count": self.bundle_variant_count,
            "directed_edge_count": self.directed_edge_count,
            "within_group_directed_edge_count": (
                self.within_group_directed_edge_count
            ),
            "across_group_directed_edge_count": (
                self.across_group_directed_edge_count
            ),
            "ambiguous_edge_count": self.ambiguous_edge_count,
            "within_group_ambiguous_edge_count": (
                self.within_group_ambiguous_edge_count
            ),
            "across_group_ambiguous_edge_count": (
                self.across_group_ambiguous_edge_count
            ),
            "change_counts": {
                change_type.value: count
                for change_type, count in self.change_counts.items()
            },
            "clusters": [cluster.to_dict() for cluster in self.clusters],
        }


@dataclass(frozen=True, slots=True)
class ArtifactGroupAnalysis:
    """Artifact-group metadata mapped onto family-wide similarity clusters."""

    group_id: int
    normalized_description: str
    artifact_ids: tuple[int, ...]
    skill_variant_count: int
    bundle_variant_count: int
    family_cluster_numbers: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "group_id": self.group_id,
            "normalized_description": self.normalized_description,
            "artifact_ids": list(self.artifact_ids),
            "skill_variant_count": self.skill_variant_count,
            "bundle_variant_count": self.bundle_variant_count,
            "family_cluster_numbers": list(self.family_cluster_numbers),
        }


@dataclass(frozen=True, slots=True)
class FamilyAnalysis:
    """Complete analysis result for one candidate family."""

    name: str
    policy: SimilarityPolicy
    family: ScopeAnalysis
    groups: tuple[ArtifactGroupAnalysis, ...]
    similarities: tuple[SimilarityResult, ...]
    skill_variants: tuple[SkillVariant, ...]
    bundle_variants: tuple[BundleVariant, ...]
    artifacts: tuple[Artifact, ...]

    @property
    def artifact_group_count(self) -> int:
        return len(self.groups)

    @property
    def related_similarities(self) -> tuple[SimilarityResult, ...]:
        return tuple(
            result
            for result in self.similarities
            if self.policy.relates(result)
        )

    @property
    def within_group_related_pair_count(self) -> int:
        variants = {variant.file_sha: variant for variant in self.skill_variants}
        count = 0
        for result in self.related_similarities:
            left = variants[result.left_file_sha]
            right = variants[result.right_file_sha]
            if set(left.group_ids) & set(right.group_ids):
                count += 1
        return count

    @property
    def across_group_related_pair_count(self) -> int:
        return len(self.related_similarities) - self.within_group_related_pair_count

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        output: dict[str, object] = {
            "name": self.name,
            "policy": self.policy.to_dict(),
            "summary": {
                "artifact_count": len(self.artifacts),
                "artifact_group_count": self.artifact_group_count,
                "skill_variant_count": self.family.skill_variant_count,
                "bundle_variant_count": self.family.bundle_variant_count,
                "cluster_count": len(self.family.clusters),
                "related_skill_pair_count": len(self.related_similarities),
                "within_group_related_pair_count": (
                    self.within_group_related_pair_count
                ),
                "across_group_related_pair_count": (
                    self.across_group_related_pair_count
                ),
                "directed_edge_count": self.family.directed_edge_count,
                "within_group_directed_edge_count": (
                    self.family.within_group_directed_edge_count
                ),
                "across_group_directed_edge_count": (
                    self.family.across_group_directed_edge_count
                ),
                "ambiguous_edge_count": self.family.ambiguous_edge_count,
                "within_group_ambiguous_edge_count": (
                    self.family.within_group_ambiguous_edge_count
                ),
                "across_group_ambiguous_edge_count": (
                    self.family.across_group_ambiguous_edge_count
                ),
                "change_counts": {
                    change_type.value: count
                    for change_type, count in self.family.change_counts.items()
                },
            },
            "family": self.family.to_dict(),
            "groups": [group.to_dict() for group in self.groups],
            "skill_variants": [
                {
                    "file_sha": variant.file_sha,
                    "artifact_ids": list(variant.artifact_ids),
                    "group_ids": list(variant.group_ids),
                    "representative_artifact_id": variant.representative_artifact_id,
                    "earliest_observed_at": variant.earliest_observed_at,
                }
                for variant in self.skill_variants
            ],
            "bundle_variants": [
                {
                    "file_sha": variant.file_sha,
                    "sibling_content_sha": variant.sibling_content_sha,
                    "sibling_state_known": variant.sibling_state_known,
                    "artifact_ids": list(variant.artifact_ids),
                    "group_ids": list(variant.group_ids),
                    "representative_artifact_id": variant.representative_artifact_id,
                    "earliest_observed_at": variant.earliest_observed_at,
                }
                for variant in self.bundle_variants
            ],
            "similarities": self._similarities_to_dict(),
        }

        if verbose:
            output["artifacts"] = [
                {
                    "artifact_id": artifact.artifact_id,
                    "group_id": artifact.group_id,
                    "repo_id": artifact.repo_id,
                    "file_sha": artifact.file_sha,
                    "first_commit_at": artifact.first_commit_at,
                    "repo_created_at": artifact.repo_created_at,
                    "sibling_file_count": artifact.sibling_file_count,
                    "sibling_content_sha": artifact.sibling_content_sha,
                }
                for artifact in self.artifacts
            ]

        return output

    def _similarities_to_dict(self) -> list[dict[str, object]]:
        variants = {variant.file_sha: variant for variant in self.skill_variants}
        output = []

        for result in self.similarities:
            left = variants[result.left_file_sha]
            right = variants[result.right_file_sha]
            shared_group_ids = sorted(set(left.group_ids) & set(right.group_ids))
            output.append(
                {
                    **result.to_dict(),
                    "left_artifact_ids": list(left.artifact_ids),
                    "right_artifact_ids": list(right.artifact_ids),
                    "left_representative_artifact_id": left.representative_artifact_id,
                    "right_representative_artifact_id": right.representative_artifact_id,
                    "shared_group_ids": shared_group_ids,
                    "same_artifact_group": bool(shared_group_ids),
                }
            )

        return output


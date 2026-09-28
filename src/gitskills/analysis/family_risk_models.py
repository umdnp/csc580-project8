"""Domain models for candidate-family security review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .family_models import ChangeType, SimilarityPolicy
from .models import RiskCategory, RuleMatch


class ScanSurface(str, Enum):
    """Content surface where a flagged rule was observed."""

    SKILL = "skill"
    SIBLING = "sibling"


@dataclass(frozen=True, slots=True)
class ActiveRule:
    """One security detection rule active during family scanning."""

    rule_id: str
    category: RiskCategory
    description: str

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class SiblingFile:
    """One sibling file associated with an artifact."""

    sibling_id: int
    artifact_id: int
    entry_name: str
    entry_sha: str | None
    content: str | None
    skipped_reason: str | None = None

    @property
    def content_available(self) -> bool:
        return self.content is not None


@dataclass(frozen=True, slots=True)
class FindingSource:
    """Concrete skill or sibling content that produced a flagged rule."""

    surface: ScanSurface
    source_id: int
    entry_name: str | None = None
    matches: tuple[RuleMatch, ...] = ()

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        output: dict[str, object] = {
            "surface": self.surface.value,
            "id": self.source_id,
        }
        if self.entry_name is not None:
            output["entry_name"] = self.entry_name
        if verbose:
            output["matches"] = [_match_to_dict(match) for match in self.matches]
        return output


@dataclass(frozen=True, slots=True)
class FlaggedRule:
    """One rule that warrants review for a directed artifact pair."""

    rule_id: str
    category: RiskCategory
    description: str
    surface: ScanSurface
    source_count: int
    destination_count: int
    finding_sources: tuple[FindingSource, ...]
    positive_delta: bool
    new_or_changed_sibling_content: bool = False

    @property
    def delta(self) -> int:
        return self.destination_count - self.source_count

    @property
    def newly_present(self) -> bool:
        return self.source_count == 0 and self.destination_count > 0

    @property
    def reasons(self) -> tuple[str, ...]:
        reasons = []
        if self.positive_delta:
            reasons.append("positive-delta")
        if self.new_or_changed_sibling_content:
            reasons.append("new-or-changed-sibling-content")
        return tuple(reasons)

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "description": self.description,
            "surface": self.surface.value,
            "source": self.source_count,
            "destination": self.destination_count,
            "delta": self.delta,
            "newly_present": self.newly_present,
            "reasons": list(self.reasons),
            "finding_sources": [
                source.to_dict(verbose=verbose) for source in self.finding_sources
            ],
        }


@dataclass(frozen=True, slots=True)
class SiblingScanSummary:
    """Coverage summary for sibling comparison on one directed pair."""

    source_files: int
    destination_files: int
    new_or_changed_destination_ids: tuple[int, ...] = ()
    unavailable_source_ids: tuple[int, ...] = ()
    unavailable_destination_ids: tuple[int, ...] = ()
    unknown_sha_source_ids: tuple[int, ...] = ()
    unknown_sha_destination_ids: tuple[int, ...] = ()

    @property
    def incomplete(self) -> bool:
        return bool(
            self.unavailable_source_ids
            or self.unavailable_destination_ids
            or self.unknown_sha_source_ids
            or self.unknown_sha_destination_ids
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_files": self.source_files,
            "destination_files": self.destination_files,
            "new_or_changed_destination_ids": list(
                self.new_or_changed_destination_ids
            ),
            "unavailable_source_ids": list(self.unavailable_source_ids),
            "unavailable_destination_ids": list(
                self.unavailable_destination_ids
            ),
            "unknown_sha_source_ids": list(self.unknown_sha_source_ids),
            "unknown_sha_destination_ids": list(self.unknown_sha_destination_ids),
            "incomplete": self.incomplete,
        }


@dataclass(frozen=True, slots=True)
class FlaggedPair:
    """One directed evolution edge with at least one security finding."""

    cluster_number: int
    source_artifact_id: int
    destination_artifact_id: int
    direction_basis: str
    direction_evidence: tuple[str, ...]
    change_type: ChangeType
    containment: float
    jaccard: float
    shared_shingles: int
    flagged_rules: tuple[FlaggedRule, ...]
    sibling_scan: SiblingScanSummary | None = None

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        output: dict[str, object] = {
            "source_artifact_id": self.source_artifact_id,
            "destination_artifact_id": self.destination_artifact_id,
            "direction_basis": self.direction_basis,
            "change_type": self.change_type.value,
            "flagged_rules": [
                rule.to_dict(verbose=verbose) for rule in self.flagged_rules
            ],
        }

        if self.sibling_scan is not None:
            output["sibling_scan"] = self.sibling_scan.to_dict()

        if verbose:
            output.update(
                {
                    "direction_evidence": list(self.direction_evidence),
                    "containment": self.containment,
                    "jaccard": self.jaccard,
                    "shared_shingles": self.shared_shingles,
                }
            )

        return output


@dataclass(frozen=True, slots=True)
class IncompletePair:
    """One directed pair whose changed sibling content could not be fully scanned."""

    cluster_number: int
    source_artifact_id: int
    destination_artifact_id: int
    change_type: ChangeType
    direction_basis: str
    sibling_scan: SiblingScanSummary

    def to_dict(self) -> dict[str, object]:
        return {
            "source_artifact_id": self.source_artifact_id,
            "destination_artifact_id": self.destination_artifact_id,
            "change_type": self.change_type.value,
            "direction_basis": self.direction_basis,
            "sibling_scan": self.sibling_scan.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ClusterRiskAnalysis:
    """Security review summary for one cluster containing directed edges."""

    cluster_number: int
    pairs_analyzed: int
    flagged_pairs: tuple[FlaggedPair, ...]
    incomplete_pairs: tuple[IncompletePair, ...] = ()

    @property
    def pairs_flagged(self) -> int:
        return len(self.flagged_pairs)

    @property
    def pairs_incomplete(self) -> int:
        return len(self.incomplete_pairs)

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        return {
            "cluster": self.cluster_number,
            "pairs_analyzed": self.pairs_analyzed,
            "pairs_flagged": self.pairs_flagged,
            "pairs_incomplete": self.pairs_incomplete,
            "flagged_pairs": [
                pair.to_dict(verbose=verbose) for pair in self.flagged_pairs
            ],
            "incomplete_pairs": [pair.to_dict() for pair in self.incomplete_pairs],
        }


@dataclass(frozen=True, slots=True)
class FamilyRiskAnalysis:
    """Security review result across directed edges in one candidate family."""

    name: str
    similarity_policy: SimilarityPolicy
    active_rules: tuple[ActiveRule, ...]
    clusters: tuple[ClusterRiskAnalysis, ...]
    ambiguous_edges_skipped: int

    @property
    def pairs_analyzed(self) -> int:
        return sum(cluster.pairs_analyzed for cluster in self.clusters)

    @property
    def pairs_flagged(self) -> int:
        return sum(cluster.pairs_flagged for cluster in self.clusters)

    @property
    def pairs_incomplete(self) -> int:
        return sum(cluster.pairs_incomplete for cluster in self.clusters)

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        return {
            "candidate_family": self.name,
            "scanner_scope": "skill-body-and-changed-siblings",
            "similarity_policy": self.similarity_policy.to_dict(),
            "active_rules": [rule.to_dict() for rule in self.active_rules],
            "summary": {
                "pairs_analyzed": self.pairs_analyzed,
                "pairs_flagged": self.pairs_flagged,
                "pairs_incomplete": self.pairs_incomplete,
                "ambiguous_edges_skipped": self.ambiguous_edges_skipped,
                "clusters_analyzed": len(self.clusters),
            },
            "clusters": [
                cluster.to_dict(verbose=verbose) for cluster in self.clusters
            ],
        }


def _match_to_dict(match: RuleMatch) -> dict[str, object]:
    matched_text = match.matched_text
    if match.category is RiskCategory.CREDENTIAL_ACCESS:
        matched_text = "[credential-related content redacted]"

    return {
        "line_number": match.line_number,
        "matched_text": matched_text,
    }

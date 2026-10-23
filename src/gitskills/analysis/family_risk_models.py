"""Domain models for candidate-family security review."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .family_models import ChangeType, SimilarityPolicy
from .models import RiskCategory, RuleMatch
from .evidence_models import Evidence, EvidenceChanges
from .risk_models import RiskAssessment
from gitskills.tools._redaction import redact_text, safe_excerpt


FAMILY_SCAN_REPORT_TYPE = "gitskills-family-scan"


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
    # Paths with stored file rows on only one side are observations about the
    # dataset snapshot, not proof of historical creation or deletion.
    recorded_base_only_paths: tuple[str, ...] = ()
    recorded_derived_only_paths: tuple[str, ...] = ()
    unavailable_source_ids: tuple[int, ...] = ()
    unavailable_destination_ids: tuple[int, ...] = ()
    unknown_sha_source_ids: tuple[int, ...] = ()
    unknown_sha_destination_ids: tuple[int, ...] = ()
    listing_incomplete: bool = False

    @property
    def incomplete(self) -> bool:
        return bool(
            self.listing_incomplete
            or self.unavailable_source_ids
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
            "recorded_base_only_paths": list(self.recorded_base_only_paths),
            "recorded_derived_only_paths": list(self.recorded_derived_only_paths),
            "unavailable_source_ids": list(self.unavailable_source_ids),
            "unavailable_destination_ids": list(
                self.unavailable_destination_ids
            ),
            "unknown_sha_source_ids": list(self.unknown_sha_source_ids),
            "unknown_sha_destination_ids": list(self.unknown_sha_destination_ids),
            "incomplete": self.incomplete,
            "listing_incomplete": self.listing_incomplete,
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
    skill_evidence: EvidenceChanges = EvidenceChanges()
    sibling_evidence: EvidenceChanges = EvidenceChanges()
    risk_assessment: RiskAssessment = RiskAssessment()

    @property
    def evidence_changed(self) -> bool:
        return any((self.skill_evidence.added, self.skill_evidence.removed,
                    self.sibling_evidence.added, self.sibling_evidence.removed))

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        output: dict[str, object] = {
            "source_artifact_id": self.source_artifact_id,
            "destination_artifact_id": self.destination_artifact_id,
            "direction_basis": self.direction_basis,
            "change_type": self.change_type.value,
            "flagged_rules": [
                rule.to_dict(verbose=verbose) for rule in self.flagged_rules
            ],
            "evidence_comparison": {
                "skill": _evidence_changes_dict(self.skill_evidence),
                "siblings": _evidence_changes_dict(self.sibling_evidence),
            },
            "risk_indicators": _risk_assessment_dict(self.risk_assessment),
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
class PairObservation:
    """Compact observation for every directed edge, including unflagged peers."""

    source_artifact_id: int
    destination_artifact_id: int
    direction_basis: str
    change_type: ChangeType
    flagged: bool
    rule_flagged: bool
    skill_evidence_added: int
    skill_evidence_removed: int
    sibling_evidence_added: int
    sibling_evidence_removed: int
    indicator_ids: tuple[str, ...]
    uncertain_indicator_ids: tuple[str, ...]
    finding_count: int
    coverage: str
    evidence_complete: int
    evidence_partial: int
    evidence_unsupported: int
    missing_sibling_content: int
    unknown_sibling_hashes: int
    sibling_listing_incomplete: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "source_artifact_id": self.source_artifact_id,
            "destination_artifact_id": self.destination_artifact_id,
            "direction_basis": self.direction_basis,
            "change_type": self.change_type.value,
            "flagged": self.flagged,
            "rule_flagged": self.rule_flagged,
            "evidence_comparison": {
                "skill": {"added": self.skill_evidence_added,
                          "removed": self.skill_evidence_removed},
                "siblings": {"added": self.sibling_evidence_added,
                             "removed": self.sibling_evidence_removed},
            },
            "indicator_ids": list(self.indicator_ids),
            "uncertain_indicator_ids": list(self.uncertain_indicator_ids),
            "finding_count": self.finding_count,
            "coverage": {
                "status": self.coverage,
                "evidence_records": {
                    "total": (self.evidence_complete + self.evidence_partial
                              + self.evidence_unsupported),
                    "complete": self.evidence_complete,
                    "partial": self.evidence_partial,
                    "unsupported": self.evidence_unsupported,
                },
                "missing_sibling_content": self.missing_sibling_content,
                "unknown_sibling_hashes": self.unknown_sibling_hashes,
                "sibling_listing_incomplete": self.sibling_listing_incomplete,
            },
        }


@dataclass(frozen=True, slots=True)
class ClusterRiskAnalysis:
    """Security review summary for one cluster containing directed edges."""

    cluster_number: int
    pairs_analyzed: int
    flagged_pairs: tuple[FlaggedPair, ...]
    pair_observations: tuple[PairObservation, ...]
    incomplete_pairs: tuple[IncompletePair, ...] = ()
    direction_basis_counts: tuple[tuple[str, int], ...] = ()

    @property
    def pairs_flagged(self) -> int:
        return len(self.flagged_pairs)

    @property
    def pairs_incomplete(self) -> int:
        return len(self.incomplete_pairs)

    @property
    def pairs_with_evidence_changes(self) -> int:
        return sum(pair.evidence_changed for pair in self.flagged_pairs)

    @property
    def pairs_with_indicators(self) -> int:
        return sum(pair.risk_assessment.indicator_count > 0 for pair in self.flagged_pairs)

    @property
    def indicator_frequency(self) -> dict[str, int]:
        counts = Counter(indicator_id for pair in self.flagged_pairs
                         for indicator_id in {i.indicator_id for i in pair.risk_assessment.supported})
        return dict(sorted(counts.items()))

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        # Never serialize a partial cohort as if every directed pair was scanned.
        if len(self.pair_observations) != self.pairs_analyzed:
            raise ValueError(
                f"Cluster {self.cluster_number}: pairs_analyzed={self.pairs_analyzed}, "
                f"pair_observations={len(self.pair_observations)}; "
                "cannot write an incomplete family scan report"
            )
        return {
            "cluster": self.cluster_number,
            "pairs_analyzed": self.pairs_analyzed,
            "pairs_flagged": self.pairs_flagged,
            "pairs_incomplete": self.pairs_incomplete,
            "pairs_with_evidence_changes": self.pairs_with_evidence_changes,
            "pairs_with_indicators": self.pairs_with_indicators,
            "indicator_frequency": self.indicator_frequency,
            "direction_basis_counts": dict(self.direction_basis_counts),
            "pair_observations": [item.to_dict() for item in self.pair_observations],
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

    @property
    def pairs_with_evidence_changes(self) -> int:
        return sum(cluster.pairs_with_evidence_changes for cluster in self.clusters)

    @property
    def pairs_with_indicators(self) -> int:
        return sum(cluster.pairs_with_indicators for cluster in self.clusters)

    @property
    def indicator_frequency(self) -> dict[str, int]:
        counts = Counter()
        for cluster in self.clusters:
            counts.update(cluster.indicator_frequency)
        return dict(sorted(counts.items()))

    @property
    def finding_count(self) -> int:
        """Sum pair-level distinct findings; a construct counts once per pair."""
        return sum(pair.risk_assessment.finding_count
                   for cluster in self.clusters for pair in cluster.flagged_pairs)

    def to_dict(self, *, verbose: bool = False) -> dict[str, object]:
        return {
            "report_type": FAMILY_SCAN_REPORT_TYPE,
            "candidate_family": self.name,
            "scanner_scope": "skill-body-and-changed-siblings",
            "similarity_policy": self.similarity_policy.to_dict(),
            "active_rules": [rule.to_dict() for rule in self.active_rules],
            "summary": {
                "pairs_analyzed": self.pairs_analyzed,
                "pairs_flagged": self.pairs_flagged,
                "pairs_incomplete": self.pairs_incomplete,
                "pairs_evidence_coverage_incomplete": sum(
                    item.coverage != "complete"
                    for cluster in self.clusters for item in cluster.pair_observations
                ),
                "pairs_with_evidence_changes": self.pairs_with_evidence_changes,
                "pairs_with_indicators": self.pairs_with_indicators,
                "indicator_frequency": self.indicator_frequency,
                "indicator_count": len(self.indicator_frequency),
                "finding_count": self.finding_count,
                "direction_basis": _direction_basis_summary(self.clusters),
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
        "matched_text": safe_excerpt(matched_text or ""),
    }


def _evidence_to_dict(item: Evidence) -> dict[str, object]:
    """Public, redacted evidence view; raw and normalized forms remain internal."""
    return {
        "type": item.kind,
        "rule_ids": list(item.rule_ids),
        "source": {
            "filename": redact_text(item.filename),
            "source_id": redact_text(item.source_id) if item.source_id else None,
            "start_offset": item.start_offset,
            "end_offset": item.end_offset,
        },
        "context": {
            "type": item.context.kind,
            "language": item.context.language,
            "heading": redact_text(item.context.heading) if item.context.heading else None,
        },
        "extraction_status": item.extraction_status.value,
        "excerpt": (
            "[credential-related content redacted]"
            if item.kind == "credential_reference"
            else safe_excerpt(item.raw_text)
        ),
    }


def _evidence_changes_dict(changes: EvidenceChanges) -> dict[str, object]:
    return {
        "removed": [_evidence_to_dict(item) for item in changes.removed],
        "added": [_evidence_to_dict(item) for item in changes.added],
    }


def _risk_assessment_dict(assessment: RiskAssessment) -> dict[str, object]:
    def report(indicator) -> dict[str, object]:
        return {
            "id": indicator.indicator_id,
            "reason": redact_text(indicator.reason),
            "evidence": {
                "added": [_evidence_to_dict(item) for item in indicator.added],
                "removed": [_evidence_to_dict(item) for item in indicator.removed],
            },
        }
    return {
        "policy_version": assessment.policy_version,
        "indicator_count": assessment.indicator_count,
        "finding_count": assessment.finding_count,
        "indicators": [report(item) for item in assessment.supported],
        "uncertain": [report(item) for item in assessment.uncertain],
        "coverage": {
            "status": assessment.coverage,
            "notes": [redact_text(note) for note in assessment.coverage_notes],
            "evidence_records": {
                "total": assessment.evidence_total,
                "complete": assessment.evidence_complete,
                "partial": assessment.evidence_partial,
                "unsupported": assessment.evidence_unsupported,
            },
            "missing_sibling_content": assessment.missing_sibling_content,
            "unknown_sibling_hashes": assessment.unknown_sibling_hashes,
            "sibling_listing_incomplete": assessment.sibling_listing_incomplete,
        },
    }


def _direction_basis_summary(clusters: tuple[ClusterRiskAnalysis, ...]) -> dict[str, dict[str, int]]:
    """Counts by direction-evidence basis, with directed edges as denominator."""
    counts: dict[str, dict[str, int]] = {}
    for cluster in clusters:
        for basis, amount in cluster.direction_basis_counts:
            entry = counts.setdefault(basis, {
                "pairs_analyzed": 0, "flagged_pairs": 0, "pairs_with_indicators": 0,
            })
            entry["pairs_analyzed"] += amount
        for pair in cluster.flagged_pairs:
            entry = counts.setdefault(pair.direction_basis, {
                "pairs_analyzed": 0, "flagged_pairs": 0, "pairs_with_indicators": 0,
            })
            entry["flagged_pairs"] += 1
            entry["pairs_with_indicators"] += int(pair.risk_assessment.indicator_count > 0)
    return dict(sorted(counts.items()))

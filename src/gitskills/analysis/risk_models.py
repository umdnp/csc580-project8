"""Observations supporting evidence-based risk review (RDR-010)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence_models import Evidence


POLICY_VERSION = "RDR-010-indicators-v1"


class IndicatorStatus(str, Enum):
    """Whether the available static evidence supports an indicator."""

    SUPPORTED = "supported"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class RiskIndicator:
    """One review signal with references to internal evidence records."""

    indicator_id: str
    reason: str
    added: tuple[Evidence, ...] = ()
    removed: tuple[Evidence, ...] = ()
    status: IndicatorStatus = IndicatorStatus.SUPPORTED


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """Observed indicators and coverage, without an overall risk label."""

    indicators: tuple[RiskIndicator, ...] = ()
    policy_version: str = POLICY_VERSION
    coverage: str = "complete"
    coverage_notes: tuple[str, ...] = ()
    evidence_complete: int = 0
    evidence_partial: int = 0
    evidence_unsupported: int = 0
    missing_sibling_content: int = 0
    unknown_sibling_hashes: int = 0
    sibling_listing_incomplete: bool = False

    @property
    def evidence_total(self) -> int:
        return self.evidence_complete + self.evidence_partial + self.evidence_unsupported

    @property
    def supported(self) -> tuple[RiskIndicator, ...]:
        return tuple(i for i in self.indicators if i.status == IndicatorStatus.SUPPORTED)

    @property
    def uncertain(self) -> tuple[RiskIndicator, ...]:
        return tuple(i for i in self.indicators if i.status == IndicatorStatus.UNCERTAIN)

    @property
    def indicator_count(self) -> int:
        """Number of distinct supported indicator categories, not matches."""
        return len({i.indicator_id for i in self.supported})

    @property
    def finding_count(self) -> int:
        """Number of distinct derived evidence constructs supporting indicators."""
        return len({(e.source_id, e.filename, e.kind, e.start_offset, e.end_offset,
                     e.normalized_text)
                    for indicator in self.supported for e in indicator.added})

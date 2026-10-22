"""Observations supporting evidence-based risk review (RDR-010)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence_models import Evidence


POLICY_VERSION = "RDR-010-phase7"


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
    """Phase 7 indicator observations; classification is deferred to Phase 8."""

    indicators: tuple[RiskIndicator, ...] = ()
    policy_version: str = POLICY_VERSION

    @property
    def supported(self) -> tuple[RiskIndicator, ...]:
        return tuple(i for i in self.indicators if i.status == IndicatorStatus.SUPPORTED)

    @property
    def uncertain(self) -> tuple[RiskIndicator, ...]:
        return tuple(i for i in self.indicators if i.status == IndicatorStatus.UNCERTAIN)

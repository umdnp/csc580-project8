"""Source evidence types used by future extraction and comparison stages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExtractionStatus(str, Enum):
    """How fully an observed source construct could be recovered."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class EvidenceContext:
    """Observable source structure, not an interpretation of intent."""

    kind: str | None = None
    language: str | None = None
    heading: str | None = None
    nearby_text: str | None = None


@dataclass(frozen=True, slots=True)
class Evidence:
    """One source construct associated with one or more detector rules."""

    kind: str
    raw_text: str
    normalized_text: str
    rule_ids: tuple[str, ...]
    filename: str = "SKILL.md"
    source_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    context: EvidenceContext = EvidenceContext()
    extraction_status: ExtractionStatus = ExtractionStatus.COMPLETE
    values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceChanges:
    """Evidence occurrences added or removed between related artifacts."""

    added: tuple[Evidence, ...] = ()
    removed: tuple[Evidence, ...] = ()

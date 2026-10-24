"""Compare normalized evidence occurrences without inferring modified pairs."""

from __future__ import annotations

from collections import Counter

from .evidence_models import Evidence, EvidenceChanges


def _identity(item: Evidence) -> tuple[str, str, str]:
    # Ignore source_id (artifact-specific), rule IDs, locations and context.
    # Retain sibling paths so identical evidence in different files is distinct.
    return item.filename.replace("\\", "/"), item.kind, item.normalized_text


def _unmatched(
    source: tuple[Evidence, ...],
    counterpart: tuple[Evidence, ...],
) -> tuple[Evidence, ...]:
    remaining = Counter(_identity(item) for item in counterpart)
    unmatched: list[Evidence] = []
    for item in source:
        key = _identity(item)
        if remaining[key]:
            remaining[key] -= 1
        else:
            unmatched.append(item)
    return tuple(unmatched)


class EvidenceComparator:
    """Return added/removed occurrences; never guess which changed item replaced another."""

    def compare(
        self,
        base: tuple[Evidence, ...],
        derived: tuple[Evidence, ...],
    ) -> EvidenceChanges:
        return EvidenceChanges(
            added=_unmatched(derived, base),
            removed=_unmatched(base, derived),
        )

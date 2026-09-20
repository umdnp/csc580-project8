"""Base classes for security detection rules."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from gitskills.analysis.models import RiskCategory, RuleMatch


class Rule(ABC):
    """Base interface for a rule that detects one security-sensitive behavior."""

    rule_id: str
    category: RiskCategory
    description: str

    @abstractmethod
    def evaluate(self, text: str) -> tuple[RuleMatch, ...]:
        """Evaluate artifact text and return matches produced by this rule."""


class RegexRule(Rule):
    """Rule implementation backed by one or more regular-expression patterns."""

    patterns: Sequence[str]
    flags: int = re.IGNORECASE | re.MULTILINE

    def evaluate(self, text: str) -> tuple[RuleMatch, ...]:
        """Evaluate all patterns against the complete artifact text."""

        candidates: list[tuple[int, int, str]] = []

        for pattern in self.patterns:
            for match in re.finditer(pattern, text, self.flags):
                candidates.append(
                    (match.start(), match.end(), match.group(0).strip())
                )

        unique_matches = _deduplicate_overlaps(candidates)

        return tuple(
            RuleMatch(
                rule_id=self.rule_id,
                category=self.category,
                message=self.description,
                line_number=_line_number(text, start),
                matched_text=matched_text,
            )
            for start, _, matched_text in unique_matches
        )


def _deduplicate_overlaps(
    matches: list[tuple[int, int, str]],
) -> list[tuple[int, int, str]]:
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    unique: list[tuple[int, int, str]] = []
    last_end = -1

    for candidate in matches:
        start, end, _ = candidate
        if start < last_end:
            continue

        unique.append(candidate)
        last_end = end

    return unique


def _line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1

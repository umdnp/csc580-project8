"""Base classes for security detection rules."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from gitskills.analysis.models import Finding, RiskCategory


class Rule(ABC):
    """Base interface for a rule that detects one security-sensitive behavior."""

    rule_id: str
    category: RiskCategory
    description: str

    @abstractmethod
    def evaluate(self, text: str) -> tuple[Finding, ...]:
        """Evaluate artifact text and return any findings produced by this rule."""


class RegexRule(Rule):
    """Rule implementation backed by one or more regular-expression patterns."""

    patterns: Sequence[str]
    flags: int = re.IGNORECASE | re.MULTILINE

    def evaluate(self, text: str) -> tuple[Finding, ...]:
        findings: list[Finding] = []

        for pattern in self.patterns:
            for match in re.finditer(pattern, text, self.flags):
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        category=self.category,
                        message=self.description,
                        line_number=_line_number(text, match.start()),
                        matched_text=match.group(0).strip(),
                    )
                )

        return tuple(findings)


def _line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1

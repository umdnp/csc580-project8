"""Artifact analyzer that evaluates registered security detection rules."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from gitskills.rules.base import Rule
from gitskills.rules.registry import DEFAULT_RULES

from .models import AnalysisResult, RiskProfile


class SkillAnalyzer:
    """Analyzes skill text and produces a normalized capability profile."""

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules = tuple(DEFAULT_RULES if rules is None else rules)
        self._validate_rule_ids()

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Return the rules evaluated by this analyzer."""

        return self._rules

    def scan(self, text: str) -> AnalysisResult:
        """Analyze artifact text and return its capability profile and findings."""

        findings = tuple(
            finding
            for rule in self._rules
            for finding in rule.evaluate(text)
        )

        profile = RiskProfile.from_categories(
            finding.category for finding in findings
        )

        return AnalysisResult(profile=profile, findings=findings)

    def _validate_rule_ids(self) -> None:
        counts = Counter(rule.rule_id for rule in self._rules)
        duplicate_ids = sorted(
            rule_id for rule_id, count in counts.items() if count > 1
        )

        if duplicate_ids:
            duplicates = ", ".join(duplicate_ids)
            raise ValueError(f"Duplicate rule IDs: {duplicates}")

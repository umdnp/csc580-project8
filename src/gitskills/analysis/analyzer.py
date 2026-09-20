"""Artifact analyzer that evaluates registered security detection rules."""

from __future__ import annotations

from collections.abc import Iterable

from gitskills.rules.base import Rule
from gitskills.rules.registry import DEFAULT_RULES

from .models import AnalysisResult, RiskProfile


class SkillAnalyzer:
    """Analyzes skill text and produces a security capability profile."""

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules = tuple(DEFAULT_RULES if rules is None else rules)
        self._validate_rule_ids()

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Return the rules evaluated by this analyzer."""

        return self._rules

    def scan(self, text: str) -> AnalysisResult:
        """Analyze artifact text and return its profile and rule matches."""

        rule_matches = tuple(
            rule_match
            for rule in self._rules
            for rule_match in rule.evaluate(text)
        )

        profile = RiskProfile.from_categories(
            rule_match.category for rule_match in rule_matches
        )

        return AnalysisResult(
            profile=profile,
            rule_matches=rule_matches,
        )

    def _validate_rule_ids(self) -> None:
        seen: set[str] = set()
        duplicates: set[str] = set()

        for rule in self._rules:
            if rule.rule_id in seen:
                duplicates.add(rule.rule_id)
            seen.add(rule.rule_id)

        if duplicates:
            duplicate_ids = ", ".join(sorted(duplicates))
            raise ValueError(f"Duplicate rule IDs: {duplicate_ids}")

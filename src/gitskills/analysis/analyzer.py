"""Artifact analyzer that evaluates registered security detection rules."""

from __future__ import annotations

from collections.abc import Iterable

from gitskills.rules.base import Rule
from gitskills.rules.registry import DEFAULT_RULES

from .content import mask_frontmatter
from .models import AnalysisResult, RiskProfile


class SkillAnalyzer:
    """Analyzes text and produces a security capability profile."""

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules = tuple(DEFAULT_RULES if rules is None else rules)
        self._validate_rule_ids()

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Return the rules evaluated by this analyzer."""

        return self._rules

    def scan(
        self,
        text: str,
        *,
        exclude_frontmatter: bool | None = None,
        filename: str = "SKILL.md",
        source_id: str | None = None,
    ) -> AnalysisResult:
        """Analyze text and return its profile and rule matches.

        SKILL.md scans exclude YAML frontmatter by default. Other file types
        do not; callers may override this behavior explicitly.
        """

        if exclude_frontmatter is None:
            basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
            exclude_frontmatter = basename.lower() == "skill.md"
        scan_text = mask_frontmatter(text) if exclude_frontmatter else text
        rule_matches = tuple(
            rule_match
            for rule in self._rules
            for rule_match in rule.evaluate(scan_text)
        )

        profile = RiskProfile.from_categories(
            rule_match.category for rule_match in rule_matches
        )

        return AnalysisResult(
            profile=profile,
            rule_matches=rule_matches,
            filename=filename,
            source_id=source_id,
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

"""Domain models used by the GitSkills analyzer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RiskCategory(str, Enum):
    """Normalized security-sensitive capabilities detected in an artifact."""

    COMMAND_EXECUTION = "command_execution"
    NETWORK_ACCESS = "network_access"
    FILESYSTEM_ACCESS = "filesystem_access"
    CREDENTIAL_ACCESS = "credential_access"
    EXTERNAL_CODE_EXECUTION = "external_code_execution"
    SYSTEM_MODIFICATION = "system_modification"


@dataclass(frozen=True, slots=True)
class RuleMatch:
    """One occurrence where a detection rule matched artifact content."""

    rule_id: str
    category: RiskCategory
    message: str
    line_number: int | None = None
    matched_text: str | None = None


@dataclass(frozen=True, slots=True)
class RiskProfile:
    """Security-sensitive capabilities detected in an artifact."""

    capabilities: frozenset[RiskCategory] = frozenset()

    @classmethod
    def from_categories(cls, categories: Iterable[RiskCategory]) -> "RiskProfile":
        """Build a profile from detected capability categories."""

        return cls(capabilities=frozenset(categories))

    def has(self, category: RiskCategory) -> bool:
        """Return whether the profile contains a capability."""

        return category in self.capabilities

    def to_dict(self) -> dict[str, bool]:
        """Return the profile as JSON-serializable data."""

        return {
            category.value: category in self.capabilities
            for category in RiskCategory
        }


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Analysis output for one artifact."""

    profile: RiskProfile
    rule_matches: tuple[RuleMatch, ...]

    @property
    def rule_match_count(self) -> int:
        """Return the total number of rule matches."""

        return len(self.rule_matches)

    def rule_counts(self) -> dict[str, int]:
        """Return rule match counts keyed by rule identifier."""

        counts = Counter(match.rule_id for match in self.rule_matches)
        return dict(sorted(counts.items()))


@dataclass(frozen=True, slots=True)
class RuleDelta:
    """Before-and-after match counts for one rule."""

    rule_id: str
    base: int
    derived: int

    @property
    def delta(self) -> int:
        """Return the change in match count from base to derived."""

        return self.derived - self.base

    def to_dict(self) -> dict[str, int]:
        """Return the rule delta as JSON-serializable data."""

        return {
            "base": self.base,
            "derived": self.derived,
            "delta": self.delta,
        }


@dataclass(frozen=True, slots=True)
class AnalysisComparison:
    """Directional comparison of a derived artifact against a base artifact."""

    base: AnalysisResult
    derived: AnalysisResult
    introduced: RiskProfile
    rule_deltas: tuple[RuleDelta, ...]

    @property
    def rule_match_delta(self) -> int:
        """Return the overall change in rule match count."""

        return self.derived.rule_match_count - self.base.rule_match_count

    def introduces(self, category: RiskCategory) -> bool:
        """Return whether the derived artifact introduced a capability."""

        return self.introduced.has(category)

    def to_dict(self, verbose: bool = False) -> dict[str, object]:
        """Return comparison data suitable for JSON output."""

        output: dict[str, object] = {
            "introduced": self.introduced.to_dict(),
            "rule_match_count": {
                "base": self.base.rule_match_count,
                "derived": self.derived.rule_match_count,
                "delta": self.rule_match_delta,
            },
            "rule_deltas": {
                rule_delta.rule_id: rule_delta.to_dict()
                for rule_delta in self.rule_deltas
            },
        }

        if not verbose:
            return output

        return {
            "base": {
                "profile": self.base.profile.to_dict(),
                "rule_match_count": self.base.rule_match_count,
            },
            "derived": {
                "profile": self.derived.profile.to_dict(),
                "rule_match_count": self.derived.rule_match_count,
            },
            **output,
        }

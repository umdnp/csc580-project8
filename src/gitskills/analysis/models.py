"""Domain models used by the GitSkills analyzer."""

from __future__ import annotations

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
class Finding:
    """A diagnostic rule match produced while analyzing artifact text."""

    rule_id: str
    category: RiskCategory
    message: str
    line_number: int | None = None
    matched_text: str | None = None


@dataclass(frozen=True, slots=True)
class RiskProfile:
    """Security-sensitive capabilities detected in a single artifact."""

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
    """Complete analysis result containing a profile and diagnostic findings."""

    profile: RiskProfile
    findings: tuple[Finding, ...]


@dataclass(frozen=True, slots=True)
class ProfileComparison:
    """Directional comparison of a derived artifact against its base artifact."""

    base: RiskProfile
    derived: RiskProfile
    introduced: RiskProfile

    def introduces(self, category: RiskCategory) -> bool:
        """Return whether the derived artifact introduced a capability."""

        return self.introduced.has(category)

    def to_dict(self, include_profiles: bool = False) -> dict[str, object]:
        """Return comparison data, optionally including both source profiles."""

        if not include_profiles:
            return self.introduced.to_dict()

        return {
            "base": self.base.to_dict(),
            "derived": self.derived.to_dict(),
            "introduced": self.introduced.to_dict(),
        }

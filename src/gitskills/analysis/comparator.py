"""Directional comparison helpers for artifact risk profiles."""

from .models import ProfileComparison, RiskProfile


def compare_profiles(base: RiskProfile, derived: RiskProfile) -> ProfileComparison:
    """Compare derived against base and identify newly introduced capabilities."""

    introduced = RiskProfile(
        capabilities=derived.capabilities - base.capabilities
    )

    return ProfileComparison(
        base=base,
        derived=derived,
        introduced=introduced,
    )

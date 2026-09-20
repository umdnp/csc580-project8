"""Directional comparison helpers for artifact analysis results."""

from .models import AnalysisComparison, AnalysisResult, RiskProfile, RuleDelta


def compare_results(
    base: AnalysisResult,
    derived: AnalysisResult,
) -> AnalysisComparison:
    """Compare derived against base and identify introduced capabilities and rule deltas."""

    introduced = RiskProfile(
        capabilities=derived.profile.capabilities - base.profile.capabilities
    )

    base_counts = base.rule_counts()
    derived_counts = derived.rule_counts()
    rule_ids = sorted(base_counts.keys() | derived_counts.keys())

    rule_deltas = tuple(
        RuleDelta(
            rule_id=rule_id,
            base=base_counts.get(rule_id, 0),
            derived=derived_counts.get(rule_id, 0),
        )
        for rule_id in rule_ids
        if base_counts.get(rule_id, 0) != derived_counts.get(rule_id, 0)
    )

    return AnalysisComparison(
        base=base,
        derived=derived,
        introduced=introduced,
        rule_deltas=rule_deltas,
    )

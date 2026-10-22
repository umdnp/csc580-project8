"""Compare two artifacts and report security-sensitive changes."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from gitskills.analysis.evidence_models import Evidence
from gitskills.analysis.risk_assessor import RiskAssessor
from gitskills.analysis.risk_models import RiskAssessment, RiskIndicator

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.models import (
    AnalysisComparison,
    RiskCategory,
    RuleMatch,
)
from . import _output
from ._redaction import redact_text, safe_excerpt


LOGGER = logging.getLogger("gitskills.scan_diff")
MAX_EXCERPT_LENGTH = 120


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare a derived GitSkills artifact against a base artifact "
            "and report security-sensitive changes."
        )
    )
    parser.add_argument(
        "base",
        type=Path,
        help="Base or earlier artifact.",
    )
    parser.add_argument(
        "derived",
        type=Path,
        help="Derived or later artifact.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include source profiles and individual rule matches.",
    )
    _output.add_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the artifact comparison command."""

    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        output_dir = _output.prepare_directory(args.output)
    except _output.OutputError as exc:
        print(exc, file=sys.stderr)
        return 2

    try:
        base_text = _read_text(args.base)
        derived_text = _read_text(args.derived)
    except (OSError, UnicodeError) as exc:
        LOGGER.error("Unable to read input file: %s", exc)
        return 1

    analyzer = SkillAnalyzer()
    base_result = analyzer.scan(
        base_text, filename=args.base.name, source_id=str(args.base.resolve(strict=False))
    )
    derived_result = analyzer.scan(
        derived_text, filename=args.derived.name, source_id=str(args.derived.resolve(strict=False))
    )
    comparison = compare_results(base_result, derived_result)
    assessment = RiskAssessor().assess(comparison)

    _log_rule_changes(comparison, verbose=args.verbose)
    _log_evidence_changes(comparison, base_text=base_text, derived_text=derived_text)
    _log_risk_indicators(assessment)

    payload = comparison.to_dict(verbose=args.verbose)
    payload["evidence_comparison"] = {
        "removed": [
            _report_evidence(item, base_text) for item in comparison.evidence_removed
        ],
        "added": [
            _report_evidence(item, derived_text) for item in comparison.evidence_added
        ],
    }
    payload["risk_indicators"] = _report_risk_indicators(
        assessment, base_text=base_text, derived_text=derived_text,
    )
    if output_dir is not None:
        try:
            _output.write_json(
                output_dir,
                _output_file_stem(args.derived),
                payload,
            )
        except _output.OutputError as exc:
            print(exc, file=sys.stderr)
            return 1

    print(json.dumps(payload, indent=2))
    return 0


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _output_file_stem(derived: Path) -> str:
    if derived.name.lower() == "skill.md":
        stem = derived.resolve(strict=False).parent.name
    else:
        stem = derived.stem

    if not stem:
        raise _output.OutputError(
            f"Unable to derive an output file name from: {derived}"
        )

    return stem


def _log_rule_changes(
    comparison: AnalysisComparison,
    *,
    verbose: bool,
) -> None:
    matches_by_rule: dict[str, list[RuleMatch]] = defaultdict(list)

    for rule_match in comparison.derived.rule_matches:
        matches_by_rule[rule_match.rule_id].append(rule_match)

    LOGGER.info("RULE COMPARISON")
    for rule_delta in comparison.rule_deltas:
        rule_matches = matches_by_rule.get(rule_delta.rule_id, [])
        description = _rule_description(
            rule_delta.rule_id,
            comparison,
        )

        LOGGER.info(
            "[%s] %d matches (base=%d, delta=%+d): %s",
            rule_delta.rule_id,
            rule_delta.derived,
            rule_delta.base,
            rule_delta.delta,
            description,
        )

        if verbose:
            for rule_match in rule_matches:
                LOGGER.info(
                    "  line %s: %s",
                    rule_match.line_number or "?",
                    _safe_excerpt(rule_match),
                )


def _rule_description(
    rule_id: str,
    comparison: AnalysisComparison,
) -> str:
    for result in (comparison.derived, comparison.base):
        for rule_match in result.rule_matches:
            if rule_match.rule_id == rule_id:
                return rule_match.message

    return "Rule match count changed"


def _source_line(text: str, offset: int | None) -> int | None:
    """Return a 1-based line number for an evidence source span."""

    if offset is None:
        return None
    return text.count("\n", 0, offset) + 1


def _report_evidence(evidence: Evidence, source_text: str) -> dict[str, object]:
    """Build a safe JSON view without exporting raw or normalized evidence."""

    context = evidence.context
    return {
        "type": evidence.kind,
        "rule_ids": list(evidence.rule_ids),
        "source": {
            "filename": redact_text(evidence.filename),
            "start_line": _source_line(source_text, evidence.start_offset),
            "end_line": _source_line(
                source_text,
                evidence.end_offset - 1 if evidence.end_offset is not None else None,
            ),
        },
        "context": {
            "type": context.kind,
            "language": context.language,
            "heading": redact_text(context.heading) if context.heading else None,
        },
        "extraction_status": evidence.extraction_status.value,
        "excerpt": safe_excerpt(evidence.raw_text),
    }


def _log_evidence_changes(
    comparison: AnalysisComparison, *, base_text: str, derived_text: str,
) -> None:
    """Print redacted evidence once per source construct, grouped by change."""

    LOGGER.info("EVIDENCE COMPARISON")
    for label, evidence_list, source in (
        ("REMOVED", comparison.evidence_removed, base_text),
        ("ADDED", comparison.evidence_added, derived_text),
    ):
        LOGGER.info("%s (%d)", label, len(evidence_list))
        for evidence in evidence_list:
            report = _report_evidence(evidence, source)
            position = report["source"]
            LOGGER.info(
                "  [%s] %s (%s:%s): %s",
                ", ".join(evidence.rule_ids),
                evidence.kind,
                position["filename"],
                position["start_line"] or "?",
                report["excerpt"],
            )


def _safe_excerpt(rule_match: RuleMatch) -> str:
    if rule_match.category is RiskCategory.CREDENTIAL_ACCESS:
        return "[credential-related content redacted]"
    return safe_excerpt(rule_match.matched_text or "", limit=MAX_EXCERPT_LENGTH)




def _report_risk_indicators(
    assessment: RiskAssessment, *, base_text: str, derived_text: str,
) -> dict[str, object]:
    """Export only redacted references, never internal Evidence objects."""
    def report(item: RiskIndicator) -> dict[str, object]:
        return {
            "id": item.indicator_id,
            "reason": redact_text(item.reason),
            "evidence": {
                "added": [_report_evidence(e, derived_text) for e in item.added],
                "removed": [_report_evidence(e, base_text) for e in item.removed],
            },
        }

    return {
        "policy_version": assessment.policy_version,
        "indicator_count": assessment.indicator_count,
        "finding_count": assessment.finding_count,
        "indicators": [report(item) for item in assessment.supported],
        "uncertain": [report(item) for item in assessment.uncertain],
        "coverage": {
            "status": assessment.coverage,
            "notes": [redact_text(note) for note in assessment.coverage_notes],
        },
    }


def _log_risk_indicators(assessment: RiskAssessment) -> None:
    """Log observable indicator categories, with uncertainty kept separate."""
    category_count = assessment.indicator_count
    finding_count = assessment.finding_count
    LOGGER.info("RISK INDICATORS (%d %s; %d %s)",
                category_count, "category" if category_count == 1 else "categories",
                finding_count, "finding" if finding_count == 1 else "findings")
    for indicator in assessment.supported:
        LOGGER.info("  [%s] %s", indicator.indicator_id, redact_text(indicator.reason))
    if assessment.uncertain:
        LOGGER.info("UNCERTAIN OBSERVATIONS (%d)", len(assessment.uncertain))
        for indicator in assessment.uncertain:
            LOGGER.info("  [%s] %s", indicator.indicator_id, redact_text(indicator.reason))
    if assessment.coverage != "complete":
        LOGGER.info("COVERAGE: %s", assessment.coverage)

if __name__ == "__main__":
    raise SystemExit(main())

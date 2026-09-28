"""Scan directed candidate-family relationships for increased risky behavior."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.analysis.family_risk_models import (
    ClusterRiskAnalysis,
    FamilyRiskAnalysis,
    FindingSource,
    FlaggedPair,
    FlaggedRule,
    ScanSurface,
    SiblingScanSummary,
)
from gitskills.analysis.models import RiskCategory, RuleMatch
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.data.siblings import DuckDBSiblingRepository
from . import _output


DEFAULT_DB_ENV = "GITSKILLS_DB"
MAX_EXCERPT_LENGTH = 120


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze one candidate family and scan its directed evolution edges "
            "for security-rule findings in SKILL.md bodies and changed siblings."
        )
    )
    parser.add_argument(
        "name",
        help="Exact candidate-family skill name, for example busybox-on-windows.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        help=f"DuckDB path. Defaults to ${DEFAULT_DB_ENV}.",
    )
    parser.add_argument(
        "--shingle-size",
        type=int,
        default=5,
        help="Token shingle size used by family analysis (default: 5).",
    )
    parser.add_argument(
        "--min-containment",
        type=float,
        default=0.80,
        help="Exploratory minimum directional containment (default: 0.80).",
    )
    parser.add_argument(
        "--min-jaccard",
        type=float,
        default=0.30,
        help="Exploratory minimum Jaccard similarity (default: 0.30).",
    )
    parser.add_argument(
        "--min-shared-shingles",
        type=int,
        default=5,
        help="Exploratory minimum shared shingles (default: 5).",
    )
    parser.add_argument(
        "--direction-margin",
        type=float,
        default=0.10,
        help=(
            "Minimum containment difference used to infer direction when "
            "stronger evidence is unavailable (default: 0.10)."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Show similarity/provenance details, sibling paths, and individual "
            "rule matches."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of the human-readable report.",
    )
    _output.add_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run candidate-family security review."""

    args = build_parser().parse_args(argv)

    try:
        output_dir = _output.prepare_directory(args.output)
    except _output.OutputError as exc:
        print(exc, file=sys.stderr)
        return 2

    database = args.db or _database_from_environment()

    if database is None:
        print(
            f"Database path required: pass --db or set {DEFAULT_DB_ENV}.",
            file=sys.stderr,
        )
        return 2

    try:
        policy = SimilarityPolicy(
            shingle_size=args.shingle_size,
            min_containment=args.min_containment,
            min_jaccard=args.min_jaccard,
            min_shared_shingles=args.min_shared_shingles,
            direction_containment_margin=args.direction_margin,
        )
        artifacts = DuckDBFamilyRepository(database).load(args.name)
        if not artifacts:
            print(f"Candidate family not found: {args.name}", file=sys.stderr)
            return 1

        sibling_files = DuckDBSiblingRepository(database).load(
            artifact.artifact_id for artifact in artifacts
        )
        result = FamilyRiskAnalyzer(policy=policy).analyze(
            artifacts,
            sibling_files=sibling_files,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Unable to scan candidate family: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict(verbose=args.verbose)

    if output_dir is not None:
        try:
            _output.write_json(output_dir, args.name, payload)
        except _output.OutputError as exc:
            print(exc, file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_report(result, verbose=args.verbose)

    return 0


def _database_from_environment() -> Path | None:
    value = os.getenv(DEFAULT_DB_ENV)
    return Path(value) if value else None


def _print_report(result: FamilyRiskAnalysis, *, verbose: bool) -> None:
    print(f"Candidate family:        {result.name}")
    print(f"Pairs analyzed:          {result.pairs_analyzed}")
    print(f"Pairs flagged:           {result.pairs_flagged}")
    print(f"Pairs incomplete:        {result.pairs_incomplete}")
    print(f"Ambiguous edges skipped: {result.ambiguous_edges_skipped}")
    print("Scanner scope:           SKILL.md body + changed sibling files")

    if not result.clusters:
        print()
        print("No directed artifact pairs to scan.")
        return

    print()
    if len(result.clusters) == 1:
        _print_flagged_pairs(result.clusters[0], verbose=verbose, indent="")
        _print_incomplete_pairs(result.clusters[0], indent="")
        return

    for cluster in result.clusters:
        print(f"Cluster {cluster.cluster_number}")
        print(f"  Pairs analyzed:   {cluster.pairs_analyzed}")
        print(f"  Pairs flagged:    {cluster.pairs_flagged}")
        print(f"  Pairs incomplete: {cluster.pairs_incomplete}")
        _print_flagged_pairs(cluster, verbose=verbose, indent="  ")
        _print_incomplete_pairs(cluster, indent="  ")
        print()


def _print_flagged_pairs(
    cluster: ClusterRiskAnalysis,
    *,
    verbose: bool,
    indent: str,
) -> None:
    if not cluster.flagged_pairs:
        print(f"{indent}Flagged pairs: none")
        return

    print(f"{indent}Flagged pairs:")
    for pair in cluster.flagged_pairs:
        _print_flagged_pair(pair, verbose=verbose, indent=f"{indent}  ")


def _print_flagged_pair(
    pair: FlaggedPair,
    *,
    verbose: bool,
    indent: str,
) -> None:
    print(
        f"{indent}base: {pair.source_artifact_id}, "
        f"derived: {pair.destination_artifact_id}, "
        f"change: {pair.change_type.value}, "
        f"basis: {pair.direction_basis}"
    )

    if verbose:
        if pair.direction_evidence:
            print(
                f"{indent}  direction evidence: "
                f"{','.join(pair.direction_evidence)}"
            )
        print(
            f"{indent}  similarity: "
            f"containment={pair.containment:.3f} "
            f"jaccard={pair.jaccard:.3f} "
            f"shared={pair.shared_shingles}"
        )

    for rule in pair.flagged_rules:
        _print_flagged_rule(rule, verbose=verbose, indent=f"{indent}  ")

    if pair.sibling_scan is not None and pair.sibling_scan.incomplete:
        _print_sibling_warning(pair.sibling_scan, indent=f"{indent}  ")


def _print_flagged_rule(
    rule: FlaggedRule,
    *,
    verbose: bool,
    indent: str,
) -> None:
    mark_changed = (
        rule.new_or_changed_sibling_content and not rule.positive_delta
    )
    suffix = _finding_source_suffix(
        rule.finding_sources,
        mark_changed=mark_changed,
    )
    delta_text = f"{rule.delta:+d}" if rule.delta else "0"

    print(
        f"{indent}{rule.rule_id} "
        f"source={rule.source_count} "
        f"destination={rule.destination_count} "
        f"delta={delta_text} "
        f"{suffix}"
    )

    if not verbose:
        return

    print(f"{indent}  {rule.description}")
    for source in rule.finding_sources:
        _print_finding_source(source, indent=f"{indent}  ")


def _finding_source_suffix(
    sources: tuple[FindingSource, ...],
    *,
    mark_changed: bool = False,
) -> str:
    if not sources:
        return ""

    surface = sources[0].surface
    ids = ", ".join(str(source.source_id) for source in sources)
    if surface is ScanSurface.SKILL:
        label = "skill"
    else:
        label = "sibling" if len(sources) == 1 else "siblings"

    changed = ", new/changed" if mark_changed else ""
    return f"({label}: {ids}{changed})"


def _print_finding_source(source: FindingSource, *, indent: str) -> None:
    if source.surface is ScanSurface.SKILL:
        print(f"{indent}skill {source.source_id}")
    else:
        path = f" {source.entry_name}" if source.entry_name else ""
        print(f"{indent}sibling {source.source_id}{path}")

    for match in source.matches:
        print(
            f"{indent}  line {match.line_number or '?'}: "
            f"{_safe_excerpt(match)}"
        )


def _print_incomplete_pairs(
    cluster: ClusterRiskAnalysis,
    *,
    indent: str,
) -> None:
    flagged_keys = {
        (pair.source_artifact_id, pair.destination_artifact_id)
        for pair in cluster.flagged_pairs
    }
    remaining = tuple(
        pair
        for pair in cluster.incomplete_pairs
        if (pair.source_artifact_id, pair.destination_artifact_id)
        not in flagged_keys
    )
    if not remaining:
        return

    print(f"{indent}Incomplete sibling scans:")
    for pair in remaining:
        print(
            f"{indent}  base: {pair.source_artifact_id}, "
            f"derived: {pair.destination_artifact_id}, "
            f"change: {pair.change_type.value}, "
            f"basis: {pair.direction_basis}"
        )
        _print_sibling_warning(pair.sibling_scan, indent=f"{indent}    ")


def _print_sibling_warning(summary: SiblingScanSummary, *, indent: str) -> None:
    details = []
    if summary.unavailable_source_ids:
        details.append(
            "source unavailable="
            + ",".join(str(value) for value in summary.unavailable_source_ids)
        )
    if summary.unavailable_destination_ids:
        details.append(
            "derived unavailable="
            + ",".join(
                str(value) for value in summary.unavailable_destination_ids
            )
        )
    if summary.unknown_sha_source_ids:
        details.append(
            "source SHA unknown="
            + ",".join(str(value) for value in summary.unknown_sha_source_ids)
        )
    if summary.unknown_sha_destination_ids:
        details.append(
            "derived SHA unknown="
            + ",".join(
                str(value) for value in summary.unknown_sha_destination_ids
            )
        )

    if details:
        print(f"{indent}sibling scan incomplete: {'; '.join(details)}")


def _safe_excerpt(rule_match: RuleMatch) -> str:
    if rule_match.category is RiskCategory.CREDENTIAL_ACCESS:
        return "[credential-related content redacted]"

    text = " ".join((rule_match.matched_text or "").split())
    if len(text) <= MAX_EXCERPT_LENGTH:
        return text

    return f"{text[:MAX_EXCERPT_LENGTH - 3]}..."


if __name__ == "__main__":
    raise SystemExit(main())

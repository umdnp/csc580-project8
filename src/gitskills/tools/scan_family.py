"""Scan directed candidate-family relationships for increased risky behavior."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import tracemalloc
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
from ._redaction import redact_text, safe_excerpt


DEFAULT_DB_ENV = "GITSKILLS_DB"
MAX_EXCERPT_LENGTH = 120


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze one or more candidate families and scan their directed evolution edges "
            "for security-rule findings in SKILL.md bodies and changed siblings."
        )
    )
    family_input = parser.add_mutually_exclusive_group(required=True)
    family_input.add_argument(
        "name", nargs="?",
        help="Exact candidate-family skill name, for example busybox-on-windows.",
    )
    family_input.add_argument(
        "--input", type=Path, metavar="FILE",
        help="UTF-8 file containing one candidate-family name per line (# comments allowed).",
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Write per-family timing and status to benchmarks.csv in the output directory.",
    )
    parser.add_argument(
        "--tracemalloc", action="store_true",
        help="With --benchmark, also measure peak Python allocations (affects timings; not native RSS).",
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="With --input, scan only the first N names for a smoke test.",
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
    """Run security scans for a named family or a pinned input list."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.tracemalloc and not args.benchmark:
        parser.error("--tracemalloc requires --benchmark")
    if args.limit is not None and (args.input is None or args.limit < 1):
        parser.error("--limit requires --input and a positive integer")
    if args.input is not None and args.output is None:
        parser.error("--input requires --output for per-family JSON reports")

    database = args.db or _database_from_environment()
    if database is None:
        print(f"Database path required: pass --db or set {DEFAULT_DB_ENV}.", file=sys.stderr)
        return 2

    try:
        names = _read_family_names(args.input, args.limit) if args.input else [args.name]
        output_dir = _output.prepare_directory(
            args.output if args.output is not None else _output.DEFAULT_OUTPUT_DIR if args.benchmark else None
        )
        output_stems = _output.report_stems(names) if output_dir is not None else {}
        if args.input is not None:
            if not database.is_file():
                raise ValueError(f"Database not found: {database}")
            assert output_dir is not None
            if any(output_dir.glob("*.json")) or (output_dir / "benchmarks.csv").exists():
                raise ValueError("Batch output already contains scan reports or benchmarks; "
                                 "use a new output directory")
        policy = SimilarityPolicy(
            shingle_size=args.shingle_size,
            min_containment=args.min_containment,
            min_jaccard=args.min_jaccard,
            min_shared_shingles=args.min_shared_shingles,
            direction_containment_margin=args.direction_margin,
        )
    except (OSError, ValueError, _output.OutputError) as exc:
        print(f"Invalid scan input: {exc}", file=sys.stderr)
        return 2

    rows = []
    failed = False
    for index, name in enumerate(names, 1):
        if args.benchmark and args.tracemalloc:
            tracemalloc.start()
        started = time.perf_counter()
        try:
            result, payload, loaded, artifacts = _scan_one(name, database, policy, verbose=args.verbose)
            if output_dir is not None:
                _output.write_json(output_dir, output_stems[name], payload)
            if args.input is None:
                if args.json:
                    print(json.dumps(payload, indent=2))
                else:
                    _print_input_summary(loaded, artifacts)
                    _print_report(result, verbose=args.verbose)
            status = "ok"
        except (OSError, RuntimeError, ValueError, _output.OutputError) as exc:
            print(f"Unable to scan candidate family {name!r}: {exc}", file=sys.stderr)
            status = "failed"
            failed = True
        seconds = time.perf_counter() - started
        peak = tracemalloc.get_traced_memory()[1] if args.benchmark and args.tracemalloc else None
        if args.benchmark and args.tracemalloc:
            tracemalloc.stop()
        if args.benchmark:
            rows.append({
                "family": name, "seconds": f"{seconds:.3f}",
                "peak_python_memory_mib": f"{peak / 1024 / 1024:.2f}" if peak is not None else "",
                "status": status,
            })
        if args.input is not None:
            print(f"[{index}/{len(names)}] {name}: {status}" +
                  (f" in {seconds:.2f}s" if args.benchmark else ""), flush=True)

    if args.benchmark:
        assert output_dir is not None
        try:
            with (output_dir / "benchmarks.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=("family", "seconds", "peak_python_memory_mib", "status")
                )
                writer.writeheader()
                writer.writerows(rows)
        except OSError as exc:
            print(f"Unable to write benchmarks.csv: {exc}", file=sys.stderr)
            return 1
        print(f"Benchmark log: {output_dir / 'benchmarks.csv'}", file=sys.stderr)
    return 1 if failed else 0


def _read_family_names(path: Path, limit: int | None) -> list[str]:
    names = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if limit is not None:
        names = names[:limit]
    if not names or len(set(names)) != len(names):
        raise ValueError("Family input must contain unique, nonempty names")
    return names


def _scan_one(name: str, database: Path, policy: SimilarityPolicy, *, verbose: bool):
    loaded = DuckDBFamilyRepository(database).load_available(name)
    artifacts = loaded.artifacts
    if not artifacts and not loaded.skipped_artifacts:
        raise ValueError(f"Candidate family not found: {name}")
    sibling_files = DuckDBSiblingRepository(database).load(
        artifact.artifact_id for artifact in artifacts
    )
    analyzer = FamilyRiskAnalyzer(policy=policy)
    result = analyzer.analyze(artifacts, sibling_files=sibling_files) if artifacts else FamilyRiskAnalysis(
        name=name, similarity_policy=policy, active_rules=analyzer.active_rules,
        clusters=(), ambiguous_edges_skipped=0,
    )
    payload = result.to_dict(verbose=verbose)
    payload["input_summary"] = {
        "artifacts_loaded": len(artifacts),
        "artifacts_skipped": len(loaded.skipped_artifacts),
        "incomplete": bool(loaded.skipped_artifacts),
    }
    payload["skipped_artifacts"] = [artifact.to_dict() for artifact in loaded.skipped_artifacts]
    return result, payload, loaded, artifacts


def _print_input_summary(loaded, artifacts) -> None:
    print(f"Artifacts loaded:        {len(artifacts)}")
    print(f"Artifacts skipped:       {len(loaded.skipped_artifacts)}")
    for artifact in loaded.skipped_artifacts:
        print(f"  Skipped artifact {artifact.artifact_id}: {artifact.reason}")
    if loaded.skipped_artifacts:
        print("Input coverage incomplete; skipped artifacts have no scan result.")


def _database_from_environment() -> Path | None:
    value = os.getenv(DEFAULT_DB_ENV)
    return Path(value) if value else None


def _print_report(result: FamilyRiskAnalysis, *, verbose: bool) -> None:
    print(f"Candidate family:        {result.name}")
    print(f"Pairs analyzed:          {result.pairs_analyzed}")
    print(f"Pairs flagged:           {result.pairs_flagged}")
    print(f"Pairs incomplete:        {result.pairs_incomplete}")
    print(f"Pairs with evidence changes: {result.pairs_with_evidence_changes}")
    print(f"Pairs with indicators:       {result.pairs_with_indicators}")
    if result.indicator_frequency:
        print("Indicator frequency (pairs):")
        for indicator_id, count in result.indicator_frequency.items():
            print(f"  {indicator_id}: {count}")
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
        print(f"  Pairs with indicators: {cluster.pairs_with_indicators}")
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

    for label, changes in (("SKILL.md", pair.skill_evidence),
                           ("siblings", pair.sibling_evidence)):
        count_added, count_removed = len(changes.added), len(changes.removed)
        if count_added or count_removed:
            print(f"{indent}  {label} evidence: +{count_added}, -{count_removed}")
            if verbose:
                for change_label, items in (("removed", changes.removed),
                                            ("added", changes.added)):
                    for item in items:
                        print(f"{indent}    {change_label}: "
                              f"[{', '.join(item.rule_ids)}] "
                              f"{redact_text(item.filename)}: {safe_excerpt(item.raw_text)}")

    assessment = pair.risk_assessment
    if assessment.indicators:
        categories, findings = assessment.indicator_count, assessment.finding_count
        print(f"{indent}  Risk indicators: {categories} "
              f"{'category' if categories == 1 else 'categories'}, "
              f"{findings} {'finding' if findings == 1 else 'findings'}")
        for indicator in assessment.supported:
            print(f"{indent}    [{indicator.indicator_id}] {redact_text(indicator.reason)}")
        if assessment.uncertain:
            print(f"{indent}    Uncertain observations: {len(assessment.uncertain)}")
    if assessment.coverage != "complete":
        sibling_incomplete = (assessment.missing_sibling_content
                              or assessment.unknown_sibling_hashes
                              or assessment.sibling_listing_incomplete)
        label = "incomplete" if sibling_incomplete else "partial"
        print(f"{indent}  Evidence coverage: {label}")
        print(f"{indent}    {assessment.evidence_complete} of {assessment.evidence_total} "
              "evidence records fully extracted")
        print(f"{indent}    Partially extracted: {assessment.evidence_partial}")
        print(f"{indent}    Unsupported: {assessment.evidence_unsupported}")
        missing = str(assessment.missing_sibling_content) if assessment.missing_sibling_content else "none"
        print(f"{indent}    Missing sibling content: {missing}")
        if assessment.unknown_sibling_hashes:
            print(f"{indent}    Unknown sibling hashes: {assessment.unknown_sibling_hashes}")
        if assessment.sibling_listing_incomplete:
            print(f"{indent}    Sibling listing incomplete")

    if pair.sibling_scan is not None:
        summary = pair.sibling_scan
        if summary.recorded_base_only_paths or summary.recorded_derived_only_paths:
            print(f"{indent}  Sibling paths recorded on one side (not proof of historical introduction/removal):")
            for label, paths in (("base only", summary.recorded_base_only_paths),
                                 ("derived only", summary.recorded_derived_only_paths)):
                if paths:
                    print(f"{indent}    {label}: {', '.join(json.dumps(path) for path in paths)}")
        if summary.incomplete:
            _print_sibling_warning(summary, indent=f"{indent}  ")


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
    if summary.listing_incomplete:
        details.append("sibling listing incomplete")
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

    text = safe_excerpt(rule_match.matched_text or "", limit=MAX_EXCERPT_LENGTH)
    if len(text) <= MAX_EXCERPT_LENGTH:
        return text

    return f"{text[:MAX_EXCERPT_LENGTH - 3]}..."


if __name__ == "__main__":
    raise SystemExit(main())

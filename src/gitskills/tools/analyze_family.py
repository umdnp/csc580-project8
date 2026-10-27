"""Analyze similarity and inferred evolution for candidate families."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from gitskills.analysis.family_models import (
    ChangeType,
    ClusterAnalysis,
    FamilyAnalysis,
    ScopeAnalysis,
    SimilarityPolicy,
)
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.analysis.family_reporting import analyze_family_report
from . import _output
from ._family_input import read_family_names


DEFAULT_DB_ENV = "GITSKILLS_DB"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze SKILL.md similarity, clusters, root candidates, and "
            "inferred evolution for one or more GitSkills candidate families."
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
        "--limit", type=int, metavar="N",
        help="With --input, analyze only the first N names for a smoke test.",
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
        help="Token shingle size (default: 5).",
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
            "chronology is unavailable (default: 0.10)."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Include additional group, variant, and provenance diagnostics. "
            "Full pairwise similarities are included only with --verbose."
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
    """Analyze one candidate family or a list of families."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and (args.input is None or args.limit < 1):
        parser.error("--limit requires --input and a positive integer")
    if args.input is not None and args.output is None:
        parser.error("--input requires --output for per-family JSON reports")

    database = args.db or _database_from_environment()
    if database is None:
        print(
            f"Database path required: pass --db or set {DEFAULT_DB_ENV}.",
            file=sys.stderr,
        )
        return 2

    try:
        names = read_family_names(args.input, args.limit) if args.input else [args.name]
        output_dir = _output.prepare_directory(args.output)
        output_stems = _output.report_stems(names) if output_dir is not None else {}
        if args.input is not None:
            if not database.is_file():
                raise ValueError(f"Database not found: {database}")
            assert output_dir is not None
            if any(output_dir.glob("*.json")) or (output_dir / "benchmarks.csv").exists():
                raise ValueError(
                    "Batch output already contains reports or benchmarks; "
                    "use a new output directory"
                )
        policy = SimilarityPolicy(
            shingle_size=args.shingle_size,
            min_containment=args.min_containment,
            min_jaccard=args.min_jaccard,
            min_shared_shingles=args.min_shared_shingles,
            direction_containment_margin=args.direction_margin,
        )
    except (OSError, ValueError, _output.OutputError) as exc:
        print(f"Invalid analysis input: {exc}", file=sys.stderr)
        return 2

    repository = DuckDBFamilyRepository(database)
    failed = False
    for index, name in enumerate(names, 1):
        try:
            loaded = repository.load_available(name)
            result, payload = analyze_family_report(
                name, loaded, policy=policy, verbose=args.verbose
            )
            output_path = (
                _output.write_json(output_dir, output_stems[name], payload)
                if output_dir is not None else None
            )
            if args.input is None:
                if args.json:
                    print(json.dumps(payload, indent=2))
                else:
                    _print_report(result, verbose=args.verbose)
                    if output_path is not None:
                        print()
                        print(f"JSON report:      {output_path.resolve()}")
            status = "ok"
        except (OSError, RuntimeError, ValueError, _output.OutputError) as exc:
            print(f"Unable to analyze candidate family {name!r}: {exc}", file=sys.stderr)
            status = "failed"
            failed = True
        if args.input is not None:
            print(f"[{index}/{len(names)}] {name}: {status}", flush=True)

    return 1 if failed else 0


def _database_from_environment() -> Path | None:
    value = os.getenv(DEFAULT_DB_ENV)
    return Path(value) if value else None


def _print_report(result: FamilyAnalysis, *, verbose: bool) -> None:
    family = result.family

    print(f"Candidate family: {result.name}")
    print(f"Artifacts:        {len(result.artifacts)}")
    print(f"Artifact groups:  {result.artifact_group_count}")
    print(f"Skill variants:   {family.skill_variant_count}")
    print(f"Bundle variants:  {family.bundle_variant_count}")
    print(f"Clusters:         {len(family.clusters)}")
    print(
        "Policy:           "
        f"{result.policy.shingle_size}-token shingles, "
        f"containment >= {result.policy.min_containment:.2f}, "
        f"Jaccard >= {result.policy.min_jaccard:.2f}, "
        f"shared >= {result.policy.min_shared_shingles}"
    )
    print("Policy status:    exploratory; validate thresholds before final analysis")
    print()

    _print_relationship_summary(result)
    print()

    _print_edge_summary(family)
    print()

    print("Family clusters")
    for cluster in family.clusters:
        _print_cluster(cluster, verbose=verbose)

    print()
    print("Artifact groups")
    for group in result.groups:
        clusters = ", ".join(str(number) for number in group.family_cluster_numbers)
        print(
            f"  Group {group.group_id}: "
            f"artifacts={len(group.artifact_ids)}, "
            f"skills={group.skill_variant_count}, "
            f"bundles={group.bundle_variant_count}, "
            f"family_clusters=[{clusters}]"
        )
        if verbose:
            print(f"    artifact_ids: {_format_ids(group.artifact_ids)}")

    if verbose:
        _print_qualifying_similarities(result)


def _print_cluster(cluster: ClusterAnalysis, *, verbose: bool) -> None:
    roots = cluster.evolution.root_candidate_artifact_ids

    print(
        f"  Cluster {cluster.number}: "
        f"artifacts={len(cluster.artifact_ids)}, "
        f"skills={cluster.skill_variant_count}, "
        f"bundles={cluster.bundle_variant_count}"
    )

    if len(roots) == 1:
        print(f"    Root candidate: {roots[0]}")
    else:
        print(f"    Root candidates: [{_format_ids(roots)}]")

    if verbose:
        print(f"    artifact_ids: {_format_ids(cluster.artifact_ids)}")

    if cluster.evolution.directed_edges:
        print("    Directed edges:")
        for edge in cluster.evolution.directed_edges:
            scope = "within-group" if edge.same_artifact_group else "across-groups"
            scope_text = f" scope={scope}" if verbose else ""
            evidence_text = (
                f" evidence={','.join(edge.evidence)}"
                if verbose and edge.evidence
                else ""
            )
            print(
                f"      {edge.source_artifact_id} -> {edge.target_artifact_id} "
                f"change={edge.change_type.value} "
                f"containment={edge.containment:.3f} "
                f"jaccard={edge.jaccard:.3f} "
                f"basis={edge.basis}"
                f"{evidence_text}"
                f"{scope_text}"
            )
            if verbose:
                for side, chronology in (
                    ("source", edge.source_chronology),
                    ("target", edge.target_chronology),
                ):
                    if chronology is None:
                        continue
                    print(
                        f"        {side} effective_chronology="
                        f"{chronology.effective_chronology} "
                        f"chronology_basis={chronology.chronology_basis} "
                        f"chronology_source=artifact "
                        f"{chronology.chronology_source_artifact_id}"
                    )
    else:
        print("    Directed edges: 0")

    equivalent = cluster.evolution.equivalent_edges
    if equivalent:
        print(
            f"    Equivalent undirected edges: {len(equivalent)} "
            f"(within groups={cluster.evolution.within_group_equivalent_edge_count}, "
            f"across groups={cluster.evolution.across_group_equivalent_edge_count})"
        )
        if verbose:
            for edge in equivalent:
                scope = "within-group" if edge.same_artifact_group else "across-groups"
                print(
                    f"      {edge.left_artifact_id} <-> "
                    f"{edge.right_artifact_id} "
                    f"change={edge.change_type.value} "
                    f"containment={edge.containment_left_to_right:.3f}/"
                    f"{edge.containment_right_to_left:.3f} "
                    f"jaccard={edge.jaccard:.3f} "
                    f"basis={edge.basis} "
                    f"scope={scope}"
                )
    else:
        print("    Equivalent undirected edges: 0")

    ambiguous = cluster.evolution.unresolved_edges
    if ambiguous:
        print(
            f"    Ambiguous edges: {len(ambiguous)} "
            f"(within groups={cluster.evolution.within_group_ambiguous_edge_count}, "
            f"across groups={cluster.evolution.across_group_ambiguous_edge_count})"
        )
        if verbose:
            for edge in ambiguous:
                scope = "within-group" if edge.same_artifact_group else "across-groups"
                evidence_text = (
                    f" evidence={','.join(edge.evidence)}"
                    if edge.evidence
                    else ""
                )
                print(
                    f"      {edge.left_artifact_id} <-> "
                    f"{edge.right_artifact_id} "
                    f"status={edge.relationship_status} "
                    f"change={edge.change_type.value} "
                    f"containment={edge.containment_left_to_right:.3f}/"
                    f"{edge.containment_right_to_left:.3f} "
                    f"jaccard={edge.jaccard:.3f} "
                    f"basis={edge.basis}"
                    f"{evidence_text} "
                    f"scope={scope}"
                )
    else:
        print("    Ambiguous edges: 0")


def _print_qualifying_similarities(result: FamilyAnalysis) -> None:
    variants = {variant.file_sha: variant for variant in result.skill_variants}
    representative = {
        file_sha: variant.representative_artifact_id
        for file_sha, variant in variants.items()
    }

    qualifying = list(result.related_similarities)
    if not qualifying:
        return

    print()
    print("Qualifying skill similarities")
    for similarity in qualifying:
        left_id = representative[similarity.left_file_sha]
        right_id = representative[similarity.right_file_sha]
        left_variant = variants[similarity.left_file_sha]
        right_variant = variants[similarity.right_file_sha]
        scope = (
            "within-group"
            if set(left_variant.group_ids) & set(right_variant.group_ids)
            else "across-groups"
        )
        print(
            f"  {left_id} <-> {right_id}: "
            f"containment="
            f"{similarity.left_to_right_containment:.3f}/"
            f"{similarity.right_to_left_containment:.3f}, "
            f"jaccard={similarity.jaccard:.3f}, "
            f"shared={similarity.shared_shingles}, "
            f"scope={scope}"
        )


def _format_ids(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _print_relationship_summary(result: FamilyAnalysis) -> None:
    total = len(result.related_similarities)
    print(f"Related skill pairs: {total}")
    print(f"  Within artifact groups: {result.within_group_related_pair_count}")
    print(f"  Across artifact groups: {result.across_group_related_pair_count}")


def _print_edge_summary(family: ScopeAnalysis) -> None:
    counts = family.change_counts
    print(f"Directed edges: {family.directed_edge_count}")
    print(f"  Skill only:         {counts[ChangeType.SKILL_ONLY]}")
    print(f"  Siblings only:      {counts[ChangeType.SIBLINGS_ONLY]}")
    print(f"  Skill + siblings:   {counts[ChangeType.SKILL_AND_SIBLINGS]}")
    print(f"  Equivalent:         {counts[ChangeType.EQUIVALENT]}")
    print(f"  Unknown:            {counts[ChangeType.UNKNOWN]}")
    print(f"  Within artifact groups: {family.within_group_directed_edge_count}")
    print(f"  Across artifact groups: {family.across_group_directed_edge_count}")
    print(f"Equivalent undirected edges: {family.equivalent_edge_count}")
    print(
        f"  Within artifact groups: {family.within_group_equivalent_edge_count}"
    )
    print(
        f"  Across artifact groups: {family.across_group_equivalent_edge_count}"
    )
    print(f"Ambiguous edges: {family.ambiguous_edge_count}")
    print(f"  Within artifact groups: {family.within_group_ambiguous_edge_count}")
    print(f"  Across artifact groups: {family.across_group_ambiguous_edge_count}")


if __name__ == "__main__":
    raise SystemExit(main())

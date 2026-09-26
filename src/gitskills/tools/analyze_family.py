"""Analyze similarity and inferred evolution within one candidate family."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_models import (
    ChangeType,
    ClusterAnalysis,
    FamilyAnalysis,
    ScopeAnalysis,
    SimilarityPolicy,
)
from gitskills.data.families import DuckDBFamilyRepository


DEFAULT_DB_ENV = "GITSKILLS_DB"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze SKILL.md similarity, clusters, root candidates, and "
            "inferred evolution for one GitSkills candidate family."
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
        help="Show artifact IDs, qualifying similarities, and ambiguous edge details.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of the human-readable report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run candidate-family analysis."""

    args = build_parser().parse_args(argv)

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
            print(
                f"Candidate family not found: {args.name}",
                file=sys.stderr,
            )
            return 1

        result = FamilyAnalyzer(policy).analyze(artifacts)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Unable to analyze candidate family: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(verbose=args.verbose), indent=2))
    else:
        _print_report(result, verbose=args.verbose)

    return 0


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
            print(
                f"      {edge.source_artifact_id} -> {edge.target_artifact_id} "
                f"change={edge.change_type.value} "
                f"containment={edge.containment:.3f} "
                f"jaccard={edge.jaccard:.3f} "
                f"basis={edge.basis}"
                f"{scope_text}"
            )
    else:
        print("    Directed edges: 0")

    ambiguous_count = len(cluster.evolution.ambiguous_edges)
    if ambiguous_count:
        print(
            f"    Ambiguous edges: {ambiguous_count} "
            f"(within groups={cluster.evolution.within_group_ambiguous_edge_count}, "
            f"across groups={cluster.evolution.across_group_ambiguous_edge_count})"
        )
        if verbose:
            for edge in cluster.evolution.ambiguous_edges:
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
    print(f"Ambiguous edges: {family.ambiguous_edge_count}")
    print(f"  Within artifact groups: {family.within_group_ambiguous_edge_count}")
    print(f"  Across artifact groups: {family.across_group_ambiguous_edge_count}")


if __name__ == "__main__":
    raise SystemExit(main())

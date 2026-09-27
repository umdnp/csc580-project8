"""Compare SKILL.md scanner results along a family's inferred directed edges."""

import argparse
import difflib
import json
import os
import sys
from pathlib import Path

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.family import FamilyAnalyzer
from gitskills.data.families import DuckDBFamilyRepository


def identity(artifact):
    return {"artifact_id": artifact.artifact_id}


def build_report(artifacts, verbose=False):
    result = FamilyAnalyzer().analyze(artifacts)
    by_id = {a.artifact_id: a for a in result.artifacts}
    scanner = SkillAnalyzer()
    scans = {}
    comparisons = []
    ambiguous = []

    for cluster in result.family.clusters:
        for edge in cluster.evolution.directed_edges:
            base = by_id[edge.source_artifact_id]
            derived = by_id[edge.target_artifact_id]
            for artifact in (base, derived):
                if artifact.artifact_id not in scans:
                    content = artifact.content.replace("\r\n", "\n").replace("\r", "\n")
                    scans[artifact.artifact_id] = scanner.scan(content)
            comparison = compare_results(
                scans[base.artifact_id], scans[derived.artifact_id]
            )
            comparisons.append({
                "cluster": cluster.number,
                "base": identity(base),
                "derived": identity(derived),
                "relationship": edge.to_dict(),
                "scan_diff": comparison.to_dict(verbose=False),
            })
        for edge in cluster.evolution.ambiguous_edges:
            ambiguous.append({
                "cluster": cluster.number,
                "left": identity(by_id[edge.left_artifact_id]),
                "right": identity(by_id[edge.right_artifact_id]),
                "relationship": edge.to_dict(),
            })

    return {
        "name": result.name,
        "policy": result.policy.to_dict(),
        "artifact_count": len(result.artifacts),
        "cluster_count": len(result.family.clusters),
        "comparison_count": len(comparisons),
        "notes": [
            "Relationships are inferred using exploratory thresholds.",
            "Scanner changes do not by themselves establish increased risk.",
            "Only SKILL.md content is scanned; sibling files are not compared.",
            "Ambiguous relationships are listed without directional scanning.",
        ],
        "comparisons": comparisons,
        "ambiguous_relationships": ambiguous,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Exact family name")
    parser.add_argument("--db", default=os.getenv("GITSKILLS_DB"))
    parser.add_argument("--output", type=Path, help="Save JSON to this file")
    parser.add_argument("--verbose", action="store_true", help="Include scanner matches")
    args = parser.parse_args(argv)
    if not args.db:
        parser.error("Pass --db or set GITSKILLS_DB")

    try:
        artifacts = DuckDBFamilyRepository(args.db).load(args.name)
        if not artifacts:
            raise ValueError(f"Candidate family not found: {args.name}")
        report = build_report(artifacts, verbose=args.verbose)
        rendered = json.dumps(report, indent=2, ensure_ascii=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
            print(f"Saved {report['comparison_count']} comparisons to {args.output}")
        else:
            print(rendered)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Unable to compare family: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

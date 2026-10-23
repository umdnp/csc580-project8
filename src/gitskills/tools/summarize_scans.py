"""Aggregate scan_family reports into reproducible research tables."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from gitskills.analysis.family_risk_models import FAMILY_SCAN_REPORT_TYPE

INDICATORS = tuple(f"RI-{index:03d}" for index in range(1, 12))
SAMPLE_STRATA = (
    "supported-indicator",
    "coverage-limited",
    "uncertain-indicator",
    "sibling-change",
    "flagged-no-indicator",
    "unflagged-directed",
)
PAIR_FIELDS = (
    "family", "cluster", "base_artifact_id", "derived_artifact_id",
    "edge_type", "direction_basis", "change_type", "flagged", "rule_flagged",
    "skill_added", "skill_removed", "sibling_added", "sibling_removed",
    "indicator_ids", "uncertain_indicator_ids", "finding_count", "coverage_status",
    "evidence_complete", "evidence_partial", "evidence_unsupported",
    "missing_sibling_content", "unknown_sibling_hashes",
    "sibling_listing_incomplete",
)


class ResearchInputError(ValueError):
    """A source report is incomplete or inconsistent with the research contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchInputError(message)


def _read_report(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchInputError(f"Cannot load {path}: {exc}") from exc
    _require(isinstance(data, dict) and data.get("report_type") == FAMILY_SCAN_REPORT_TYPE,
             f"{path}: expected a scan_family report (report_type={FAMILY_SCAN_REPORT_TYPE})")
    _require(isinstance(data.get("candidate_family"), str) and data["candidate_family"],
             f"{path}: missing candidate_family")
    _require(isinstance(data.get("clusters"), list) and isinstance(data.get("summary"), dict),
             f"{path}: missing clusters or summary")
    _require(data.get("edge_selection") in ("primary", "all"),
             f"{path}: missing or invalid edge_selection")
    _require(isinstance(data.get("similarity_policy"), dict) and
             isinstance(data.get("active_rules"), list) and
             isinstance(data.get("scanner_scope"), str),
             f"{path}: missing scan settings")
    return data


def _rows(report: dict) -> list[dict]:
    family = report["candidate_family"]
    summary = report["summary"]
    rows = []
    flagged_keys = set()
    all_keys = set()
    counted_bases: Counter = Counter()
    indicator_counts: Counter = Counter()
    edge_counts: Counter = Counter()
    for cluster in report["clusters"]:
        number = cluster["cluster"]
        observations = cluster.get("pair_observations")
        _require(isinstance(observations, list), f"{family}: missing pair_observations in cluster {number}")
        _require(len(observations) == cluster["pairs_analyzed"],
                 f"{family}: pair count mismatch in cluster {number}: "
                 f"pairs_analyzed={cluster['pairs_analyzed']}, "
                 f"pair_observations={len(observations)}. "
                 "This JSON is internally inconsistent; regenerate this family's report with scan_family.")
        _require(dict(Counter(p.get("edge_type") for p in observations)) == cluster.get("edge_type_counts"),
                 f"{family}: edge types mismatch in cluster {number}")
        _require(sum(bool(p["flagged"]) for p in observations) == cluster["pairs_flagged"],
                 f"{family}: flagged count mismatch in cluster {number}")
        for item in observations:
            key = (number, item["source_artifact_id"], item["destination_artifact_id"])
            _require(key not in all_keys, f"{family}: duplicate directed edge {key}")
            all_keys.add(key)
            edge_type = item.get("edge_type")
            _require(edge_type in ("primary", "additional"), f"{family}: invalid edge_type at {key}")
            _require(report["edge_selection"] == "all" or edge_type == "primary",
                     f"{family}: additional edge in primary scan at {key}")
            edge_counts[edge_type] += 1
            basis = item["direction_basis"]
            counted_bases[basis] += 1
            ids = tuple(sorted(set(item["indicator_ids"])))
            _require(all(i in INDICATORS for i in ids), f"{family}: unknown indicator ID")
            uncertain_ids = tuple(sorted(set(item["uncertain_indicator_ids"])))
            _require(all(i in INDICATORS for i in uncertain_ids), f"{family}: unknown uncertain ID")
            if ids:
                indicator_counts.update(ids)
            coverage = item["coverage"]
            er = coverage["evidence_records"]
            _require(er["total"] == er["complete"] + er["partial"] + er["unsupported"],
                     f"{family}: extraction record totals disagree at {key}")
            ec = item["evidence_comparison"]
            rows.append({
                "family": family, "cluster": number, "edge_type": edge_type,
                "base_artifact_id": item["source_artifact_id"],
                "derived_artifact_id": item["destination_artifact_id"],
                "direction_basis": basis, "change_type": item["change_type"],
                "flagged": int(bool(item["flagged"])),
                "rule_flagged": int(bool(item["rule_flagged"])),
                "skill_added": ec["skill"]["added"],
                "skill_removed": ec["skill"]["removed"],
                "sibling_added": ec["siblings"]["added"],
                "sibling_removed": ec["siblings"]["removed"],
                "indicator_ids": ";".join(ids),
                "uncertain_indicator_ids": ";".join(uncertain_ids),
                "finding_count": item["finding_count"],
                "coverage_status": coverage["status"],
                "evidence_complete": er["complete"],
                "evidence_partial": er["partial"],
                "evidence_unsupported": er["unsupported"],
                "missing_sibling_content": coverage["missing_sibling_content"],
                "unknown_sibling_hashes": coverage["unknown_sibling_hashes"],
                "sibling_listing_incomplete": int(coverage["sibling_listing_incomplete"]),
            })
        flagged = {(number, p["source_artifact_id"], p["destination_artifact_id"])
                   for p in cluster["flagged_pairs"]}
        _require(flagged == {(number, p["source_artifact_id"], p["destination_artifact_id"])
                            for p in observations if p["flagged"]},
                 f"{family}: flagged detail rows disagree with observations in cluster {number}")
        flagged_keys.update(flagged)
        _require(dict(Counter(p["direction_basis"] for p in observations)) == cluster["direction_basis_counts"],
                 f"{family}: direction basis mismatch in cluster {number}")
        _require(dict(Counter(i for p in observations for i in set(p["indicator_ids"])))
                 == cluster["indicator_frequency"],
                 f"{family}: indicator frequency mismatch in cluster {number}")
    _require(dict(edge_counts) == summary.get("edge_type_counts"),
             f"{family}: family edge type counts mismatch")
    _require(len(rows) == summary["pairs_analyzed"], f"{family}: family pair count mismatch")
    _require(len(flagged_keys) == summary["pairs_flagged"], f"{family}: family flagged count mismatch")
    _require(sum(bool(row["indicator_ids"]) for row in rows) == summary["pairs_with_indicators"],
             f"{family}: family indicator-pair count mismatch")
    _require(dict(indicator_counts) == summary["indicator_frequency"],
             f"{family}: family indicator frequency mismatch")
    _require(sum(row["finding_count"] for row in rows) == summary["finding_count"],
             f"{family}: evidence finding count mismatch")
    _require(sum(bool(row["missing_sibling_content"] or row["unknown_sibling_hashes"]
                      or row["sibling_listing_incomplete"]) for row in rows)
             == summary["pairs_incomplete"],
             f"{family}: sibling incomplete pair count mismatch")
    _require(sum(row["skill_added"] + row["skill_removed"] + row["sibling_added"]
                 + row["sibling_removed"] > 0 for row in rows)
             == summary["pairs_with_evidence_changes"],
             f"{family}: evidence change pair count mismatch")
    _require(sum(row["coverage_status"] != "complete" for row in rows)
             == summary["pairs_evidence_coverage_incomplete"],
             f"{family}: coverage count mismatch")
    _require(dict(counted_bases) == {basis: block["pairs_analyzed"]
                                    for basis, block in summary["direction_basis"].items()},
             f"{family}: family direction counts mismatch")
    return rows


def _write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            # Protect exported text identifiers if opened in spreadsheet software.
            safe = {key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                    else value for key, value in row.items()}
            writer.writerow(safe)


def _sample(rows: list[dict], per_stratum: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    chosen = set()
    selected = []
    def matches(row: dict, label: str) -> bool:
        return {
            "supported-indicator": bool(row["indicator_ids"]),
            "coverage-limited": row["coverage_status"] != "complete",
            "uncertain-indicator": bool(row["uncertain_indicator_ids"]),
            "sibling-change": row["change_type"] in ("siblings-only", "skill+siblings"),
            "flagged-no-indicator": bool(row["flagged"] and not row["indicator_ids"]),
            "unflagged-directed": not row["flagged"],
        }[label]
    for stratum in SAMPLE_STRATA:
        candidates = [row for row in rows if matches(row, stratum)
                      and (row["family"], row["cluster"], row["base_artifact_id"],
                           row["derived_artifact_id"]) not in chosen]
        rng.shuffle(candidates)
        for row in candidates[:per_stratum]:
            key = (row["family"], row["cluster"], row["base_artifact_id"], row["derived_artifact_id"])
            chosen.add(key)
            selected.append({**row, "sampling_stratum": stratum})
    return selected


def _annotation_metrics(path: Path, rows: list[dict]) -> dict:
    lookup = {(str(row["family"]), str(row["cluster"]), str(row["base_artifact_id"]),
               str(row["derived_artifact_id"])): row for row in rows}
    totals = Counter()
    per_indicator = {iid: Counter() for iid in INDICATORS}
    reviewed = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("review_status", "").strip().lower() != "complete":
                continue
            key = (row["family"], row["cluster"], row["base_artifact_id"], row["derived_artifact_id"])
            _require(key in lookup, f"Unknown reviewed pair: {key}")
            _require(key not in reviewed, f"Duplicate reviewed pair: {key}")
            reviewed.add(key)
            observed = set(filter(None, row["manual_supported_indicator_ids"].split(";")))
            _require(observed <= set(INDICATORS), f"Unrecognized manual indicator at {key}")
            uncertain = set(filter(None, row.get("manual_uncertain_indicator_ids", "").split(";")))
            _require(uncertain <= set(INDICATORS) and not (uncertain & observed),
                     f"Invalid manual uncertain indicators at {key}")
            predicted = set(filter(None, lookup[key]["indicator_ids"].split(";")))
            for iid in INDICATORS:
                if iid in uncertain:
                    continue
                outcome = ("tp" if iid in predicted and iid in observed else
                           "fp" if iid in predicted else "fn" if iid in observed else "tn")
                totals[outcome] += 1
                per_indicator[iid][outcome] += 1
    def rates(ct: Counter) -> dict:
        return {"tp": ct["tp"], "fp": ct["fp"], "fn": ct["fn"], "tn": ct["tn"],
                "precision": round(ct["tp"] / (ct["tp"] + ct["fp"]), 4)
                if ct["tp"] + ct["fp"] else None,
                "recall": round(ct["tp"] / (ct["tp"] + ct["fn"]), 4)
                if ct["tp"] + ct["fn"] else None}
    return {"reviewed_pairs": len(reviewed), "scope": "reviewed sample only; not population estimates",
            "micro": rates(totals), "by_indicator": {i: rates(ct) for i, ct in per_indicator.items()}}


def _svg_frequency(path: Path, frequency: Counter, total: int) -> None:
    max_count = max([*frequency.values(), 1])
    canvas = ['<svg xmlns="http://www.w3.org/2000/svg" width="780" height="520" viewBox="0 0 780 520">',
              '<rect width="780" height="520" fill="white"/>',
              '<text x="25" y="32" font-family="sans-serif" font-weight="bold" font-size="18">Risk indicators in directed pairs</text>',
              f'<text x="25" y="55" font-family="sans-serif" font-size="12" fill="#555">Denominator: {total} directed pairs; indicators may overlap</text>']
    for idx, iid in enumerate(INDICATORS):
        y = 80 + idx * 38
        count = frequency[iid]
        width = int(535 * count / max_count)
        canvas.append(f'<text x="25" y="{y+17}" font-family="monospace" font-size="13">{escape(iid)}</text>')
        canvas.append(f'<rect x="105" y="{y}" width="{width}" height="21" fill="#3a6082"/>')
        canvas.append(f'<text x="{113+width}" y="{y+16}" font-family="sans-serif" font-size="12">{count} ({count / total:.1%})</text>' if total
                      else f'<text x="113" y="{y+16}" font-family="sans-serif" font-size="12">0</text>')
    canvas.append('</svg>')
    path.write_text("\n".join(canvas) + "\n", encoding="utf-8")


def summarize(paths: list[Path], output: Path, *, per_stratum: int | None = None,
              seed: int = 580, annotations: Path | None = None) -> dict:
    """Summarize family reports; reject malformed or duplicate inputs."""
    _require(bool(paths), "At least one report is required")
    reports = [_read_report(path) for path in sorted(paths)]
    names = [r["candidate_family"] for r in reports]
    _require(len(names) == len(set(names)), "Duplicate family report: each family must be counted once")
    policies = {json.dumps(r["similarity_policy"], sort_keys=True) for r in reports}
    rules = {json.dumps(r["active_rules"], sort_keys=True) for r in reports}
    scopes = {r["scanner_scope"] for r in reports}
    selections = {r["edge_selection"] for r in reports}
    _require(len(policies) == len(rules) == len(scopes) == len(selections) == 1,
             "Reports have different similarity policies, rules, scanner scopes, or edge selections; analyze separate cohorts")
    all_rows = sorted((row for report in reports for row in _rows(report)),
                      key=lambda r: (r["family"], r["cluster"], r["base_artifact_id"],
                                     r["derived_artifact_id"]))
    pairs = len(all_rows)
    indicator_frequency: Counter = Counter(i for row in all_rows
                                           for i in row["indicator_ids"].split(";") if i)
    family_rows = []
    direction = defaultdict(lambda: Counter())
    type_stats = {kind: Counter() for kind in ("primary", "additional")}
    type_indicators = {kind: Counter() for kind in ("primary", "additional")}
    for report in sorted(reports, key=lambda r: r["candidate_family"]):
        count = report["summary"]
        family_rows.append({"family": report["candidate_family"],
                            "artifacts_loaded": report.get("input_summary", {}).get("artifacts_loaded", ""),
                            "artifacts_skipped": report.get("input_summary", {}).get("artifacts_skipped", ""),
                            "primary_pairs": count["edge_type_counts"].get("primary", 0),
                            "additional_pairs": count["edge_type_counts"].get("additional", 0),
                            **{k: count[k] for k in ("pairs_analyzed", "pairs_flagged", "pairs_incomplete",
                                                   "pairs_with_evidence_changes", "pairs_with_indicators",
                                                   "pairs_evidence_coverage_incomplete", "ambiguous_edges_skipped")}})
    for row in all_rows:
        category = type_stats[row["edge_type"]]
        category["pairs_analyzed"] += 1
        category["pairs_flagged"] += row["flagged"]
        category["pairs_with_indicators"] += bool(row["indicator_ids"])
        category["pairs_coverage_incomplete"] += row["coverage_status"] != "complete"
        category["finding_count"] += row["finding_count"]
        type_indicators[row["edge_type"]].update(filter(None, row["indicator_ids"].split(";")))
        ct = direction[row["direction_basis"]]
        ct["pairs_analyzed"] += 1
        ct["pairs_flagged"] += row["flagged"]
        ct["pairs_with_indicators"] += bool(row["indicator_ids"])
        ct["pairs_coverage_incomplete"] += row["coverage_status"] != "complete"
    summary = {
        "report_type": "gitskills-research-summary",
        "similarity_policy": reports[0]["similarity_policy"],
        "scanner_scope": reports[0]["scanner_scope"],
        "edge_selection": reports[0]["edge_selection"],
        "family_count": len(reports),
        "directed_pairs_analyzed": pairs,
        "edge_type_breakdown": {
            kind: {"pairs_analyzed": type_stats[kind]["pairs_analyzed"],
                   "pairs_flagged": type_stats[kind]["pairs_flagged"],
                   "pairs_with_indicators": type_stats[kind]["pairs_with_indicators"],
                   "pairs_coverage_incomplete": type_stats[kind]["pairs_coverage_incomplete"],
                   "finding_count": type_stats[kind]["finding_count"],
                   "indicator_frequency_pairs": {iid: type_indicators[kind][iid] for iid in INDICATORS}}
            for kind in ("primary", "additional")
        },
        "flagged_pairs": sum(r["flagged"] for r in all_rows),
        "pairs_with_supported_indicators": sum(bool(r["indicator_ids"]) for r in all_rows),
        "supported_findings": sum(r["finding_count"] for r in all_rows),
        "families_with_supported_indicators": len({r["family"] for r in all_rows if r["indicator_ids"]}),
        "pairs_with_evidence_changes": sum(r["skill_added"] + r["skill_removed"]
                                           + r["sibling_added"] + r["sibling_removed"] > 0 for r in all_rows),
        "pairs_with_sibling_evidence_changes": sum(r["sibling_added"] + r["sibling_removed"] > 0 for r in all_rows),
        "pairs_with_incomplete_evidence_coverage": sum(r["coverage_status"] != "complete" for r in all_rows),
        "pairs_with_missing_sibling_content": sum(r["missing_sibling_content"] > 0 for r in all_rows),
        "sibling_incomplete_pairs": sum(r["pairs_incomplete"] for r in family_rows),
        "ambiguous_edges_skipped": sum(r["ambiguous_edges_skipped"] for r in family_rows),
        "indicator_frequency_pairs": {iid: indicator_frequency[iid] for iid in INDICATORS},
        "denominator_note": "Percentages use directed_pairs_analyzed (or the corresponding edge-type denominator); categories overlap. Ambiguous edges are excluded. Comparisons can share artifacts and are not independent historical events.",
    }
    chosen = _sample(all_rows, per_stratum, seed) if per_stratum is not None else []
    if annotations is not None and annotations.resolve() == (output / "validation_annotations_template.csv").resolve():
        raise ResearchInputError("Copy the template to a separate reviewed CSV before using --annotations")
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "directed_pairs.csv", all_rows, PAIR_FIELDS)
    _write_csv(output / "families.csv", family_rows, tuple(family_rows[0].keys()))
    _write_csv(output / "direction_basis.csv", [dict(direction_basis=k, **v) for k, v in sorted(direction.items())],
               ("direction_basis", "pairs_analyzed", "pairs_flagged", "pairs_with_indicators", "pairs_coverage_incomplete"))
    _write_csv(output / "edge_types.csv", [
        {"edge_type": kind,
         **{field: type_stats[kind][field] for field in (
             "pairs_analyzed", "pairs_flagged", "pairs_with_indicators",
             "pairs_coverage_incomplete", "finding_count")}}
        for kind in ("primary", "additional")
    ], ("edge_type", "pairs_analyzed", "pairs_flagged", "pairs_with_indicators",
        "pairs_coverage_incomplete", "finding_count"))
    _write_csv(output / "indicator_frequency_by_edge_type.csv", [
        {"edge_type": kind, "indicator_id": iid, "pairs": type_indicators[kind][iid],
         "directed_pairs": type_stats[kind]["pairs_analyzed"],
         "percent_of_directed_pairs":
             round(100 * type_indicators[kind][iid] / type_stats[kind]["pairs_analyzed"], 3)
             if type_stats[kind]["pairs_analyzed"] else 0}
        for kind in ("primary", "additional") for iid in INDICATORS
    ], ("edge_type", "indicator_id", "pairs", "directed_pairs", "percent_of_directed_pairs"))
    _write_csv(output / "indicator_frequency.csv", [
        {"indicator_id": iid, "pairs": indicator_frequency[iid], "directed_pairs": pairs,
         "percent_of_directed_pairs": round(100 * indicator_frequency[iid] / pairs, 3) if pairs else 0}
        for iid in INDICATORS], ("indicator_id", "pairs", "directed_pairs", "percent_of_directed_pairs"))
    if per_stratum is not None:
        _write_csv(output / "validation_sample.csv", chosen, (*PAIR_FIELDS, "sampling_stratum"))
        _write_csv(output / "validation_annotations_template.csv", [
            {**row, "reviewer": "", "review_status": "pending", "review_date": "",
             "manual_supported_indicator_ids": "", "manual_uncertain_indicator_ids": "",
             "direction_basis_review": "", "sibling_coverage_review": "",
             "missed_observations": "", "false_positive_notes": "", "notes": ""}
            for row in chosen], (*PAIR_FIELDS, "sampling_stratum", "reviewer", "review_status",
                                "review_date", "manual_supported_indicator_ids", "manual_uncertain_indicator_ids",
                                "direction_basis_review", "sibling_coverage_review",
                                "missed_observations", "false_positive_notes", "notes"))
    _svg_frequency(output / "indicator_frequency.svg", indicator_frequency, pairs)
    if per_stratum is not None:
        summary["sampling"] = {"seed": seed, "per_stratum": per_stratum,
                               "sampled_pairs": len(chosen),
                               "strata_counts": dict(sorted(Counter(row["sampling_stratum"] for row in chosen).items()))}
    if annotations is not None:
        summary["manual_validation"] = _annotation_metrics(annotations, all_rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path,
                        help="scan_family JSON files, or directories containing those files")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument("--per-stratum", type=int,
                        help="Optionally select up to N pairs per manual-review stratum")
    parser.add_argument("--seed", type=int, default=580)
    parser.add_argument("--annotations", type=Path,
                        help="Optional completed validation_annotations.csv for sample-only metrics")
    args = parser.parse_args(argv)
    if args.per_stratum is not None and args.per_stratum < 1:
        parser.error("--per-stratum must be at least 1")
    if args.annotations is not None and args.per_stratum is None:
        parser.error("--annotations requires --per-stratum to select a review sample")
    paths = []
    for path in args.reports:
        paths.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    try:
        result = summarize(paths, args.output, per_stratum=args.per_stratum,
                           seed=args.seed, annotations=args.annotations)
    except (OSError, KeyError, TypeError, ResearchInputError) as exc:
        print(f"Unable to summarize reports: {exc}", file=sys.stderr)
        return 1
    print(f"Families: {result['family_count']}; directed pairs: {result['directed_pairs_analyzed']}; "
          f"pairs with indicators: {result['pairs_with_supported_indicators']}")
    print(f"Research outputs: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

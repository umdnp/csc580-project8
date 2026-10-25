"""Summarize research cohorts and prepare reproducible manual validation samples."""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from gitskills.analysis.family_risk_models import FAMILY_SCAN_REPORT_TYPE
from gitskills.analysis.family_models import FamilyAnalysis

INDICATORS = tuple(f"RI-{index:03d}" for index in range(1, 12))
SAMPLE_STRATA = (
    "supported-indicator",
    "coverage-limited",
    "uncertain-indicator",
    "sibling-change",
    "flagged-no-indicator",
    "unflagged-directed",
)
RELATIONSHIP_STRATA = ("ambiguous", "equivalent", "no-related-edge")
RELATIONSHIP_FIELDS = (
    "family", "cluster", "artifact_a_id", "artifact_b_id", "relationship_status",
    "direction_basis", "change_type", "similarity_jaccard", "similarity_containment",
    "similarity_shared_shingles", "sampling_stratum",
)
DIRECTED_REVIEW_FIELDS = (
    "reviewer", "review_phase", "review_status", "review_date",
    "manual_relatedness", "direction_basis_review", "scanner_rule_review",
    "manual_rule_judgments", "manual_change_review", "manual_change_judgments", "indicator_review_scope",
    "manual_supported_indicator_ids", "manual_uncertain_indicator_ids",
    "sibling_coverage_review", "missed_observations", "false_positive_notes", "notes",
)
RELATIONSHIP_REVIEW_FIELDS = (
    "reviewer", "review_phase", "review_status", "review_date",
    "manual_relatedness", "direction_basis_review", "notes",
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


def _read_report(path: Path | dict) -> dict:
    if isinstance(path, dict):
        data = path
        path = Path("<in-memory-scan>")
    else:
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


def _split_ids(value: str, *, key: tuple, field: str) -> set[str]:
    values = [part.strip() for part in value.split(";") if part.strip()]
    _require(len(values) == len(set(values)), f"Duplicate {field} at {key}")
    _require(set(values) <= set(INDICATORS), f"Unknown {field} at {key}")
    return set(values)


def _read_adjudicated(path: Path, lookup: dict[tuple[str, ...], dict],
                      key_fields: tuple[str, ...], required_fields: tuple[str, ...]):
    """Read final decisions only; independently completed reviewer copies stay separate."""
    reviewed = set()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _require(reader.fieldnames is not None and
                 set((*key_fields, *required_fields)) <= set(reader.fieldnames),
                 f"{path}: missing review columns: "
                 f"{sorted(set((*key_fields, *required_fields)) - set(reader.fieldnames or []))}")
        for row in reader:
            status = (row["review_status"] or "").strip().lower()
            _require(status in ("pending", "complete"),
                     f"{path}: review_status must be pending or complete")
            if status != "complete":
                continue
            key = tuple(row[field].strip() for field in key_fields)
            _require(key in lookup, f"Unknown or unsampled reviewed pair: {key}")
            _require(key not in reviewed, f"Duplicate reviewed pair: {key}")
            reviewed.add(key)
            _require(row["review_phase"].strip() == "adjudicated",
                     f"{key}: metrics require review_phase=adjudicated")
            _require(bool(row["reviewer"].strip()) and bool(row["review_date"].strip()),
                     f"{key}: completed review requires reviewer and review_date")
            yield key, row, lookup[key]


def _label(row: dict, field: str, options: tuple[str, ...], key: tuple) -> str:
    value = row.get(field, "").strip()
    _require(value in options, f"{key}: {field} must be one of {', '.join(options)}")
    return value


def _annotation_metrics(path: Path, selected_rows: list[dict]) -> dict:
    """Calculate indicator metrics only after explicit comprehensive review."""
    key_fields = ("family", "cluster", "base_artifact_id", "derived_artifact_id")
    lookup = {tuple(str(row[field]) for field in key_fields): row for row in selected_rows}
    totals = Counter()
    per_indicator = {iid: Counter() for iid in INDICATORS}
    reasons = Counter()
    reviewed_count = 0
    for key, row, reference in _read_adjudicated(path, lookup, key_fields, DIRECTED_REVIEW_FIELDS):
        reviewed_count += 1
        related = _label(row, "manual_relatedness", ("related", "not_related", "uncertain"), key)
        direction = _label(row, "direction_basis_review",
                           ("supported", "unsupported", "uncertain", "not_applicable"), key)
        _label(row, "scanner_rule_review",
               ("correct", "partially_correct", "incorrect", "uncertain", "not_applicable"), key)
        _label(row, "manual_change_review",
               ("correct", "partially_correct", "incorrect", "uncertain", "not_applicable"), key)
        rule_judgments = [entry.strip() for entry in row["manual_rule_judgments"].split(";") if entry.strip()]
        for judgment in rule_judgments:
            _require(re.fullmatch(r"[A-Z]+-\d{3}=(correct|false_positive|false_negative|uncertain|not_applicable)",
                                  judgment) is not None,
                     f"{key}: invalid rule judgment {judgment!r}")
        _require(len(rule_judgments) == len({entry.split("=", 1)[0] for entry in rule_judgments}),
                 f"{key}: duplicate rule judgment")
        coverage = _label(row, "sibling_coverage_review",
                          ("complete", "incomplete", "uncertain", "not_applicable"), key)
        _label(row, "indicator_review_scope", ("all_assessed", "not_assessable"), key)
        supported = _split_ids(row["manual_supported_indicator_ids"], key=key, field="manual supported indicators")
        uncertain = _split_ids(row["manual_uncertain_indicator_ids"], key=key, field="manual uncertain indicators")
        _require(not supported & uncertain, f"{key}: overlapping supported and uncertain indicators")
        change_judgments = [entry.strip() for entry in row["manual_change_judgments"].split(";") if entry.strip()]
        for judgment in change_judgments:
            pieces = judgment.split("=", 1)
            _require(len(pieces) == 2 and pieces[0] in INDICATORS and pieces[1] in
                     ("introduced", "removed", "retained", "mixed", "none_detected",
                      "direction_unknown", "uncertain", "not_applicable"),
                     f"{key}: invalid change judgment {judgment!r}")
        _require(len(change_judgments) == len({entry.split('=', 1)[0] for entry in change_judgments}),
                 f"{key}: duplicate indicator change judgment")
        if row["indicator_review_scope"] != "all_assessed":
            reasons["not_assessable"] += 1
        elif related != "related":
            reasons["unrelated_or_uncertain"] += 1
        elif direction != "supported":
            reasons["direction_not_supported"] += 1
        elif reference["coverage_status"] != "complete" or coverage != "complete":
            reasons["incomplete_coverage"] += 1
        else:
            reasons["assessable_pairs"] += 1
            predicted = set(filter(None, reference["indicator_ids"].split(";")))
            for iid in INDICATORS:
                if iid in uncertain:
                    reasons["uncertain_indicator_judgments"] += 1
                    continue
                outcome = ("tp" if iid in predicted and iid in supported else
                           "fp" if iid in predicted else "fn" if iid in supported else "tn")
                totals[outcome] += 1
                per_indicator[iid][outcome] += 1

    def rates(ct: Counter) -> dict:
        return {"tp": ct["tp"], "fp": ct["fp"], "fn": ct["fn"], "tn": ct["tn"],
                "precision": round(ct["tp"] / (ct["tp"] + ct["fp"]), 4)
                if ct["tp"] + ct["fp"] else None,
                "recall": round(ct["tp"] / (ct["tp"] + ct["fn"]), 4)
                if ct["tp"] + ct["fn"] else None}
    return {"reviewed_pairs": reviewed_count, "assessable_pairs": reasons["assessable_pairs"],
            "excluded_pairs": {name: reasons[name] for name in
                               ("not_assessable", "unrelated_or_uncertain",
                                "direction_not_supported", "incomplete_coverage")},
            "uncertain_indicator_judgments": reasons["uncertain_indicator_judgments"],
            "scope": "adjudicated, assessable sample only; not population estimates",
            "micro": rates(totals), "by_indicator": {i: rates(ct) for i, ct in per_indicator.items()}}


def _read_family_report(path: Path, policies: set[str], allowed_names: set[str]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ResearchInputError(f"Cannot load {path}: {exc}") from exc
    _require(isinstance(data, dict) and data.get("name") in allowed_names,
             f"{path}: analyze_family report must correspond to a scanned family")
    _require(json.dumps(data.get("policy"), sort_keys=True) in policies,
             f"{path}: analyze_family similarity policy differs from scan reports")
    _require(isinstance(data.get("artifacts"), list) and
             isinstance(data.get("similarities"), list) and
             isinstance(data.get("family", {}).get("clusters"), list),
             f"{path}: requires a complete analyze_family report (artifacts and similarities); regenerate this family")
    return data


def _relationship_candidates(reports: list[dict]) -> list[dict]:
    """Select unresolved edges and measured non-qualifying, same-name comparisons."""
    output = []
    for report in reports:
        family = report["name"]
        for cluster in report["family"]["clusters"]:
            for edge in cluster["evolution"]["ambiguous_edges"]:
                left, right = sorted((edge["left_artifact_id"], edge["right_artifact_id"]))
                label = ("equivalent" if edge["relationship_status"] == "equivalent" else "ambiguous")
                output.append({"family": family, "cluster": cluster["cluster"],
                               "artifact_a_id": left, "artifact_b_id": right,
                               "relationship_status": edge["relationship_status"],
                               "direction_basis": edge["basis"], "change_type": edge["change_type"],
                               "similarity_jaccard": edge["jaccard"],
                               "similarity_containment": max(edge["containment_left_to_right"],
                                                             edge["containment_right_to_left"]),
                               "similarity_shared_shingles": edge["shared_shingles"],
                               "sampling_stratum": label})
        policy = report["policy"]
        seen = set()
        for sim in report["similarities"]:
            if (max(sim["left_to_right_containment"], sim["right_to_left_containment"])
                    >= policy["min_containment"] and sim["jaccard"] >= policy["min_jaccard"]
                    and sim["shared_shingles"] >= policy["min_shared_shingles"]):
                continue
            # Identical content occurrences are not treated as negative relationships.
            if sim["left_file_sha"] == sim["right_file_sha"]:
                continue
            for left in sim["left_artifact_ids"]:
                for right in sim["right_artifact_ids"]:
                    a, b = sorted((left, right))
                    if a == b or (a, b) in seen:
                        continue
                    seen.add((a, b))
                    output.append({"family": family, "cluster": "",
                                   "artifact_a_id": a, "artifact_b_id": b,
                                   "relationship_status": "no-related-edge",
                                   "direction_basis": "not_applicable", "change_type": "not_applicable",
                                   "similarity_jaccard": sim["jaccard"],
                                   "similarity_containment": max(sim["left_to_right_containment"],
                                                                 sim["right_to_left_containment"]),
                                   "similarity_shared_shingles": sim["shared_shingles"],
                                   "sampling_stratum": "no-related-edge"})
    return sorted(output, key=lambda r: (r["family"], str(r["cluster"]), r["artifact_a_id"],
                                         r["artifact_b_id"], r["sampling_stratum"]))


def _relationship_sample(reports: list[dict], per_stratum: int, seed: int) -> list[dict]:
    candidates = _relationship_candidates(reports)
    rng = random.Random(seed)
    chosen = set()
    output = []
    for label in RELATIONSHIP_STRATA:
        eligible = [row for row in candidates if row["sampling_stratum"] == label and
                    (row["family"], row["artifact_a_id"], row["artifact_b_id"]) not in chosen]
        rng.shuffle(eligible)
        for row in eligible[:per_stratum]:
            chosen.add((row["family"], row["artifact_a_id"], row["artifact_b_id"]))
            output.append(row)
    return output


def _relationship_metrics(path: Path, selected: list[dict]) -> dict:
    key_fields = ("family", "artifact_a_id", "artifact_b_id")
    lookup = {tuple(str(row[field]) for field in key_fields): row for row in selected}
    counts = Counter()
    for key, row, ref in _read_adjudicated(path, lookup, key_fields, RELATIONSHIP_REVIEW_FIELDS):
        related = _label(row, "manual_relatedness", ("related", "not_related", "uncertain"), key)
        direction = _label(row, "direction_basis_review",
                           ("supported", "unsupported", "uncertain", "not_applicable"), key)
        counts["reviewed_pairs"] += 1
        counts[f"relatedness_{related}"] += 1
        counts[f"direction_{direction}"] += 1
        predicted_related = ref["relationship_status"] != "no-related-edge"
        if related != "uncertain":
            counts["relatedness_agree" if (related == "related") == predicted_related
                   else "relatedness_disagree"] += 1
    return {"reviewed_pairs": counts["reviewed_pairs"],
            "relatedness_agree": counts["relatedness_agree"],
            "relatedness_disagree": counts["relatedness_disagree"],
            "relatedness_uncertain": counts["relatedness_uncertain"],
            "direction_review": {label: counts[f"direction_{label}"] for label in
                                 ("supported", "unsupported", "uncertain", "not_applicable")},
            "scope": "adjudicated relationship review sample; excludes directed indicator metrics"}


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


def summarize(paths: list[Path | dict], output: Path, *, per_stratum: int | None = None,
              seed: int = 580, annotations: Path | None = None,
              family_reports: list[Path] | None = None,
              relationship_annotations: Path | None = None,
              relationship_selected: list[dict] | None = None,
              manual_review: Path | None = None,
              figures: Path | None = None) -> dict:
    """Summarize family reports; reject malformed or duplicate inputs."""
    _require(bool(paths), "At least one report is required")
    reports = [_read_report(path) for path in (sorted(paths) if all(isinstance(p, Path) for p in paths) else paths)]
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
    _require(not family_reports or per_stratum is not None,
             "--family-reports requires --per-stratum")
    _require(relationship_annotations is None or bool(family_reports) or
             relationship_selected is not None,
             "--relationship-annotations requires relationship validation samples")
    family_data = ([_read_family_report(path, policies, set(names)) for path in sorted(family_reports)]
                   if family_reports else [])
    family_names = [r["name"] for r in family_data]
    _require(len(family_names) == len(set(family_names)), "Duplicate analyze_family report")
    if relationship_selected is None:
        relationship_selected = (_relationship_sample(family_data, per_stratum, seed)
                                 if family_data else [])
    has_relationships = bool(family_data) or (relationship_selected is not None and per_stratum is not None
                                              and manual_review is not None)
    directed_folder = manual_review / "directed-pairs" if manual_review else output
    relation_folder = manual_review / "relationship-pairs" if manual_review else output
    if annotations is not None and annotations.resolve() == (directed_folder / "validation_annotations_template.csv").resolve():
        raise ResearchInputError("Copy the template to a separate reviewed CSV before using --annotations")
    if (relationship_annotations is not None and relationship_annotations.resolve() ==
            (relation_folder / "relationship_validation_annotations_template.csv").resolve()):
        raise ResearchInputError("Copy the relationship template before using --relationship-annotations")
    output.mkdir(parents=True, exist_ok=True)
    if manual_review:
        directed_folder.mkdir(parents=True, exist_ok=True)
        relation_folder.mkdir(parents=True, exist_ok=True)
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
        _write_csv(directed_folder / "validation_sample.csv", chosen, (*PAIR_FIELDS, "sampling_stratum"))
        _write_csv(directed_folder / "validation_annotations_template.csv", [
            {**row, **{field: "" for field in DIRECTED_REVIEW_FIELDS},
             "review_phase": "independent", "review_status": "pending"}
            for row in chosen], (*PAIR_FIELDS, "sampling_stratum", *DIRECTED_REVIEW_FIELDS))
    if has_relationships:
        _write_csv(relation_folder / "relationship_validation_sample.csv", relationship_selected, RELATIONSHIP_FIELDS)
        _write_csv(relation_folder / "relationship_validation_annotations_template.csv", [
            {**row, **{field: "" for field in RELATIONSHIP_REVIEW_FIELDS},
             "review_phase": "independent", "review_status": "pending"}
            for row in relationship_selected], (*RELATIONSHIP_FIELDS, *RELATIONSHIP_REVIEW_FIELDS))
    if figures is not None:
        figures.mkdir(parents=True, exist_ok=True)
    _svg_frequency((figures or output) / "indicator_frequency.svg", indicator_frequency, pairs)
    if per_stratum is not None:
        summary["sampling"] = {"seed": seed, "per_stratum": per_stratum,
                               "sampled_pairs": len(chosen),
                               "strata_counts": dict(sorted(Counter(row["sampling_stratum"] for row in chosen).items()))}
    if has_relationships:
        summary["relationship_sampling"] = {
            "seed": seed, "per_stratum": per_stratum, "sampled_pairs": len(relationship_selected),
            "strata_counts": dict(sorted(Counter(row["sampling_stratum"]
                                                for row in relationship_selected).items())),
            "families_supplied": len(family_data) if family_data else len(reports),
        }
    if annotations is not None:
        summary["manual_validation"] = _annotation_metrics(annotations, chosen)
    if relationship_annotations is not None:
        summary["relationship_validation"] = _relationship_metrics(
            relationship_annotations, relationship_selected)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _read_saved_sample(path: Path, fields: tuple[str, ...],
                       key_fields: tuple[str, ...]) -> list[dict]:
    """Read saved review evidence without rerunning family similarity analysis."""
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            _require(reader.fieldnames is not None and set(fields) <= set(reader.fieldnames),
                     f"{path}: saved validation sample has missing columns")
            rows = list(reader)
    except OSError as exc:
        raise ResearchInputError(f"Cannot read saved validation sample {path}: {exc}") from exc
    keys = [tuple(row[field] for field in key_fields) for row in rows]
    _require(len(set(keys)) == len(keys), f"{path}: duplicate pair in saved validation sample")
    return rows


def apply_adjudications(results: Path, *, directed_annotations: Path | None = None,
                        relationship_annotations: Path | None = None) -> dict:
    """Update saved summary metrics from approved samples, without analyzing families."""
    review = results / "review"
    manual = results / "manual-review"
    directed = manual / "directed-pairs"
    relationships = manual / "relationship-pairs"
    if (directed_annotations is not None and directed_annotations.resolve() ==
            (directed / "validation_annotations_template.csv").resolve()):
        raise ResearchInputError("Copy the template to a reviewed CSV before using --annotations")
    if (relationship_annotations is not None and relationship_annotations.resolve() ==
            (relationships / "relationship_validation_annotations_template.csv").resolve()):
        raise ResearchInputError("Copy the relationship template before using --relationship-annotations")
    try:
        summary = json.loads((review / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ResearchInputError(f"Cannot load saved research summary: {exc}") from exc
    _require(isinstance(summary, dict) and summary.get("report_type") == "gitskills-research-summary",
             "Saved research summary is invalid")
    chosen = _read_saved_sample(directed / "validation_sample.csv",
                                (*PAIR_FIELDS, "sampling_stratum"),
                                ("family", "cluster", "base_artifact_id", "derived_artifact_id"))
    related = _read_saved_sample(relationships / "relationship_validation_sample.csv",
                                 RELATIONSHIP_FIELDS,
                                 ("family", "artifact_a_id", "artifact_b_id"))
    _require(summary.get("sampling", {}).get("sampled_pairs") == len(chosen),
             "Saved directed sample count differs from research summary")
    _require(summary.get("relationship_sampling", {}).get("sampled_pairs") == len(related),
             "Saved relationship sample count differs from research summary")
    _require(summary["sampling"].get("strata_counts") ==
             dict(sorted(Counter(row["sampling_stratum"] for row in chosen).items())),
             "Saved directed sample strata differ from research summary")
    _require(summary["relationship_sampling"].get("strata_counts") ==
             dict(sorted(Counter(row["sampling_stratum"] for row in related).items())),
             "Saved relationship sample strata differ from research summary")
    # Match the original summarize() behavior when only one annotation is supplied.
    summary.pop("manual_validation", None)
    summary.pop("relationship_validation", None)
    if directed_annotations is not None:
        summary["manual_validation"] = _annotation_metrics(directed_annotations, chosen)
    if relationship_annotations is not None:
        summary["relationship_validation"] = _relationship_metrics(relationship_annotations, related)
    return summary




class RelationshipSampler:
    """Bounded, reproducible stratified sampling of all relationship candidates.

    Each candidate is considered exactly once; reservoir sampling is uniform
    without replacement within the *whole cohort*, even across family loads.
    Unlike shuffling a materialized candidate list, this retains at most
    per_stratum rows per relationship stratum in memory.
    """

    def __init__(self, per_stratum: int, seed: int):
        if per_stratum < 1:
            raise ValueError("per_stratum must be positive")
        self.per_stratum = per_stratum
        self._random = {label: random.Random(f"{seed}:{label}") for label in RELATIONSHIP_STRATA}
        self._seen = Counter()
        self._reservoir = {label: [] for label in RELATIONSHIP_STRATA}

    def _consider(self, row: dict) -> None:
        stratum = row["sampling_stratum"]
        self._seen[stratum] += 1
        rows = self._reservoir[stratum]
        if len(rows) < self.per_stratum:
            rows.append(row)
        else:
            index = self._random[stratum].randrange(self._seen[stratum])
            if index < self.per_stratum:
                rows[index] = row

    def add_family(self, family: FamilyAnalysis) -> None:
        """Examine all variants and inferred undirected edges without JSON expansion."""
        for cluster in family.family.clusters:
            for edge in cluster.evolution.ambiguous_edges:
                left, right = sorted((edge.left_artifact_id, edge.right_artifact_id))
                label = "equivalent" if edge.relationship_status == "equivalent" else "ambiguous"
                self._consider({
                    "family": family.name, "cluster": cluster.number,
                    "artifact_a_id": left, "artifact_b_id": right,
                    "relationship_status": edge.relationship_status,
                    "direction_basis": edge.basis, "change_type": edge.change_type.value,
                    "similarity_jaccard": edge.jaccard,
                    "similarity_containment": max(edge.containment_left_to_right,
                                                  edge.containment_right_to_left),
                    "similarity_shared_shingles": edge.shared_shingles,
                    "sampling_stratum": label,
                })
        variants = {variant.file_sha: variant for variant in family.skill_variants}
        for sim in family.similarities:
            if family.policy.relates(sim) or sim.left_file_sha == sim.right_file_sha:
                continue
            left = variants[sim.left_file_sha]
            right = variants[sim.right_file_sha]
            for left_id in left.artifact_ids:
                for right_id in right.artifact_ids:
                    a, b = sorted((left_id, right_id))
                    if a == b:
                        continue
                    self._consider({
                        "family": family.name, "cluster": "",
                        "artifact_a_id": a, "artifact_b_id": b,
                        "relationship_status": "no-related-edge",
                        "direction_basis": "not_applicable", "change_type": "not_applicable",
                        "similarity_jaccard": sim.jaccard,
                        "similarity_containment": max(sim.left_to_right_containment,
                                                      sim.right_to_left_containment),
                        "similarity_shared_shingles": sim.shared_shingles,
                        "sampling_stratum": "no-related-edge",
                    })

    def selected(self) -> list[dict]:
        return [row for label in RELATIONSHIP_STRATA for row in self._reservoir[label]]

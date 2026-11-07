"""Validate family-scan inputs and select directed-pair review samples."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

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


def read_scan_report(path: Path | dict) -> dict:
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


def validated_pair_rows(report: dict) -> list[dict]:
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


def sample_directed_pairs(rows: list[dict], per_stratum: int, seed: int) -> list[dict]:
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




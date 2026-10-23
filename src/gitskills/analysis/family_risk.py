"""Security review across directed relationships in a candidate family."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace

from gitskills.rules.base import Rule

from .analyzer import SkillAnalyzer
from .comparator import compare_results
from .family import FamilyAnalyzer
from .family_models import Artifact, ChangeType, SimilarityPolicy, SkillVariant
from .family_risk_models import (
    ActiveRule,
    ClusterRiskAnalysis,
    FamilyRiskAnalysis,
    FindingSource,
    FlaggedPair,
    FlaggedRule,
    IncompletePair,
    PairObservation,
    ScanSurface,
    SiblingFile,
    SiblingScanSummary,
)
from .models import AnalysisResult, RiskProfile, RuleDelta, RuleMatch
from .risk_assessor import RiskAssessor
from .evidence_models import EvidenceChanges


_SIBLING_CHANGE_TYPES = {
    ChangeType.SIBLINGS_ONLY,
    ChangeType.SKILL_AND_SIBLINGS,
}


@dataclass(frozen=True, slots=True)
class _SiblingDifference:
    source_only: tuple[SiblingFile, ...]
    destination_only: tuple[SiblingFile, ...]
    unknown_sha_source: tuple[SiblingFile, ...]
    unknown_sha_destination: tuple[SiblingFile, ...]


@dataclass(frozen=True, slots=True)
class _SiblingReview:
    rules: tuple[FlaggedRule, ...]
    summary: SiblingScanSummary
    source_changed: AnalysisResult
    destination_changed: AnalysisResult


class FamilyRiskAnalyzer:
    """Scan directed family-analysis edges for security-rule findings."""

    def __init__(
        self,
        *,
        policy: SimilarityPolicy | None = None,
        family_analyzer: FamilyAnalyzer | None = None,
        skill_analyzer: SkillAnalyzer | None = None,
        edges: str = "primary",
    ) -> None:
        if family_analyzer is not None and policy is not None:
            raise ValueError("Pass either policy or family_analyzer, not both")

        if edges not in ("primary", "all"):
            raise ValueError("edges must be primary or all")
        self._edges = edges
        self._family_analyzer = family_analyzer or FamilyAnalyzer(policy)
        self._skill_analyzer = skill_analyzer or SkillAnalyzer()
        self._rule_catalog = _rule_catalog(self._skill_analyzer.rules)
        self._risk_assessor = RiskAssessor()

    @property
    def policy(self) -> SimilarityPolicy:
        return self._family_analyzer.policy

    @property
    def active_rules(self) -> tuple[ActiveRule, ...]:
        return tuple(self._rule_catalog[rule_id] for rule_id in sorted(self._rule_catalog))

    def analyze(
        self,
        artifacts: Iterable[Artifact],
        *,
        sibling_files: Iterable[SiblingFile] = (),
    ) -> FamilyRiskAnalysis:
        """Analyze primary or all direction-supported family relationships."""

        artifacts = tuple(artifacts)
        siblings = tuple(sibling_files)
        family = self._family_analyzer.analyze(artifacts)
        variants = {variant.file_sha: variant for variant in family.skill_variants}
        artifacts_by_id = {artifact.artifact_id: artifact for artifact in artifacts}

        siblings_by_artifact: dict[int, tuple[SiblingFile, ...]] = {}
        sibling_lists: dict[int, list[SiblingFile]] = defaultdict(list)
        for sibling in siblings:
            sibling_lists[sibling.artifact_id].append(sibling)
        for artifact_id, members in sibling_lists.items():
            siblings_by_artifact[artifact_id] = tuple(
                sorted(members, key=lambda item: item.sibling_id)
            )

        sibling_content_by_sha = {
            sibling.entry_sha: sibling.content
            for sibling in siblings
            if sibling.entry_sha is not None and sibling.content is not None
        }

        skill_scan_cache: dict[str, AnalysisResult] = {}
        sibling_scan_cache: dict[tuple[str, str, str], AnalysisResult] = {}
        clusters: list[ClusterRiskAnalysis] = []

        for cluster in family.family.clusters:
            primary = cluster.evolution.directed_edges
            # The reduced evolution graph contains preferred predecessor edges;
            # related_edges contain other directionally supported comparisons.
            # Deduplicate by artifact IDs, preferring primary classification.
            seen_pairs: set[tuple[int, int]] = set()
            edges_to_scan = []
            candidates = [(edge, "primary") for edge in primary]
            if self._edges == "all":
                candidates.extend((edge, "additional") for edge in cluster.evolution.related_edges)
            for edge, edge_type in candidates:
                key = (edge.source_artifact_id, edge.target_artifact_id)
                if key not in seen_pairs:
                    seen_pairs.add(key)
                    edges_to_scan.append((edge, edge_type))
            if not edges_to_scan:
                continue

            flagged_pairs: list[FlaggedPair] = []
            incomplete_pairs: list[IncompletePair] = []
            pair_observations: list[PairObservation] = []

            for edge, edge_type in edges_to_scan:
                source_result = self._scan_variant(
                    edge.source.file_sha,
                    variants,
                    skill_scan_cache,
                )
                destination_result = self._scan_variant(
                    edge.target.file_sha,
                    variants,
                    skill_scan_cache,
                )
                comparison = compare_results(source_result, destination_result)
                skill_rules = self._positive_skill_rule_deltas(
                    comparison.rule_deltas,
                    destination_result,
                    destination_artifact_id=edge.target_artifact_id,
                )

                sibling_rules: tuple[FlaggedRule, ...] = ()
                sibling_summary: SiblingScanSummary | None = None
                skill_evidence = comparison.evidence_changes
                sibling_evidence = EvidenceChanges()
                source_changed = _combine_results(())
                destination_changed = _combine_results(())
                if edge.change_type in _SIBLING_CHANGE_TYPES:
                    source_files = siblings_by_artifact.get(edge.source_artifact_id, ())
                    destination_files = siblings_by_artifact.get(edge.target_artifact_id, ())
                    sibling_review = self._analyze_siblings(
                        source_files=source_files,
                        destination_files=destination_files,
                        content_by_sha=sibling_content_by_sha,
                        scan_cache=sibling_scan_cache,
                    )
                    sibling_rules = sibling_review.rules
                    sibling_summary = sibling_review.summary
                    source_changed = sibling_review.source_changed
                    destination_changed = sibling_review.destination_changed
                    # Missing sibling rows are not evidence of an empty bundle.
                    source_artifact = artifacts_by_id[edge.source_artifact_id]
                    destination_artifact = artifacts_by_id[edge.target_artifact_id]
                    listing_incomplete = any(
                        expected is None or len(available) < expected
                        for expected, available in (
                            (source_artifact.sibling_file_count, source_files),
                            (destination_artifact.sibling_file_count, destination_files),
                        )
                    )
                    if listing_incomplete:
                        sibling_summary = replace(sibling_summary, listing_incomplete=True)
                    if sibling_summary.incomplete:
                        incomplete_pairs.append(
                            IncompletePair(
                                cluster_number=cluster.number,
                                edge_type=edge_type,
                                source_artifact_id=edge.source_artifact_id,
                                destination_artifact_id=edge.target_artifact_id,
                                change_type=edge.change_type,
                                direction_basis=edge.basis,
                                sibling_scan=sibling_summary,
                            )
                        )
                    sibling_evidence = compare_results(
                        source_changed, destination_changed
                    ).evidence_changes

                # One assessment per directed pair: no double counting between
                # SKILL.md and changed sibling constructs.
                combined = compare_results(
                    _combine_results((source_result, source_changed)),
                    _combine_results((destination_result, destination_changed)),
                )
                assessment = self._risk_assessor.assess(
                    combined,
                    base_script_hashes=_sibling_hashes(
                        siblings_by_artifact.get(edge.source_artifact_id, ())
                    ),
                    derived_script_hashes=_sibling_hashes(
                        siblings_by_artifact.get(edge.target_artifact_id, ())
                    ),
                )
                if sibling_summary is not None:
                    missing_content = (len(sibling_summary.unavailable_source_ids)
                                       + len(sibling_summary.unavailable_destination_ids))
                    unknown_hashes = (len(sibling_summary.unknown_sha_source_ids)
                                      + len(sibling_summary.unknown_sha_destination_ids))
                    assessment = replace(
                        assessment,
                        missing_sibling_content=missing_content,
                        unknown_sibling_hashes=unknown_hashes,
                        sibling_listing_incomplete=sibling_summary.listing_incomplete,
                        coverage="incomplete" if sibling_summary.incomplete else assessment.coverage,
                        coverage_notes=(assessment.coverage_notes
                                        + ("Unavailable or unknown sibling data",))
                        if sibling_summary.incomplete else assessment.coverage_notes,
                    )

                flagged_rules = tuple(
                    sorted(
                        (*skill_rules, *sibling_rules),
                        key=lambda rule: (rule.rule_id, rule.surface.value),
                    )
                )
                # Keep every directed edge for unbiased validation denominators.
                flagged = bool(flagged_rules or skill_evidence.added or skill_evidence.removed
                               or sibling_evidence.added or sibling_evidence.removed
                               or assessment.indicators)
                pair_observations.append(PairObservation(
                    edge_type=edge_type,
                    source_artifact_id=edge.source_artifact_id,
                    destination_artifact_id=edge.target_artifact_id,
                    direction_basis=edge.basis,
                    change_type=edge.change_type,
                    flagged=flagged,
                    rule_flagged=bool(flagged_rules),
                    skill_evidence_added=len(skill_evidence.added),
                    skill_evidence_removed=len(skill_evidence.removed),
                    sibling_evidence_added=len(sibling_evidence.added),
                    sibling_evidence_removed=len(sibling_evidence.removed),
                    indicator_ids=tuple(sorted({i.indicator_id for i in assessment.supported})),
                    uncertain_indicator_ids=tuple(sorted({i.indicator_id for i in assessment.uncertain})),
                    finding_count=assessment.finding_count,
                    coverage=assessment.coverage,
                    evidence_complete=assessment.evidence_complete,
                    evidence_partial=assessment.evidence_partial,
                    evidence_unsupported=assessment.evidence_unsupported,
                    missing_sibling_content=assessment.missing_sibling_content,
                    unknown_sibling_hashes=assessment.unknown_sibling_hashes,
                    sibling_listing_incomplete=assessment.sibling_listing_incomplete,
                ))
                if not flagged:
                    continue

                flagged_pairs.append(
                    FlaggedPair(
                        cluster_number=cluster.number,
                        edge_type=edge_type,
                        source_artifact_id=edge.source_artifact_id,
                        destination_artifact_id=edge.target_artifact_id,
                        direction_basis=edge.basis,
                        direction_evidence=edge.evidence,
                        change_type=edge.change_type,
                        containment=edge.containment,
                        jaccard=edge.jaccard,
                        shared_shingles=edge.shared_shingles,
                        flagged_rules=flagged_rules,
                        sibling_scan=sibling_summary,
                        skill_evidence=skill_evidence,
                        sibling_evidence=sibling_evidence,
                        risk_assessment=assessment,
                    )
                )

            clusters.append(
                ClusterRiskAnalysis(
                    cluster_number=cluster.number,
                    pairs_analyzed=len(edges_to_scan),
                    flagged_pairs=tuple(flagged_pairs),
                    incomplete_pairs=tuple(incomplete_pairs),
                    pair_observations=tuple(pair_observations),
                    direction_basis_counts=tuple(sorted(
                        Counter(edge.basis for edge, _ in edges_to_scan).items()
                    )),
                )
            )

        return FamilyRiskAnalysis(
            name=family.name,
            similarity_policy=family.policy,
            active_rules=self.active_rules,
            clusters=tuple(clusters),
            edge_selection=self._edges,
            ambiguous_edges_skipped=family.family.ambiguous_edge_count,
        )

    def _scan_variant(
        self,
        file_sha: str,
        variants: dict[str, SkillVariant],
        cache: dict[str, AnalysisResult],
    ) -> AnalysisResult:
        cached = cache.get(file_sha)
        if cached is not None:
            return cached

        variant = variants[file_sha]
        result = self._skill_analyzer.scan(
            variant.content,
            filename="SKILL.md",
            source_id=f"skill_sha:{file_sha}",
        )
        cache[file_sha] = result
        return result

    def _positive_skill_rule_deltas(
        self,
        rule_deltas: tuple[RuleDelta, ...],
        destination: AnalysisResult,
        *,
        destination_artifact_id: int,
    ) -> tuple[FlaggedRule, ...]:
        matches_by_rule: dict[str, list[RuleMatch]] = defaultdict(list)
        for match in destination.rule_matches:
            matches_by_rule[match.rule_id].append(match)

        flagged: list[FlaggedRule] = []
        for delta in rule_deltas:
            if delta.delta <= 0:
                continue

            rule_id = delta.rule_id
            rule = self._rule_catalog[rule_id]
            matches = tuple(matches_by_rule.get(rule_id, ()))
            flagged.append(
                FlaggedRule(
                    rule_id=rule_id,
                    category=rule.category,
                    description=rule.description,
                    surface=ScanSurface.SKILL,
                    source_count=delta.base,
                    destination_count=delta.derived,
                    finding_sources=(
                        FindingSource(
                            surface=ScanSurface.SKILL,
                            source_id=destination_artifact_id,
                            matches=matches,
                        ),
                    ),
                    positive_delta=True,
                )
            )

        return tuple(flagged)

    def _analyze_siblings(
        self,
        *,
        source_files: tuple[SiblingFile, ...],
        destination_files: tuple[SiblingFile, ...],
        content_by_sha: dict[str, str],
        scan_cache: dict[tuple[str, str, str], AnalysisResult],
    ) -> _SiblingReview:
        difference = _sibling_difference(source_files, destination_files)

        source_scans = self._scan_sibling_collection(
            source_files,
            content_by_sha=content_by_sha,
            cache=scan_cache,
        )
        destination_scans = self._scan_sibling_collection(
            destination_files,
            content_by_sha=content_by_sha,
            cache=scan_cache,
        )

        source_aggregate = _combine_results(result for _, result in source_scans)
        destination_aggregate = _combine_results(
            result for _, result in destination_scans
        )
        comparison = compare_results(source_aggregate, destination_aggregate)
        positive_rule_ids = {
            delta.rule_id
            for delta in comparison.rule_deltas
            if delta.delta > 0
        }

        destination_only_ids = {
            sibling.sibling_id for sibling in difference.destination_only
        }
        new_sources_by_rule = _finding_sources_by_rule(
            (
                (sibling, result)
                for sibling, result in destination_scans
                if sibling.sibling_id in destination_only_ids
            )
        )
        all_destination_sources_by_rule = _finding_sources_by_rule(destination_scans)

        rule_ids = sorted(positive_rule_ids | set(new_sources_by_rule))
        source_counts = source_aggregate.rule_counts()
        destination_counts = destination_aggregate.rule_counts()
        flagged: list[FlaggedRule] = []

        for rule_id in rule_ids:
            new_sources = new_sources_by_rule.get(rule_id, ())
            finding_sources = (
                new_sources
                if new_sources
                else all_destination_sources_by_rule.get(rule_id, ())
            )
            if not finding_sources:
                continue

            rule = self._rule_catalog[rule_id]
            flagged.append(
                FlaggedRule(
                    rule_id=rule_id,
                    category=rule.category,
                    description=rule.description,
                    surface=ScanSurface.SIBLING,
                    source_count=source_counts.get(rule_id, 0),
                    destination_count=destination_counts.get(rule_id, 0),
                    finding_sources=finding_sources,
                    positive_delta=rule_id in positive_rule_ids,
                    new_or_changed_sibling_content=bool(new_sources),
                )
            )

        source_scan_ids = {sibling.sibling_id for sibling, _ in source_scans}
        destination_scan_ids = {
            sibling.sibling_id for sibling, _ in destination_scans
        }

        unavailable_source = tuple(
            sorted(
                sibling.sibling_id
                for sibling in difference.source_only
                if sibling.sibling_id not in source_scan_ids
            )
        )
        unavailable_destination = tuple(
            sorted(
                sibling.sibling_id
                for sibling in difference.destination_only
                if sibling.sibling_id not in destination_scan_ids
            )
        )

        source_paths = {sibling.entry_name for sibling in source_files}
        destination_paths = {sibling.entry_name for sibling in destination_files}
        summary = SiblingScanSummary(
            source_files=len(source_files),
            destination_files=len(destination_files),
            recorded_base_only_paths=tuple(sorted(source_paths - destination_paths)),
            recorded_derived_only_paths=tuple(sorted(destination_paths - source_paths)),
            new_or_changed_destination_ids=tuple(
                sorted(destination_only_ids)
            ),
            unavailable_source_ids=unavailable_source,
            unavailable_destination_ids=unavailable_destination,
            unknown_sha_source_ids=tuple(
                sibling.sibling_id
                for sibling in difference.unknown_sha_source
            ),
            unknown_sha_destination_ids=tuple(
                sibling.sibling_id
                for sibling in difference.unknown_sha_destination
            ),
        )
        source_only_ids = {item.sibling_id for item in difference.source_only}
        destination_only_ids = {item.sibling_id for item in difference.destination_only}
        # Fingerprint-matched siblings are unchanged even when moved or renamed.
        # Preserve them for historical rule counts, not evidence changes.
        return _SiblingReview(
            rules=tuple(flagged),
            summary=summary,
            source_changed=_combine_results(
                result for sibling, result in source_scans
                if sibling.sibling_id in source_only_ids
            ),
            destination_changed=_combine_results(
                result for sibling, result in destination_scans
                if sibling.sibling_id in destination_only_ids
            ),
        )

    def _scan_sibling_collection(
        self,
        sibling_files: tuple[SiblingFile, ...],
        *,
        content_by_sha: dict[str, str],
        cache: dict[tuple[str, str, str], AnalysisResult],
    ) -> tuple[tuple[SiblingFile, AnalysisResult], ...]:
        scanned = []
        for sibling in sibling_files:
            result = self._scan_sibling(
                sibling,
                content_by_sha=content_by_sha,
                cache=cache,
            )
            if result is not None:
                scanned.append((sibling, result))
        return tuple(scanned)

    def _scan_sibling(
        self,
        sibling: SiblingFile,
        *,
        content_by_sha: dict[str, str],
        cache: dict[tuple[str, str, str], AnalysisResult],
    ) -> AnalysisResult | None:
        text = sibling.content
        if text is None and sibling.entry_sha is not None:
            text = content_by_sha.get(sibling.entry_sha)
        if text is None:
            return None

        if sibling.entry_sha is not None:
            cache_key = ("sha", sibling.entry_sha, sibling.entry_name)
        else:
            cache_key = ("id", str(sibling.sibling_id), sibling.entry_name)

        cached = cache.get(cache_key)
        if cached is None:
            cached = self._skill_analyzer.scan(
                text,
                filename=sibling.entry_name,
                exclude_frontmatter=False,
            )
            cache[cache_key] = cached
        source_id = f"sibling:{sibling.sibling_id}"
        return replace(
            cached,
            source_id=source_id,
            evidence=tuple(replace(item, source_id=source_id) for item in cached.evidence),
        )


def _sibling_difference(
    source_files: tuple[SiblingFile, ...],
    destination_files: tuple[SiblingFile, ...],
) -> _SiblingDifference:
    source_by_sha: dict[str, list[SiblingFile]] = defaultdict(list)
    destination_by_sha: dict[str, list[SiblingFile]] = defaultdict(list)
    unknown_source = []
    unknown_destination = []

    for sibling in source_files:
        if sibling.entry_sha is None:
            unknown_source.append(sibling)
        else:
            source_by_sha[sibling.entry_sha].append(sibling)

    for sibling in destination_files:
        if sibling.entry_sha is None:
            unknown_destination.append(sibling)
        else:
            destination_by_sha[sibling.entry_sha].append(sibling)

    source_only = []
    destination_only = []
    for entry_sha in sorted(source_by_sha.keys() | destination_by_sha.keys()):
        source_members = sorted(
            source_by_sha.get(entry_sha, ()),
            key=lambda item: item.sibling_id,
        )
        destination_members = sorted(
            destination_by_sha.get(entry_sha, ()),
            key=lambda item: item.sibling_id,
        )
        shared_count = min(len(source_members), len(destination_members))
        source_only.extend(source_members[shared_count:])
        destination_only.extend(destination_members[shared_count:])

    return _SiblingDifference(
        source_only=tuple(source_only),
        destination_only=tuple(destination_only),
        unknown_sha_source=tuple(sorted(unknown_source, key=lambda item: item.sibling_id)),
        unknown_sha_destination=tuple(
            sorted(unknown_destination, key=lambda item: item.sibling_id)
        ),
    )


def _finding_sources_by_rule(
    scans: Iterable[tuple[SiblingFile, AnalysisResult]],
) -> dict[str, tuple[FindingSource, ...]]:
    grouped: dict[str, list[FindingSource]] = defaultdict(list)

    for sibling, result in scans:
        matches_by_rule: dict[str, list[RuleMatch]] = defaultdict(list)
        for match in result.rule_matches:
            matches_by_rule[match.rule_id].append(match)

        for rule_id, matches in matches_by_rule.items():
            grouped[rule_id].append(
                FindingSource(
                    surface=ScanSurface.SIBLING,
                    source_id=sibling.sibling_id,
                    entry_name=sibling.entry_name,
                    matches=tuple(matches),
                )
            )

    return {
        rule_id: tuple(sorted(sources, key=lambda item: item.source_id))
        for rule_id, sources in grouped.items()
    }


def _combine_results(results: Iterable[AnalysisResult]) -> AnalysisResult:
    results = tuple(results)
    rule_matches = tuple(match for result in results for match in result.rule_matches)
    return AnalysisResult(
        profile=RiskProfile.from_categories(match.category for match in rule_matches),
        rule_matches=rule_matches,
        filename="<aggregate>",
        evidence=tuple(item for result in results for item in result.evidence),
    )


def _sibling_hashes(siblings: tuple[SiblingFile, ...]) -> dict[str, str]:
    """Use only known, unambiguous sibling hashes supplied by GitSkills."""
    hashes: dict[str, str] = {}
    ambiguous: set[str] = set()
    for sibling in siblings:
        name = sibling.entry_name.replace("\\", "/").removeprefix("./")
        if sibling.entry_sha is None:
            ambiguous.add(name)
        elif name in hashes and hashes[name] != sibling.entry_sha:
            ambiguous.add(name)
        else:
            hashes[name] = sibling.entry_sha
    return {name: sha for name, sha in hashes.items() if name not in ambiguous}


def _rule_catalog(rules: tuple[Rule, ...]) -> dict[str, ActiveRule]:
    return {
        rule.rule_id: ActiveRule(
            rule_id=rule.rule_id,
            category=rule.category,
            description=rule.description,
        )
        for rule in rules
    }

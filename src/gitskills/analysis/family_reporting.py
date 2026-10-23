"""Shared report builders for CLI, notebooks, and research workflows."""

from __future__ import annotations

import hashlib
from pathlib import Path

from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_models import FamilyAnalysis, ScopeAnalysis, SimilarityPolicy
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.analysis.family_risk_models import FamilyRiskAnalysis, SiblingFile
from gitskills.data.families import FamilyLoad


def implementation_fingerprint() -> str:
    """Fingerprint analysis and rule implementations for incremental report reuse."""
    root = Path(__file__).resolve().parents[1]
    files = sorted((*root.glob("analysis/*.py"), *root.glob("rules/*.py")))
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def source_records(loaded: FamilyLoad) -> list[dict]:
    """Return a stable source reference for every analyzable artifact."""
    return [
        {
            "artifact_id": item.artifact_id,
            "group_id": item.group_id,
            "repo_full_name": item.repo_full_name,
            "path": item.path,
            "file_sha": item.file_sha,
            "sibling_file_count": item.sibling_file_count,
            "sibling_content_sha": item.sibling_content_sha,
        }
        for item in sorted(loaded.artifacts, key=lambda artifact: artifact.artifact_id)
    ]


def _coverage(loaded: FamilyLoad) -> dict:
    return {
        "input_summary": {
            "artifacts_loaded": len(loaded.artifacts),
            "artifacts_skipped": len(loaded.skipped_artifacts),
            "incomplete": bool(loaded.skipped_artifacts),
        },
        "skipped_artifacts": [item.to_dict() for item in loaded.skipped_artifacts],
    }


def analyze_family_report(name: str, loaded: FamilyLoad, *,
                          policy: SimilarityPolicy | None = None,
                          verbose: bool = False) -> tuple[FamilyAnalysis, dict]:
    """Analyze available artifacts; preserve reasons for skipped inputs."""
    if not loaded.artifacts and not loaded.skipped_artifacts:
        raise ValueError(f"Candidate family not found: {name}")
    policy = policy or SimilarityPolicy()
    if loaded.artifacts:
        result = FamilyAnalyzer(policy).analyze(loaded.artifacts)
    else:
        result = FamilyAnalysis(
            name=name, policy=policy,
            family=ScopeAnalysis(artifact_ids=(), skill_variant_count=0,
                                 bundle_variant_count=0, clusters=()),
            groups=(), similarities=(), skill_variants=(), bundle_variants=(),
            artifacts=(),
        )
    payload = result.to_dict(verbose=verbose)
    payload.update(_coverage(loaded))
    payload["implementation_fingerprint"] = implementation_fingerprint()
    return result, payload


def scan_family_report(name: str, loaded: FamilyLoad,
                       sibling_files: tuple[SiblingFile, ...] = (), *,
                       policy: SimilarityPolicy | None = None,
                       edges: str = "all", verbose: bool = False
                       ) -> tuple[FamilyRiskAnalysis, dict]:
    """Scan direction-supported edges using the same input contract as family analysis."""
    if not loaded.artifacts and not loaded.skipped_artifacts:
        raise ValueError(f"Candidate family not found: {name}")
    policy = policy or SimilarityPolicy()
    analyzer = FamilyRiskAnalyzer(policy=policy, edges=edges)
    result = (analyzer.analyze(loaded.artifacts, sibling_files=sibling_files)
              if loaded.artifacts else FamilyRiskAnalysis(
                  name=name, similarity_policy=policy,
                  active_rules=analyzer.active_rules, clusters=(),
                  ambiguous_edges_skipped=0, edge_selection=edges))
    payload = result.to_dict(verbose=verbose)
    payload.update(_coverage(loaded))
    payload["input_artifacts"] = source_records(loaded)
    payload["implementation_fingerprint"] = implementation_fingerprint()
    return result, payload

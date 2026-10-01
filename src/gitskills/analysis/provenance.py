"""Explicit frontmatter provenance helpers for candidate-family analysis."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .content import extract_frontmatter


PROVENANCE_FIELDS = (
    "derived_from",
    "upstream_skill",
    "source_repo",
    "upstream_source",
)


@dataclass(frozen=True, slots=True)
class DeclaredProvenance:
    """Selected explicit provenance fields from SKILL.md frontmatter."""

    derived_from: str | None = None
    upstream_skill: str | None = None
    source_repo: str | None = None
    upstream_source: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "derived_from": self.derived_from,
            "upstream_skill": self.upstream_skill,
            "source_repo": self.source_repo,
            "upstream_source": self.upstream_source,
        }

    def has_values(self) -> bool:
        return any(value is not None for value in self.to_dict().values())


def extract_declared_provenance(text: str) -> DeclaredProvenance:
    """Extract supported top-level scalar provenance fields from frontmatter.

    Similarity intentionally ignores frontmatter. These fields are extracted
    separately and are used only as conservative evidence for edge direction.
    """

    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        return DeclaredProvenance()

    values: dict[str, str | None] = {field: None for field in PROVENANCE_FIELDS}

    for line in frontmatter.splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key not in values or values[key] is not None:
            continue

        values[key] = _parse_scalar(raw_value)

    return DeclaredProvenance(**values)


def normalize_skill_path(value: str | None) -> str | None:
    """Normalize a declared skill path for exact family-local matching."""

    if not value:
        return None

    normalized = value.strip().replace("\\", "/").strip("/")
    if not normalized:
        return None

    if normalized.lower().endswith("/skill.md"):
        normalized = normalized[: -len("/SKILL.md")]
    elif normalized.lower() == "skill.md":
        normalized = ""

    return normalized.strip("/") or None


def normalize_repo_reference(value: str | None) -> str | None:
    """Normalize an explicit GitHub repository reference to owner/repo."""

    if not value:
        return None

    normalized = value.strip().replace("\\", "/")

    if normalized.startswith("git@github.com:"):
        normalized = normalized[len("git@github.com:") :]
    elif "://" in normalized:
        parsed = urlparse(normalized)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            return None
        normalized = parsed.path
    elif normalized.lower().startswith("github.com/"):
        normalized = normalized[len("github.com/") :]

    normalized = normalized.strip("/")
    if normalized.lower().endswith(".git"):
        normalized = normalized[:-4]

    parts = normalized.split("/")
    if len(parts) != 2 or not all(parts):
        return None

    return f"{parts[0]}/{parts[1]}".casefold()


def skill_path_matches(declared: str | None, artifact_path: str | None) -> bool:
    """Return whether a declared path identifies an artifact's skill directory."""

    declared_path = normalize_skill_path(declared)
    artifact_skill_path = normalize_skill_path(artifact_path)
    return (
        declared_path is not None
        and artifact_skill_path is not None
        and declared_path == artifact_skill_path
    )


def _parse_scalar(raw_value: str) -> str | None:
    value = raw_value.strip()
    if not value or value.lower() in {"null", "~"}:
        return None

    if value[0] in "[{|>" or value in {"|", ">"}:
        return None

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
        if raw_value.strip().startswith("'"):
            value = value.replace("''", "'")
        else:
            value = value.replace(r'\"', '"').replace(r"\\", "\\")

    return value.strip() or None

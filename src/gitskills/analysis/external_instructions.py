"""Conservative classification of external instruction references in Markdown."""

from __future__ import annotations

import re
from enum import Enum

from .evidence_models import Evidence, ExtractionStatus


class InstructionRole(str, Enum):
    """Observed role of a URL reference, not a claim about remote content."""

    DEPENDENCY = "instruction_dependency"
    REFERENCE = "ordinary_reference"
    UNCERTAIN = "uncertain"


_INSTRUCTION = re.compile(r"\b(?:instructions?|steps?|procedures?|workflows?|rules|guidance)\b", re.I)
_DIRECTIVE = re.compile(r"\b(?:follow|obey|apply|load|retrieve|fetch|use)\b", re.I)
_EXPLICIT = re.compile(
    r"\b(?:follow|obey|apply|load|retrieve|fetch|use)\b"
    r"(?:\s+(?:and|then)\s+(?:follow|obey|apply))?"
    r"(?:\s+\S+){0,7}\s+\[?"
    r"(?:instructions?|steps?|procedures?|workflows?|rules|guidance)\b",
    re.I,
)
_DIRECT_URL = re.compile(r"\b(?:follow|retrieve\s+and\s+follow|fetch\s+and\s+follow)\s+"
                         r"(?:the\s+)?(?:https?://|\[)", re.I)
_NEGATED = re.compile(r"\b(?:do\s+not|don't|never|must\s+not|should\s+not|avoid)\b", re.I)
_BACKGROUND = re.compile(r"\b(?:for\s+(?:background|reference|more\s+information|details)|"
                         r"(?:see|refer\s+to)\b)", re.I)


def instruction_role(evidence: Evidence) -> InstructionRole:
    """Evaluate only bounded local context; never retrieve the referenced URL."""
    if evidence.kind not in {"url_reference", "markdown_link"} or "NET-001" not in evidence.rule_ids:
        return InstructionRole.UNCERTAIN
    if not evidence.filename.lower().endswith(".md"):
        return InstructionRole.UNCERTAIN
    if evidence.extraction_status != ExtractionStatus.COMPLETE:
        return InstructionRole.UNCERTAIN
    if evidence.context.kind not in {"markdown_prose", "markdown_link"}:
        return InstructionRole.UNCERTAIN

    text = evidence.context.nearby_text or ""
    # Treat quoted examples and negated imperatives as uncertain, never positive.
    if _NEGATED.search(text):
        return InstructionRole.UNCERTAIN
    if _EXPLICIT.search(text) or _DIRECT_URL.search(text):
        return InstructionRole.DEPENDENCY
    if _BACKGROUND.search(text):
        return InstructionRole.REFERENCE
    if _INSTRUCTION.search(text) or _DIRECTIVE.search(text):
        return InstructionRole.UNCERTAIN
    # With no instruction-related language, a URL alone is not enough to
    # create an uncertain risk observation. Its ordinary evidence is retained.
    return InstructionRole.REFERENCE

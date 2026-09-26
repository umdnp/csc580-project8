"""Helpers for preparing skill content for behavioral security scanning."""

from __future__ import annotations

import re


_FRONTMATTER_START = re.compile(r"\A(?:\ufeff)?---[ \t]*(?:\r\n|\n|\r)")
_FRONTMATTER_END = re.compile(r"^---[ \t]*(?:\r\n|\n|\r|$)", re.MULTILINE)


def extract_frontmatter(text: str) -> str | None:
    """Return top-of-file YAML frontmatter without delimiters, when present."""

    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return None

    content_start, content_end, _ = bounds
    return text[content_start:content_end]


def mask_frontmatter(text: str) -> str:
    """Mask top-of-file YAML frontmatter while preserving source positions.

    Behavioral rules should evaluate the Markdown body of a skill rather than
    descriptive/configuration metadata in YAML frontmatter. Characters in a
    valid top-of-file frontmatter block are replaced with spaces, while line
    endings are preserved. This keeps match offsets and reported line numbers
    aligned with the original source text.

    If the text does not begin with a frontmatter delimiter, or if no closing
    delimiter is found, the original text is returned unchanged.
    """

    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return text

    _, _, frontmatter_end = bounds
    masked_frontmatter = _mask_non_newline_characters(text[:frontmatter_end])
    return masked_frontmatter + text[frontmatter_end:]


def _frontmatter_bounds(text: str) -> tuple[int, int, int] | None:
    start_match = _FRONTMATTER_START.match(text)
    if start_match is None:
        return None

    end_match = _FRONTMATTER_END.search(text, start_match.end())
    if end_match is None:
        return None

    return start_match.end(), end_match.start(), end_match.end()


def _mask_non_newline_characters(text: str) -> str:
    """Replace non-newline characters with spaces without changing length."""

    return "".join(char if char in "\r\n" else " " for char in text)

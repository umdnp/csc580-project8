"""Helpers for preparing skill content for behavioral security scanning."""

from __future__ import annotations

import re


_FRONTMATTER_START = re.compile(r"\A(?:\ufeff)?---[ \t]*(?:\r\n|\n|\r)")
_FRONTMATTER_END = re.compile(r"^---[ \t]*(?:\r\n|\n|\r|$)", re.MULTILINE)


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

    start_match = _FRONTMATTER_START.match(text)
    if start_match is None:
        return text

    end_match = _FRONTMATTER_END.search(text, start_match.end())
    if end_match is None:
        return text

    frontmatter_end = end_match.end()
    masked_frontmatter = _mask_non_newline_characters(text[:frontmatter_end])
    return masked_frontmatter + text[frontmatter_end:]


def _mask_non_newline_characters(text: str) -> str:
    """Replace non-newline characters with spaces without changing length."""

    return "".join(char if char in "\r\n" else " " for char in text)

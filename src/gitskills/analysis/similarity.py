"""Token-shingle similarity helpers for SKILL.md candidate analysis."""

from __future__ import annotations

import re
from itertools import combinations

from .content import mask_frontmatter
from .family_models import SimilarityResult, SkillVariant


# Preserve common technical structures before falling back to ordinary Unicode
# word tokens. Exact punctuation is not generally important to reuse detection,
# but URLs, paths, environment variables, flags, and dotted identifiers should
# remain intact where practical.
_TOKEN_RE = re.compile(
    r"""
    https?://[^\s<>()`\"']+
    |(?:~|\.{1,2})?/[^^\s<>()`\"']+
    |\$[A-Za-z_][A-Za-z0-9_]*
    |--?[A-Za-z0-9][A-Za-z0-9_-]*
    |[\w]+(?:[./:@-][\w~%+?=&.#-]+)+
    |[\w]+
    """,
    re.VERBOSE | re.UNICODE,
)


def tokenize_skill_body(text: str) -> tuple[str, ...]:
    """Tokenize a SKILL.md body while excluding top-of-file frontmatter."""

    body = mask_frontmatter(text)
    return tuple(match.group(0).lower() for match in _TOKEN_RE.finditer(body))


def make_shingles(
    text: str,
    *,
    size: int = 5,
) -> frozenset[tuple[str, ...]]:
    """Build contiguous token shingles from SKILL.md body content."""

    if size < 1:
        raise ValueError("size must be at least 1")

    tokens = tokenize_skill_body(text)
    if len(tokens) < size:
        return frozenset()

    return frozenset(
        tuple(tokens[index : index + size])
        for index in range(len(tokens) - size + 1)
    )


def compare_shingles(
    left_file_sha: str,
    right_file_sha: str,
    left: frozenset[tuple[str, ...]],
    right: frozenset[tuple[str, ...]],
) -> SimilarityResult:
    """Calculate directional containment and Jaccard for two shingle sets."""

    shared = len(left & right)

    left_to_right = shared / len(left) if left else 0.0
    right_to_left = shared / len(right) if right else 0.0

    union_size = len(left) + len(right) - shared
    jaccard = shared / union_size if union_size else 0.0

    return SimilarityResult(
        left_file_sha=left_file_sha,
        right_file_sha=right_file_sha,
        left_to_right_containment=left_to_right,
        right_to_left_containment=right_to_left,
        jaccard=jaccard,
        shared_shingles=shared,
        left_shingles=len(left),
        right_shingles=len(right),
    )


def compare_skill_variants(
    variants: tuple[SkillVariant, ...],
    *,
    shingle_size: int = 5,
) -> tuple[SimilarityResult, ...]:
    """Compare every distinct skill variant once, reusing prebuilt shingles."""

    shingle_cache = {
        variant.file_sha: make_shingles(
            variant.content,
            size=shingle_size,
        )
        for variant in variants
    }

    results = []
    for left, right in combinations(
        sorted(variants, key=lambda variant: variant.file_sha),
        2,
    ):
        results.append(
            compare_shingles(
                left.file_sha,
                right.file_sha,
                shingle_cache[left.file_sha],
                shingle_cache[right.file_sha],
            )
        )

    return tuple(results)

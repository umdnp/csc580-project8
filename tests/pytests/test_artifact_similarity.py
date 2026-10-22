"""Known shingle sets and boundary cases for the RDR-004 relationship policy."""

from dataclasses import replace

import pytest

from gitskills.analysis.family_models import SimilarityPolicy, SimilarityResult
from gitskills.analysis.similarity import compare_shingles, make_shingles, tokenize_skill_body


def test_similarity_measures_retained_content_in_both_directions():
    left = frozenset((token,) for token in "abcd")
    right = frozenset((token,) for token in "cdefg")
    result = compare_shingles("source-sha", "target-sha", left, right)
    assert result.shared_shingles == 2
    assert (result.left_shingles, result.right_shingles) == (4, 5)
    assert result.containment("source-sha", "target-sha") == pytest.approx(2 / 4)
    assert result.containment("target-sha", "source-sha") == pytest.approx(2 / 5)
    assert result.jaccard == pytest.approx(2 / 7)
    assert not result.equivalent


def test_repeated_shingles_do_not_inflate_overlap():
    shingles = make_shingles("alpha beta alpha beta alpha beta", size=2)
    assert shingles == frozenset({("alpha", "beta"), ("beta", "alpha")})
    result = compare_shingles("one", "two", shingles, shingles)
    assert result.shared_shingles == 2
    assert result.equivalent


@pytest.mark.parametrize("left,right", [(frozenset(), frozenset()), (frozenset(), frozenset({("word",)}))])
def test_empty_shingles_are_not_evidence_of_relatedness(left, right):
    result = compare_shingles("one", "two", left, right)
    assert result.jaccard == 0
    assert result.shared_shingles == 0
    assert not result.equivalent
    assert not SimilarityPolicy().relates(result)


def test_body_tokens_ignore_metadata_case_and_whitespace_but_keep_technical_values():
    text = (
        "---\nname: ignored\nurl: https://metadata.example\n---\n"
        "RUN\t Python setup.py\nhttps://example.com/api $TOKEN --flag /tmp/report\n"
    )
    assert tokenize_skill_body(text) == (
        "run", "python", "setup.py", "https://example.com/api", "$token", "--flag", "/tmp/report",
    )


def test_non_english_body_tokens_remain_comparable():
    text = "检查 项目 配置 然后 生成 报告"
    assert make_shingles(text) == frozenset({
        ("检查", "项目", "配置", "然后", "生成"),
        ("项目", "配置", "然后", "生成", "报告"),
    })


@pytest.mark.parametrize("text", ["", " \n\t", "one two three four"])
def test_body_shorter_than_shingle_size_has_no_shingles(text):
    assert make_shingles(text) == frozenset()


def test_relationship_thresholds_accept_exact_boundaries_and_either_containment_direction():
    result = SimilarityResult("a", "b", 0.80, 0.30, 0.30, 5, 6, 16)
    policy = SimilarityPolicy()
    assert policy.relates(result)
    assert policy.relates(replace(result, left_to_right_containment=0.30, right_to_left_containment=0.80))


@pytest.mark.parametrize("changes", [
    {"left_to_right_containment": 0.799999},
    {"jaccard": 0.299999},
    {"shared_shingles": 4},
], ids=["insufficient-containment", "insufficient-jaccard", "too-few-shared-shingles"])
def test_each_relationship_threshold_is_required(changes):
    boundary = SimilarityResult("a", "b", 0.80, 0.30, 0.30, 5, 6, 16)
    assert not SimilarityPolicy().relates(replace(boundary, **changes))


@pytest.mark.parametrize("options", [
    {"shingle_size": 0}, {"min_shared_shingles": 0},
    {"min_containment": -0.01}, {"min_jaccard": 1.01},
    {"direction_containment_margin": -0.01},
])
def test_invalid_policy_settings_are_rejected(options):
    with pytest.raises(ValueError):
        SimilarityPolicy(**options)

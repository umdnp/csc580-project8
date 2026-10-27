"""Shared report redaction is independent of CLI entry points."""

from gitskills.reporting.redaction import redact_text, safe_excerpt


def test_redaction_masks_credential_values_without_changing_safe_text():
    source = "curl https://example.test?api_key=hidden-value --header 'Authorization: Bearer secret-token'"
    redacted = redact_text(source)
    assert "hidden-value" not in redacted
    assert "secret-token" not in redacted
    assert "example.test" in redacted


def test_excerpt_redacts_before_truncating():
    source = "TOKEN=hidden-value " + "a" * 400
    result = safe_excerpt(source, limit=60)
    assert "hidden-value" not in result
    assert result.startswith("TOKEN=[REDACTED]")
    assert len(result) <= 60

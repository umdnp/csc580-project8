"""Rules that detect credential and secret-related access."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class SecretReferenceRule(RegexRule):
    """Detect references to common credential or secret identifiers."""

    rule_id = "CRED-001"
    category = RiskCategory.CREDENTIAL_ACCESS
    description = "Credential or secret reference detected"
    patterns = (
        r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)\b",
        r"\b(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|OPENAI_API_KEY)\b",
    )


class CredentialFileRule(RegexRule):
    """Detect references to common credential-bearing files."""

    rule_id = "CRED-002"
    category = RiskCategory.CREDENTIAL_ACCESS
    description = "Credential file reference detected"
    patterns = (
        r"(?<![\w.-])\.env(?:\.[\w.-]+)?\b",
        r"(?:~|/home/[^/\s]+)?/\.ssh/(?:id_rsa|id_ed25519|config)\b",
        r"(?:~|/home/[^/\s]+)?/\.aws/credentials\b",
    )

"""Rules that detect network access capability."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class UrlReferenceRule(RegexRule):
    """Detect HTTP and HTTPS URL references."""

    rule_id = "NET-001"
    category = RiskCategory.NETWORK_ACCESS
    description = "HTTP or HTTPS URL detected"
    patterns = (
        r"https?://[^\s<>()\"']+",
    )


class NetworkClientRule(RegexRule):
    """Detect common command-line and Python HTTP clients."""

    rule_id = "NET-002"
    category = RiskCategory.NETWORK_ACCESS
    description = "Network client usage detected"
    patterns = (
        r"(?<![\w.-])(?:curl|wget)[ \t]+(?=[^\s`])",
        r"\brequests\.(?:get|post|put|patch|delete|head)\s*\(",
    )

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
    """Detect common command-line, Python, and PowerShell HTTP clients."""

    rule_id = "NET-002"
    category = RiskCategory.NETWORK_ACCESS
    description = "Network client usage detected"
    patterns = (
        r"(?<![\w.-])(?:curl|wget)[ \t]+(?=[^\s`])",
        r"\b(?:requests|httpx)\.(?:get|post|put|patch|delete|head|request)[ \t]*\(",
        r"(?<![\w.])fetch[ \t]*\(",
        r"\baxios(?:\.(?:get|post|put|patch|delete|head|request))?[ \t]*\(",
        r"(?<![\w.-])(?:Invoke-WebRequest|Invoke-RestMethod)[ \t]+(?=[^\s`])",
    )

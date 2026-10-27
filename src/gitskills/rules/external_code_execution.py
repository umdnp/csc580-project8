"""Rules that detect execution of externally sourced code or dependencies."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class DownloadAndExecuteRule(RegexRule):
    """Detect remote content piped directly into a shell interpreter."""

    rule_id = "EXT-001"
    category = RiskCategory.EXTERNAL_CODE_EXECUTION
    description = "Downloaded content is piped to a shell interpreter"
    patterns = (
        r"\b(?:curl|wget)\b[^\n|]*\|[ \t]*(?:bash|sh|zsh)\b",
        # Explicit shell continuations, not arbitrary neighboring lines.
        r"\b(?:curl|wget)\b[^\n|]*(?:\\\r?\n[ \t]*[^\n|]*)+"
        r"\|[ \t]*(?:bash|sh|zsh)\b",
        r"\b(?:curl|wget)\b[^\n|]*\|[ \t]*\\\r?\n[ \t]*"
        r"(?:bash|sh|zsh)\b",
    )


class PackageInstallRule(RegexRule):
    """Detect common commands that install external packages."""

    rule_id = "EXT-002"
    category = RiskCategory.EXTERNAL_CODE_EXECUTION
    description = "External package installation detected"
    patterns = (
        r"\b(?:pip(?:3)?[ \t]+install|npm[ \t]+install|npm[ \t]+i)\b",
        r"\b(?:apt(?:-get)?|dnf|yum|brew)[ \t]+install\b",
        r"(?<![\w.-])(?:pnpm|yarn|bun)[ \t]+add\b",
    )

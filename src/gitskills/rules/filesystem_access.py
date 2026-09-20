"""Rules that detect file-system operations."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class FileCommandRule(RegexRule):
    """Detect common shell commands that modify the file system."""

    rule_id = "FS-001"
    category = RiskCategory.FILESYSTEM_ACCESS
    description = "File-system command detected"
    patterns = (
        r"(?<![\w.-])(?:rm|mv|cp|mkdir|touch)[ \t]+(?=[^\s`])",
    )


class FileWriteApiRule(RegexRule):
    """Detect common Python file-writing APIs."""

    rule_id = "FS-002"
    category = RiskCategory.FILESYSTEM_ACCESS
    description = "File-writing API detected"
    patterns = (
        r"\bopen[ \t]*\([^\n]*,[ \t]*[\"'][^\"']*[wax+][^\"']*[\"']",
        r"\.(?:write_text|write_bytes|write)[ \t]*\(",
    )

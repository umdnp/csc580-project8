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
        r"(?<![\w.-])(?:Remove-Item|Move-Item|Copy-Item|Set-Content|Add-Content)"
        r"[ \t]+(?=[^\s`])",
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


class FileReadRule(RegexRule):
    """Detect file-reading commands and APIs without head/tail or generic read."""

    rule_id = "FS-003"
    category = RiskCategory.FILESYSTEM_ACCESS
    description = "File-reading command or API detected"
    patterns = (
        r"(?<![\w.-])(?:cat|less|more|Get-Content)[ \t]+(?=[^\s`])",
        r"\.(?:read_text|read_bytes)[ \t]*\(",
        r"\bfs(?:\.promises)?\.(?:readFile|readFileSync|createReadStream)[ \t]*\(",
    )

"""Rules that detect file-system operations."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class FileCommandRule(RegexRule):
    """Detect common shell commands that modify the file system."""

    rule_id = "FS-001"
    category = RiskCategory.FILESYSTEM_ACCESS
    description = "File-system command detected"
    patterns = (
        r"(?<![\w.-])(?:rm|mv|cp|mkdir)[ \t]+(?=[^\s`])",
        # "touch any wiring or entry-point code" is prose, not a path.
        # Keep bare filenames when touch starts a shell command line.
        r"^[ \t]*touch[ \t]+(?=[^\s`])",
        r"(?<![\w.-])touch[ \t]+(?=(?:[~./\\$-][^\s`]|[\w.-]+\.[\w.-]+))",
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
        # A generic stream.write() might be a network response or an
        # in-memory buffer. Keep explicit filesystem APIs instead.
        r"\.(?:write_text|write_bytes)[ \t]*\(",
        r"\bfs(?:\.promises)?\.(?:writeFile|writeFileSync|appendFile|appendFileSync|createWriteStream)[ \t]*\(",
    )


class FileReadRule(RegexRule):
    """Detect file-reading commands and APIs without head/tail or generic read."""

    rule_id = "FS-003"
    category = RiskCategory.FILESYSTEM_ACCESS
    description = "File-reading command or API detected"
    patterns = (
        r"(?<![\w.-])(?:cat|Get-Content)[ \t]+(?=[^\s`])",
        # Read-only viewers are frequent words in prose. Require an explicit
        # path or a filename with an extension before treating them as commands.
        r"(?<![\w.-])(?:less|more)[ \t]+(?=(?:[~./\\$-][^\s`]|[\w-]+\.[\w-]+))",
        r"\.(?:read_text|read_bytes)[ \t]*\(",
        r"\bfs(?:\.promises)?\.(?:readFile|readFileSync|createReadStream)[ \t]*\(",
    )

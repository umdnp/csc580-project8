"""Rules that detect command execution capability."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class ShellCodeBlockRule(RegexRule):
    """Detect fenced blocks that explicitly contain shell commands."""

    rule_id = "CMD-001"
    category = RiskCategory.COMMAND_EXECUTION
    description = "Shell command block detected"
    patterns = (
        r"^```(?:bash|sh|shell|zsh|fish|powershell|pwsh)[ \t]*$",
    )


class CommandInvocationRule(RegexRule):
    """Detect common command interpreters and executable tooling."""

    rule_id = "CMD-002"
    category = RiskCategory.COMMAND_EXECUTION
    description = "Command invocation detected"
    patterns = (
        r"(?<![\w.-])(?:bash|sh|zsh|fish|python(?:\d+(?:\.\d+)*)?|"
        r"node|bun|uv|uvx|npm|npx|pnpm|yarn|pip(?:\d+(?:\.\d+)*)?|docker|"
        r"powershell(?:\.exe)?|pwsh(?:\.exe)?|cmd\.exe)[ \t]+(?=[^\s`])",
        # A local script at the start of a command line. Requiring a script
        # extension and line-start avoids treating inline path references as
        # invocations (e.g., "See `./scripts/install.sh`").
        r"^[ \t]*\./(?:[\w.-]+/)*[\w.-]+\.(?:sh|bash|py|js|mjs|ps1)"
        r"(?=$|[ \t;|&])",
    )

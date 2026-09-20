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
        r"(?<![\w.-])(?:bash|sh|zsh|python(?:3)?|npm|pip(?:3)?|docker)[ \t]+(?=[^\s`])",
    )

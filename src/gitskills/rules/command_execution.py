"""Rules that detect command execution capability."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class ShellCodeBlockRule(RegexRule):
    """Detect fenced blocks that explicitly contain shell commands."""

    rule_id = "CMD-001"
    category = RiskCategory.COMMAND_EXECUTION
    description = "Shell command block detected"
    patterns = (
        # Markdown allows up to three spaces of indentation and backtick or
        # tilde fences of length three or more; preserve original offsets.
        r"^ {0,3}(?:`{3,}|~{3,})[ \t]*(?:bash|sh|shell|zsh|fish|powershell|pwsh)[ \t]*\r?$",
    )


class CommandInvocationRule(RegexRule):
    """Detect common command interpreters and executable tooling."""

    rule_id = "CMD-002"
    category = RiskCategory.COMMAND_EXECUTION
    description = "Command invocation detected"
    patterns = (
        # Require invocation-shaped arguments, not words in ordinary prose.
        # E.g. "Python environment compatibility" and "npm + OpenAI" are not commands.
        r"(?<![\w.-])python(?:\d+(?:\.\d+)*)?[ \t]+"
        r"(?=(?:-[mcuEOBIWV]\b|--[\w-]+\b|[~./\\]|(?:[\w.-]+/)*[\w.-]+\.pyw?\b))",
        r"(?<![\w.-])(?:bash|sh|zsh|fish)[ \t]+"
        r"(?=(?:-[a-z]*[cex][a-z]*\b|--[\w-]+\b|[~./\\]|(?:[\w.-]+/)*[\w.-]+\.(?:sh|bash)\b))",
        r"(?<![\w.-])node[ \t]+"
        r"(?=(?:-[epv]\b|--[\w-]+\b|[~./\\]|(?:[\w.-]+/)*[\w.-]+\.(?:js|mjs|cjs)\b))",
        r"(?<![\w.-])(?:npm|pnpm|yarn|bun|pip\d*|uv|uvx|docker)[ \t]+"
        r"(?=(?:install|i|ci|run|exec|test|build|add|remove|uninstall|update|"
        r"list|show|audit|publish|start|stop|init|create|x|pip|sync|lock|tool|"
        r"venv|build|pull|push|compose|ps|logs|images|version|--[\w-]+)\b)",
        # npx/uvx run arbitrary package CLIs, not only known npm verbs.
        r"(?<![\w.-])(?:npx|uvx)[ \t]+(?=(?:--[\w-]+|[A-Za-z@./][\w@./:-]+))",
        # The PowerShell prose and placeholder cases are represented as
        # command references/templates by ShellExtractor, not executable lines.
        r"(?<![\w.-])(?:powershell(?:\.exe)?|pwsh(?:\.exe)?)[ \t]+"
        r"(?=(?:commands?\b|-[\w]+\b|[~./\\]|[\w.-]+\.ps1\b))",
        r"(?<![\w.-])cmd\.exe[ \t]+(?=(?:/[cCkK]\b|--[\w-]+\b))",
        # Read-only service/schedule queries are command invocations, not
        # system modifications (SYS-002 handles modifying operations).
        r"(?<![\w.-])systemctl[ \t]+(?=(?:--[\w-]+[ \t]+)*"
        r"(?:status|show|is-active|is-enabled|list-units|list-unit-files|"
        r"cat|help|start|stop|restart|reload|enable|disable|mask|unmask|"
        r"reenable|edit|daemon-reload|set-default|try-restart)\b)",
        r"(?<![\w.-])crontab[ \t]+(?=(?:-u[ \t]+[\w.-]+[ \t]+)?"
        r"(?:-[elr]\b|--(?:list|edit|remove)\b))",
        r"(?<![\w.-])service[ \t]+[\w.@-]+[ \t]+"
        r"(?=(?:status|start|stop|restart|reload|force-reload)\b)",
        r"\b(?:subprocess\.(?:run|Popen|call|check_call|check_output)|os\.system)\s*\(",
        r"(?<![\w.-])exec[ \t]+(?=(?:[~./\\]|[\w.-]+/)[\w./-]+)",
        # A local script at the start of a command line. Requiring a script
        # extension and line-start avoids inline path references.
        r"^[ \t]*\./(?:[\w.-]+/)*[\w.-]+\.(?:sh|bash|py|js|mjs|ps1)"
        r"(?=$|[ \t;|&])",
    )

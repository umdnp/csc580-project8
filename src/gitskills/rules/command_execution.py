"""Rules that detect command execution capability."""

import re

from gitskills.analysis.models import RiskCategory, RuleMatch

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


_BUN_SCRIPT = re.compile(r"(?<![\w.-])bun[ \t]+(?=[A-Za-z][\w:.-]*\b)", re.I)
_SHELL_LANGUAGES = {"bash", "sh", "shell", "zsh", "fish", "powershell", "pwsh"}


def _bun_command_context(text: str, position: int) -> bool:
    """Allow arbitrary Bun scripts only in explicit Markdown command contexts."""
    line_start = text.rfind("\n", 0, position) + 1
    line_end = text.find("\n", position)
    line_end = len(text) if line_end < 0 else line_end
    before = text[line_start:position]
    after = text[position:line_end]
    if before.count("`") % 2 and "`" in after:
        return True
    if before.strip():
        return False

    fence: str | None = None
    language = ""
    for line in text[:line_start].splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)$", line)
        if not match:
            continue
        marker, rest = match.groups()
        if fence is None:
            fence = marker
            language = rest.strip().split(maxsplit=1)[0].lower() if rest.strip() else ""
        elif marker[0] == fence[0] and len(marker) >= len(fence) and not rest.strip():
            fence = None
            language = ""
    return fence is not None and language in _SHELL_LANGUAGES


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
        # npx/uvx/bunx run arbitrary package CLIs, not only known npm verbs.
        r"(?<![\w.-])(?:npx|uvx|bunx)[ \t]+(?=(?:--[\w-]+|[A-Za-z@./][\w@./:-]+))",
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

    def evaluate(self, text: str) -> tuple[RuleMatch, ...]:
        matches = list(super().evaluate(text))
        positions = {match.start_offset for match in matches}
        for candidate in _BUN_SCRIPT.finditer(text):
            start = candidate.start()
            if start in positions or not _bun_command_context(text, start):
                continue
            matches.append(RuleMatch(
                rule_id=self.rule_id, category=self.category,
                message=self.description, line_number=text.count("\n", 0, start) + 1,
                matched_text="bun", start_offset=start, end_offset=start + 3,
            ))
        return tuple(sorted(matches, key=lambda match: (match.start_offset, match.end_offset)))

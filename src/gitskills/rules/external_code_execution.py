"""Rules that detect execution of externally sourced code or dependencies."""

from gitskills.analysis.evidence_extractors import staged_download_execution
from gitskills.analysis.models import RiskCategory, RuleMatch

from .base import RegexRule, Rule


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


class StagedDownloadAndExecuteRule(Rule):
    """Detect a downloaded file executed later in the same && chain."""

    rule_id = "EXT-003"
    category = RiskCategory.EXTERNAL_CODE_EXECUTION
    description = "Downloaded file executed by a linked local command"

    def evaluate(self, text: str) -> tuple[RuleMatch, ...]:
        matches: list[RuleMatch] = []
        offset = 0
        for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
            command = line.strip()
            if staged_download_execution(command):
                start = offset + len(line) - len(line.lstrip())
                matches.append(RuleMatch(
                    rule_id=self.rule_id, category=self.category,
                    message=self.description, line_number=line_number,
                    matched_text=command, start_offset=start,
                    end_offset=start + len(command),
                ))
            offset += len(line)
        return tuple(matches)


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

"""Rules that detect execution of externally sourced code or dependencies."""

from __future__ import annotations

import re
import shlex

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


_INSTALL_PREFIXES = (
    r"(?<![\w.-])(?:pip(?:3)?[ \t]+install|npm[ \t]+(?:install|i|ci)|"
    r"(?:pnpm|yarn|bun)[ \t]+(?:add|install)|"
    r"(?:apt(?:-get)?|dnf|yum|brew)[ \t]+install)\b",
)
_INSTALL_ARG_VALUES = {"--registry", "--index-url", "--extra-index-url", "--find-links",
                       "--prefix", "--cache-dir", "--config", "--cwd"}
_LOCAL_PATH = re.compile(r"(?:\.{1,2}(?:/.*)?|~/\S+|/\S+)$")


def _manifest_install(text: str, match: RuleMatch) -> bool:
    """Classify only recognizable installs whose package targets are not named."""
    command = match.matched_text.lower()
    if re.match(r"(?:apt(?:-get)?|dnf|yum|brew)\s+install|(?:pnpm|yarn|bun)\s+add", command):
        return False

    # Inspect only this command, never instructions on a subsequent line.
    rest = re.split(r"[`\r\n;&|]|[ \t]+#", text[match.end_offset:], maxsplit=1)[0]
    try:
        args = shlex.split(rest)
    except ValueError:
        return False
    targets: list[str] = []
    local_targets: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in _INSTALL_ARG_VALUES:
            if index + 1 >= len(args):
                return False
            index += 2
            continue
        if command.startswith("pip") and arg in {"-e", "--editable", "-r", "--requirement"}:
            if index + 1 >= len(args):
                return False
            local_targets.append(args[index + 1])
            index += 2
            continue
        if command.startswith("pip") and re.match(r"-(?:e|r)\S+", arg):
            local_targets.append(arg[2:])
        elif arg.startswith("-"):
            pass
        else:
            targets.append(arg)
        index += 1

    if command.startswith("pip"):
        if local_targets:
            return not targets and all(
                _LOCAL_PATH.fullmatch(path) or path.endswith((".txt", ".in", ".lock"))
                for path in local_targets
            )
        return bool(targets) and all(_LOCAL_PATH.fullmatch(path) for path in targets)
    return not targets


class _InstallRule(RegexRule):
    """Assign an install command to exactly one acquisition rule."""

    category = RiskCategory.EXTERNAL_CODE_EXECUTION
    patterns = _INSTALL_PREFIXES
    manifest: bool

    def evaluate(self, text: str) -> tuple[RuleMatch, ...]:
        return tuple(match for match in super().evaluate(text)
                     if _manifest_install(text, match) == self.manifest)


class PackageInstallRule(_InstallRule):
    """Detect installation commands naming explicit packages."""

    rule_id = "EXT-002"
    description = "Explicit package installation detected"
    manifest = False


class ManifestInstallRule(_InstallRule):
    """Detect project dependency installs with targets defined elsewhere."""

    rule_id = "EXT-004"
    description = "Manifest-based dependency installation detected"
    manifest = True

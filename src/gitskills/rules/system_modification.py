"""Rules that detect privileged or system-level modification."""

from gitskills.analysis.models import RiskCategory

from .base import RegexRule


class PrivilegeCommandRule(RegexRule):
    """Detect commands that explicitly request elevated privileges."""

    rule_id = "SYS-001"
    category = RiskCategory.SYSTEM_MODIFICATION
    description = "Privilege-elevation command detected"
    patterns = (
        r"(?<![\w.-])sudo[ \t]+(?=[^\s`])",
        r"(?<![\w.-])su[ \t]+(?:-|--login|\w+)",
    )


class SystemChangeCommandRule(RegexRule):
    """Detect permission, service, and scheduled-task modification commands."""

    rule_id = "SYS-002"
    category = RiskCategory.SYSTEM_MODIFICATION
    description = "System modification command detected"
    patterns = (
        r"(?<![\w.-])(?:chmod|chown|setfacl)[ \t]+(?=[^\s`])",
        r"(?<![\w.-])(?:systemctl|service|crontab)[ \t]+(?=[^\s`])",
    )

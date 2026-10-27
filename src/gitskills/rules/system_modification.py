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
        # Information-only verbs such as status, show, and is-active are
        # deliberately not system modifications.
        r"(?<![\w.-])systemctl[ \t]+(?:(?:--user|--system|--global|--runtime|--now|--force)[ \t]+)*"
        r"(?:enable|disable|reenable|start|stop|restart|reload|try-restart|"
        r"reload-or-restart|mask|unmask|edit|daemon-reload|set-default|"
        r"preset|preset-all|isolate|kill)\b",
        # -l is listing only. Editing/removing or replacing the crontab
        # from a named file/standard input changes scheduled tasks.
        r"(?<![\w.-])crontab[ \t]+(?:-u[ \t]+[\w.-]+[ \t]+)?"
        r"(?:-e\b|-r\b|--edit\b|--remove\b|-(?=\s|$)|"
        r"(?!-)[\w./~$-]+(?=\s|$))",
        # A reference to a software "service layer" is not a service command.
        # Require a service name followed by a modifying action.
        r"(?<![\w.-])service[ \t]+[\w.@-]+[ \t]+"
        r"(?:start|stop|restart|reload|force-reload)\b",
    )

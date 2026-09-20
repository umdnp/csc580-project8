"""Default rule registry for the GitSkills analyzer."""

from .base import Rule
from .command_execution import CommandInvocationRule, ShellCodeBlockRule
from .credential_access import CredentialFileRule, SecretReferenceRule
from .external_code_execution import DownloadAndExecuteRule, PackageInstallRule
from .filesystem_access import FileCommandRule, FileWriteApiRule
from .network_access import NetworkClientRule, UrlReferenceRule
from .system_modification import PrivilegeCommandRule, SystemChangeCommandRule


DEFAULT_RULES: tuple[Rule, ...] = (
    ShellCodeBlockRule(),
    CommandInvocationRule(),
    UrlReferenceRule(),
    NetworkClientRule(),
    FileCommandRule(),
    FileWriteApiRule(),
    SecretReferenceRule(),
    CredentialFileRule(),
    DownloadAndExecuteRule(),
    PackageInstallRule(),
    PrivilegeCommandRule(),
    SystemChangeCommandRule(),
)

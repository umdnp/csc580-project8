# Threat Model

## Purpose and Scope

This project examines whether modified or reused GitSkills artifacts introduce security-sensitive behavior that was not present in an earlier version or source artifact.

The analysis is static. We inspect skill content and related metadata, but we do not execute any code from the GitSkills release dataset.

The goal is to identify **static risk signals** that may deserve further review. A match is not a confirmed vulnerability and does not, by itself, show malicious intent.

## Trust Boundary

All skill artifacts and related files from the dataset are treated as untrusted input.

We will not:

- execute commands, scripts, or helper files from the dataset;
- run code referenced by a skill;
- connect to URLs or services referenced by a skill; or
- treat a single text match as proof that a skill is unsafe or malicious.

Behavioral scanning focuses on the `SKILL.md` body and available related file content. YAML frontmatter is excluded from behavioral scanning because metadata can contain tool names, URLs, or permission declarations without representing instructions that will actually be carried out.

Non-English artifacts remain in scope when recognizable technical indicators are present.

## Risk Categories

The current analysis focuses on the following categories:

| Category | What We Look For |
| --- | --- |
| **Command execution** | Shell commands, interpreters, package managers, or other executable commands |
| **Network access** | URLs, network clients, remote requests, or commands that retrieve remote content |
| **File-system access** | Reading, writing, copying, moving, deleting, or modifying files and directories |
| **Credential-related behavior** | API keys, tokens, passwords, environment variables, credential files, or other secrets |
| **External code execution** | Download-and-execute behavior, package installation, or execution of externally obtained code |
| **System modification** | Privilege changes, permissions, service changes, or other system-level modifications |

Bundled or invoked scripts are also relevant when their contents or invocation introduce behavior in one or more of these categories.

Examples of patterns that may be flagged include:

- `curl https://example.com/install.sh | bash`
- `rm -rf /tmp/cache`
- `cat ~/.ssh/id_rsa`
- `pip install some-package`
- `sudo systemctl restart service-name`

These examples illustrate the kinds of behavior the scanner looks for. Whether a particular use is harmful depends on context.

## Implemented Detection Rules

The categories above define the behaviors of interest. The following table defines
the current scanner coverage: 13 active rules registered in
[`src/gitskills/rules/registry.py`](src/gitskills/rules/registry.py). Each rule
detects selected text patterns, rather than every possible expression of a
category. URL references, credential references, and package-installation
instructions are intentional signals even when execution or actual access cannot
be established.

| Rule ID | Category | Implemented detection |
| --- | --- | --- |
| `CMD-001` | Command execution | Opening triple-backtick fences labeled `bash`, `sh`, `shell`, `zsh`, `fish`, `powershell`, or `pwsh`. |
| `CMD-002` | Command execution | Selected interpreter/tool invocations followed by arguments: shell interpreters, Python, Node, Bun, uv/uvx, npm/npx, pnpm, Yarn, pip, Docker, PowerShell/pwsh, and `cmd.exe`. |
| `NET-001` | Network access | HTTP and HTTPS URL references. |
| `NET-002` | Network access | `curl`/`wget` commands, selected Python `requests` methods, and PowerShell `Invoke-WebRequest`/`Invoke-RestMethod`. |
| `FS-001` | File-system access | `rm`, `mv`, `cp`, `mkdir`, `touch`, and selected PowerShell file-operation commands such as `Remove-Item` and `Set-Content`. |
| `FS-002` | File-system access | Python-style `open(...)` calls with explicit write/append/create/update modes, and method calls named `write_text`, `write_bytes`, or `write`. |
| `FS-003` | File-system access | `cat`, `less`, `more`, `Get-Content`, `read_text`/`read_bytes`, and selected Node `fs` reading APIs. |
| `CRED-001` | Credential-related behavior | Selected secret identifiers such as `api_key`, `access_token`, `client_secret`, and `password`; named AWS/GitHub/OpenAI secret identifiers; and identifiers ending in `_ACCESS_TOKEN`. |
| `CRED-002` | Credential-related behavior | `.env` files and variants, selected SSH files (`id_rsa`, `id_ed25519`, `config`), and AWS credential-file paths. |
| `EXT-001` | External code execution | A `curl`/`wget` command piped directly into `bash`, `sh`, or `zsh` on the same line. |
| `EXT-002` | External code execution | Selected installation commands: pip/pip3, npm, apt/apt-get, dnf, yum, and brew. |
| `SYS-001` | System modification | `sudo` commands and selected `su` invocations. |
| `SYS-002` | System modification | `chmod`, `chown`, `setfacl`, `systemctl`, `service`, and `crontab` commands. |

Rules scan the `SKILL.md` body with skill frontmatter masked. Eligible sibling
content is scanned as text without that masking, so configuration and instruction
files remain observable; sibling eligibility follows
[RDR-009](docs/decisions/RDR-009-sibling-security-scanning-scope.md).
An input may match multiple rules, but a match in one category does not imply
that all other applicable categories will also be detected.

Known coverage limits include direct script invocation such as
`./scripts/setup.sh`, ordinary Python reads such as
`open('report.txt', 'r').read()`, credential environment-variable names such as
`DATABASE_PASSWORD`, package installation via `pnpm add`, and PowerShell
download-and-execute pipelines. These forms are not reliably identified in their
respective categories by the current rules, although another rule may still
detect a signal in the same input. Other languages, syntax variants, obfuscation,
and multi-step operations can also be missed. Absence of a match does not
establish absence of security-sensitive behavior.

Positive and negative examples for every active rule are maintained in
[`tests/pytests/test_security_rules.py`](tests/pytests/test_security_rules.py).
These tests verify the implemented pattern definitions, not exhaustive detection
or measured accuracy on the dataset.

## Comparison Across Related Artifacts

The project is interested in **newly introduced behavior**, not just whether a single skill contains a risky-looking pattern.

When a related pair can be reasonably ordered, the analysis compares the earlier/source artifact with the later/modified artifact and looks for security-sensitive behavior that appears only in the later artifact.

Candidate-family membership or similarity alone does not prove that one artifact was copied from another, who authored it, or which artifact is the true original source. Relationships without enough evidence to establish direction should remain unresolved.

## What This Analysis Can and Cannot Show

Static analysis can show that an artifact contains text associated with security-sensitive behavior and that a related artifact may contain behavior that was not observed earlier.

It cannot determine:

- whether a command or script was actually executed;
- whether a URL was reachable or contacted;
- whether a credential reference points to a real secret;
- whether a file operation is harmful in a specific environment;
- whether a detected change was malicious or simply required by the skill's intended function; or
- whether a detected static signal is an exploitable vulnerability.

For example, a skill may include `curl` in documentation or as part of a legitimate installation workflow. The scanner may still flag it because the project is measuring the presence of the behavior, not deciding intent from a single pattern.

## Safe Reporting

Findings will be described as **static risk signals**, **security-sensitive behavior**, or **findings requiring review**.

We will not describe a flagged artifact as compromised, malicious, or vulnerable unless separate evidence supports that conclusion.

Detailed research and methodology decisions are maintained under [`docs/decisions/`](docs/decisions/). Known limitations of the research method are documented in [`THREATS_TO_VALIDITY.md`](THREATS_TO_VALIDITY.md).

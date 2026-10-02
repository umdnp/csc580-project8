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

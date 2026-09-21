# Threat Model for GitSkills Risk Analysis

## Purpose

This project analyzes whether reused or modified skills in the GitSkills dataset introduce risky behavior that was not present in an earlier version or source artifact. The project is scoped to static analysis of skill content and related metadata from the GitSkills release, and it is limited to the risk categories described in the project research question. We are not executing any code from the dataset.

The goal is to identify risk signals associated with command execution, file-system access, network access, credential handling, bundled or invoked scripts, and other risky behavior that can appear when skills are reused or modified across versions. These signals help us assess whether a reused skill may be more risky than the earlier version or source artifact it was derived from. We treat these as static security indicators, not evidence of malicious behavior.

## Safety and Trust Boundary

We treat every skill artifact in the dataset as untrusted input.

- We will not execute any commands, scripts, or helper files from the dataset.
- We will not run any code referenced by a skill.
- We will not connect to any URLs or services referenced by a skill.
- We will not assume a skill is safe or malicious based on a single textual pattern alone.

This analysis is limited to static inspection of the Markdown body content and relevant bundled file references for a base artifact and a reused or modified version. YAML frontmatter is excluded from behavioral rule processing because it can contain command names, URLs, tool names, and permission declarations without representing the actual skill instructions. Any result is a risk indicator, not proof of malicious behavior or active exploitation.

## Language and Frontmatter Handling

- Non-English artifacts remain in scope when they contain recognizable technical constructs such as URLs, shell commands, file paths, tool names, environment variables, or credential indicators. We do not exclude artifacts solely because they are written in a non-English language.
- Frontmatter is excluded from behavioral rule processing. The scanner analyzes the Markdown body and bundled artifacts, not YAML metadata such as `description`, `allowed-tools`, or other permission declarations.
- Metadata-only changes in frontmatter do not count as newly introduced risky behavior unless the corresponding risky instruction also appears in the skill body.
- This decision reduces false positives from declarative metadata while keeping the analysis grounded in the actual instructions that could change behavior across skill versions.
- A limitation remains: risky behavior expressed in non-English prose without recognizable technical indicators may be missed by static regex rules.

## Detection Model

The detector is implemented as a set of regex-based rules grouped by risk category. The default rule set includes:

- Command execution
  - CMD-001: shell code block detected
  - CMD-002: command invocation detected
- Network access
  - NET-001: HTTP/HTTPS URL detected
  - NET-002: network client usage detected
- Filesystem access
  - FS-001: file-system command detected
  - FS-002: file-writing API detected
- Credential access
  - CRED-001: credential or secret reference detected
  - CRED-002: credential file reference detected
- External code execution
  - EXT-001: downloaded content piped to a shell interpreter
  - EXT-002: external package installation detected
- System modification
  - SYS-001: privilege-elevation command detected
  - SYS-002: system modification command detected

This set is intentionally aligned with the project’s implementation and with the risk categories named in the research question. Bundled or invoked scripts are treated as a risk pattern in the broader static analysis model, especially where a skill invokes a script or downloads and executes external content.

The current implementation will not apply these behavioral rules to YAML frontmatter. We keep non-English artifacts in the analysis population when they contain recognizable technical constructs, but we recognize that some risky instructions written only in non-English prose without such indicators may be missed.

## Categories We Will Detect

### 1. Command execution

Definition: instructions or code that invoke shells, interpreters, package managers, or executables in ways that can act on the host system.

Examples we may flag:
- `bash -lc "rm -rf /tmp/cache"`
- `python -c "import os; os.system('whoami')"`
- `npm install`
- `curl ... | bash`
- `git clone https://example.com/repo.git`

Example from a skill:

```bash
bash -lc 'echo hello && rm -rf /tmp/cache'
```

Likely false positive:
- A documentation example showing a command as a usage example, without the skill instructing the agent to execute it.
- A tutorial snippet that references a command but does not meaningfully run it.

Limitations:
- Static pattern matching does not prove a command was executed in a real environment.
- We cannot determine whether the command is benign, privileged, or context-dependent.

### 2. File-system access

Definition: instructions or code that read, write, delete, rename, or traverse local files or directories, especially sensitive locations or user data.

Examples we may flag:
- `cat ~/.ssh/id_rsa`
- `cp .env .env.bak`
- `rm -rf /tmp/output`
- `open('/etc/hosts', 'w')`
- `Path('/var/log/system.log').read_text()`

Example from a skill:

```bash
cp .env .env.bak
```

Likely false positive:
- A path appears in prose as an example location rather than a command that modifies the file system.
- Documentation describing a config file without actually instructing the system to access it.

Limitations:
- We cannot know which files exist in the target environment or whether they are sensitive there.
- We cannot determine whether the file operation is read-only, user-scoped, or safe in context.

### 3. Network access

Definition: instructions or code that initiate outbound HTTP requests, remote connections, or fetch content from external services.

Examples we may flag:
- `curl https://api.example.com/health`
- `wget http://server/file.tar.gz`
- `requests.get("https://example.com")`
- `ssh user@host`
- `git clone https://github.com/example/project.git`

Example from a skill:

```bash
curl -fsSL https://example.com/install.sh | sh
```

Likely false positive:
- A documentation section listing URLs for API references, package registries, or external services without actually fetching them as part of the skill workflow.
- A plain-text example that references a URL but does not instruct remote access.

Limitations:
- Static detection cannot confirm whether the network call is made, reachable, or malicious.
- We cannot determine the runtime destination, authentication state, or the effect of the request.

### 4. Credential-related instructions

Definition: instructions or code that access, expose, store, or manipulate secrets, tokens, passwords, API keys, or private credentials.

Examples we may flag:
- `export AWS_SECRET_ACCESS_KEY=...`
- `api_key = os.getenv("GITHUB_TOKEN")`
- `cat ~/.ssh/id_rsa`
- `print(process.env.OPENAI_API_KEY)`
- `echo "$GITHUB_TOKEN" >> ~/.bash_history`

Example from a skill:

```bash
echo "$GITHUB_TOKEN" >> ~/.bash_history
```

Likely false positive:
- A tutorial showing `YOUR_API_KEY` as a placeholder value.
- Documentation describing how to set environment variables securely without actually leaking a secret.

Limitations:
- We cannot know whether a value is a real secret or a harmless placeholder.
- We cannot determine whether the credential is used legitimately or exfiltrated.

### 5. Bundled or invoked scripts

Definition: helper files, scripts, or other executable resources packaged with a skill or referenced by the skill instructions. This includes both script files bundled in a skill directory and commands that invoke them during execution.

Examples we may flag:
- `./scripts/install.sh`
- `python scripts/cleanup.py`
- `node scripts/worker.js`
- `bash .claude/skills/example/run.sh`
- a skill folder containing script files such as `setup.py`, `deploy.sh`, or `main.py`

Example from a skill:

```bash
python scripts/cleanup.py --delete-old-logs
```

Likely false positive:
- A script file is included in the repo but never invoked by the skill instructions.
- A helper file exists only as a template or example, not as an active execution path.
- A repository includes a script for a future workflow, but the skill itself never triggers it.

Limitations:
- The presence of bundled scripts is not proof of malicious intent.
- Static analysis cannot determine the script’s runtime behavior without executing it, which is explicitly out of scope for this project.
- We cannot infer whether a bundled helper is harmless, necessary, or malicious without review of the surrounding context.

### 6. Other risky behavior

Definition: any additional behavior that can increase supply-chain or host risk but does not fit cleanly into the categories above. This is intentionally scoped to the project question: behavior that may be introduced when a skill is modified or reused, beyond the core categories of command execution, file-system access, and network access. Examples include handling credentials or secrets, creating or invoking scripts, changing permissions, or modifying system configuration.

Examples we may flag:
- `sudo apt-get install ...`
- `chmod 600 ~/.ssh/id_rsa`
- `systemctl restart service-name`

Example from a skill:

```bash
chmod 600 ./backup/example-app/settings.conf
```

Likely false positive:
- A documentation note explaining a permission change without the workflow actually performing it.
- A tutorial that references a configuration change as an example but does not direct the agent to carry it out.

Limitations:
- Static rules cannot know if the behavior is justified in context.
- We are not making a claim about safety or malicious intent based solely on a textual pattern.

## Comparison Logic Across Related Artifacts

This project is interested in whether a reused or modified skill introduces new risky behavior relative to an earlier version or source artifact. We will compare the Markdown body of skill files, not the YAML frontmatter, for static differences in:

- command strings
- file operations
- URL references
- credential handling
- bundled or invoked script references
- system or permission changes

This is a static delta analysis, not a runtime exploit analysis. A change is treated as a candidate risk signal when the newer artifact adds one or more patterns that were not present in the earlier source. We will interpret the result as a review trigger, not a confirmed exploit. Metadata-only changes such as tool declarations in YAML frontmatter will not count as newly introduced behavioral risk unless the corresponding behavior also appears in the skill body.

## What Our Analysis Cannot Determine

This project cannot determine the following from static text inspection alone:

- whether a command was actually executed at runtime
- whether a script is malicious, harmless, or simply unused
- whether a URL was reachable or live
- whether a credential is real, redacted, or placeholder text
- whether a file access is harmful in a specific environment
- whether observed behavior reflects malicious intent or a legitimate workflow
- whether the original artifact created the behavior or whether it was added later in a different project
- whether a risky instruction is hidden only in non-English prose without recognizable technical indicators

Static rule-based detection can identify suspicious patterns; it cannot prove compromise, exploitation, or malicious purpose. This limitation is a direct consequence of working with a static scanner and a dataset that includes both English and non-English skill text.

## What Is Outside the Scope of This Project

The following are outside the scope of this project:

- executing untrusted code from the dataset
- running scripts or commands from community skill artifacts
- sandboxing or instrumenting skills in a real environment
- building a definitive malware detector for arbitrary code
- determining whether a repository is compromised in production
- proving malicious intent or security impact from a single pattern match
- claiming that a skill is unsafe without a human review of the surrounding context

## Reporting Standard

When we report findings, we will describe them as risk indicators or suspicious static signals rather than confirmed exploits. If a skill is flagged, it should be treated as a candidate requiring manual review rather than a proven malicious artifact.

## Summary

This threat model is intentionally conservative and aligned with the repository’s current scope as defined in the project research question and the language/frontmatter decision recorded in RDR-002. It focuses on the security-related patterns explicitly named there: command execution, file-system access, network access, credential-related instructions, bundled or invoked scripts, and other risky behavior introduced when skills are modified or reused. The project will review these signals statically, compare them across versions, exclude YAML frontmatter from behavioral rule processing, keep non-English artifacts in scope when technical indicators remain visible, and will not execute any content from the dataset.

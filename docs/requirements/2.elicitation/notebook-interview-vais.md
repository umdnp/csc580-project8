# Chat Log: Requirements Engineering & Agent Skills Security Threat Modeling

**Notebook:** Copy of [Project-8] CSC 580 Group Assignment 2: Requirements Engineering  
**Date:** September 21, 2026  

---

## Turn 1

### User Question
What types of operational capabilities (e.g., shell command execution, file system access, external network calls, or bundled scripts) are commonly found in public agent skills?

### Gemini Notebook Response
Public agent skills—as documented in the Agent Skills specification, MSR 2027 challenge materials, and the GitSkills dataset—commonly contain the following types of operational capabilities:

* **Bundled Executable Scripts (`scripts/` directory)**: Skills frequently bundle custom executable code and utility scripts in a dedicated `scripts/` folder within the skill package. Commonly observed script types include:
  * **Bash/Shell scripts**: Used for host checks, dependency validation, git operations, or environment setup (e.g., `check-prereqs.sh`, `collect-debug-snapshot.sh`, `finalize.sh`).
  * **Python scripts**: Used for data mining, contact extraction, web scraping, and content building (e.g., `build_csv.py`, `discover_businesses.py`, `domain_analyzer.py`).
  * **JavaScript / Node.js files**: Used for custom integrations or API functions (e.g., `search.mjs`).
  
  In the GitSkills dataset, the presence of these files is tracked via the `has_scripts` flag and detailed in the `artifact_siblings` table.

* **Shell Command Execution**: Natural language instructions that direct language-model agents to execute command-line instructions, build pipelines, or system utilities directly on the host machine. Skills can also explicitly list pre-approved CLI tools in their YAML frontmatter using the experimental `allowed-tools` field (for example, `allowed-tools: Bash(git:*) Bash(jq:*) Read`).

* **External Network Calls & Remote Services**: Instructions or embedded scripts that perform web searches, scrape external web pages, connect to REST/GraphQL APIs, or interface with remote language models. Skills declare system requirements—such as needing internet access, Docker, or specific system tools—in the frontmatter `compatibility` field.

* **File System Access & Local Resource Management**: Instructions for reading, writing, modifying, and organizing local files or repository trees. Skills organize static resources using standard subdirectories:
  * **`references/`**: Domain documentation, compliance guidelines, safety rules, or schema guides loaded on demand by the agent.
  * **`assets/`**: Static resource files, document/CSV templates, images, or schemas.

* **Environment & Credential Configuration**: Instructions and code for setting environment variables, managing local API keys/tokens, or configuring CLI operational profiles.

### Sources Cited
* **Specification - Agent Skills**: [https://agentskills.io/specification](https://agentskills.io/specification)
* **GitSkills: A Dataset of Agent Skills on GitHub**: arXiv:2608.10906, Zenodo DOI: 10.5281/zenodo.21875637, Hugging Face `mvaccargiu/gitskills`
* **MSR 2027 Mining Challenge Track**: [https://2027.msrconf.org/track/msr-2027-mining-challenge](https://2027.msrconf.org/track/msr-2027-mining-challenge)
* **CSC 580 Group Project Syllabus & Requirements**: `CSC_580_Group_Project_V2026.09.10.pdf`

---

## Turn 2

### User Question
How should a security threat model operationally define "other risky behavior" beyond basic shell commands and URLs—such as credential/secret handling, script creation/invocation, or system/data exposure?

### Gemini Notebook Response
To construct a security threat model for agent skills, **"other risky behavior"** can be operationally defined as static, measurable rules that inspect the `SKILL.md` instruction body (`artifacts.content`), bundled folder siblings (`artifact_siblings`), and version deltas across skill copies. 

A static analyzer can operationalize these security risks into five distinct threat categories:

1. **Credential & Secret Handling**
   * **Operational Indicator**: Natural language directives or embedded code requiring the agent to read, parse, or transmit sensitive authentication tokens.
   * **Static Detection Rules**:
     * **Keyword/Pattern Matches**: Regular expressions in `artifacts.content` scanning for hardcoded secrets, private keys, or environment variable references (e.g., `API_KEY`, `OPENROUTER_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `TOKEN`).
     * **Sensitive File Targets**: Instructions directing agents or scripts to open, read, or export local secret stores (e.g., `.env`, `~/.aws/credentials`, `~/.ssh/id_rsa`).

2. **Script Bundling, Creation & Dynamic Invocation**
   * **Operational Indicator**: The presence of unverified executable files or instructions that dynamically generate and execute scripts on the host environment.
   * **Static Detection Rules**:
     * **Bundled Script Flagging**: Queries checking `artifacts.has_scripts = 1` or filtering `artifact_siblings` for executable file types (`.sh`, `.py`, `.js`, `.mjs`) in the `scripts/` directory or root folder.
     * **Dynamic Script Generation**: Regex detection in `SKILL.md` body text for shell patterns that write code to disk at runtime (e.g., `cat << 'EOF' >`, `echo ... > payload.py`) followed immediately by execution commands (`chmod +x`, `python3`, `bash`, `node`).

3. **File System Access & System Operations**
   * **Operational Indicator**: Directives or scripts that attempt to read, modify, or delete files outside the agent's intended local working workspace.
   * **Static Detection Rules**:
     * **Privilege Escalation & Root Access**: Commands invoking administrative or root privileges (e.g., `sudo`, `su`, root-level package managers).
     * **Path Traversal & System File Targeting**: Shell string patterns matching directory traversal (`../`) or modifications to critical system paths (e.g., `/etc/`, `/usr/bin/`, startup scripts like `~/.bashrc`).
     * **Destructive Command Execution**: Unbounded file deletion or overwrite commands (e.g., `rm -rf *`, `dd`, formatting commands).

4. **Data Harvesting & Unsanctioned Network Calls**
   * **Operational Indicator**: Instructions or bundled code that gather host/environment telemetry or local data and perform external remote requests.
   * **Static Detection Rules**:
     * **Network Call Detection**: Identifying HTTP request libraries or network CLI utilities (`curl`, `wget`, `requests.post`, `fetch`) within `SKILL.md` or sibling scripts.
     * **System Telemetry / Reconnaissance**: Scripts designed to snapshot system state, environment variables, or local user files (e.g., debug snapshot collectors or contact extraction scripts) when paired with network output directives.

5. **Supply-Chain Risk & Cross-Version Deltas**
   * **Operational Indicator**: Modifications introduced when a skill is copied or reused across repositories that add capabilities absent in the original source artifact.
   * **Static Detection Rules**:
     * **Delta Scanners**: Comparing verbatim or near-duplicate skill copies (linked by `file_sha` or content similarity) across commits or repositories.
     * **Risk Inflation Rules**: Flagging instances where a downstream copy introduces new `has_scripts` flags, added network calls, or new tool privileges (e.g., additions to the frontmatter `allowed-tools` field) that were not present in the original representative skill.

### Sources Cited
* **CSC 580 Group Project Syllabus**: `CSC_580_Group_Project_V2026.09.10.pdf` (Research Question 4: Skill Security and Supply-Chain Risk)
* **GitSkills: A Dataset of Agent Skills on GitHub**: arXiv:2608.10906, Zenodo DOI: 10.5281/zenodo.21875637, Hugging Face `mvaccargiu/gitskills`
* **MSR 2027 Mining Challenge Track**: [https://2027.msrconf.org/track/msr-2027-mining-challenge](https://2027.msrconf.org/track/msr-2027-mining-challenge)

---

## Turn 3

### User Question
Can static analysis differentiate between a skill that requires benign operational permissions (e.g., local project setup) versus one that introduces unnecessary exfiltration or system exposure?

### Gemini Notebook Response
Static analysis can differentiate between benign operational permissions and exfiltration or system exposure by implementing **rule-based scanning, capability mismatch detection, and cross-version delta analysis**. 

Because agent skills consist of YAML frontmatter, natural-language instructions in `SKILL.md`, and optional bundled executable code in `scripts/`, a static analyzer can evaluate risk across the following dimensions:

1. **Declared vs. Inferred Capability Matching**
   * **Declared Constraints**: The Agent Skills specification allows skills to explicitly declare environment requirements in the frontmatter `compatibility` field (e.g., requiring specific system tools or network access) and pre-approved tool execution scopes in the experimental `allowed-tools` field (e.g., `allowed-tools: Bash(git:*) Bash(jq:*) Read`).
   * **Inferred Behavior**: Static scanners parse the natural-language body and bundled script files (such as `.sh`, `.py`, or `.mjs` in `scripts/`) to extract all actual command patterns, system calls, and URLs.
   * **Differentiation Rule**: A skill is flagged for potential exposure or privilege inflation if its executable scripts or body instructions attempt actions (e.g., outbound `curl` requests or reading host environment variables) that fall outside its declared `compatibility` profile or `allowed-tools` list.

2. **Path Scoping & Operational Boundaries**
   * **Benign Operational Setup**: Benign setup commands restrict file-system access to workspace-local relative paths (`./build`, `./node_modules`) and execute host checks or build workflows (e.g., `git status`, verifying `node`/`npm` versions in a `check-prereqs.sh` script).
   * **Unnecessary System Exposure**: Scanners flag path traversal (`../`), privilege escalation (`sudo`), or access to system/user configuration directories outside the working repository (e.g., `~/.ssh/`, `~/.aws/credentials`, `/etc/`).

3. **Source-to-Sink Data-Flow Heuristics**
   * **Exfiltration Risk Rules**: Static analysis flags pattern combinations where a sensitive data **source** (e.g., reading environment keys like `OPENROUTER_API_KEY` or scanning local `.env` files) connects to an external network **sink** (e.g., `curl -X POST`, `requests.post()`, or webhooks).
   * **Purpose Mismatch**: If a skill's YAML `description` states it performs local tasks (e.g., local PDF form extraction or formatting), but its code or instructions contain remote network requests, the static analyzer flags the discrepancy as an unnecessary security risk.

4. **Supply-Chain Delta Analysis (Risk Inflation)**
   * Over **50.5%** of files in the GitSkills dataset represent verbatim copies reused across repositories. 
   * A static analyzer can group identical skills via content hash (`file_sha`) and trace their commit lineage to compare derivative copies against primary upstream sources.
   * **Differentiation Rule**: If an upstream parent skill contains only benign setup scripts, but a downstream copied version introduces new network calls, credentials-handling code, or extra bundled scripts (`has_scripts = 1`), the analyzer isolates the modified delta as an introduced supply-chain threat.

5. **Limitations & False-Positive Challenges**
   * **Natural-Language Ambiguity**: Unlike traditional source code verified by a compiler, skills rely heavily on natural language instructions evaluated probabilistically by language models. A static scanner must carefully distinguish between executable instructions versus documentation examples or warning guidelines to prevent false positives.
   * **Dynamic Generation**: Instructions that direct an LLM agent to construct and execute shell scripts dynamically at runtime bypass simple string/regex scanners, requiring deeper AST parsing of bundled scripts.

### Sources Cited
* **Specification - Agent Skills**: [https://agentskills.io/specification](https://agentskills.io/specification)
* **CSC 580 Group Project Syllabus**: `CSC_580_Group_Project_V2026.09.10.pdf` (Research Questions 1 & 4)
* **GitSkills: A Dataset of Agent Skills on GitHub**: arXiv:2608.10906, Hugging Face `mvaccargiu/gitskills`, Zenodo DOI: 10.5281/zenodo.21875637

---

## Turn 4

### User Question
How can static detection rules distinguish between passive, informational code examples (e.g., Markdown documentation showing a curl usage example) and active prompt instructions directing an LLM agent to execute a command?

### Gemini Notebook Response
To minimize false positives in a static analyzer for agent skills, detection rules must move beyond simple string matching (such as searching for `curl` or `rm`). Static analyzers can differentiate between **passive, informational code examples** (e.g., Markdown documentation) and **active prompt instructions** (directing an LLM agent to execute a command) using the following structured techniques:

1. **Markdown Abstract Syntax Tree (AST) & Heading Hierarchy Parsing**
   * **Section Context Extraction**: A Markdown AST parser classifies code snippets based on their parent heading. Snippets residing under standard documentation headings—such as `## Examples`, `## Usage Examples`, `## Syntax`, or `## References`—are categorized as passive documentation.
   * **Instruction Section Scoping**: Commands located under imperative operational headings—such as `## Instructions`, `## Workflow`, `## Steps`, or `## Execution`—are flagged as active prompt directives.
   * **Fenced Code Block Context**: Fenced code blocks (e.g., ```bash ... ```) in documentation sections are treated as sample syntax unless accompanied by explicit imperative trigger text.

2. **Syntactic & Linguistic Prompt Rules (Imperative vs. Indicative Mood)**
   * **Imperative Directives (Active Trigger)**: Active instructions use direct imperative language instructing the agent to perform an operation (e.g., *"Run the following script to extract data..."*, *"Execute `curl ...` to fetch the response"*, or *"Call `scripts/extract.py`"*).
   * **Descriptive / Conditional Context (Passive Trigger)**: Passive examples rely on indicative or conditional framing (e.g., *"For example, a user might run..."*, *"Sample output:"*, or *"Syntax reference:"*).
   * **Proximity Matching**: The scanner checks if an imperative command verb occurs within a tight window (e.g., within 1–2 sentences) of a command or executable snippet.

3. **Frontmatter & Tool Execution Declarations**
   * **Pre-approved Tool Matching (`allowed-tools`)**: Under the Agent Skills specification, skills can declare pre-approved CLI execution permissions in YAML frontmatter via the experimental `allowed-tools` field (e.g., `allowed-tools: Bash(curl:*)`).
   * **Rule**: If a command snippet matches an explicit `allowed-tools` or `compatibility` permission declared in the frontmatter, the analyzer elevates its classification to an **active capability requirement** rather than an arbitrary text example.

4. **Folder Scope & File Context (Progressive Disclosure)**
   * **`SKILL.md` vs. Auxiliary Directories**: Under progressive disclosure rules, an agent loads the main `SKILL.md` body when activated, whereas auxiliary documentation files in `references/` or `assets/` are loaded on demand as background context.
   * **Rule**: Command occurrences in `references/` or `assets/` files carry a lower default risk weighting than commands embedded in the core `SKILL.md` instruction file or bundled executable scripts in `scripts/`.

5. **Multi-Version Delta Scanning**
   * **Copy Delta Analysis**: Over 50% of skills in the GitSkills dataset represent verbatim copies across repositories. Comparing a derivative skill against its primary source (`file_sha`) reveals whether an edit converted a passive example in an upstream `## Examples` block into an active instruction in the main execution workflow.

### Sources Cited
* **Specification - Agent Skills**: [https://agentskills.io/specification](https://agentskills.io/specification) (Progressive Disclosure & SKILL.md format)
* **CSC 580 Group Project Syllabus**: `CSC_580_Group_Project_V2026.09.10.pdf` (Research Questions 4 & 5)
* **GitSkills: A Dataset of Agent Skills on GitHub**: arXiv:2608.10906, Zenodo DOI: 10.5281/zenodo.21875637

# CANTRELL QUESTIONS

## Question 1
A lot of the content in the dataset is not in English. What's the best way to handle analyzing non-English content?

## Answer 1
The sources recognize non-English artifacts as an important aspect of AI-native software engineering and outline how natural language content is stored and evaluated within the datasets:

### 1. How Non-English Content is Handled in the Data
* **UTF-8 Encoding**: All string columns across the dataset tables are stored as **UTF-8**, ensuring that multi-byte characters and non-English scripts are preserved without encoding corruption.
* **Multilingual Agent Design**: The MSR Mining Challenge explicitly notes that because AI coding agents operate on **multilingual models**, developers often write skills or specifications in their native language to describe workflows more precisely than they might in English. Investigating which natural languages appear across skills is one of the proposed research directions.

---

### 2. Best Strategies for Analyzing Non-English Content

When building your project pipeline, you can structure your analysis using the following approach:

1. **Language Identification**:
   * Add a language-detection step (e.g., using fastText or `langdetect`) to your feature extraction pipeline to tag each artifact with its primary natural language.
   * This allows you to compare structural and adoption metrics across language cohorts.

2. **Language-Agnostic / Structural Feature Extraction**:
   * Extract features that depend on document structure rather than English vocabulary, such as YAML front matter fields (`name`, `description`), heading depth, character counts (`body_chars`), task lists, code block counts, and file reference links.

3. **Multilingual Embeddings or Translation**:
   * **Multilingual LLM/Embeddings**: Since modern LLMs process multilingual text natively, you can pass non-English text directly into multilingual embedding models or LLMs for semantic classification and clustering.
   * **Machine Translation**: If using English-specific NLP metrics (such as readability scores or English keyword lexicons), translate non-English contents into English as an intermediate pipeline step.

4. **Validation and Validity Threats**:
   * Manually inspect a sample of non-English and translated artifacts to assess translation quality or classification accuracy.
   * Document language-detection inaccuracies, translation semantic shift, or dataset bias in your project's `THREATS_TO_VALIDITY.md`.

---

### What the Sources Do Not Specify
The challenge documentation does **not prescribe a mandatory translation library or specific language-detection tool**, leaving the choice of NLP framework to your team's pipeline implementation.

💡 **Would you like help outlining a Python feature-extraction script to detect natural languages or parse structural metadata from a sample of the dataset?**

## Question 2
I have only begun scratching the surface about what is available in the dataset. I don't know what I don't know. Are there any glaring datapoints that are omitted from the dataset that would have helped a research project? This will help to define limitations with the data.

## Answer 2
Understanding what is **missing or omitted** from the datasets is critical for defining the scope, threats to validity, and research limitations of your project. The dataset documentations explicitly identify several key omissions and sampling boundaries across **GitSkills**, **SpecMine**, and the underlying **GitHub mining process**:

---

### 1. Omissions in GitSkills
* **Truncated History on Renames**: Commit history follows a file's **current path**. If a skill file was moved or renamed, `first_commit_at` records the rename date rather than its original creation date, and `commit_count` only covers commits at the current path.
* **Incomplete Commit History Coverage**: Commit history was collected for standard locations (`.claude/skills/` or `skills/`) plus a size-stratified sample of other paths. Rows where `history_fetched = 0` lack commit metadata.
* **Unextracted YAML Frontmatter Fields**: While the Agent Skills specification allows optional frontmatter fields like `license`, `compatibility`, `allowed-tools`, and custom `metadata`, GitSkills **only extracts `name` and `description`** as dedicated table columns.
* **Folder & Sibling File Caps**: Sibling text files are only fetched up to **100 KB per file**, binary files are skipped, and large skill folders exceeding listing limits are flagged as truncated (`composition_truncated = 1`). Sibling folders describe only the primary representative (`dedup_primary = 1`), not duplicate occurrences.
* **No True Reuse Provenance**: Because skills spread by direct folder copying without a central package manager, the primary representative (`dedup_primary = 1`) is selected via a path-preference rule and **is not assumed to be the original source or author**.

---

### 2. Omissions in SpecMine
* **PR Layer Restricted to High-Star Repositories**: The pull-request sweep targeted repositories with **\\(\ge 10\\) stars** across 10–11 tool families (5,992 PRs across 581 repos). PR co-change history is omitted for the remaining ~72,000 broad-census repositories.
* **Missing Spec Text in Parquet Mirrors**: The full raw Markdown text of specifications is included in `specs.jsonl.gz` on Zenodo, but is **omitted from the Hugging Face Parquet tables**.
* **GitHub Diff Truncation**: A small fraction (0.08%) of PRs have `n_spec_files = 0` because GitHub caps PR diff listings at 3,000 files per PR.

---

### 3. Redacted & Anonymized Data (Both Datasets)
* **Privacy Redactions**: Personal names, committer/author email addresses (including GitHub noreply emails), GPG signature blobs, avatar URLs, and repository descriptions have been redacted or masked across both datasets.
* **Anonymized Author Accounts**: Commit authors in GitSkills are replaced with keyed one-way hash codes (bots retain their logins).

---

### 4. Ecosystem & Platform-Level Blind Spots
* **GitHub Code Search Bounds**: Neither dataset captures private repositories, non-default branches, files over 384 KB, repositories with over 500,000 files, or forks (unless the fork has more stars than its parent).
* **No Runtime or LLM Execution Tracing**: The datasets contain static files, commit histories, and pull requests. They do **not contain runtime prompt logs, agent interaction traces, model outputs, or probabilistic selection records** showing how an AI agent actually processed a spec or skill at runtime.

---

🔍 **Would you like to draft a section for your project's `THREATS_TO_VALIDITY.md` file addressing how these dataset limitations impact your specific research question?**

## Question 3
My understanding is that GitSkills are an Anthropic/claude initiative. I would believe that the contents of the SKILL.md files are optimized for running with claude, its agents, and with any other Anthropic-based applications. Could the SKILL.md files being ingested by a non-Anthropic product have adverse affects? Or are the skills generic enough to be used by basically an LLM and its associated agents, etc.?

## Answer 3
Anthropic introduced the **Agent Skills format in October 2025 as an open specification**. While Anthropic maintains its own repository of skills for Claude, the core specification is open and managed independently at `agentskills.io`. 

---

### 1. Are Skills Generic Enough for Other LLMs?

**Yes.** At its core, an agent skill is simply a directory containing a `SKILL.md` file formatted with standard YAML frontmatter (`name`, `description`) followed by plain Markdown instructions. 

* **Natural Language Instructions**: Because skill contents consist primarily of natural language guidelines, step-by-step procedures, and Markdown examples, any modern instruction-following LLM or agent framework can parse and act on them.
* **Progressive Disclosure**: The specification uses a progressive disclosure architecture—agents inspect lightweight metadata (~100 tokens) to decide whether to activate a skill, load the main `SKILL.md` instructions when active, and fetch supporting reference files only as needed. This design is vendor-agnostic and applies to virtually any LLM agent context.
* **Ecosystem Adoption**: In the GitSkills dataset, **55.4%** of collected skills reside under generic `skills/` directories, while **9.8%** sit in the canonical `.claude/skills/` directory and **34.8%** reside in other paths.

---

### 2. Potential Adverse Effects or Limitations with Non-Anthropic Products

Ingesting `SKILL.md` files into a non-Anthropic product or different LLM architecture does present several operational, behavioral, and security risks:

* **Tool and System Dependencies**: Skills frequently bundle executable code in a `scripts/` directory or specify system dependencies using the optional `compatibility` or `allowed-tools` YAML frontmatter fields. If a non-Anthropic agent lacks the required CLI tools, Python environment, or tool-calling schema, running the skill will fail or produce execution errors.
* **Security and Command Execution Risks**: Skills can instruct agents to execute shell commands, manipulate files, or access network endpoints. Ingesting untrusted skills into an agent product without strict sandboxing, containerization, or permission prompts creates significant security and supply-chain vulnerabilities.
* **Instruction Drift & Prompt Sensitivity**: Skills are interpreted probabilistically at runtime without type checkers or compilers verifying execution accuracy. Instructions crafted and prompt-engineered specifically for Claude's reasoning style or context window may produce unexpected outputs, hallucinated tool calls, or missed steps when evaluated by different LLMs.
* **Path Discovery Assumptions**: Non-Anthropic agents scanning a codebase might look exclusively in vendor-neutral directories (`skills/`) and miss skills placed strictly in Anthropic's vendor-specific path (`.claude/skills/`).

---

### 3. Empirical Context in the Dataset

Whether skill files are converging toward a universal standard or remaining tool-specific is explicitly highlighted as a core research topic in the MSR 2027 Mining Challenge. Specifically, **Research Question 5** invites researchers to analyze whether skills are adopting vendor-neutral structures or maintaining distinct tool-specific conventions across different ecosystems.

---

💡 **Would you like to write a SQL query or Python script to analyze the proportion of vendor-neutral (`skills/`) vs. Claude-specific (`.claude/skills/`) paths in the GitSkills dataset?**

## Question 4
My team chose a research question that looks for security-relevant actions that a SKILL.md file could prompt the LLM to attempt. The list includes: executable commands, URLs, scripts, file operations, and credential-related instructions. Is there already an all encompassing, documented list of these actions found within the dataset?

## Answer 4
**No**, there is no pre-existing or documented all-encompassing list of security-relevant actions built into the dataset. 

---

### What the Dataset Provides vs. What is Missing

1. **High-Level Structural Summary Flags**:
   * The `artifacts` table includes basic summary flags such as **`has_scripts`** (indicating whether bundled script files exist in the skill directory) and **`has_references`**.
   * The **`artifact_siblings`** table records bundled files and scripts stored alongside a skill (e.g., `.sh`, `.py` scripts) up to a 100 KB text size limit.

2. **Unextracted Security Specifications**:
   * The Agent Skills specification defines optional frontmatter fields like `compatibility` (e.g., system package requirements) and `allowed-tools` (pre-approved tool permissions). However, **GitSkills does not extract these into dedicated database columns**. 
   * The full Markdown instructions are stored as unparsed raw text in the `content` column of the `artifacts` table.

---

### Why You Must Build This Scanner Yourself

The absence of a pre-built list is intentional. Identifying these actions is the core requirement of **Research Question 4 ("Skill security and supply-chain risk")** in your group project assignment. 

Your team is required to build a **static analyzer or rule-based scanner** that parses the raw `content` of `SKILL.md` files to extract:
* **Executable commands** (e.g., CLI triggers like `bash`, `curl`, `chmod`, `eval`, or system calls).
* **Network & URL access** (e.g., HTTP/HTTPS links, API endpoints, webhooks).
* **File-system operations** (e.g., read/write paths, directory traversals, deletions).
* **Credential-related instructions** (e.g., references to environment variables like `API_KEY`, `TOKEN`, `password`, or authorization headers).

---

🛡️ **Would you like help drafting a set of regular expression rules or static analysis patterns to parse `artifacts.content` for these security categories?**

## Question 5
Is there another efficient way to parse for the security-relevant actions without using regex?

## Answer 5
**Yes**, there are several structured, efficient alternatives to using plain regular expressions for parsing security-relevant actions. Relying solely on regex can be fragile when parsing natural language or code blocks due to false positives in standard text. 

Using an **AST-based (Abstract Syntax Tree)** approach or leveraging existing database metadata provides much cleaner results:

---

### 1. Markdown AST (Abstract Syntax Tree) Parsing
Instead of scanning raw text line by line, you can parse `SKILL.md` into an AST using standard Markdown parsers (such as `mistune`, `mistletoe`, or `markdown-it-py`).

* **Targeted Node Extraction**: The parser categorizes content into node types (e.g., `CodeBlock`, `InlineCode`, `Link`, `Heading`, `Paragraph`).
* **Isolate Code Blocks**: You can filter specifically for `CodeBlock` nodes with language tags like `bash`, `sh`, or `zsh`. This completely eliminates false positives caused by command names mentioned in general documentation text.
* **URL Extraction**: Extract `Link` node destinations directly to identify all HTTP/HTTPS endpoints without needing complex regex URL matchers.

---

### 2. Shell Command AST Parsing (e.g., `bashlex`)
Once you extract code blocks using Markdown AST, you can pass shell commands through a shell AST parser like Python's **`bashlex`**.

* **Command Recognition**: `bashlex` tokenizes commands and identifies the actual binary/utility being invoked, isolating executable commands (e.g., `curl`, `chmod`, `eval`, `rm`).
* **Environment Variable Detection**: Identifies environment variable accesses (e.g., `$API_KEY`, `$TOKEN`) as AST variable nodes to capture credential-related instructions.
* **File Operations**: AST nodes flag redirection operators (`>`, `>>`, `<`), piping, and file paths accurately.

---

### 3. Leveraging Dataset Metadata for Bundled Scripts
For identifying bundled scripts or executable files, you don't need to parse raw `SKILL.md` text at all:

* **Query `artifact_siblings`**: Query the `artifact_siblings` table directly for entries where `entry_type = 'file'` and check for script extensions (`.sh`, `.py`, `.ps1`, `.bat`) or paths residing in the `scripts/` directory.
* **Use `artifacts.has_scripts`**: Filter representative records on the `has_scripts = 1` flag in the `artifacts` table.

---

### 4. Semantic Rule Engines (e.g., Semgrep)
If you want a pre-built static analysis engine, **Semgrep** can run against code blocks extracted from skill files. Semgrep uses Tree-sitter ASTs to match abstract semantic patterns (e.g., `curl -X POST ...`, reading `~/.ssh/id_rsa`, or exporting environment tokens) rather than raw text patterns.

---

### Recommended Pipeline Architecture
Combining these methods gives you a robust static analyzer satisfying the requirements for Research Question 4:

1. **Database Query**: Identify bundled script files using `artifact_siblings`.
2. **Markdown AST**: Extract all `CodeBlock` and `Link` nodes from `artifacts.content`.
3. **Shell AST**: Parse code blocks with `bashlex` to categorize commands, credentials, and file operations.

---

💡 **Would you like a sample Python snippet demonstrating how to parse a `SKILL.md` text string into a Markdown AST and extract code blocks?**
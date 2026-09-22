# [Project-8] CSC 580 Group Assignment 2_ Requirements Engineering - Gemini Notebook

Exported on: 9/21/2026, 6:36:04 PM

---

### User

A lot of the content in the dataset is not in English. What's the best way to handle analyzing non-English content?

---

### Model

The sources recognize non-English artifacts as an important aspect of AI-native software engineering and outline how natural language content is stored and evaluated within the datasets:

1\. How Non-English Content is Handled in the Data

-   **UTF-8 Encoding**: All string columns across the dataset tables are stored as **UTF-8**, ensuring that multi-byte characters and non-English scripts are preserved without encoding corruption \[Source: 1: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Multilingual Agent Design**: The MSR Mining Challenge explicitly notes that because AI coding agents operate on **multilingual models**, developers often write skills or specifications in their native language to describe workflows more precisely than they might in English \[Source: 2: MSR 2027 - Mining Challenge - MSR 2027\] . Investigating which natural languages appear across skills is one of the proposed research directions \[Source: 2: MSR 2027 - Mining Challenge - MSR 2027\] .

* * *

2\. Best Strategies for Analyzing Non-English Content

When building your project pipeline, you can structure your analysis using the following approach:

-   **Language Identification**:
    -   Add a language-detection step (e.g., using fastText or `langdetect`) to your feature extraction pipeline to tag each artifact with its primary natural language \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 4: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   This allows you to compare structural and adoption metrics across language cohorts \[Source: 2: MSR 2027 - Mining Challenge - MSR 2027\] \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Language-Agnostic / Structural Feature Extraction**:
    -   Extract features that depend on document structure rather than English vocabulary, such as YAML front matter fields (`name`, `description`), heading depth, character counts (`body_chars`), task lists, code block counts, and file reference links \[Source: 1: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Multilingual Embeddings or Translation**:
    -   **Multilingual LLM/Embeddings**: Since modern LLMs process multilingual text natively, you can pass non-English text directly into multilingual embedding models or LLMs for semantic classification and clustering \[Source: 2: MSR 2027 - Mining Challenge - MSR 2027\] .-   **Machine Translation**: If using English-specific NLP metrics (such as readability scores or English keyword lexicons), translate non-English contents into English as an intermediate pipeline step \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 4: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Validation and Validity Threats**:
    -   Manually inspect a sample of non-English and translated artifacts to assess translation quality or classification accuracy \[Source: 4: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   Document language-detection inaccuracies, translation semantic shift, or dataset bias in your project's `THREATS_TO_VALIDITY.md` \[Source: 8: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

What the Sources Do Not Specify

The challenge documentation does **not prescribe a mandatory translation library or specific language-detection tool**, leaving the choice of NLP framework to your team's pipeline implementation \[Source: 4: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

💡 **Would you like help outlining a Python feature-extraction script to detect natural languages or parse structural metadata from a sample of the dataset?**

---

### User

I have only begun scratching the surface about what is available in the dataset. I don't know what I don't know. Are there any glaring datapoints that are omitted from the dataset that would have helped a research project? This will help to define limitations with the data.

---

### Model

Understanding what is **missing or omitted** from the datasets is critical for defining the scope, threats to validity, and research limitations of your project \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 2: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] . The dataset documentations explicitly identify several key omissions and sampling boundaries across **GitSkills**, **SpecMine**, and the underlying **GitHub mining process**:

* * *

1\. Omissions in GitSkills

-   **Truncated History on Renames**: Commit history follows a file's **current path** \[Source: 3: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . If a skill file was moved or renamed, `first_commit_at` records the rename date rather than its original creation date, and `commit_count` only covers commits at the current path \[Source: 3: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Incomplete Commit History Coverage**: Commit history was collected for standard locations (`.claude/skills/` or `skills/`) plus a size-stratified sample of other paths \[Source: 3: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . Rows where `history_fetched = 0` lack commit metadata \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 6: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Unextracted YAML Frontmatter Fields**: While the Agent Skills specification allows optional frontmatter fields like `license`, `compatibility`, `allowed-tools`, and custom `metadata` \[Source: 7: Specification - Agent Skills\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] , GitSkills **only extracts** **name** **and** **description** as dedicated table columns \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 9: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Folder & Sibling File Caps**: Sibling text files are only fetched up to **100 KB per file** \[Source: 10: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 11: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] , binary files are skipped \[Source: 11: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] , and large skill folders exceeding listing limits are flagged as truncated (`composition_truncated = 1`) \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . Sibling folders describe only the primary representative (`dedup_primary = 1`), not duplicate occurrences \[Source: 13: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **No True Reuse Provenance**: Because skills spread by direct folder copying without a central package manager \[Source: 16: MSR 2027 - Mining Challenge - MSR 2027\] \[Source: 17: \[2608.10906\] GitSkills: A Dataset of Agent Skills on GitHub\] , the primary representative (`dedup_primary = 1`) is selected via a path-preference rule and **is not assumed to be the original source or author** \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 14: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

2\. Omissions in SpecMine

-   **PR Layer Restricted to High-Star Repositories**: The pull-request sweep targeted repositories with $≥10$ **stars** across 10–11 tool families (5,992 PRs across 581 repos) \[Source: 18: GitHub - shyamagarwal13/specmine-official · GitHub\] . PR co-change history is omitted for the remaining ~72,000 broad-census repositories \[Source: 18: GitHub - shyamagarwal13/specmine-official · GitHub\] \[Source: 19: MSR 2027 - Mining Challenge - MSR 2027\] .-   **Missing Spec Text in Parquet Mirrors**: The full raw Markdown text of specifications is included in `specs.jsonl.gz` on Zenodo, but is **omitted from the Hugging Face Parquet tables** \[Source: 21: ShyAgarwal/specmine · Datasets at Hugging Face\] \[Source: 22: \[2608.25202\] SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts\] .-   **GitHub Diff Truncation**: A small fraction (0.08%) of PRs have `n_spec_files = 0` because GitHub caps PR diff listings at 3,000 files per PR \[Source: 23: GitHub - shyamagarwal13/specmine-official · GitHub\] .

* * *

3\. Redacted & Anonymized Data (Both Datasets)

-   **Privacy Redactions**: Personal names, committer/author email addresses (including GitHub noreply emails), GPG signature blobs, avatar URLs, and repository descriptions have been redacted or masked across both datasets \[Source: 12: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Anonymized Author Accounts**: Commit authors in GitSkills are replaced with keyed one-way hash codes (bots retain their logins) \[Source: 12: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .

* * *

4\. Ecosystem & Platform-Level Blind Spots

-   **GitHub Code Search Bounds**: Neither dataset captures private repositories, non-default branches, files over 384 KB, repositories with over 500,000 files, or forks (unless the fork has more stars than its parent) \[Source: 25: mvaccargiu/gitskills · Datasets at Hugging Face\] .-   **No Runtime or LLM Execution Tracing**: The datasets contain static files, commit histories, and pull requests \[Source: 28: GitSkills: A Dataset of Agent Skills on GitHub | Zenodo\] \[Source: 29: SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts | Zenodo\] . They do **not contain runtime prompt logs, agent interaction traces, model outputs, or probabilistic selection records** showing how an AI agent actually processed a spec or skill at runtime \[Source: 16: MSR 2027 - Mining Challenge - MSR 2027\] .

* * *

🔍 **Would you like to draft a section for your project's** **THREATS\_TO\_VALIDITY.md** **file addressing how these dataset limitations impact your specific research question?**

---

### User

My understanding is that GitSkills are an Anthropic/claude initiative. I would believe that the contents of the SKILL.md files are optimized for running with claude, its agents, and with any other Anthropic-based applications. Could the SKILL.md files being ingested by a non-Anthropic product have adverse affects? Or are the skills generic enough to be used by basically an LLM and its associated agents, etc.?

---

### Model

Anthropic introduced the **Agent Skills format in October 2025 as an open specification** \[Source: 1: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . While Anthropic maintains its own repository of skills for Claude \[Source: 5: GitHub - anthropics/skills: Public repository for Agent Skills · GitHub\] , the core specification is open and managed independently at `agentskills.io` \[Source: 5: GitHub - anthropics/skills: Public repository for Agent Skills · GitHub\] \[Source: 6: Specification - Agent Skills\] .

* * *

1\. Are Skills Generic Enough for Other LLMs?

**Yes.** At its core, an agent skill is simply a directory containing a `SKILL.md` file formatted with standard YAML frontmatter (`name`, `description`) followed by plain Markdown instructions \[Source: 7: GitHub - anthropics/skills: Public repository for Agent Skills · GitHub\] .

-   **Natural Language Instructions**: Because skill contents consist primarily of natural language guidelines, step-by-step procedures, and Markdown examples \[Source: 4: \[2608.10906\] GitSkills: A Dataset of Agent Skills on GitHub\] \[Source: 10: Specification - Agent Skills\] , any modern instruction-following LLM or agent framework can parse and act on them \[Source: 3: MSR 2027 - Mining Challenge - MSR 2027\] \[Source: 11: MSR 2027 - Mining Challenge - MSR 2027\] .-   **Progressive Disclosure**: The specification uses a progressive disclosure architecture—agents inspect lightweight metadata (~100 tokens) to decide whether to activate a skill, load the main `SKILL.md` instructions when active, and fetch supporting reference files only as needed \[Source: 12: Specification - Agent Skills\] \[Source: 13: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . This design is vendor-agnostic and applies to virtually any LLM agent context \[Source: 14: mvaccargiu/gitskills · Datasets at Hugging Face\] .-   **Ecosystem Adoption**: In the GitSkills dataset, **55.4%** of collected skills reside under generic `skills/` directories, while **9.8%** sit in the canonical `.claude/skills/` directory and **34.8%** reside in other paths \[Source: 15: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 16: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

2\. Potential Adverse Effects or Limitations with Non-Anthropic Products

Ingesting `SKILL.md` files into a non-Anthropic product or different LLM architecture does present several operational, behavioral, and security risks:

-   **Tool and System Dependencies**: Skills frequently bundle executable code in a `scripts/` directory \[Source: 8: Specification - Agent Skills\] \[Source: 17: Specification - Agent Skills\] or specify system dependencies using the optional `compatibility` or `allowed-tools` YAML frontmatter fields \[Source: 9: Specification - Agent Skills\] . If a non-Anthropic agent lacks the required CLI tools, Python environment, or tool-calling schema, running the skill will fail or produce execution errors \[Source: 18: Specification - Agent Skills\] \[Source: 19: Specification - Agent Skills\] .-   **Security and Command Execution Risks**: Skills can instruct agents to execute shell commands, manipulate files, or access network endpoints \[Source: 14: mvaccargiu/gitskills · Datasets at Hugging Face\] . Ingesting untrusted skills into an agent product without strict sandboxing, containerization, or permission prompts creates significant security and supply-chain vulnerabilities \[Source: 21: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 22: MSR 2027 - Mining Challenge - MSR 2027\] .-   **Instruction Drift & Prompt Sensitivity**: Skills are interpreted probabilistically at runtime without type checkers or compilers verifying execution accuracy \[Source: 3: MSR 2027 - Mining Challenge - MSR 2027\] . Instructions crafted and prompt-engineered specifically for Claude's reasoning style or context window may produce unexpected outputs, hallucinated tool calls, or missed steps when evaluated by different LLMs \[Source: 3: MSR 2027 - Mining Challenge - MSR 2027\] \[Source: 11: MSR 2027 - Mining Challenge - MSR 2027\] .-   **Path Discovery Assumptions**: Non-Anthropic agents scanning a codebase might look exclusively in vendor-neutral directories (`skills/`) and miss skills placed strictly in Anthropic's vendor-specific path (`.claude/skills/`) \[Source: 15: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .

* * *

3\. Empirical Context in the Dataset

Whether skill files are converging toward a universal standard or remaining tool-specific is explicitly highlighted as a core research topic in the MSR 2027 Mining Challenge \[Source: 11: MSR 2027 - Mining Challenge - MSR 2027\] . Specifically, **Research Question 5** invites researchers to analyze whether skills are adopting vendor-neutral structures or maintaining distinct tool-specific conventions across different ecosystems \[Source: 23: MSR 2027 - Mining Challenge - MSR 2027\] \[Source: 24: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

💡 **Would you like to write a SQL query or Python script to analyze the proportion of vendor-neutral (****skills/****) vs. Claude-specific (****.claude/skills/****) paths in the GitSkills dataset?**

---

### User

My team chose a research question that looks for security-relevant actions that a SKILL.md file could prompt the LLM to attempt. The list includes: executable commands, URLs, scripts, file operations, and credential-related instructions. Is there already an all encompassing, documented list of these actions found within the dataset?

---

### Model

**No**, there is no pre-existing or documented all-encompassing list of security-relevant actions built into the dataset.

* * *

What the Dataset Provides vs. What is Missing

-   **High-Level Structural Summary Flags**:
    -   The `artifacts` table includes basic summary flags such as **has\_scripts** (indicating whether bundled script files exist in the skill directory) and **has\_references** \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   The **artifact\_siblings** table records bundled files and scripts stored alongside a skill (e.g., `.sh`, `.py` scripts) up to a 100 KB text size limit \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Unextracted Security Specifications**:
    -   The Agent Skills specification defines optional frontmatter fields like `compatibility` (e.g., system package requirements) and `allowed-tools` (pre-approved tool permissions) \[Source: 5: Specification - Agent Skills\] . However, **GitSkills does not extract these into dedicated database columns** \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   The full Markdown instructions are stored as unparsed raw text in the `content` column of the `artifacts` table \[Source: 9: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 10: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

Why You Must Build This Scanner Yourself

The absence of a pre-built list is intentional. Identifying these actions is the core requirement of **Research Question 4 ("Skill security and supply-chain risk")** in your group project assignment \[Source: 11: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

Your team is required to build a **static analyzer or rule-based scanner** that parses the raw `content` of `SKILL.md` files to extract \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] :

-   **Executable commands** (e.g., CLI triggers like `bash`, `curl`, `chmod`, `eval`, or system calls) \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Network & URL access** (e.g., HTTP/HTTPS links, API endpoints, webhooks) \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **File-system operations** (e.g., read/write paths, directory traversals, deletions) \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Credential-related instructions** (e.g., references to environment variables like `API_KEY`, `TOKEN`, `password`, or authorization headers) \[Source: 12: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

🛡️ **Would you like help drafting a set of regular expression rules or static analysis patterns to parse** **artifacts.content** **for these security categories?**

---

### User

Is there another efficient way to parse for the security-relevant actions without using regex?

---

### Model

**Yes**, there are several structured, efficient alternatives to using plain regular expressions for parsing security-relevant actions. Relying solely on regex can be fragile when parsing natural language or code blocks due to false positives in standard text.

Using an **AST-based (Abstract Syntax Tree)** approach or leveraging existing database metadata provides much cleaner results:

* * *

1\. Markdown AST (Abstract Syntax Tree) Parsing

Instead of scanning raw text line by line, you can parse `SKILL.md` into an AST using standard Markdown parsers (such as `mistune`, `mistletoe`, or `markdown-it-py`).

-   **Targeted Node Extraction**: The parser categorizes content into node types (e.g., `CodeBlock`, `InlineCode`, `Link`, `Heading`, `Paragraph`).-   **Isolate Code Blocks**: You can filter specifically for `CodeBlock` nodes with language tags like `bash`, `sh`, or `zsh`. This completely eliminates false positives caused by command names mentioned in general documentation text.-   **URL Extraction**: Extract `Link` node destinations directly to identify all HTTP/HTTPS endpoints without needing complex regex URL matchers.

* * *

2\. Shell Command AST Parsing (e.g., `bashlex`)

Once you extract code blocks using Markdown AST, you can pass shell commands through a shell AST parser like Python's **bashlex**.

-   **Command Recognition**: `bashlex` tokenizes commands and identifies the actual binary/utility being invoked, isolating executable commands (e.g., `curl`, `chmod`, `eval`, `rm`).-   **Environment Variable Detection**: Identifies environment variable accesses (e.g., `$API_KEY`, `$TOKEN`) as AST variable nodes to capture credential-related instructions.-   **File Operations**: AST nodes flag redirection operators (`>`, `>>`, `<`), piping, and file paths accurately.

* * *

3\. Leveraging Dataset Metadata for Bundled Scripts

For identifying bundled scripts or executable files, you don't need to parse raw `SKILL.md` text at all:

-   **Query** **artifact\_siblings**: Query the `artifact_siblings` table directly for entries where `entry_type = 'file'` and check for script extensions (`.sh`, `.py`, `.ps1`, `.bat`) or paths residing in the `scripts/` directory \[Source: 1: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Use** **artifacts.has\_scripts**: Filter representative records on the `has_scripts = 1` flag in the `artifacts` table \[Source: 4: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

4\. Semantic Rule Engines (e.g., Semgrep)

If you want a pre-built static analysis engine, **Semgrep** can run against code blocks extracted from skill files. Semgrep uses Tree-sitter ASTs to match abstract semantic patterns (e.g., `curl -X POST ...`, reading `~/.ssh/id_rsa`, or exporting environment tokens) rather than raw text patterns.

* * *

Recommended Pipeline Architecture

Combining these methods gives you a robust static analyzer satisfying the requirements for Research Question 4 \[Source: 6: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] :

-   **Database Query**: Identify bundled script files using `artifact_siblings` \[Source: 1: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Markdown AST**: Extract all `CodeBlock` and `Link` nodes from `artifacts.content` \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Shell AST**: Parse code blocks with `bashlex` to categorize commands, credentials, and file operations.

* * *

💡 **Would you like a sample Python snippet demonstrating how to parse a** **SKILL.md** **text string into a Markdown AST and extract code blocks?**
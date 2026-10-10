# RDR-009: Sibling Artifact Security Scanning Scope

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-10-10 |
| **Type** | Research methodology, data, and scope |
| **Related work** | Question 4, Sprint 2, security scanner, RDR-002, RDR-003, RDR-008 |
| **Evidence** | GitSkills `artifact_siblings` exploratory DuckDB analysis |
| **Supersedes** | None |

## Context

Question 4 asks whether modified or reused skills introduce security-sensitive behavior that was absent from an earlier version or source artifact. Such behavior may occur in bundled sibling files, not only in `SKILL.md`.

RDR-003 established that identical `SKILL.md` contents can have different bundled resources and that sibling fingerprints can identify content changes. RDR-008 defines how scanner evidence is compared across related artifacts. The project also needs to determine which sibling files should be scanned when bundled resources differ.

Restricting scanning to common script extensions would simplify the analysis, but could exclude agent instructions, configuration, and other text containing commands, network references, file operations, or credential-related behavior. At the same time, many sibling entries have no stored content available for static analysis.

## Decision Drivers

- Detect newly introduced security-sensitive behavior in bundled sibling artifacts.
- Include relevant evidence regardless of file extension or whether behavior is expressed as code, configuration, or instructions.
- Limit content analysis to changed siblings with available, nonempty content.
- Distinguish unavailable content from evidence that security-sensitive behavior is absent.
- Preserve consistency with the sibling fingerprinting and evidence-comparison decisions established in RDR-003 and RDR-008.

## Decision

> **Scan added or changed sibling files with available, nonempty content, regardless of file extension. Do not content-scan unchanged files or files without available content. For executable or packaged files without stored content, report additions, removals, and hash changes from available metadata, but do not draw conclusions about their behavior.**

The decision applies to sibling files associated with validated base/derived artifact comparisons. When both versions have available content, differences can be assessed using the project's existing scanner and evidence-comparison approach. When only one version has available content, the available text may be scanned, but the comparison remains incomplete. Added siblings with available, nonempty content are included in the scan.

Existing sibling fingerprints are used to identify unchanged content. File extensions do not determine whether content is scanned or whether a file is risky. The current scanner rules provide the initial coverage; file-type-specific rules may be considered if validation identifies important gaps.

Files with unavailable content cannot support behavioral findings. Additions, removals, or hash changes involving executables, libraries, or packages may still be reported as changes to uninspected resources. Missing content must not be treated as evidence that a capability is absent.

## Evidence

### Sibling file distribution

The following DuckDB query was used to examine file extensions and stored-content availability in `artifact_siblings`:

```sql
WITH sibling_files AS (
    SELECT
        entry_name,
        lower(
            regexp_extract(
                entry_name,
                '\.([^./]+)$',
                1
            )
        ) AS extension,
        content
    FROM artifact_siblings
    WHERE entry_type = 'file'
)
SELECT
    CASE
        WHEN extension = '' THEN '[no extension]'
        ELSE '.' || extension
    END AS extension,
    COUNT(*) AS file_count,
    COUNT_IF(content IS NOT NULL) AS with_content,
    COUNT_IF(content IS NULL) AS without_content
FROM sibling_files
GROUP BY extension
ORDER BY file_count DESC;
```

The dataset-wide totals were verified separately:

| Measure | Count |
| --- | ---: |
| Total sibling files | 5,858,945 |
| Distinct file extensions | 4,426 |
| Files without a detected extension | 73,765 |
| Files with stored content | 3,497,752 |
| Files without stored content (`NULL`) | 2,361,193 |
| Files with nonempty stored content | 3,486,865 |
| Files with empty stored content | 10,887 |

Approximately 59.5% of sibling files have nonempty stored content. These files form the potential content-scanning population, not the number of changed files in validated comparisons. Approximately 40.3% lack stored content; the remainder have empty stored content.

The following groups illustrate the range of relevant file types. They include selected, nonoverlapping extensions rather than every file in the dataset, and the counts describe content availability, **not observed security threats**.

| Category | Extensions included | Total files | With content | Without content |
| --- | --- | ---: | ---: | ---: |
| Executable scripts and source | `.py`, `.sh`, `.js`, `.ts`, `.mjs`, `.ps1`, `.bash` | 1,208,516 | 782,237 | 426,279 |
| Instructions and configuration | `.md`, `.json`, `.yaml`, `.yml`, `.toml`, `.txt`, `.xml`, `.env` | 3,459,364 | 2,519,351 | 940,013 |
| No detected extension | `[no extension]` | 73,765 | 43,083 | 30,682 |

The data also includes content-bearing source files outside these groups, such as `.go`, `.rs`, `.tsx`, `.jsx`, and `.rb`. Files without a detected extension may include executable scripts or build instructions. These observations argue against a fixed extension allowlist.

The significance of a file also depends on how it is used. Scripts and source code may contain executable operations. JSON, YAML, XML, and other configuration files may define commands or tool behavior. Markdown and related text may instruct an agent to perform security-sensitive actions. Unlike descriptive `SKILL.md` frontmatter excluded under RDR-002, sibling configuration files may define executable behavior and remain eligible for scanning. None of these formats is inherently malicious.

For example, a JSON configuration may define a command for a tool to execute:

```json
{
  "command": "bash",
  "args": ["scripts/setup.sh"]
}
```

A Markdown reference file may instead instruct an agent to run a command:

````markdown
Before processing the request, run:

```bash
python scripts/initialize.py
```
````

Both are illustrative examples, not observed findings from the dataset.

The results also contain files with no captured content, including `.exe` (254), `.dll` (1,597), `.so` (332), `.dylib` (183), `.jar` (267), `.wasm` (180), and `.whl` (154). These files are excluded from content scanning. Additions, removals, and hash changes are instead recorded from available metadata as supply-chain change indicators. Their behavior cannot be determined from the dataset.

File extensions were derived from filenames and do not necessarily represent normalized file types.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Scan only shell and Python siblings | Not selected | Excludes other executable source, configuration, and agent-facing instructions with observable security-sensitive content. |
| Scan a fixed list of security-relevant extensions | Not selected | May omit extensionless or less common files containing relevant evidence. |
| Scan all siblings, including unchanged content | Not selected | Unchanged content adds no new evidence of introduced behavior and creates unnecessary work. |
| Classify files as risky based on extension | Not selected | File type alone does not establish a security-sensitive capability. |
| Treat unavailable content as empty or safe | Not selected | Missing content does not establish an absence of risk. |
| Retrieve or execute files whose content is unavailable | Not selected | Outside the chosen dataset-based static-analysis scope; executing untrusted scripts is prohibited. |

## Consequences and Limitations

- The scan covers relevant changed text without requiring a language-specific file allowlist.
- Scanner matches are indicators of security-sensitive behavior, not evidence of execution, malicious intent, or actual harm.
- General-purpose rules may produce false positives in examples, documentation, and configuration, or miss behavior expressed in unsupported syntax. Manual validation may justify additional rules.
- Fingerprint differences establish changes in content, not necessarily changes in security-sensitive behavior. File moves or renames alone do not establish new capabilities.
- Files lacking stored content remain outside behavioral analysis. Metadata changes involving such files can be reported, but their security impact remains unknown.
- The reported distribution describes all sibling-file entries, not the smaller set of changed siblings in validated comparisons. Counts may include repeated files across artifacts.

## Follow-up Actions

- Apply sibling content scanning within the validated comparison and fingerprinting process established by the existing RDRs.
- Validate findings across executable source, agent instructions, and configuration files; assess false positives and detection gaps.
- Report relevant uninspected resource changes separately from content-based security findings.

## Revisit Criteria

Revisit this decision if validation shows that scanning all changed text produces unacceptable false positives or cost, or that missing-content files or file-type-specific behavior materially limit the project's ability to answer Question 4.

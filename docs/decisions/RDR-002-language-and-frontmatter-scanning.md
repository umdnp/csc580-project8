# RDR-002: Language and Frontmatter Handling for Security Scanning

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-20 |
| **Type** | Research methodology and implementation |
| **Related work** | Question 4, security scanner, Sprint 1 |
| **Evidence** | DuckDB exploratory analysis of GitSkills artifacts |
| **Supersedes** | None |

## Context

The security scanner for Question 4 will compare related `SKILL.md` artifacts and look for newly introduced security-sensitive behavior, including command execution, file-system access, network access, scripts, and credential-related instructions.

During exploratory analysis, two questions came up that could affect how the scanner works:

1. Should skills containing non-English text be excluded because some rules may rely on English terms?
2. Should YAML frontmatter, especially the optional `allowed-tools` field, be included when applying security rules?

Both decisions affect the accuracy of the scanner and the population used in the analysis.

## Decision Drivers

- Keep as much of the valid GitSkills analysis population as possible.
- Avoid excluding artifacts when the security-sensitive technical content can still be detected.
- Detect security-sensitive instructions and technical constructs rather than metadata that only describes a skill.
- Avoid false positives caused by command names, URLs, tool names, or other technical terms appearing only in frontmatter.
- Keep the scanner focused on behavior relevant to Question 4.

## Evidence

Exploratory DuckDB queries found candidate artifacts containing non-Latin scripts such as Han, Hiragana, Katakana, Hangul, Cyrillic, Arabic, Hebrew, and Greek.

Reviewing these records showed that the surrounding text may be written in another language while the technical constructs relevant to the scanner generally remain recognizable. Examples include:

- shell commands such as `curl` and `wget`
- `http://` and `https://` URLs
- file paths
- `Bash`
- tool names such as `Read`, `Write`, `Edit`, `WebFetch`, and `WebSearch`
- MCP tool names
- environment variables and credential-related identifiers

A combined exploratory query found **801 candidate-family artifacts** containing both non-Latin-script content and a populated `allowed-tools` entry. Inspection of these records showed that technical commands and tool identifiers were still represented using the same forms the scanner would normally detect.

The query does not prove that all 801 artifacts are primarily written in a foreign language. Some may contain only limited non-Latin text, mathematical symbols, or other isolated characters. It does show that the presence of non-Latin text does not prevent the artifacts from containing recognizable technical constructs.

The analysis also showed that frontmatter can contain terms that would otherwise match scanner rules. For example:

```yaml
---
description: Uses curl-based APIs to retrieve documentation
allowed-tools: Bash, Read, Write, WebFetch
---
```

The words `curl`, `Bash`, and `WebFetch` describe the skill or its permitted tools. They do not by themselves show that the skill body performs or instructs those operations.

The `allowed-tools` field is also optional. A skill can contain a Bash command, network request, file operation, or other security-sensitive instruction without listing the related tool in frontmatter. Likewise, listing `Bash` in `allowed-tools` does not mean the skill contains a risky Bash command.

## Decision

> **Do not exclude skills because they contain non-English text, and exclude YAML frontmatter from behavioral security-rule processing.**

### Language Handling

Skills will remain in the analysis population even when they contain non-English or non-Latin-script text.

The scanner is primarily looking for technical constructs such as commands, URLs, file operations, scripts, tool identifiers, and credential-related patterns. These are generally represented in recognizable forms even when the surrounding instructions are written in another language.

Language will therefore not be used as an exclusion criterion.

A limitation remains for risky instructions written entirely in non-English prose without recognizable technical indicators. Those cases may not be detected by rules that depend on English keywords or technical syntax. This will be documented as a limitation rather than handled by removing non-English artifacts from the dataset.

### Frontmatter Handling

YAML frontmatter is outside the scope of behavioral rule processing for the current analysis.

Before behavioral rules are applied, the scanner will separate the frontmatter from the `SKILL.md` body. Rules for command execution, file-system access, network access, credential handling, and similar behavior will run against the body only.

For example:

```yaml
allowed-tools: Bash, Read, Write
```

will not generate a command-execution finding.

Likewise, a description such as:

```yaml
description: Uses curl to retrieve documentation
```

will not generate a network or command finding simply because it contains the word `curl`.

This is important because frontmatter describes the skill rather than providing the operational instructions the scanner is intended to evaluate.

Changes to `allowed-tools` or other frontmatter fields will not be analyzed separately for the current research question. If a related artifact adds `Bash` to `allowed-tools` but does not introduce a corresponding security-sensitive instruction in the body, the scanner will not treat that metadata change as newly introduced risky behavior.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Exclude skills containing non-English text | Not selected | This would remove valid artifacts even though the technical constructs used by the scanner are often still detectable. |
| Scan frontmatter and body with the same rules | Not selected | Metadata can contain command names, URLs, tool names, and other terms without representing actual behavioral instructions. |
| Exclude only `allowed-tools` from scanning | Not selected | Other frontmatter fields, especially `description`, can contain the same kinds of terms and create similar false positives. |
| Exclude all frontmatter from behavioral scanning | **Selected** | Provides a clear separation between descriptive metadata and the skill instructions being analyzed. |

## Consequences and Limitations

This approach keeps non-English artifacts in the analysis while reducing false positives caused by frontmatter.

The main limitations are:

- The exploratory language check detects writing systems, not the actual language of an entire artifact.
- Languages that use the Latin alphabet cannot be distinguished from English using the current script-based query.
- Security-sensitive behavior expressed only in unsupported non-English prose may be missed if it contains no recognizable technical indicators.
- Frontmatter may describe tools or capabilities that are security relevant in a broader sense, but those declarations are not evidence that the skill body actually contains the behavior being measured.
- Metadata-only changes will not count as newly introduced security-sensitive behavior.

These limitations should be included in the project methodology and `THREATS_TO_VALIDITY.md`.

## Follow-up Actions

- Separate YAML frontmatter from the `SKILL.md` body before applying behavioral rules.
- Apply command execution, file-system, network, credential, and related rules only to body content.
- Add tests confirming that terms such as `Bash`, `curl`, URLs, and file paths appearing only in frontmatter do not generate findings.
- Add tests confirming that the same constructs appearing in the skill body are still detected.
- Include some non-English artifacts when manually validating scanner results.
- Document the natural-language limitation in `THREATS_TO_VALIDITY.md`.

## Revisit Criteria

Revisit this decision if later validation shows that:

- a meaningful number of security-sensitive behaviors are missed because they are expressed only in non-English natural language;
- excluding frontmatter causes important behavior relevant to Question 4 to be systematically missed; or
- the scope of the research question changes in a way that makes metadata declarations themselves part of the behavior being studied.

If that happens, language-aware analysis or frontmatter analysis can be considered separately rather than being mixed into the current behavioral rule processing.

# RDR-002: Language and Frontmatter Handling for Security Scanning

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-20 |
| **Type** | Research methodology and implementation |
| **Related work** | Question 4, security scanner, Sprint 1 |
| **Evidence** | DuckDB exploratory analysis, manual review of GitSkills artifacts, [Agent Skills specification](https://agentskills.io/specification) |
| **Supersedes** | None |

## Context

The security scanner for Question 4 will compare related `SKILL.md` artifacts and look for newly introduced security-sensitive behavior, including command execution, file-system access, network access, scripts, and credential-related instructions.

During exploratory analysis, two questions came up:

1. Should skills containing non-English text be excluded because some rules may rely on English terms?
2. Should YAML frontmatter, especially the optional `allowed-tools` field, be included when applying security rules?

## Decision Drivers

- Keep as much of the valid GitSkills population as possible.
- Avoid false positives caused by metadata that only describes a skill.
- Focus the scanner on security-sensitive instructions and technical constructs in the skill body.
- Avoid using `allowed-tools` in a way that could hide newly introduced security-sensitive behavior.

## Evidence

We manually reviewed a broad sample of skills containing non-English text. In the skills we reviewed, technical terms such as shell commands, URLs, tool names, file paths, and environment variables were still written in their usual English or programming-language forms.

We also identified **801 artifacts** that contained both non-English text in the frontmatter and a populated `allowed-tools` field. We reviewed these specifically to see whether tool names were translated. The tool names we inspected were still written as `Bash`, `Read`, `Write`, `WebFetch`, and other standard tool names.

We also found that non-ASCII characters are not always evidence of another language. Some skills contain mathematical, scientific, or technical notation such as `Σ`, `Δ`, `θ`, `μ`, `³`, `≤`, `×`, and `→`. Because of this, simply excluding artifacts with non-ASCII characters would also remove valid English-language skills.

One limitation is that the scanner may miss security-sensitive instructions that are written entirely in non-English prose. For example, if a skill says in another language, “copy the user’s credentials and send them to a remote server,” but does not include a recognizable command, URL, file path, tool name, or credential keyword, an English-based rule may not detect it.

Frontmatter can also contain text that would otherwise match scanner rules. For example:

```yaml
---
description: Uses curl-based APIs to retrieve documentation
allowed-tools: Bash, Read, Write, WebFetch
---
```

The presence of `curl`, `Bash`, or `WebFetch` in frontmatter does not mean the skill body actually contains those behaviors.

The Agent Skills specification defines `allowed-tools` as a list of tools that may be pre-approved by supporting clients. The field is currently **experimental**, and support may vary between agent implementations. This means `allowed-tools` can affect how a client treats a skill, but it is a permission or configuration declaration rather than evidence of security-sensitive instructions in the skill body.

## Decision

> **Do not exclude skills because they contain non-English text, and exclude YAML frontmatter from behavioral scanning.**

### Language Handling

Skills will remain in the analysis population even when they contain non-English text.

The scanner will continue to look for technical indicators such as commands, URLs, file operations, scripts, tool identifiers, and credential-related patterns. These indicators were still recognizable in the non-English skills we reviewed.

Security-sensitive instructions written only in unsupported non-English prose may still be missed. This will be documented as a limitation rather than handled by excluding non-English artifacts.

### Frontmatter Handling

Behavioral rules will run against the `SKILL.md` body only. YAML frontmatter will be excluded before rule processing.

This prevents metadata such as the following from generating findings on its own:

```yaml
allowed-tools: Bash, Read, Write
```

```yaml
description: Uses curl to retrieve documentation
```

`allowed-tools` will also **not** be used to suppress findings in the skill body. A tool being allowed does not mean every use of that tool is safe. For example, a skill might already use Bash for a harmless command, while a later copy adds a security-sensitive Bash command. Ignoring Bash findings because it appears in `allowed-tools` could cause us to miss the type of change Question 4 is intended to detect.

For the current research question, frontmatter changes will not be analyzed separately. The scanner is focused on security-sensitive behavior introduced in the `SKILL.md` body or bundled textual resources associated with the skill.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Exclude skills containing non-English text | Not selected | Technical indicators were still recognizable, and non-ASCII text is not a reliable language test. |
| Scan frontmatter and body with the same rules | Not selected | Metadata can contain commands, URLs, tool names, or paths without representing behavioral instructions. |
| Exclude only `allowed-tools` from scanning | Not selected | Other frontmatter fields, especially `description`, can create the same false positives. |
| Use `allowed-tools` to suppress matching body findings | Not selected | A permitted tool can still be used in a newly introduced security-sensitive way. |
| Exclude all frontmatter from behavioral scanning | **Selected** | Keeps metadata separate from the skill instructions being analyzed. |

## Consequences and Limitations

- Non-ASCII or non-Latin characters do not reliably identify the language of a skill.
- Security-sensitive instructions written only in unsupported non-English prose may be missed when they contain no recognizable technical indicator.
- Frontmatter is intentionally excluded from behavioral findings even though fields such as `allowed-tools` may affect supporting clients.
- The current analysis does not study permission expansion in frontmatter as a separate security dimension.

These limitations should also be documented in the project methodology and `THREATS_TO_VALIDITY.md`.

## Follow-up Actions

- Mask YAML frontmatter before behavioral rules run while preserving source line numbers.
- Confirm that rule-triggering text appearing only in frontmatter does not generate findings.
- Confirm that the same text appearing in the body is still detected.
- Include non-English artifacts in manual scanner validation and document the natural-language limitation in `THREATS_TO_VALIDITY.md`.

## Revisit Criteria

Revisit this decision if validation shows that non-English prose causes a meaningful number of missed security-sensitive behaviors, or if the project scope expands to study permission or configuration changes in frontmatter as a separate security dimension.

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

Question 4 requires the project to compare related `SKILL.md` artifacts and identify security-sensitive behavior that appears in one artifact but not another.

Two issues came up during exploratory analysis:

1. whether skills containing non-English text should remain in the analysis; and
2. whether YAML frontmatter should be treated as part of the behavior being scanned.

Both decisions affect the validity of the results. Excluding non-English artifacts could remove useful examples, while scanning frontmatter could confuse descriptive metadata with instructions that the skill actually tells an agent to perform.

## Decision Drivers

- Preserve as much of the valid GitSkills population as practical.
- Keep behavioral findings focused on actionable instructions.
- Avoid false positives caused by descriptive or configuration metadata.
- Do not assume non-English skills are unusable simply because some scanner rules rely on English terms.
- Keep the treatment of `allowed-tools` consistent with its role as metadata rather than evidence of behavior.

## Evidence

Manual review showed that technical indicators often remain recognizable even when the surrounding prose is not English. Commands, URLs, file paths, environment variables, and tool names generally retain their normal technical form.

An exploratory query identified 801 artifacts containing non-English frontmatter text and a populated `allowed-tools` field. In the reviewed examples, tool names such as `Bash`, `Read`, `Write`, and `WebFetch` remained recognizable.

We also found that non-ASCII text is not a reliable language test. English-language skills may contain mathematical, scientific, or technical symbols such as `Σ`, `Δ`, `μ`, `≤`, and `→`.

Frontmatter creates a different problem. It can contain terms that look security-sensitive without representing an instruction. For example:

```yaml
description: Uses curl-based APIs to retrieve documentation
allowed-tools: Bash, Read, Write, WebFetch
```

The presence of `curl`, `Bash`, or `WebFetch` in this metadata does not mean the skill body actually instructs an agent to use them.

## Decision

> **Keep non-English skills in the analysis, and exclude YAML frontmatter from behavioral security scanning.**

Non-English artifacts remain eligible for analysis. The scanner will continue to rely on recognizable technical indicators such as commands, URLs, file operations, scripts, tool identifiers, and credential-related patterns.

Behavioral scanning will focus on the `SKILL.md` body. Frontmatter fields such as `description` and `allowed-tools` may help describe or configure a skill, but they are not treated as evidence that the behavior is actually performed.

`allowed-tools` also will not suppress findings in the body. A tool being permitted does not mean every use of that tool is safe. For example, a skill may legitimately allow Bash while still introducing a new Bash command that deserves to be reported.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Exclude skills containing non-English text | Not selected | It would remove potentially useful artifacts, and non-ASCII text is not a reliable language indicator. |
| Scan frontmatter and body together | Not selected | Metadata can contain scanner terms without representing actual behavior. |
| Exclude only `allowed-tools` | Not selected | Other frontmatter fields can create the same problem. |
| Use `allowed-tools` to suppress findings | Not selected | An allowed tool can still be used in a security-sensitive way. |
| Exclude all frontmatter from behavioral scanning | **Selected** | Keeps metadata separate from the instructions being evaluated. |

## Consequences and Limitations

- Security-sensitive instructions written only in unsupported non-English prose may be missed if they contain no recognizable technical indicator.
- Frontmatter changes are outside the current behavioral analysis.
- `allowed-tools` may affect how a supporting client handles a skill, but this project does not treat it as proof that the corresponding behavior occurs.
- Keeping non-English artifacts improves coverage but may make scanner validation more important.

## Follow-up Actions

- Validate the scanner against both English and non-English examples.
- Confirm that terms appearing only in frontmatter do not generate behavioral findings.
- Document the natural-language limitation in `THREATS_TO_VALIDITY.md`.

## Revisit Criteria

Revisit this decision if validation shows that non-English prose causes a meaningful number of missed security-sensitive behaviors, or if the project expands to study frontmatter permissions or configuration changes as a separate security dimension.

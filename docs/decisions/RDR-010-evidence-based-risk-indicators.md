# RDR-010: Evidence-Based Risk Indicators

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-10-21 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 2, `THREAT_MODEL.md`, `scan_diff`, `scan_family`, RDR-007, RDR-008 |
| **Evidence** | RDR-008, current scanner rules and comparison output; Sprint 2 validation examples (planned) |
| **Supersedes** | None |

## Context

Question 4 asks whether modified or reused skills introduce security-sensitive behavior that was absent from an earlier version or source artifact. The scanner reports rule matches and capability changes. RDR-008 adds evidence comparison so changes to commands, URLs, paths, and other constructs remain visible even when rule-match counts stay the same.

Not all evidence changes have the same security implications. Changing a documentation link from `microsoft.com/learning/page1` to `page2` is different from changing the source of a script executed through `curl ... | bash`. Even a path-only change can matter when the referenced content is executed.

The project therefore needs a consistent way to identify and measure security-sensitive changes without treating every changed construct as a threat or claiming that detected behavior is malicious.

## Decision Drivers

- Evaluate what changed and how evidence is used, not just which rule matched.
- Preserve ordinary evidence changes without treating all of them as security risk indicators.
- Keep indicators explainable, reproducible, and practical to validate.
- Retain existing rule counts, capability profiles, and evidence comparisons.
- Avoid double-counting overlapping rules and indicators.
- Account for source context, sibling files, missing data, and uncertain comparison direction.
- Support meaningful measurements across related GitSkills artifacts and families.

## Decision

> **Evaluate changed evidence using explicit, observable risk indicators. Report the indicators, their supporting evidence, and how frequently they occur, while recording coverage and direction limitations separately.**

A `RiskAssessor` examines evidence after extraction and comparison. It uses the existing detection rules, complete source constructs, and available context. It does not replace rule detection. Changes to rule coverage are documented and validated separately.

### Risk indicators

The initial assessment uses 11 indicators. Each requires an observable change, not merely the presence of a keyword or rule match.

| ID | Indicator | Trigger |
| --- | --- | --- |
| **RI-001** | Download-and-execute introduced | New downloaded content is passed directly to an interpreter, such as `curl URL \| bash`. |
| **RI-002** | Executed code source changed | The source URL of remotely executed content changes, including its path within the same domain. |
| **RI-003** | Network access expanded or redirected | A network operation targets a new hostname or domain, or a new explicit outbound data-transfer operation appears. |
| **RI-004** | Network security weakened | HTTPS is downgraded to HTTP, or certificate verification is disabled. |
| **RI-005** | External code or dependency acquisition changed | A package-install or external code-acquisition operation is introduced, or its source or registry changes. Package-name or version changes alone do not automatically trigger it. |
| **RI-006** | Destructive or privileged file operation | Destructive file operations are introduced or expand in scope or privilege. |
| **RI-007** | Credential access or potential exposure | A new operation accesses a recognized credential file or directly includes a recognizable credential reference in an outbound request. |
| **RI-008** | System configuration or permissions changed | An operation introduces or expands changes to permissions, services, scheduled tasks, or system configuration. |
| **RI-009** | Sensitive file-system access or modification | A read or write operation newly targets a recognizable sensitive file or directory. |
| **RI-010** | Local script execution introduced or changed | A local script invocation is introduced or changes to a different script with observably different content. A rename with identical known content does not qualify. |
| **RI-011** | External instruction dependency introduced or changed | A skill newly directs an agent to follow external instructions, changes that source, or turns a reference into an instruction to follow it. |

Indicators are **reasons for review**, not confirmed vulnerabilities. Multiple indicators may describe the same evidence. For example, `cat ~/.aws/credentials` may support both RI-007 and RI-009 without representing two separate incidents.

### Evidence and context

The assessor uses observable command arguments, URLs, paths, and source context. A documentation URL and a URL in a download-and-execute command are treated differently. A URL path change remains visible as evidence but does not by itself trigger RI-003 when the hostname is unchanged.

Some indicators require recognizing the same operation across two artifacts. Evidence is associated across versions only when the correspondence is sufficiently clear. Otherwise, added and removed evidence remain separate, as defined in RDR-008. The assessor does not infer data flow between unrelated statements or variables.

Context helps avoid misleading findings. For example:

```text
Never run: curl https://example.com/install.sh | bash
```

This remains detectable evidence, but an explicit warning should not automatically trigger RI-001. Comments, code blocks, and examples are preserved as context; none establishes intent by itself.

RI-011 also considers changes in how a URL is used, even when the URL stays the same:

```text
Base:     See https://example.com/agent.md for background.
Derived:  Before starting, follow the instructions at https://example.com/agent.md.
```

A limited, rule-based context check distinguishes explicit external instructions from ordinary references and uncertain wording. Negated or ambiguous statements should not automatically trigger RI-011.

Sibling files are scanned only when their contents are already available in GitSkills. The project does not clone repositories, retrieve external content, install packages, or execute scripts.

### Indicator counts and coverage

For each comparison, the assessor preserves:

- **`indicators`** — The supported indicator IDs, reasons, and references to their supporting evidence.
- **`indicator_count`** — The number of distinct indicator categories triggered, not the number of regex matches or occurrences.
- **`finding_count`** — The number of distinct evidence changes supporting those indicators, without counting the same construct again for each indicator.
- **Coverage and uncertainty** — Whether relevant content was available and which observations could not be assessed reliably.

A single changed command may trigger several indicators but still represent one evidence change. **A larger indicator count does not, by itself, establish greater danger.** Counts are descriptive measures used to compare the kinds and frequency of observed changes.

An `indicator_count` of zero means that no defined indicator was supported by the available evidence. It does not establish that the skill is safe. Missing sibling content, partial extraction, and uncertain findings must remain visible rather than being silently treated as negative results.

RDR-007 governs comparison direction. Directed relationships can support claims that a behavior was introduced or removed; undirected relationships can show differences but not which artifact introduced them. The direction-evidence basis remains available for analysis.

### Reporting and validation

`scan_diff` retains `introduced`, `rule_match_count`, `rule_deltas`, and existing capability profiles. It adds indicator counts, supported indicators, uncertain observations, coverage, and a policy version alongside evidence comparison. Exported CLI, JSON, and saved reports redact sensitive values without obscuring changes during internal comparison.

`scan_family` applies the same assessment to directed artifact pairs and available siblings. Research results should report the frequency of each indicator, the distribution of indicator counts, and the proportion of assessed pairs and families with one or more supported indicators. Incomplete and undirected comparisons are reported separately, with findings also grouped by the direction-evidence basis from RDR-007.

Percentages may overlap because one comparison can trigger multiple indicator categories. The denominator and coverage of each reported measure must be explicit.

Validation should include comparisons with and without supported indicators, plus routine maintenance, warnings, ambiguous wording, and missing sibling content. Manual review is needed to identify false positives and missed indicators.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Rely on rule matches alone | Not selected | Matches do not show what changed or how the evidence is used. |
| Treat every evidence change as a risk indicator | Not selected | Routine maintenance and documentation updates would inflate results. |
| Use only positive rule-count deltas | Not selected | Meaningful changes can leave match counts unchanged. |
| Treat zero indicators as proof of safety | Not selected | Static detection has limited coverage and cannot establish that an artifact is safe. |
| Infer execution or data flows between separate statements | Deferred | General program-flow analysis is outside the current scope. |

## Consequences and Limitations

- The project can report the frequency and types of observable security-sensitive changes without assigning an overall risk label.
- One comparison may trigger multiple indicators, so indicator counts must not be interpreted as separate incidents or a measure of danger.
- Legitimate changes may trigger indicators, and some security-sensitive changes may be missed.
- Missing content, uncertain context, and inferred direction limit what can be concluded.
- Scan coverage indicates whether the available artifact content was processed completely. Even `complete` coverage does not mean the scanner can detect every possible security risk.
- Static evidence does not establish execution, malicious intent, or actual supply-chain compromise.

## Follow-up Actions

- Finalize indicator triggers, exclusions, and required evidence through tests and manual review.
- Implement RI-011 and indicator counts without changing existing rule or evidence-comparison metrics.
- Preserve coverage and uncertain observations separately from supported indicator counts.
- Validate overlapping indicators, sensitive paths, local scripts, external instructions, and incomplete comparisons.
- Report indicator prevalence by directed pair, family, coverage, and direction-evidence basis.

## Revisit Criteria

Revisit this decision if validation shows excessive false positives, important missed behavior, unreliable indicator distinctions, or insufficient coverage to support meaningful findings.

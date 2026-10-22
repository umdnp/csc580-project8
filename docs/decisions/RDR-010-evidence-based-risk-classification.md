# RDR-010: Evidence-Based Risk Classification

| Field | Value |
| --- | --- |
| **Status** | Proposed |
| **Date** | 2026-10-21 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 2, `THREAT_MODEL.md`, `scan_diff`, `scan_family`, RDR-007, RDR-008 |
| **Evidence** | RDR-008, current scanner rules and comparison output; Sprint 2 validation examples (planned) |
| **Supersedes** | None |

## Context

Question 4 asks whether modified or reused skills introduce security-sensitive behavior that was absent from an earlier version or source artifact. The scanner already reports rule matches and capability changes. RDR-008 adds evidence comparison so changes to commands, URLs, paths, and other constructs remain visible even when rule-match counts stay the same.

Not all evidence changes raise the same concern. Changing a documentation link from `microsoft.com/learning/page1` to `page2` is different from changing the source of a script executed through `curl ... | bash`. Even a path-only URL change can matter when the referenced content is executed.

The project therefore needs a consistent way to identify changes worth security review without treating every changed construct as risky or claiming that detected behavior is malicious.

## Decision Drivers

- Assess what changed and how evidence is used, not just which rule matched.
- Preserve ordinary evidence changes without treating all of them as risk.
- Keep assessment criteria explainable, reproducible, and practical to validate.
- Retain existing rule counts, capability profiles, and evidence comparisons.
- Avoid double-counting overlapping rules or risk indicators.
- Account for source context, sibling files, missing data, and uncertain comparison direction.
- Support meaningful measurements of potential supply-chain risk across GitSkills families.

## Decision

> **Classify changed evidence using explicit, observable risk indicators. Keep the underlying detections and evidence visible, and report uncertainty separately.**

A `RiskAssessor` evaluates evidence after extraction and comparison. It uses the existing 13 detection rules, complete evidence constructs, and available source context. It does not replace rule detection. Any expansion of rule coverage is documented and validated separately.

### Risk indicators

The initial assessment uses 11 indicators based on observable changes, not the presence of a keyword or rule match alone.

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

Indicators identify **reasons for review**, not confirmed vulnerabilities. Several indicators may apply to one construct. For example, `cat ~/.aws/credentials` may trigger RI-007 and RI-009 without representing two separate incidents.

### Evidence, context, and comparison

The assessor uses observable command arguments, URLs, paths, and source context. A documentation URL and a URL used in an execution pipeline are assessed differently. A path-only URL change remains visible as evidence, but does not by itself trigger RI-003 when the hostname is unchanged.

Some indicators require recognizing the same operation across artifacts. The assessor pairs evidence only when correspondence is sufficiently clear. Otherwise, it preserves separate added and removed records as defined in RDR-008. It does not infer data flow between separate commands or variables.

Context helps reduce false positives. For example:

```text
Never run: curl https://example.com/install.sh | bash
```

This remains detectable evidence, but an explicit warning should not automatically trigger RI-001 as an instruction to execute it. Comments, code blocks, and examples are retained as context; none proves intent by itself.

RI-011 also considers how a URL is used, even when the URL itself is unchanged:

```text
Base:     See https://example.com/agent.md for background.
Derived:  Before starting, follow the instructions at https://example.com/agent.md.
```

A small, rule-based context check distinguishes explicit external instructions from ordinary references and uncertain wording. Negated or ambiguous statements should not automatically trigger the indicator.

Sibling files are scanned only when their contents are already available in GitSkills. The project does not clone repositories, download referenced content, install packages, or execute scripts. Missing sibling content remains unknown.

### Classification and coverage

For comparisons with defensible direction, the assessor reports:

- **`RISK`** — At least one supported indicator identifies introduced or changed security-sensitive behavior.
- **`NO_RISK_DETECTED`** — No indicator triggers and the relevant evidence was sufficiently complete to assess.
- **`UNDETERMINED`** — Missing content or uncertain evidence prevents a defensible classification.

Coverage is recorded separately; a `RISK` result can still have incomplete coverage. An unchanged risky construct remains in the rule results but is not a new risk signal. Removing a risky construct does not itself trigger a positive indicator.

RDR-007 governs direction. Undirected relationships can show differences, but cannot support claims about which artifact introduced a behavior. The direction-evidence basis is retained for later analysis.

`NO_RISK_DETECTED` does **not** mean that a skill is safe, only that none of the defined indicators was detected within the assessable scope.

### Reporting and validation

`scan_diff` retains `introduced`, `rule_match_count`, `rule_deltas`, and existing capability profiles. It adds evidence changes and a separate assessment with the classification, triggered indicators, supporting evidence, coverage, and policy version. Exported JSON, CLI output, and logs redact sensitive values without hiding changes during internal comparison.

`scan_family` applies the assessment to related artifact pairs and available siblings. Results should report indicator frequencies for assessed directed pairs and families, with incomplete and undirected comparisons shown separately. Percentages may overlap because one pair can trigger several indicators. Findings should also be broken down by the direction-evidence basis defined in RDR-007.

Validation must review both flagged and nonflagged examples, including ordinary maintenance, warnings, ambiguous wording, and incomplete sibling data, to assess false positives and missed indicators.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Classify risk from rule matches alone | Not selected | Rule matches do not show what changed or how the evidence is used. |
| Treat every evidence change as risk | Not selected | Routine maintenance and documentation updates would inflate results. |
| Use only positive rule-count deltas | Not selected | Meaningful changes can leave match counts unchanged. |
| Require proof of malicious behavior or compromise | Not selected | Static artifacts cannot establish intent, execution, or real-world impact. |
| Infer execution or data flows between separate statements | Deferred | General program-flow analysis is outside the current scope. |

## Consequences and Limitations

- Findings describe the frequency and types of observable risk signals.
- Legitimate changes may trigger indicators, and some risky behavior may be missed; manual validation is required.
- Context, indirect behavior, missing sibling content, and uncertain direction can limit conclusions.
- A triggered indicator warrants review; it does not prove maliciousness or supply-chain compromise.

## Follow-up Actions

- Finalize indicator triggers, exclusions, and required evidence through tests and manual review.
- Implement `RiskAssessor` without changing existing detection or evidence-comparison metrics.
- Test overlapping indicators, network transfers, sensitive paths, local scripts, external instructions, and incomplete comparisons.
- Validate flagged and nonflagged examples; record errors and the risk-policy version.
- Report indicator prevalence by directed pair, family, coverage, and direction-evidence basis.

## Revisit Criteria

Revisit this decision if validation shows excessive false positives, important missed behavior, unreliable indicator distinctions, or too little complete evidence to support meaningful findings.

# Research Decision Records

This directory contains **Research Decision Records (RDRs)** for significant project decisions involving research scope, methodology, data, analysis, or implementation.

RDRs document what the team decided, why the decision was needed, and the evidence or tradeoffs that influenced it.

## Naming

Use sequential identifiers:

```text
RDR-NNN-short-description.md
```

Examples:

```text
RDR-001-retain-question-4-versioning-strategy.md
RDR-002-select-similarity-method.md
```

## Status

| Status | Meaning |
| --- | --- |
| **Proposed** | Under discussion |
| **Accepted** | Approved by the team |
| **Superseded** | Replaced by a later RDR |
| **Rejected** | Considered but not adopted |

If a decision changes, keep the original RDR and mark it **Superseded** rather than deleting or rewriting its history.

## Template

```markdown
# RDR-NNN: Decision Title

| Field | Value |
| --- | --- |
| **Status** | Proposed |
| **Date** | YYYY-MM-DD |
| **Type** | Research / Methodology / Data / Implementation / Scope |
| **Related work** | Issue #... / PR #... / Sprint ... |
| **Evidence** | Path to notebook, analysis, issue, or other supporting artifact |
| **Supersedes** | None |

## Context

What problem or uncertainty required a decision?

## Decision

> **State the decision clearly.**

Briefly explain how the decision will be applied.

## Evidence

Include the findings, requirements, or observations that materially influenced the decision.

## Alternatives Considered

Summarize the realistic alternatives and why they were or were not selected.

## Consequences and Limitations

Record important tradeoffs, assumptions, risks, or limitations.

## Follow-up Actions

Record any work needed to implement or validate the decision.

## Revisit Criteria

Describe what would cause the team to reconsider the decision.
```

Not every RDR needs every optional section. Keep records concise and include only the information needed to understand the decision later.

# RDR-008: Evidence Representation and Comparison

| Field | Value |
| --- | --- |
| **Status** | Proposed |
| **Date** | 2026-10-02 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 2, security scanner, `scan_diff`, RDR-002 |
| **Evidence** | `THREAT_MODEL.md`, current scanner comparison output, Sprint 1 sample review |
| **Supersedes** | None |

## Context

Question 4 asks whether modified or reused skills introduce security-sensitive behavior that was absent from an earlier version or source artifact. The current scanner supports this by detecting rules and comparing the number of matches for each rule between related artifacts.

Rule counts are useful, but counts alone do not always show when the behavior behind a match has changed. For example:

```text
Base:     curl https://trusted.example/install.sh
Derived:  curl -k https://other.example/payload.sh
```

A network rule may still report `1 -> 1` with a delta of `0`, even though the command arguments and destination changed.

The same issue can appear when the operation itself does not change. For example:

```python
# Base
url = "https://trusted.example/api"
requests.get(url)

# Derived
url = "https://other.example/payload"
requests.get(url)
```

The API call is unchanged, but the URL evidence is different. The comparison should preserve both observations without assuming more about program flow than the static text supports.

There is also overlap between rules. A single source construct such as:

```text
curl -fsSL https://example.com/install.sh | bash
```

may match command-execution, URL, network-client, and external-execution rules at the same time. Storing a separate copy of the same source text under every rule would make the results harder to review and compare.

The project therefore needs a consistent way to preserve the evidence behind rule matches and compare that evidence across related artifacts.

## Decision Drivers

- Preserve the source evidence behind scanner findings so results can be reviewed and validated.
- Detect meaningful changes even when rule-match counts stay the same.
- Avoid duplicating the same source evidence when several rules match it.
- Keep the existing rule counts and deltas as useful summary measures.
- Avoid treating formatting-only differences as behavioral changes while preserving security-relevant differences.
- Keep comparisons grounded in what can be observed directly from the static artifact.
- Keep the approach practical to test and validate during Sprint 2.

## Decision

> **Represent scanner findings as evidence records that may be associated with one or more rules, preserve both raw and normalized evidence, and compare evidence between related artifacts using added and removed evidence alongside the existing rule-count deltas.**

An evidence record represents the source construct that caused one or more rules to match. Evidence may represent a shell command, URL reference, API call, file operation, credential reference, script reference, or another scanner-supported construct.

A single evidence record may be associated with multiple rule IDs when the same source text supports more than one finding. This keeps overlapping rules visible without duplicating the evidence.

Each evidence record should preserve enough information to support review and comparison, including:

- the type of evidence being represented;
- the original source text;
- a normalized form used for comparison;
- the applicable rule IDs;
- enough source location or context to find the evidence again; and
- structured values when they can be extracted reliably, such as commands, arguments, URLs, paths, or API calls.

### Raw and normalized evidence

The raw form preserves what appeared in the artifact for manual review and traceability.

The normalized form is used to determine whether two pieces of evidence are equivalent for comparison. Normalization should remove differences that do not change the observed behavior, such as harmless whitespace or shell line continuation, while preserving meaningful values such as command options, URLs, paths, script names, and arguments.

Normalization may differ by evidence type and should remain conservative so meaningful changes are not hidden.

### Evidence comparison

Evidence comparison is separate from rule-match counts.

The existing rule deltas continue to show how often each rule matched in the base and derived artifacts. Evidence comparison shows whether the actual matched content changed.

Evidence present only in the earlier artifact is reported as **removed**. Evidence present only in the later artifact is reported as **added**.

A separate `modified` category is not required initially. A changed item can be represented as removed evidence plus added evidence without requiring the comparison to guess which two records correspond to one another.

Evidence identity should not depend on generated evidence IDs, line numbers, or the set of matching rules. Moving the same command to another line should not by itself count as a behavioral change. Repeated occurrences should still be preserved so changes in occurrence count remain observable.

### Scope of interpretation

The evidence model records what the scanner can observe directly. It does not establish that a command was executed, a URL was contacted, a credential was exposed, or a finding is malicious.

The comparison also does not require general variable resolution or data-flow analysis. For example, a changed URL assignment and an unchanged `requests.get(url)` call may be reported as separate observations without claiming that the changed value definitely flowed into that call.

Higher-level relationships between findings, such as download-then-execute or credential-to-network flows, are not required at this stage. They can be reconsidered later if validation shows that they materially improve the project's ability to answer Question 4.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Continue using only rule-match counts and deltas | Not selected | Counts can remain unchanged even when the matched command, URL, path, or other evidence changes. |
| Store separate evidence under every matching rule | Not selected | The same source construct can match several rules and would be duplicated in the output. |
| Treat every change as a direct `modified` pair | Deferred | Pairing removed and added evidence introduces matching assumptions that are not necessary for the initial comparison. |
| Require variable/data-flow analysis or higher-level behavior relationships | Deferred | These may add value in some cases, but they add complexity beyond what is currently needed to compare directly observable evidence. |

## Consequences and Limitations

- The scanner can identify changes that rule counts alone would miss.
- Rule counts and evidence records become related but distinct measures; one evidence record may contribute to several rule counts.
- Formatting-only changes can be ignored when normalized evidence remains equivalent.
- Poor normalization could create false changes or hide meaningful ones, so normalization requires testing and manual validation.
- A changed construct may initially appear as one removed record and one added record rather than a single modified record.
- Dynamically constructed values or relationships between variables may remain unresolved.
- Static evidence does not establish runtime execution, malicious intent, or actual security impact.
- Raw evidence may contain sensitive-looking values, so exported results must follow the project's safe-reporting rules.

## Follow-up Actions

- Define the minimum evidence representation needed by the current scanner rules.
- Add evidence extraction and normalization while retaining the existing rule-count and delta output.
- Add tests for overlapping rules, formatting-only changes, repeated evidence, and same-count cases where the evidence changes.
- Validate evidence comparison against manually reviewed Sprint 2 examples.
- Document scanner-rule coverage changes separately from this evidence-representation decision.

## Revisit Criteria

Revisit this decision if validation shows that normalized evidence cannot be compared reliably, the representation creates excessive duplication or ambiguity, or important Question 4 cases consistently require relationships or program-flow analysis that the current approach cannot express.

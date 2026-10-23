# Threat Model

## Purpose and Scope

This project investigates whether modified or reused GitSkills artifacts contain **new or changed security-sensitive behavior** relative to a sufficiently related artifact. Such changes may increase the opportunities for an agent or its tools to affect the host environment, access sensitive information, or depend on external code and services.

We use **static analysis** of the GitSkills dataset to identify observable signals that warrant review. A detection is not proof that an instruction was executed, that a vulnerability exists, or that an artifact is malicious. The threat model defines the behaviors of interest and the limits of what our evidence can establish.

## Trust Boundary

GitSkills artifacts, bundled files, and their instructions are **untrusted data**. The analysis does not execute commands or scripts found in artifacts, retrieve referenced code, or contact services named in their content.

Behavioral analysis covers the body of `SKILL.md` and eligible bundled sibling files. YAML frontmatter in `SKILL.md` is excluded from behavioral detection because descriptive metadata and declared tools do not themselves demonstrate an operation. Sibling files, including configuration and instructional content, may contain behavior-relevant text and are assessed separately.

Candidate relationships are inferred from content similarity and available provenance or chronology evidence. They do not prove direct copying, authorship, or historical ancestry.

## Threat Categories and Detection Coverage

The scanner uses **13 rules across six categories**, primarily based on textual patterns. The rules detect selected signals, not all possible expressions of each behavior.

| Category | Rules | Signals of interest | Main coverage limitation |
| --- | --- | --- | --- |
| **Command execution** | `CMD-001`, `CMD-002` | Shell code, interpreters, executable commands, and script invocations | Indirect, dynamic, or unfamiliar execution syntax may be missed. |
| **Network access** | `NET-001`, `NET-002` | URLs, network clients, requests, and downloads | A URL may be only a reference; dynamically constructed destinations and some protocols may be missed. |
| **File-system access** | `FS-001`, `FS-002`, `FS-003` | File reads, writes, copies, moves, deletions, and directory changes | Language-specific APIs and indirect or dynamic operations are not exhaustively recognized. |
| **Credentials and secrets** | `CRED-001`, `CRED-002` | Secret-related identifiers, tokens, environment-variable references, and credential-file paths | Not every credential name or path is recognized; a reference does not prove exposure. |
| **External code execution** | `EXT-001`, `EXT-002` | Download-and-execute patterns and package installation | Multi-step execution chains, alternate installers, and some platform-specific forms may be missed. |
| **System modification** | `SYS-001`, `SYS-002` | Privilege elevation, permission changes, services, and system commands | Alternate APIs and platform-specific mechanisms may be missed. |

Bundled and invoked scripts are assessed through these categories rather than a separate script category. One construct may match multiple rules or categories. For example, downloading a script and piping it to a shell can involve network access, command execution, and external code execution.

The detector records rule IDs, categories, match counts, and source evidence. Rule matches are **signals of possible behavior**, including when they occur in examples or documentation; they are not findings of malicious intent. The active rule definitions and tests are maintained in the source repository.

## Threat Scenarios

The following scenarios illustrate changes that could warrant security review. They are **hypothetical**, not claims about particular artifacts in the dataset.

| Scenario | Security-sensitive change |
| --- | --- |
| **Remote code execution** | A skill begins directing an agent to download and run code from an external source. |
| **Credential exposure** | A skill introduces access to credential files or includes secrets in an outbound operation. |
| **Destructive file operations** | A skill adds deletion commands or expands the scope or privileges of file modifications. |
| **Supply-chain redirection** | A skill changes where executable code, dependencies, or external instructions are obtained. |
| **System modification** | A skill adds privileged operations or changes permissions, services, or system configuration. |

These behaviors can also be part of legitimate workflows. The analysis evaluates observable changes and context, not an author's intent.

## Comparing Related Artifacts

The analysis distinguishes three complementary stages:

1. **Detection:** Identify security-sensitive patterns and record their rules, categories, counts, and source locations.
2. **Evidence comparison:** Extract recognizable source constructs and compare related artifacts to identify added, removed, or matching evidence. Changes in rule counts are reported separately from changes in the underlying constructs.
3. **Risk assessment:** Evaluate changed evidence against **11 defined risk indicators (RI-001–RI-011)**. Indicators require supporting observations; a rule match or increased count alone is not enough. Uncertain observations are reported separately.

Directional conclusions are made only when there is sufficient evidence to treat one artifact as the base and another as the derived candidate. When direction is uncertain, the relationship remains unresolved rather than being characterized as an introduction or removal of behavior. The method does not assume that any particular removed instruction was directly replaced by an added one.

The evidence-comparison and risk-indicator methods are documented in [RDR-008](docs/decisions/RDR-008-evidence-representation-and-comparison.md) and [RDR-010](docs/decisions/RDR-010-evidence-based-risk-indicators.md).

## Coverage and Uncertainty

Eligible **added or changed sibling files with available, nonempty content** are examined regardless of file extension. Files without stored content are not fetched or executed. Their metadata may indicate that a resource changed, but its behavior cannot be determined. The sibling-selection policy is documented in [RDR-009](docs/decisions/RDR-009-sibling-security-scanning-scope.md).

Extracted evidence is identified as **complete**, **partial**, or **unsupported**, and unavailable sibling content is reported separately. Complete extraction means that the *detected constructs* were fully captured from available content; it does **not** mean that all security-sensitive behavior was found.

Regex-based static analysis can miss obfuscated or indirect actions, unfamiliar syntax, and risky instructions expressed only in prose, including non-English prose without recognizable technical indicators. It may also flag benign documentation, examples, or warnings. Neither the absence of a detection nor the absence of a supported risk indicator establishes that an artifact is safe.

## Interpretation and Safe Reporting

Our results describe **static detections, observable evidence changes, and supported or uncertain risk indicators requiring review**. They do not establish runtime execution, successful network access, actual credential disclosure, exploitability, malicious intent, or verified artifact lineage.

Reports preserve relevant source evidence and coverage limitations. Sensitive-looking excerpts are redacted on a best-effort basis, and generated reports should be reviewed before sharing. Manual validation is necessary to assess false positives, missed behavior, and the reliability of inferred changes.

Detailed operational instructions are maintained in [`TOOLS.md`](TOOLS.md). Broader methodological limitations are documented in [`THREATS_TO_VALIDITY.md`](THREATS_TO_VALIDITY.md).

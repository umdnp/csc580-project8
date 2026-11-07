# RDR-012: Scanner Precision and Risk Interpretation

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-11-06 |
| **Type** | Research methodology and implementation |
| **Related work** | Question 4, Sprint 3, security scanner, SkillTrace, RDR-007, RDR-008, RDR-010 |
| **Evidence** | Manual review of GitSkills comparisons, including `argent-react-native-app-workflow` and `cometchat-core`; scanner regression tests |
| **Supersedes** | None; refines the application of RDR-008 and RDR-010 |

## Context

RDR-008 preserves the evidence behind rule matches, and RDR-010 uses that evidence to identify changes that warrant review. Manual validation exposed gaps in both detection and interpretation.

Some operations were missed when expressed through different tools or syntax. Others appeared to introduce risk when only the tooling changed. For example, replacing an npm package-install command with an equivalent Bun command could appear to introduce an installation even though both versions already instructed installation of the same named packages.

We need more consistent coverage and comparisons without treating ordinary maintenance as increased risk.

## Decision Drivers

- Recognize security-sensitive operations consistently across common tools and command forms.
- Distinguish what the scanner detects from what a comparison supports as introduced risk.
- Preserve meaningful changes without inflating indicator counts for equivalent operations.
- Avoid inferring behavior that depends on unavailable scripts, manifests, or runtime context.
- Keep results reproducible as detection rules evolve.

## Decision

> **Refine rule coverage around observable operations and assess risk indicators from meaningful changes in those operations, not from command wording or rule matches alone. Preserve the underlying evidence and use regression examples to validate both detections and exclusions.**

### Rule coverage

Recognize observable operations across supported command runners, network clients, and direct or staged download-and-execute patterns. Explicit descriptions of downloads or outbound transfers can also provide evidence of network behavior; ordinary URL references do not.

Separate dependency installation into two detection rules:

- **EXT-002:** An installation that explicitly names the packages or external sources to acquire.
- **EXT-004:** An installation that obtains dependencies defined by a project manifest or requirements file.

Both remain in the existing `external_code_execution` category, which includes **external dependency acquisition**. A match does not establish execution. Separating these capabilities is not necessary for the current analysis.

### Interpreting changes

Compare the operation and its context, not just the executable name or command text. Switching package managers is not, by itself, a new acquisition operation; the command differences remain visible as evidence.

A new installation, changed registry or package source, or changed workspace scope can still support RI-005, including changes to direct URLs or Git sources. Commands are treated as equivalent only when the available evidence supports the correspondence.

The same restraint applies to network and execution evidence. A changed documentation link is not a new network operation. Referencing a script does not establish what it does without its content. Ambiguous observations remain uncertain, not supported indicators.

### Validation examples

In `argent-react-native-app-workflow`, the derived artifact replaces `npm install` with `bun install` and adds project-specific Bun commands and Android build guidance. The revised scanner recognizes the installations in both versions and records the additional command evidence, but reports no supported risk indicators.

**This is the intended result: the scanner can detect meaningful command changes without automatically treating them as increased risk.**

In `cometchat-core`, both artifacts already discuss authentication keys, but the derived artifact adds a `cometchat-settings.json` example and instructs agents not to gitignore it. Generic names such as `AUTH_KEY` and `authKey` are now recognized as credential references; they do not, on their own, satisfy RI-007, which requires an observable credential-file access or a credential-bearing outbound request. This could expose credentials through source control, but whether it introduces risk depends on the intended use of the key. The scanner cannot determine that from the instructions alone.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Treat every command change or added rule match as an indicator | Not selected | Tool substitutions and routine workflow changes would inflate risk findings. |
| Treat new credential references alone as RI-007 | Not selected | Identifiers and placeholders do not establish credential access or exposure. |
| Keep all dependency installations under EXT-002 | Not selected | Explicit package acquisition and project-defined dependency installation provide different levels of observable evidence. |
| Infer hidden behavior from script names or unavailable manifests | Not selected | Their effects cannot be established reliably without the relevant content. |
| Separate acquisition from execution in the capability model now | Deferred | The distinction is important, but changing the existing profile would add scope without improving the current comparisons enough to justify it. |

## Consequences and Limitations

- Rule counts may change as detection coverage improves, even when supported risk indicators do not. Counts are not measures of severity.
- Equivalent commands may still resolve different dependencies or behave differently at runtime; static comparison cannot establish that they are identical.
- Explicit sources and workspace scopes can be compared, but unavailable project files and scripts leave gaps.
- Destructive operations are not limited to explicit deletion. Overwriting a modified file can erase user changes, but recognizing that effect may require understanding the workflow. Options such as `--force` can override safeguards but do not, on their own, establish destructive behavior.
- Changes to credential storage or sharing instructions may introduce exposure risks without the operations required by RI-007. Such changes may need contextual review.
- Zero indicators do not prove safety; coverage describes scanned evidence, not all possible behavior.
- Containment-based direction remains weaker than observed chronology or declared provenance (RDR-007).
- Updated rules can change historical counts, so results must retain the scanner revision used.

## Follow-up Actions

- Retain positive and negative regression examples, including equivalent installations, changed acquisition sources, documented network operations, and ordinary references.
- Validate the revised rules and indicators against Sprint 3 samples, recording false positives, missed behavior, and uncertain cases.
- Revisit RI-007 using `cometchat-core` and similar credential-storage or source-control examples before considering broader detection rules.
- Run cohorts with a consistent scanner revision and preserve earlier results when comparing changes in measurements.
- Include the remaining limits of static interpretation in the final validity discussion.

## Revisit Criteria

Revisit this decision if validation shows recurring false positives or missed behavior, if separating acquisition from execution becomes necessary for the research measures, or if the current evidence model cannot reliably distinguish meaningful changes from ordinary maintenance.

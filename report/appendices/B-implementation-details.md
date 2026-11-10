
# Appendix B Pipeline implementation {#app-b}

## Detection rule registry

The saved Sprint 3 manifests identify **15 active rules across six categories**. These rules recognize candidate evidence, while the eleven risk indicators (RIs) in [Section V](#sec-method) assess whether *changes* in that evidence satisfy specific criteria. A new rule match, increased rule count, or changed command text alone does not establish an RI.

| Category | Active rules | What they recognize | Main limitation |
| --- | --- | --- | --- |
| Command execution | `CMD-001`, `CMD-002` | Shell-command blocks and recognized command invocations | A code example is not proof of execution. |
| Network access | `NET-001`, `NET-002` | HTTP(S) URLs and recognized network clients | A documentation link alone is not a network operation. |
| File-system access | `FS-001`, `FS-002`, `FS-003` | File commands, writing APIs, and reading commands/APIs | Ordinary file use is not automatically sensitive or destructive. |
| Credentials | `CRED-001`, `CRED-002` | Secret-related references and recognized credential files | A name or placeholder does not prove access to a secret. |
| External code and dependency acquisition | `EXT-001`, `EXT-002`, `EXT-003`, `EXT-004` | Direct download-to-shell, explicit package installs, staged download-and-execute, and manifest-based dependency installs | A legitimate installation may match; multi-step behavior may be incomplete. |
| System modification | `SYS-001`, `SYS-002` | Privilege elevation and system-changing commands | Administrative instructions can be legitimate. |

: Fifteen detection rules and their coverage limits {#tbl-detection-rules} {.wide}

The executable definitions are in `src/gitskills/rules/registry.py` and the category modules. For example, `EXT-002` covers explicit package installation, `EXT-004` covers manifest-based dependency installation, and `EXT-003` detects staged downloaded-file execution. Overlapping rules can describe the same command, so individual matches are not independent events. Leading `SKILL.md` frontmatter is masked for behavioral analysis; sibling-file content is scanned separately when eligible and available. Dataset instructions are never executed.

## End-to-end workflow and saved policy

For each selected family, the pipeline loads all qualifying artifacts, forms content variants and similarity clusters, evaluates the direction hierarchy, selects primary predecessors, and scans the directed pairs. It extracts evidence from both skill bodies and eligible added or changed sibling files, compares the base and derived evidence, applies RI-001 through RI-011, and records uncertainty and missing content. Cached family scans are reused only when their source, implementation, rule, and policy fingerprints are compatible.

| Setting | Sprint 3 value |
| --- | --- |
| Main study | Three non-overlapping, 100-family stratified samples |
| Family seeds | 5801, 5802, 5803 |
| Manual review seed | 580 |
| Edge selection | `primary` only |
| Shingle width | 5 tokens |
| Minimum containment | 0.80 |
| Minimum Jaccard | 0.30 |
| Minimum shared shingles | 5 |
| Containment direction margin | 0.10 |
| Detection rules / risk indicators | 15 / 11 |
| Source code revision | `ae69732ed8988ad7066ff351848f7d2e8ad311a1` |

: Pinned analysis configuration for Sprint 3 {#tbl-sprint3-configuration}

Direction priority is declared source, direct chronology, equivalent-peer chronology, repository-creation boundary, then asymmetric containment. These are inference rules, not proofs of copying. Additional directed edges exist in the analysis method but **were not scanned for the three Sprint 3 result sets**. Ambiguous directions and equivalent peers remain available for relationship review without being treated as evidence that a behavior was introduced.

## Skill and sibling-file change classification

| Change type | Meaning |
| --- | --- |
| `skill-only` | `SKILL.md` content differs; known sibling state is equivalent. |
| `siblings-only` | `SKILL.md` content is equivalent **under the analyzer's similarity representation**; known sibling state differs. |
| `skill+siblings` | `SKILL.md` content and known sibling-file content both differ. |
| `equivalent` | Both `SKILL.md` content and known sibling-file states are equivalent. |
| `unknown` | Missing or uncertain sibling state prevents reliable bundle classification. |

: Bundle change classifications {#tbl-bundle-change-classes} {.wide}

Similarity equivalence does not require the same byte hash, so a `siblings-only` comparison can still contain textual differences in `SKILL.md`. Added or changed sibling **files** with available nonempty content are eligible for static scanning, regardless of extension. Unavailable content is reported as missing; paths, filenames, and directory changes alone are not treated as the behavior of an unknown script.

## Relationship and scanning diagrams

The first diagram shows how the analyzer separates relatedness, direction, equivalent peers, and selected versus additional edges. It is a **conceptual diagram**; only selected primary edges enter the Sprint 3 security counts. The second diagram outlines the family-scanning component, including conditional sibling analysis. Risk-indicator assessment and cohort aggregation follow the underlying evidence comparison.

```{#fig-relationship-state .plantuml .fullpage .wide source="report/diagrams/relationship-state.puml" caption="Conceptual UML state diagram for relationship classification. Scanner flags are separate from lineage outcomes."}
```

```{#fig-family-scan .plantuml .fullpage .wide source="report/diagrams/family-scan-sequence.puml" caption="Family scanning and conditional sibling analysis; shown as a component-level summary rather than the complete research aggregation."}
```

\clearpage

# Appendix B Pipeline implementation

## Rule definitions

The pipeline uses thirteen extraction rules across six categories. These rules identify candidate evidence; the eleven RIs in the main report assess whether a changed operation satisfies a defined indicator. A new match or larger match count alone does not establish an RI.

| Category | Registered rules and indicators | Reason for inclusion | Interpretation limit |
| --- | --- | --- | --- |
| Command execution | CMD-001: shell-language code fences; CMD-002: recognized command invocations | Instructions can launch interpreters and executable programs. | A fence or command reference can be explanatory documentation. |
| Network access | NET-001: HTTP/HTTPS URLs; NET-002: recognized network-client usage | Instructions can contact external resources or retrieve data. | A URL alone does not show a request or data transfer. |
| File-system access | FS-001: file commands; FS-002: writing APIs; FS-003: reading commands/APIs | Instructions can read or modify local data. | Detection does not establish sensitive targets or harmful changes. |
| Credential access | CRED-001: secret-related terms; CRED-002: credential-file references | Instructions can involve authentication material and secret-bearing resources. | A reference is not evidence that a real secret was exposed. |
| External code execution | EXT-001: download-to-shell pipelines; EXT-002: package installation | Instructions can introduce externally supplied executable content. | Legitimate dependency installation is common; source trust is not verified. |
| System modification | SYS-001: privilege elevation; SYS-002: system-changing commands | Instructions can affect permissions and host configuration. | Administrative workflows may legitimately require these commands. |

The executable definitions are in `src/gitskills/rules/registry.py` and the category modules. Skill-body scans mask leading frontmatter while preserving source locations; sibling content is scanned separately. Overlapping rules can describe the same instruction and must not be counted as independent actions. The scanner does not execute the analyzed content.

## End-to-end processing

The end-to-end notebook invokes the cohort summarizer directly. It loads the selected exact-name families, establishes relatedness and direction, scans supported directed comparisons, assesses changed constructs against RI-001 through RI-011, and writes cohort summaries, coverage records, and validation samples. Compatible cached scans avoid repeating the same work; a saved manifest connects the outputs to source identities and run settings.

The saved run uses five-token shingles, containment of at least 0.80, Jaccard similarity of at least 0.30, and at least five shared shingles for distinct skill variants. Direction considers resolved source declarations, observed chronology, equivalent-peer chronology, repository boundaries, and finally containment asymmetry with a 0.10 margin. These are inference criteria rather than proof of copying. Ambiguous relationships remain outside directional scanning.

Primary edges select an acyclic predecessor structure; additional edges retain other supported comparisons. Both are included in the reported run. Skill and sibling states remain distinct so a changed script can be assessed even when its invoking skill text is unchanged. Unavailable sibling content is recorded as a coverage gap.

## Relationship classification

The state diagram summarizes comparison eligibility and relationship outcomes. These outcomes are computed classifications; they do not represent verified historical descent.

```{#fig-relationship-state .plantuml source="report/diagrams/relationship-state.puml" caption="Conceptual UML state diagram for relationship classification. Scanner flags are separate from lineage outcomes."}
```

## Scanning interactions

The sequence diagram shows the family-scanning component used within the cohort pipeline, including conditional sibling analysis and comparison.

```{#fig-family-scan .plantuml source="report/diagrams/family-scan-sequence.puml" width="5.6in" caption="Sequence diagram of family scanning, including conditional sibling analysis and comparison."}
```

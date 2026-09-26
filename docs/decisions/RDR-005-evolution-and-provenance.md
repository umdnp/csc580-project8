# RDR-005: Evolution Direction and Provenance Evidence

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-26 |
| **Type** | Research methodology |
| **Related work** | Question 4, RDR-001, RDR-002, RDR-003, RDR-004, `analyze_family`, Sprint 1 |
| **Evidence** | Manual review of `busybox-on-windows` candidate-family results and GitSkills metadata |
| **Supersedes** | None |

## Context

RDR-004 defines how the project determines whether two candidate `SKILL.md` bodies are sufficiently similar to be treated as related. The next problem is deciding whether the available evidence supports an earlier/later direction between related artifacts.

Direction matters for Question 4 because a security-sensitive behavior can only be described as introduced or removed when there is a defensible ordering between the artifacts being compared. Similarity alone does not provide that ordering.

Exploratory analysis showed that commit-history information is incomplete for many artifacts. Some closely related skills therefore cannot be ordered using `first_commit_at` alone. At the same time, manual review found that some artifacts contain explicit provenance metadata identifying the skill or repository from which they were derived.

The project needs a consistent way to use these different forms of evidence without forcing a direction where the dataset does not support one.

## Decision Drivers

- Infer direction only when the available evidence supports it.
- Prefer explicit provenance over weaker indirect signals.
- Keep similarity and provenance as separate concepts.
- Do not treat repository age as equivalent to skill age.
- Preserve ambiguous relationships rather than inventing chronology.
- Keep lineage claims cautious because the dataset does not provide complete history for every artifact.
- Produce relationships that can later support meaningful security comparisons.

## Evidence

The `busybox-on-windows` candidate family exposed the need for more than one source of direction evidence.

Two closely related artifacts, `2733595` and `2811614`, had no usable `first_commit_at` history. Similarity showed that they were strongly related, but chronology alone could not determine which came first.

Manual review of artifact `2811614` showed explicit provenance fields including:

```text
derived_from: skills/busybox-on-windows
upstream_skill: skills/busybox-on-windows
source_repo: diegosouzapw/awesome-omni-skills
```

Artifact `2733595` is located at the referenced source path in the same repository. This provides substantially stronger direction evidence than repository creation dates or small differences in similarity scores and supports the relationship:

```text
2733595 -> 2811614
basis=declared-source
```

Other reviewed cases showed the opposite problem: artifacts could be strongly related while lacking both explicit provenance and useful chronology. In those cases, forcing one artifact to be the base would overstate what the evidence supports.

## Decision

> **For artifacts already determined to be related, infer evolution direction using declared source information first, observed skill chronology second, and directional containment third. If none provides defensible direction, retain the relationship as ambiguous.**

The direction evidence is evaluated in this order:

```text
declared-source
      ↓
chronology
      ↓
containment
      ↓
ambiguous
```

### Declared source

Selected frontmatter fields may be used as provenance evidence:

- `derived_from`
- `upstream_skill`
- `source_repo`
- `upstream_source`

These fields are considered only for provenance and direction. They remain excluded from `SKILL.md` body similarity and behavioral security scanning.

More specific declarations, such as a clearly resolvable `derived_from` or `upstream_skill`, provide the strongest provenance evidence. Repository- or source-level fields can corroborate that relationship and may support direction when they identify a source unambiguously. Conflicting or unresolved declarations do not establish direction.

Declared provenance is used to direct relationships that have already been established through the project's similarity analysis. It does not create or merge similarity clusters on its own.

### Chronology

When declared provenance does not resolve direction, available `first_commit_at` evidence may be used to establish an observed earlier/later ordering.

Repository `created_at` is not treated as a substitute for `first_commit_at`. An older repository does not establish that the skill existed there earlier; it only shows when the repository itself existed.

Chronology remains observational evidence rather than proof of original authorship or direct lineage because GitSkills history follows the file at its current path and is incomplete for part of the dataset.

### Directional containment

When provenance and chronology are unavailable or inconclusive, strong asymmetric containment may support an inferred direction. A smaller artifact that is largely preserved inside a larger related artifact can be treated as a plausible predecessor when the difference is sufficiently clear.

Containment is not used to force direction when the scores are similar in both directions. Those relationships remain ambiguous.

### Ambiguous relationships and roots

A related pair whose direction cannot be established is retained as an ambiguous edge:

```text
A <-> B
```

A directed relationship is represented as:

```text
A -> B
```

Clusters are therefore treated as inferred evolution graphs rather than requiring a single base artifact. A cluster may have one or more **root candidates**. A root candidate is an artifact with no defensible incoming directed edge; it is not claimed to be the original source.

This distinction also governs later security interpretation. Directed relationships can support introduced/removed behavior comparisons. Ambiguous relationships can support comparisons of differences, but not claims about which artifact introduced a behavior.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Require `first_commit_at` for every directed comparison | Not selected | History is unavailable for many otherwise useful related artifacts. |
| Use repository `created_at` as a fallback skill timestamp | Not selected | Repository age does not establish when a skill was added. |
| Use containment alone to order all related artifacts | Not selected | Similar containment in both directions does not provide defensible chronology. |
| Treat all frontmatter as similarity or behavioral evidence | Not selected | Metadata and body instructions serve different purposes; RDR-002 and RDR-004 intentionally separate them. |
| Use selected provenance metadata as direction evidence | **Selected** | Explicit source declarations can resolve relationships that similarity and incomplete history leave ambiguous. |
| Force one base artifact per cluster | Not selected | Some clusters contain multiple plausible roots because available evidence cannot connect every lineage. |

## Consequences and Limitations

- Direction remains an inference unless supported by explicit provenance or observed chronology.
- Declared source metadata is repository-authored and may itself be incomplete or incorrect.
- Not every repository uses the selected provenance fields consistently.
- `first_commit_at` does not capture history before a file was renamed or moved to its current path.
- Directional containment is structural evidence, not proof of copying or ancestry.
- Some related artifacts will remain ambiguous, and some clusters will contain multiple root candidates.
- Preserving ambiguity reduces the number of comparisons that can support claims about introduced or removed behavior, but avoids overstating the evidence.

## Follow-up Actions

- Manually validate a sample of relationships directed by declared provenance, chronology, and containment.
- Record the evidence basis for each directed relationship in analysis outputs.
- Preserve ambiguous edges for later neutral security comparison without introduction/removal claims.
- Document remaining provenance and chronology limitations in `THREATS_TO_VALIDITY.md`.

## Revisit Criteria

Revisit this decision if validation shows that declared provenance fields are unreliable, containment produces too many incorrect directions, or the available direction evidence is insufficient to support a meaningful number of security-change comparisons.

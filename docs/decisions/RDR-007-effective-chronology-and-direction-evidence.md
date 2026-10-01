# RDR-007: Effective Chronology and Direction Evidence

| Field | Value |
| --- | --- |
| **Status** | Proposed |
| **Date** | 2026-09-29 |
| **Type** | Research methodology |
| **Related work** | Question 4, RDR-001, RDR-003, RDR-004, RDR-005, `analyze_family`, `scan_family` |
| **Evidence** | Manual review of current candidate-family results, including `busybox-on-windows`, and GitSkills commit/repository metadata |
| **Supersedes** | RDR-005 |

## Context

RDR-005 established that related artifacts need a reasonable earlier/later ordering before the project can describe security-sensitive behavior as introduced or removed. It used declared provenance, observed `first_commit_at` chronology, and directional containment while leaving unresolved relationships undirected.

Further analysis exposed two gaps in that approach.

First, commit history is not fetched for every artifact. In some cases, an artifact without history has an equivalent peer with a usable date. That peer can show that the same skill state existed earlier and provide useful chronology that would otherwise be missing.

Second, repository creation dates are not skill creation dates, but they can rule out some orderings. If one state was observed before another artifact's repository existed, that repository occurrence cannot be the earlier observation.

The project therefore needs a broader chronology model that can use these signals without treating them as proof of authorship, copying, or exact lineage.

## Decision Drivers

- Use the strongest available evidence before relying on structural similarity.
- Recover useful chronology when direct commit history is incomplete.
- Use equivalent-peer dates only when the skill body and known sibling resources represent the same state.
- Use repository creation only as a time boundary, not as a skill timestamp.
- Record why each direction was selected.
- Leave direction unresolved when the available evidence is not strong enough.

## Evidence

Manual review showed that some artifacts without fetched history have peers with equivalent `SKILL.md` content and the same known sibling state. When one of those peers has a date, it shows that the same state existed by that date. This can resolve comparisons that direct commit history alone cannot order.

Review also confirmed that repository age alone is not useful for ordering skills. An older repository may receive a skill much later. Repository creation becomes useful only as a boundary when another state is independently known to have existed before that repository was created.

## Decision

> **Use declared provenance first, then effective chronology, repository-creation boundaries, and directional containment. Record the basis used for each inferred direction and leave relationships unresolved when none of those signals is sufficient.**

The direction evidence is evaluated in this order:

```text
declared source
      ↓
effective chronology
  ├─ direct observation        -> chronology
  └─ equivalent peer           -> equivalent-peer-chronology
      ↓
repository-creation boundary
      ↓
directional containment
      ↓
direction unknown
```

### Declared source

Explicit source declarations remain the strongest direction evidence. Supported provenance metadata may identify another related artifact as an upstream or source artifact.

Declared provenance is considered only after similarity has established that the artifacts are related. Conflicting declarations do not establish direction.

### Effective chronology

Effective chronology is the earliest date at which we have evidence that a particular skill state existed. The date can come directly from the artifact's `first_commit_at` or from an equivalent peer that was observed earlier.

If no usable date exists for the state, effective chronology remains unknown.

#### Direct chronology

When the date comes directly from the artifact's own `first_commit_at`, the relationship uses `basis=chronology`.

For example:

```text
State A first observed: February 1
State B first observed: April 10

A was observed before B
    -> A can precede B
    -> basis=chronology
```

This establishes an observed ordering, not proof that A is the original source. GitSkills history follows the file at its current path and may not include earlier history before a rename or move.

#### Equivalent-peer chronology

When direct history is missing, or when an equivalent peer shows that the same state existed earlier, the project may use the earliest observed date of that equivalent state.

An equivalent peer can provide chronology only when:

- the `SKILL.md` body is identical or equivalent under the project's validated similarity representation; and
- the sibling-resource state is known and unchanged.

For example:

```text
Artifact A:   commit history not fetched
Artifact A':  equivalent state, observed January 10
Artifact B:   changed state, observed March 5

A' shows that the A-state existed by January 10
    -> effective chronology for A-state = January 10
    -> A-state can precede B
    -> basis=equivalent-peer-chronology
```

The peer date establishes when the shared state was observed; it does not become Artifact A's own commit date. If sibling state is unknown or different, the peer date is not used.

### Repository-creation boundary

Repository `created_at` may be used as a conservative time boundary. It is not treated as the date when a skill was added.

For example:

```text
State A observed:         February 1
Repository for B created: March 1

A existed before B's repository existed
    -> A can precede B
    -> basis=repo-created-boundary
```

The boundary tells us only that B could not have existed in that repository before March 1.

By contrast:

```text
Repository A created: January 1
Repository B created: March 1

This does not show that Skill A existed before Skill B.
```

An older repository is never treated as the source simply because it is older.

### Directional containment

If provenance and chronology-based evidence do not resolve direction, sufficiently asymmetric containment may support a plausible earlier/later ordering between already-related artifacts.

Containment is the weakest directional signal in the hierarchy. Similar containment in both directions does not justify choosing a predecessor.

### Evidence basis and unresolved relationships

Each directed relationship records why direction was selected. The current basis categories are:

- `declared-source`
- `chronology`
- `equivalent-peer-chronology`
- `repo-created-boundary`
- `containment`

Relationships that cannot be directed remain unresolved. Equivalent states remain peers. Their chronology becomes useful when that shared state is compared with a changed state.

This distinction controls how the security results are interpreted. Directed relationships can support base-to-derived claims about behavior being introduced or removed. Undirected relationships can show differences or equivalence, but not which artifact introduced a change.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Require direct `first_commit_at` on both artifacts | Not selected | It leaves useful relationships unresolved when the same state is dated elsewhere. |
| Treat a peer's date as the artifact's own commit date | Not selected | The peer establishes when the shared state was observed, not the artifact's own history. |
| Use repository `created_at` as a fallback skill timestamp | Not selected | Repository age does not establish when the skill was added. |
| Ignore repository creation entirely | Not selected | It can provide a useful boundary when another state is known to predate the repository. |
| Transfer chronology when only the `SKILL.md` body matches | Not selected | Bundled resource changes may represent a different security-relevant state. |
| Use containment before chronology or repository boundaries | Not selected | Temporal and provenance evidence is stronger for ordering than structural asymmetry. |
| Force a direction for every related pair | Not selected | Some relationships do not have enough evidence and should remain unresolved. |

## Consequences and Limitations

- More related artifacts can receive a reasonable direction even when their own commit history was not fetched.
- Equivalent-peer chronology depends on reliable body equivalence and sibling-state information.
- Repository creation can rule out some orderings but cannot identify when a skill was added to a repository.
- Declared provenance may be incomplete or incorrect because it is repository-authored metadata.
- Directional containment remains an inference and does not prove copying or ancestry.
- Some relationships will remain unresolved and should not support introduced/removed claims.

## Follow-up Actions

- Validate a sample of relationships directed by each evidence basis.
- Record the direction basis in analysis outputs used for later security comparisons.
- Include equivalent-peer chronology and repository-boundary assumptions in `THREATS_TO_VALIDITY.md`.
- Measure how many otherwise unresolved relationships are directed by equivalent-peer chronology and repository boundaries in the final analysis population.

## Revisit Criteria

Revisit this decision if validation shows that equivalent-state chronology produces incorrect orderings, sibling fingerprints are too incomplete to support reliable equivalence, repository boundaries introduce misleading directions, or the evidence hierarchy does not improve direction coverage without unacceptable error.

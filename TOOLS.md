# GitSkills Tools

This document describes the command-line tools provided by the project, including their purpose, usage, arguments, output, and interpretation.

## Quick Reference

| Tool | Purpose |
|---|---|
| `scan_diff` | Compare a base skill file with a derived skill file and report changes in security-sensitive behavior. |
| `analyze_family` | Analyze similarity, clusters, root candidates, and directed or ambiguous edges within one candidate family from the GitSkills DuckDB database. |

Use `<tool> --help` to display the command-line help for any installed tool.

---

## `scan_diff`

### Purpose

`scan_diff` performs a directional security comparison between two skill files. It scans the **base** and **derived** files with the project's static-analysis rules, builds a risk profile for each file, and reports capabilities or rule matches that changed in the derived file.

The comparison is directional: the first file is treated as the base or earlier artifact, and the second file is treated as the derived or later artifact.

YAML front matter at the beginning of a skill file is masked before behavioral rules are evaluated. Line positions are preserved so reported match line numbers continue to correspond to the original file.

### Synopsis

```bash
scan_diff BASE DERIVED [--verbose]
```

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `BASE` | Yes | Path to the base or earlier skill file. |
| `DERIVED` | Yes | Path to the derived or later skill file. |

### Options

| Option | Description |
|---|---|
| `--verbose` | Include source risk profiles in the JSON output and print individual matching lines for changed rules. |
| `-h`, `--help` | Show command help and exit. |

### How It Works

`scan_diff` performs the following steps:

1. Reads the base and derived files as UTF-8 text.
2. Masks top-of-file YAML front matter while preserving line positions.
3. Runs the configured static-analysis rules against each file.
4. Builds a security capability profile for each file.
5. Compares rule-match counts between the base and derived files.
6. Identifies capabilities present in the derived file that were absent from the base file.
7. Emits a JSON comparison result.

The current risk-profile categories are:

- `command_execution`
- `network_access`
- `filesystem_access`
- `credential_access`
- `external_code_execution`
- `system_modification`

### Output

`scan_diff` always writes the structured comparison as JSON to standard output.

The default JSON contains:

```text
introduced
rule_match_count
rule_deltas
```

`introduced` indicates which security-sensitive capability categories appear in the derived file but not in the base file.

`rule_match_count` contains the total number of rule matches in each file and the overall change:

```json
{
  "base": 3,
  "derived": 5,
  "delta": 2
}
```

`rule_deltas` contains only rules whose match counts changed. Each entry records the base count, derived count, and delta.

When `--verbose` is used, the JSON also includes the base and derived capability profiles. The tool additionally prints individual matching lines for changed rules. Credential-related excerpts are redacted in this diagnostic output.

### Examples

Compare two skill files:

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md
```

Include individual rule matches and source profiles:

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md --verbose
```

Save the JSON result to a file:

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md > comparison.json
```

Because diagnostic logging is separate from the JSON written to standard output, the JSON can be redirected without mixing it with the normal rule-change log messages.

### Interpretation

A positive rule delta means that the derived file contains more matches for that rule than the base file. A negative delta means that matches were removed.

An introduced capability means that at least one rule in that capability category matched the derived file and no rule in that category matched the base file. It does **not** by itself establish malicious intent or exploitability; the scanner reports security-sensitive behavior for later analysis and validation.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Comparison completed successfully. |
| `1` | An input file could not be read or decoded. |
| `2` | Command-line argument parsing failed. |

---

## `analyze_family`

### Purpose

`analyze_family` performs family-wide similarity and inferred-evolution analysis for one GitSkills **candidate family**. A candidate family consists of qualifying artifacts with the same exact skill `name` in `artifact_groupings`.

The tool compares `SKILL.md` body content across the entire candidate family, forms similarity clusters, identifies plausible directed edges when the evidence supports direction, and preserves related-but-undirected pairs as ambiguous edges.

Artifact groups (`name + normalized_description`) are retained as contextual metadata. They do not limit similarity comparison or create separate local clusters.

`analyze_family` does **not** run the security scanner and does not report command, network, filesystem, credential, or other risk-rule findings.

### Synopsis

```bash
analyze_family NAME [OPTIONS]
```

For example:

```bash
analyze_family busybox-on-windows
```

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `NAME` | Yes | Exact candidate-family skill name to analyze, such as `busybox-on-windows`. |

### Options

| Option | Default | Description |
|---|---:|---|
| `--db PATH` | `$GITSKILLS_DB` | Path to the GitSkills DuckDB database. If omitted, the `GITSKILLS_DB` environment variable is used. |
| `--shingle-size N` | `5` | Number of contiguous tokens in each shingle used for similarity comparison. |
| `--min-containment FLOAT` | `0.80` | Minimum directional containment required for two skill variants to be considered related. |
| `--min-jaccard FLOAT` | `0.30` | Minimum Jaccard similarity required for two skill variants to be considered related. |
| `--min-shared-shingles N` | `5` | Minimum number of shared shingles required for two skill variants to be considered related. |
| `--direction-margin FLOAT` | `0.10` | Minimum difference between the two directional-containment values required to infer direction when chronology does not distinguish the variants. |
| `--verbose` | Off | Show artifact IDs, qualifying similarities, group scope, and ambiguous-edge details. |
| `--json` | Off | Emit structured JSON instead of the human-readable report. Can be combined with `--verbose`. |
| `-h`, `--help` | — | Show command help and exit. |

The similarity thresholds are currently **exploratory**. They are configurable so they can be adjusted after manual validation without changing the similarity implementation.

### Database Selection

The database can be supplied explicitly:

```bash
analyze_family busybox-on-windows --db /path/to/gitskills.duckdb
```

On Windows PowerShell, a native Windows path can be used:

```powershell
analyze_family busybox-on-windows --db C:/data/duckdb/agent_skills_release.db
```

Or use the project environment variable:

```bash
export GITSKILLS_DB=/path/to/gitskills.duckdb
analyze_family busybox-on-windows
```

If neither `--db` nor `GITSKILLS_DB` is provided, the tool exits without running the analysis.

### How It Works

For the requested candidate family, `analyze_family`:

1. Loads every matching row from `artifact_groupings` and joins it to the associated artifact and repository metadata.
2. Identifies **artifact groups**, where each group represents one exact `name + normalized_description` combination.
3. Identifies **skill variants**, where each distinct `file_sha` represents distinct raw `SKILL.md` content.
4. Identifies **bundle variants**, using the skill variant together with its sibling-content state.
5. Extracts the top-level frontmatter fields `derived_from`, `upstream_skill`, `source_repo`, and `upstream_source` as optional provenance evidence. These fields do not participate in similarity scoring.
6. Masks top-of-file YAML front matter before similarity analysis.
7. Tokenizes the remaining `SKILL.md` body in a way that ignores whitespace differences and normalizes token case.
8. Builds contiguous token shingles, using 5-token shingles by default.
9. Compares every distinct pair of skill variants across the **entire candidate family** once, regardless of artifact-group membership.
10. Calculates directional containment, Jaccard similarity, and shared-shingle counts.
11. Applies the configured similarity policy to identify related skill variants.
12. Forms family-wide similarity **clusters** from those relationships.
13. Infers direction between already-related bundle variants using explicit declared provenance first, then chronology, then directional containment.
14. Reduces directed candidates so each target receives at most one selected predecessor and cycles are avoided.
15. Classifies selected directed and ambiguous edges by whether the skill, sibling resources, or both differ.
16. Reports bundle variants with no selected incoming edge as root candidates and preserves related pairs whose direction remains ambiguous.

### Artifacts, Skill Variants, and Bundle Variants

The analysis uses three distinct concepts:

**Artifact**  
An individual artifact represented by an `artifact_id`.

**Skill variant**  
A distinct raw `SKILL.md` content variant, identified by `file_sha`. Multiple artifacts with the same `file_sha` share the same skill variant, so their skill text is tokenized and compared only once.

**Bundle variant**  
A skill variant together with its known sibling-content state. When `sibling_content_sha` is available, artifacts with the same `file_sha` and the same `sibling_content_sha` are treated as the same bundle variant. When sibling state is unknown, the artifact remains separate rather than being collapsed with another unknown artifact.

This avoids repeated `SKILL.md` comparisons while preserving differences in resources bundled with otherwise identical skills.

### Artifact Groups

An artifact group is the project-defined `name + normalized_description` grouping represented by `artifact_groupings.id`.

Artifact groups provide context for interpreting relationships but **do not constrain similarity analysis**. Two artifacts from different artifact groups can still be placed in the same family-wide cluster when their skill bodies satisfy the similarity policy.

The report therefore distinguishes:

- related pairs **within artifact groups**; and
- related pairs **across artifact groups**.

Each artifact-group summary lists the family-wide cluster numbers containing its artifacts. The tool does not calculate separate local clusters or local root candidates for each artifact group.

### Similarity Measures

For two skill variants, the tool calculates:

**Directional containment**

```text
shared shingles / shingles in the source variant
```

Because containment is directional, `A -> B` containment can differ from `B -> A` containment. High `A -> B` containment can indicate that most of A is preserved inside B.

**Jaccard similarity**

```text
shared shingles / all unique shingles across both variants
```

Jaccard is symmetric and reflects overall overlap between the two shingle sets.

**Shared shingles**

The raw number of shingles present in both skill variants.

A pair is considered related only when all of the following are true:

```text
max directional containment >= --min-containment
Jaccard similarity          >= --min-jaccard
shared shingles             >= --min-shared-shingles
```

The raw measures are retained independently of the threshold policy so the policy can be changed during validation.

### Similarity Preprocessing

Similarity is computed on the `SKILL.md` **body**, not YAML front matter. Top-of-file front matter is masked before tokenization so metadata differences do not influence body similarity.

The analyzer may separately inspect the selected provenance fields `derived_from`, `upstream_skill`, `source_repo`, and `upstream_source` to help infer direction between variants that are already related. Those values never contribute tokens, shingles, containment, Jaccard similarity, or cluster membership.

Whitespace differences do not affect the token sequence used for shingling. Token matching is also case-insensitive.

A similarity score of `1.0` therefore means equivalent under the analyzer's body-token/shingle representation; it does not necessarily mean the raw files are byte-for-byte identical.

### Clusters

A cluster is a family-wide similarity-derived grouping of related skill variants.

Two skill variants are connected when they satisfy the configured similarity policy. Connected variants are placed in the same cluster, including transitive cases. For example, if A is related to B and B is related to C, all three can belong to the same cluster even if A and C do not independently satisfy the threshold.

Clusters are numbered deterministically. Larger clusters sort first; observed chronology and artifact ID provide stable tie breakers.

Cluster membership establishes relatedness through the similarity graph. It does not mean every pair of members is directly related.

### Declared Provenance

`analyze_family` inspects four top-level YAML frontmatter fields as optional provenance evidence:

- `derived_from`
- `upstream_skill`
- `source_repo`
- `upstream_source`

This is separate from similarity analysis. Frontmatter remains excluded from body similarity and cannot by itself cause two skill variants to enter the same cluster. Provenance is considered only after body similarity has already established a related pair.

`derived_from` and `upstream_skill` are treated as the strongest declarations when their values can be matched conservatively to another artifact path in the candidate family. `source_repo` and `upstream_source` can corroborate that match when they identify the same repository. A repository field can establish a source on its own only when it clearly identifies a unique source artifact in a different repository; generic values such as `community` are not treated as artifact references.

Path matching is exact after simple normalization, such as treating `skills/foo` and `skills/foo/SKILL.md` as the same skill path. The analyzer does not perform fuzzy provenance matching or parse arbitrary prose for ancestry.

If explicit provenance declarations conflict, the analyzer does not guess. The affected relationship remains ambiguous and can be reported with `basis=provenance-conflict`.

A successfully resolved relationship is reported compactly by default:

```text
2733595 -> 2811614 change=skill+siblings containment=... jaccard=... basis=declared-source
```

With `--verbose`, the edge also identifies which fields supported that direction:

```text
evidence=derived_from,upstream_skill,source_repo
```

### Evolution Graph and Root Candidates

Within each family-wide cluster, the analyzer builds an inferred evolution graph from related bundle variants. The graph contains two kinds of edges:

**Directed edge**

```text
A -> B
```

The available evidence supports treating A as the plausible predecessor side and B as the plausible derived side.

**Ambiguous edge**

```text
A <-> B
```

The variants are related, but the available evidence does not establish which direction is more defensible.

Direction is inferred in the following order:

1. If an already-related variant explicitly and unambiguously declares another family artifact as its source through the supported provenance fields, the relationship is directed with `basis=declared-source`.
2. Otherwise, if both variants have usable and different earliest observed `first_commit_at` values, the earlier observed variant is treated as the source with `basis=chronology`.
3. If chronology does not distinguish them, directional containment can be used when the difference between the two containment values is at least `--direction-margin`, producing `basis=containment`.
4. If none of those methods establishes direction, the relationship remains an ambiguous edge with `basis=similarity-only`. Conflicting explicit provenance remains ambiguous with `basis=provenance-conflict`.

When multiple directed candidates can precede the same target, predecessor selection prefers:

1. declared-source candidates;
2. chronology-supported candidates;
3. the temporally closest earlier candidate when chronology is available;
4. stronger directional containment;
5. stronger Jaccard similarity;
6. more shared shingles; and
7. a stable artifact-ID tie breaker.

The selected directed graph allows at most one predecessor per target and avoids cycles. Bundle variants with no selected incoming directed edge are reported as **root candidates**. A root candidate is not a verified source or original artifact; it only means that the analyzer cannot establish a defensible incoming directed edge for that variant.

A cluster can therefore have one root candidate or several root candidates. Multiple roots represent an evolution forest or unresolved ancestry within the cluster rather than an analysis failure.

The graph is an **inferred** evolution model, not proof of repository ancestry or authorship. `first_commit_at` represents the earliest commit observed for a file at its current path and may not capture its true origin. `repo.created_at` is not used to infer direction.

### Related Pairs and Edge Types

The report separates three ideas:

**Related skill pairs**  
All skill-variant pairs that satisfy the similarity policy.

**Directed edges**  
The reduced set of selected predecessor relationships for which direction can be inferred. These are shown as `A -> B`.

**Ambiguous edges**  
Qualifying related bundle-variant pairs for which declared provenance, chronology, and containment do not provide enough evidence to infer direction. These are shown as `A <-> B`.

Ambiguous edges are intentionally preserved rather than forced into a direction. They can establish that related variants differ, but they should not be interpreted as evidence that one variant introduced a change into the other.

For directed edges, `basis` records why direction was selected: `declared-source`, `chronology`, or `containment`. Normal ambiguous edges use `basis=similarity-only`; conflicting explicit provenance uses `basis=provenance-conflict`.

### Default Output

The default report is intentionally compact. It includes:

- candidate-family name;
- artifact count;
- artifact-group count;
- skill-variant count;
- bundle-variant count;
- family-wide cluster count;
- active similarity policy;
- related skill-pair counts, split into within-group and across-group pairs;
- directed-edge counts and change types;
- ambiguous-edge counts, split into within-group and across-group pairs;
- cluster-level root candidates;
- selected directed edges; and
- artifact-group summaries mapped to family-wide cluster numbers.

Ambiguous edge details are summarized by count in the default report and expanded with `--verbose`.

Example structure:

```text
Candidate family: busybox-on-windows
Artifacts:        26
Artifact groups:  6
Skill variants:   26
Bundle variants:  26
Clusters:         3
Policy:           5-token shingles, containment >= 0.80, Jaccard >= 0.30, shared >= 5
Policy status:    exploratory; validate thresholds before final analysis

Related skill pairs: 253
  Within artifact groups: 191
  Across artifact groups: 62

Directed edges: 17
  Skill only:         11
  Siblings only:      1
  Skill + siblings:   2
  Equivalent:         3
  Unknown:            0
  Within artifact groups: 14
  Across artifact groups: 3
Ambiguous edges: 102
  Within artifact groups: 78
  Across artifact groups: 24

Family clusters
  Cluster 1: artifacts=23, skills=23, bundles=23
    Root candidates: [571389, 572392, 580239, 620659, 648200, 701823]
    Directed edges:
      571909 -> 624960 change=skill+siblings containment=1.000 jaccard=0.916 basis=chronology
      620659 -> 786882 change=skill-only containment=1.000 jaccard=0.819 basis=containment
    Ambiguous edges: 101 (within groups=77, across groups=24)

Artifact groups
  Group 141815: artifacts=1, skills=1, bundles=1, family_clusters=[1]
  Group 311222: artifacts=1, skills=1, bundles=1, family_clusters=[1]
```

The numeric counts in this example are illustrative. Artifact IDs are used as the primary human-readable identifiers so specific records can be retrieved easily from DuckDB for manual validation.

### Verbose Output

Use `--verbose` when manually validating the analysis:

```bash
analyze_family busybox-on-windows --verbose
```

In addition to the normal report, verbose output includes:

- artifact IDs for each cluster;
- artifact IDs for each artifact group;
- every qualifying skill-variant similarity;
- directional containment in both directions;
- Jaccard similarity;
- shared-shingle counts;
- whether a relationship is within one artifact group or across artifact groups;
- selected directed-edge scope and inference basis;
- `evidence=` for declared-source edges, listing the provenance fields that actually supported the direction, for example `evidence=derived_from,upstream_skill`; and
- ambiguous edges shown as `A <-> B`, including both containment directions, change type, basis, provenance-conflict evidence when applicable, and scope.

### JSON Output

Use `--json` for a structured result suitable for notebooks, scripts, or saved analysis artifacts:

```bash
analyze_family busybox-on-windows --json
```

The JSON representation includes family-wide cluster results, artifact-group-to-cluster mappings, related-pair counts, root candidates, directed edges, ambiguous edges, within/across-group counts, change counts, edge basis, edge evidence, `change_type`, group-scope metadata, and the extracted provenance fields for artifacts that declare them.

Combine it with `--verbose` for the expanded structured representation, including artifacts, skill variants, bundle variants, and the full pairwise similarity results:

```bash
analyze_family busybox-on-windows --json --verbose
```

### Threshold Examples

Run the default exploratory policy:

```bash
analyze_family busybox-on-windows
```

Require stronger overall similarity:

```bash
analyze_family busybox-on-windows \
  --min-containment 0.90 \
  --min-jaccard 0.50
```

Require more shared evidence before treating variants as related:

```bash
analyze_family busybox-on-windows --min-shared-shingles 20
```

Change the token-shingle size:

```bash
analyze_family busybox-on-windows --shingle-size 7
```

Require a larger containment difference before using containment to infer direction:

```bash
analyze_family busybox-on-windows --direction-margin 0.20
```

### Change Types

Each directed edge and each ambiguous edge is classified by how its variants differ:

| Change type | Meaning |
|---|---|
| `skill-only` | The skill variants differ, but both bundle variants have known matching sibling-content fingerprints. |
| `siblings-only` | The skill variants are equivalent under the analyzer's similarity representation, but both bundle variants have known different sibling-content fingerprints. |
| `skill+siblings` | The skill variants differ and both bundle variants have known different sibling-content fingerprints. |
| `equivalent` | The skill variants are equivalent under the analyzer's similarity representation and both bundle variants have known matching sibling-content fingerprints. |
| `unknown` | At least one bundle variant does not have a known sibling-content fingerprint, so the sibling change state cannot be determined. |

Two skill variants are considered **equivalent under the similarity representation** when they have the same `file_sha`, or when both directional containment values and Jaccard similarity are exactly `1.0`. This does not necessarily mean the raw `SKILL.md` files are byte-for-byte identical; differences removed by preprocessing or token/shingle representation may still exist.

Change types describe structural differences between related variants only. `analyze_family` does not scan skill or sibling contents for security-sensitive behavior.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Analysis completed successfully. |
| `1` | Candidate family was not found, database access failed, or analysis could not be completed. |
| `2` | No database path was supplied through `--db` or `GITSKILLS_DB`, or command-line argument parsing failed. |

### Important Notes

- `NAME` is matched exactly against `artifact_groupings.name`.
- The database is opened read-only.
- Similarity is computed on the `SKILL.md` body rather than YAML front matter.
- The selected provenance fields are used only to help direct already-related variants; they do not affect similarity scores or cluster membership.
- Whitespace differences are ignored by tokenization for similarity analysis.
- Skill variants are compared once per distinct `file_sha` to avoid redundant work.
- Similarity comparison is family-wide; artifact-group boundaries do not restrict which skill variants can be related.
- Artifact groups are metadata mapped onto family-wide clusters; they do not have independent local clusters or local root candidates.
- Bundle differences are retained even when `SKILL.md` content is identical or equivalent under the similarity representation.
- Related-pair counts cover all qualifying skill-variant pairs, while directed-edge counts cover only selected predecessor edges.
- Ambiguous edges are preserved separately and use `A <-> B` to show that direction is unresolved.
- Root candidates are bundle variants with no selected incoming directed edge; they are not claimed to be verified original sources.
- Change-type summaries are based on selected directed edges, not the full pairwise similarity matrix.
- `repo.created_at` may be loaded as supporting metadata, but it is not used to infer evolution direction.
- The current threshold defaults are exploratory and should not be treated as validated research thresholds.
- The inferred evolution graph identifies plausible directed and ambiguous comparison paths for later analysis; it does not run the project's security scanner.

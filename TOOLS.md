# GitSkills Tools

This document describes the command-line tools provided by the project, including their purpose, usage, arguments, output, and interpretation.

## Quick Reference

| Tool | Purpose |
|---|---|
| `scan_diff` | Compare a base skill file with a derived skill file and report changes in security-sensitive behavior. |
| `analyze_family` | Analyze similarity, clusters, base candidates, and inferred evolution within one candidate family from the GitSkills DuckDB database. |

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

`analyze_family` performs similarity and evolution analysis for one GitSkills **candidate family**. A candidate family consists of qualifying artifacts with the same exact skill `name` in `artifact_groupings`.

The tool analyzes relationships among the artifacts in that family. It does **not** run the security scanner and does not report command, network, filesystem, credential, or other risk-rule findings.

Its purpose is to identify plausible relationships that can later be used to decide which artifacts should be compared by the security-analysis stage.

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
| `--verbose` | Off | Show artifact IDs, qualifying pairwise similarities, and ambiguous evolution relationships. |
| `--json` | Off | Emit structured JSON instead of the human-readable report. Can be combined with `--verbose`. |
| `-h`, `--help` | — | Show command help and exit. |

The similarity thresholds are currently **exploratory**. They are configurable so they can be adjusted after manual validation without changing the similarity implementation.

### Database Selection

The database can be supplied explicitly:

```bash
analyze_family busybox-on-windows --db /path/to/gitskills.duckdb
```

Or through the project environment variable:

```bash
export GITSKILLS_DB=/path/to/gitskills.duckdb
analyze_family busybox-on-windows
```

If neither `--db` nor `GITSKILLS_DB` is provided, the tool exits without running the analysis.

### How It Works

For the requested candidate family, `analyze_family`:

1. Loads every matching row from `artifact_groupings` and joins it to the associated artifact and repository metadata.
2. Identifies **artifact groups**, where each group represents one exact `name + normalized_description` combination.
3. Identifies **skill variants**, where each distinct `file_sha` represents distinct `SKILL.md` content.
4. Identifies **bundle variants**, using the skill variant together with its sibling-content state.
5. Masks YAML front matter and tokenizes the `SKILL.md` body.
6. Builds contiguous token shingles, using 5-token shingles by default.
7. Compares every distinct pair of skill variants once.
8. Calculates directional containment, Jaccard similarity, and shared-shingle counts.
9. Applies the configured similarity policy to identify related skill variants.
10. Forms similarity **clusters** from related skill variants.
11. Infers plausible evolution direction where the available evidence supports it.
12. Classifies each inferred evolution relationship by whether the skill, sibling resources, or both differ.
13. Reports cluster roots as base candidates and summarizes the inferred evolution graph.

### Artifacts, Skill Variants, and Bundle Variants

The analysis uses three distinct concepts:

**Artifact**  
An individual artifact represented by an `artifact_id`.

**Skill variant**  
A distinct `SKILL.md` content variant, identified by `file_sha`. Multiple artifacts with the same `file_sha` share the same skill variant, so their skill text is tokenized and compared only once.

**Bundle variant**  
A skill variant together with its known sibling-content state. When `sibling_content_sha` is available, artifacts with the same `file_sha` and the same `sibling_content_sha` are treated as the same bundle variant. When sibling state is unknown, the artifact remains separate rather than being collapsed with another unknown artifact.

This allows the analysis to avoid repeated SKILL.md comparisons while still preserving differences in the resources bundled with a skill.

### Similarity Measures

For two skill variants, the tool calculates:

**Directional containment**

```text
shared shingles / shingles in the source variant
```

Because containment is directional, `A -> B` containment can differ from `B -> A` containment. High `A -> B` containment can indicate that most of A is preserved inside a larger B.

**Jaccard similarity**

```text
shared shingles / all unique shingles across both variants
```

Jaccard is symmetric and reflects overall similarity between the two shingle sets.

**Shared shingles**

The raw number of shingles present in both skill variants.

A pair is considered related only when all of the following are true:

```text
max directional containment >= --min-containment
Jaccard similarity          >= --min-jaccard
shared shingles             >= --min-shared-shingles
```

The raw measures are retained independently of the threshold policy so the policy can be changed during validation.

### Clusters

A cluster is a similarity-derived grouping of related skill variants.

Two variants are connected when they satisfy the configured similarity policy. Connected variants are placed in the same cluster, including cases where the relationship is transitive. For example, if A is related to B and B is related to C, all three can belong to the same cluster even if A and C do not independently satisfy the threshold.

Clusters are numbered deterministically as `Cluster 1`, `Cluster 2`, and so on.

### Evolution and Base Candidates

Within each cluster, the analyzer attempts to infer plausible directional relationships between bundle variants.

Direction is inferred in the following order:

1. If both variants have usable and different `first_commit_at` values, the earlier observed variant is treated as the source for that relationship.
2. If chronology does not distinguish them, directional containment can be used when the difference between the two containment values is at least `--direction-margin`.
3. If neither method establishes direction, the relationship remains ambiguous.

The analyzer reduces directed candidates so that a bundle variant receives at most one selected predecessor and avoids creating cycles. Cluster members with no selected incoming edge are reported as base candidates.

The resulting graph is an **inferred** evolution model, not proof of repository ancestry or authorship. `first_commit_at` represents the earliest commit observed for a file at its current path and may not capture its true origin.

### Default Output

The default report is intentionally compact. It includes:

- candidate-family name;
- artifact count;
- artifact-group count;
- skill-variant count;
- bundle-variant count;
- cluster count;
- active similarity policy;
- family base candidate or candidates;
- evolution-relationship counts by change type;
- cluster summaries and inferred evolution edges;
- artifact-group summaries.

The evolution-relationship counts summarize only the **selected inferred evolution edges**, not every possible pairwise similarity comparison.

Example structure:

```text
Candidate family: busybox-on-windows
Artifacts:        87
Artifact groups:  12
Skill variants:   19
Bundle variants:  24
Clusters:         3

Family base candidate: 48192

Evolution relationships: 17
  Skill only:         4
  Siblings only:      3
  Skill + siblings:   7
  Equivalent:         2
  Unknown:            1

Family clusters
  Cluster 1: artifacts=72, skills=14, bundles=18, base=48192
    Evolution:
      48192 -> 51201 change=skill+siblings containment=0.942 jaccard=0.811 basis=chronology
      51201 -> 61344 change=skill-only containment=0.915 jaccard=0.873 basis=chronology
```

Artifact IDs are used as the primary human-readable identifiers so specific records can be retrieved easily from DuckDB for manual validation.

### Verbose Output

Use `--verbose` when manually validating the analysis:

```bash
analyze_family busybox-on-windows --verbose
```

In addition to the normal report, verbose output includes:

- artifact IDs for each cluster;
- artifact IDs for each artifact group;
- qualifying skill-variant similarities;
- directional containment in both directions;
- Jaccard similarity;
- shared-shingle counts;
- ambiguous evolution relationships, including their change type.

### JSON Output

Use `--json` for a structured result suitable for notebooks, scripts, or saved analysis artifacts:

```bash
analyze_family busybox-on-windows --json
```

The JSON representation includes family-level change counts and a `change_type` value on inferred evolution edges. Ambiguous relationships also include their change type.

Combine it with `--verbose` for the expanded structured representation:

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

Each inferred evolution edge is classified by how its two bundle variants differ:

| Change type | Meaning |
|---|---|
| `skill-only` | The skill variants differ, but both bundle variants have known matching sibling-content fingerprints. |
| `siblings-only` | The skill variants are equivalent under the analyzer's similarity representation, but both bundle variants have known different sibling-content fingerprints. |
| `skill+siblings` | The skill variants differ and both bundle variants have known different sibling-content fingerprints. |
| `equivalent` | The skill variants are equivalent under the analyzer's similarity representation and both bundle variants have known matching sibling-content fingerprints. |
| `unknown` | At least one bundle variant does not have a known sibling-content fingerprint, so the sibling change state cannot be determined. |

Two skill variants are considered **equivalent under the similarity representation** when they have the same `file_sha`, or when both directional containment values and Jaccard similarity are exactly `1.0`. This does not necessarily mean the raw `SKILL.md` files are byte-for-byte identical; differences removed by preprocessing or token/shingle representation may still exist.

Change types describe structural differences between related variants only. `analyze_family` does not scan the skill or sibling contents for security-sensitive behavior.

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
- Skill variants are compared once per distinct `file_sha` to avoid redundant work.
- Bundle differences are retained even when the `SKILL.md` content is identical or equivalent under the similarity representation.
- Change-type summaries are based on selected inferred evolution edges, not the full pairwise similarity matrix.
- `repo.created_at` may be loaded as supporting metadata, but it is not used to infer evolution direction.
- The current threshold defaults are exploratory and should not be treated as validated research thresholds.
- The inferred evolution graph identifies plausible comparison paths for later analysis; it does not run the project's security scanner.

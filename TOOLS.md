# GitSkills Tools

This document describes the project command-line tools and the options most developers need to run them.

## Quick Reference

| Tool | Purpose |
|---|---|
| [`scan_diff`](#scan_diff) | Compare two skill files and report changes in security-sensitive behavior. |
| [`analyze_family`](#analyze_family) | Analyze similarity, clusters, chronology, and inferred relationships within one candidate family. |
| [`scan_family`](#scan_family) | Scan selected directed family relationships for newly introduced or increased security-sensitive behavior. |
| [`family_picker`](#family_picker) | Interactively browse candidate families and run [`analyze_family`](#analyze_family). |

Use `<tool> --help` for the complete command-line help. When running directly from the source tree, the equivalent form is `python -m gitskills.tools.<tool>`.

## `family_picker`

### Purpose

`family_picker` is an interactive convenience interface for repeatedly running `analyze_family` while exploring candidate families. It does not replace the `analyze_family` command or expose its analysis configuration options.

The picker reads candidate-family names from `artifact_groupings` using the database configured by `GITSKILLS_DB`. Each selection screen shows 10 randomly selected families together with the number of artifacts that share each family name.

### Usage

**Run the picker from the project root:**

```bash
python -m gitskills.tools.family_picker
```

The selection screen supports:

- entering `1` through `10` to analyze one of the displayed random families;
- typing an exact family name directly;
- entering `R` to refresh the list with 10 new random families; and
- entering `Q` or pressing `Ctrl+C` to exit cleanly.

After an analysis finishes, the picker returns to the family-selection screen with a new random set so additional families can be reviewed without restarting the tool.

### Analysis Command

For the selected family, the picker runs the equivalent of:

```bash
python -m gitskills.tools.analyze_family NAME --output apps/skilltrace/reports
```

Reports produced through the picker are therefore written to `apps/skilltrace/reports`. Use `analyze_family` directly when custom similarity thresholds, JSON output, verbose output, a different database path, or a different output directory are required.

---

## Common Options

`analyze_family` and `scan_family` use the GitSkills DuckDB database. Pass `--db PATH`, or set `GITSKILLS_DB` when `--db` is omitted.

All three tools support:

| Option | Description |
|---|---|
| `--output [DIR]` | Write JSON to `DIR`. If `DIR` is omitted, use `./output`. Existing directories are reused. |
| `--verbose` | Include additional diagnostic detail. |
| `-h`, `--help` | Show command help and exit. |

---

## `scan_diff`

### Purpose

`scan_diff` compares a **base** skill file with a **derived** skill file and reports security-rule changes. The comparison is directional: the first file is treated as earlier and the second as later.

Top-of-file YAML front matter is excluded from behavioral scanning while line positions are preserved.

### Synopsis

```bash
scan_diff BASE DERIVED [--verbose] [--output [DIR]]
```

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `BASE` | Yes | Base or earlier skill file. |
| `DERIVED` | Yes | Derived or later skill file. |

### Output

JSON is always written to standard output. The default result includes:

- `introduced` capability categories;
- total `rule_match_count` values for base and derived files; and
- `rule_deltas` for rules whose counts changed.

With `--verbose`, the JSON also includes source risk profiles and the diagnostic log shows individual matching lines. Credential-related excerpts are redacted.

If `--output` is used, the same JSON is also written to a file. For a derived `SKILL.md`, the parent directory name is used as the file name.

### Examples

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md
```

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md --verbose
```

```bash
scan_diff sample_skills/base/SKILL.md sample_skills/derived/SKILL.md --output results
```

### Interpretation

A positive rule delta means the derived file contains more matches for that rule. An introduced capability means a capability category appears in the derived file but not the base file. These findings identify security-sensitive behavior for review; they do not establish malicious intent.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Comparison completed successfully. |
| `1` | An input file could not be read or output could not be written. |
| `2` | Command-line or output-directory setup failed. |

---

## `analyze_family`

### Purpose

`analyze_family` performs similarity and inferred-evolution analysis for one GitSkills **candidate family**. A candidate family contains qualifying artifacts with the same exact skill `name` in `artifact_groupings`.

The tool compares `SKILL.md` bodies, forms similarity clusters, identifies selected predecessor relationships when direction is supported, and preserves equivalent or direction-unknown relationships separately. It does **not** run the security scanner.

### Synopsis

```bash
analyze_family NAME [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `NAME` | Yes | Exact candidate-family skill name, such as `busybox-on-windows`. |

### Options

| Option | Default | Description |
|---|---:|---|
| `--db PATH` | `$GITSKILLS_DB` | GitSkills DuckDB database path. |
| `--shingle-size N` | `5` | Tokens per similarity shingle. |
| `--min-containment FLOAT` | `0.80` | Minimum directional containment for related variants. |
| `--min-jaccard FLOAT` | `0.30` | Minimum Jaccard similarity for related variants. |
| `--min-shared-shingles N` | `5` | Minimum shared shingles for related variants. |
| `--direction-margin FLOAT` | `0.10` | Minimum containment difference used when stronger direction evidence is unavailable. |
| `--json` | Off | Print structured JSON instead of the human-readable report. |
| `--verbose` | Off | Add artifact metadata, full pairwise similarities, variants, provenance, and detailed relationship evidence. |
| `--output [DIR]` | Off | Save JSON to `DIR`; use `./output` when `DIR` is omitted. |

The similarity thresholds are exploratory and should be validated before final analysis.

### How It Works

For the requested family, `analyze_family`:

1. Loads artifacts and repository metadata from `artifact_groupings`.
2. Groups identical raw `SKILL.md` content by `file_sha` into skill variants.
3. Combines skill content and known sibling state into bundle variants.
4. Masks top-of-file YAML front matter and compares body content with token shingles.
5. Forms family-wide similarity clusters.
6. Classifies relationships as directed, equivalent, or direction unknown.
7. Selects at most one predecessor per target while avoiding cycles.
8. Retains other related directed candidates for comparison without making them selected parent edges.

Artifact groups (`name + normalized_description`) remain contextual metadata; they do not limit family-wide similarity comparison.

### Similarity

A pair is related when all configured thresholds pass:

```text
max directional containment >= --min-containment
Jaccard similarity          >= --min-jaccard
shared shingles             >= --min-shared-shingles
```

Similarity is computed from the `SKILL.md` body. Frontmatter, whitespace differences, and token case do not affect the body comparison.

A similarity result of `1.0` means equivalent under the token/shingle representation, not necessarily byte-for-byte identical files.

### Direction Evidence

Direction is inferred only after a pair is already related. Evidence is considered in this order:

1. `declared-source` — supported frontmatter provenance fields identify a source artifact.
2. `chronology` — direct `first_commit_at` observations establish an earlier state.
3. `equivalent-peer-chronology` — an equivalent bundle state supplies an earlier observed chronology proxy.
4. `repo-created-boundary` — an observed state predates the other repository's creation time, used only as a conservative lower-bound check.
5. `containment` — directional containment differs by at least `--direction-margin`.

If direction cannot be supported, the relationship remains undirected. Equivalent bundle states are kept as equivalent peers rather than forcing a direction.

`first_commit_at` is the earliest commit observed for the file at its current path, not proof of original authorship or provenance.

### Change Types

| Change type | Meaning |
|---|---|
| `skill-only` | Skill content differs; known sibling state matches. |
| `siblings-only` | Skill content is equivalent; known sibling state differs. |
| `skill+siblings` | Both skill content and known sibling state differ. |
| `equivalent` | Skill content and known sibling state are equivalent. |
| `unknown` | Sibling state is not known well enough to classify the bundle change. |

### Output

The human-readable report summarizes:

- family, artifact, variant, and cluster counts;
- related skill-pair counts;
- selected directed edges and change types;
- equivalent undirected edges;
- ambiguous direction-unknown edges; and
- root candidates for each cluster.

The default JSON is intentionally compact for saved reports and visualization. It contains the summary, clusters, selected directed edges, undirected relationships, additional related comparison edges, and chronology proxies.

`--verbose` adds diagnostic data such as artifact groups, artifacts, skill and bundle variants, provenance fields, and the full pairwise similarity matrix.

When `--output` is used, the report is written as `<NAME>.json`. The normal human-readable report is still printed unless `--json` is also used.

### Examples

```bash
analyze_family busybox-on-windows --db C:/data/duckdb/agent_skills_release.db
```

```bash
analyze_family busybox-on-windows --output reports
```

```bash
analyze_family busybox-on-windows --json --verbose
```

```bash
analyze_family busybox-on-windows --min-containment 0.90 --min-jaccard 0.50
```

### Important Notes

- Root candidates are bundle variants with no selected incoming edge; they are not verified originals.
- Equivalent peers can supply chronology only when the behavior-bearing bundle state is equivalent and sibling state is known.
- `repo.created_at` is used only as a lower-bound check, never as the skill creation date.
- Additional related edges retained for comparison are not automatically selected as parent relationships.
- The inferred graph represents plausible evolution evidence, not proven repository ancestry.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Analysis completed successfully. |
| `1` | Family lookup, database access, analysis, or output writing failed. |
| `2` | Database path, command-line, or output-directory setup failed. |

---

## `scan_family`

### Purpose

`scan_family` combines family analysis with the static security scanner. It scans the **selected directed evolution edges** produced by `analyze_family` and reports security-rule findings that increase or appear on the derived side.

Direction-unknown and equivalent peer relationships are not scanned as base-to-derived comparisons because the tool does not have a defensible direction for them.

### Synopsis

```bash
scan_family NAME [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `NAME` | Yes | Exact candidate-family skill name, such as `busybox-on-windows`. |

### Options

`scan_family` accepts the same family-analysis options as `analyze_family`:

| Option | Default | Description |
|---|---:|---|
| `--db PATH` | `$GITSKILLS_DB` | GitSkills DuckDB database path. |
| `--shingle-size N` | `5` | Tokens per similarity shingle. |
| `--min-containment FLOAT` | `0.80` | Minimum directional containment. |
| `--min-jaccard FLOAT` | `0.30` | Minimum Jaccard similarity. |
| `--min-shared-shingles N` | `5` | Minimum shared shingles. |
| `--direction-margin FLOAT` | `0.10` | Minimum containment difference used when stronger direction evidence is unavailable. |
| `--json` | Off | Print structured JSON instead of the human-readable report. |
| `--verbose` | Off | Show direction evidence, similarity details, sibling paths, and individual rule matches. |
| `--output [DIR]` | Off | Save JSON to `DIR`; use `./output` when `DIR` is omitted. |

### How It Works

For each selected directed edge, `scan_family`:

1. Scans the base and derived `SKILL.md` bodies with the project's security rules.
2. Flags positive rule-count deltas on the derived side.
3. When siblings changed, scans sibling content and identifies findings in new or changed derived sibling files.
4. Records incomplete sibling scans when required content or SHA information is unavailable.

`SKILL.md` frontmatter is excluded from behavioral scanning. Sibling files are scanned as file content.

### Output

The default report includes:

- pairs analyzed, flagged, and incomplete;
- direction-unknown edges skipped;
- flagged base/derived artifact pairs;
- rule IDs with source, destination, and delta counts; and
- warnings for incomplete sibling scans.

With `--verbose`, the report also shows direction evidence, similarity values, sibling paths, rule descriptions, and matching lines. Credential-related excerpts are redacted.

The JSON includes the active rule catalog, similarity policy, family summary, flagged pairs, finding sources, and sibling scan coverage. `--verbose` adds detailed match and direction evidence.

When `--output` is used, the JSON is written as `<NAME>.json`.

### Examples

```bash
scan_family busybox-on-windows --db C:/data/duckdb/agent_skills_release.db
```

```bash
scan_family busybox-on-windows --output scan-results
```

```bash
scan_family busybox-on-windows --json --verbose
```

### Interpretation

A flagged pair means at least one security rule increased in the derived `SKILL.md`, or a finding was observed in new or changed derived sibling content. It identifies a change that warrants review; it does not establish malicious intent or exploitability.

An incomplete sibling scan means the tool could not fully inspect the changed sibling surface. Treat the result as incomplete rather than as evidence that no risky change exists.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Family scan completed successfully. |
| `1` | Family lookup, database access, scan, or output writing failed. |
| `2` | Database path, command-line, or output-directory setup failed. |

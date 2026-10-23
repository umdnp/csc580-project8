# GitSkills Tools

This document describes the project command-line tools and the options most developers need to run them.

## Quick Reference

| Tool | Purpose |
|---|---|
| [`scan_diff`](#scan_diff) | Compare two skill files and report changes in security-sensitive behavior. |
| [`analyze_family`](#analyze_family) | Analyze similarity, clusters, chronology, and inferred relationships within one candidate family. |
| [`scan_family`](#scan_family) | Scan one candidate family or a list of families for security-sensitive evidence changes and risk indicators; optionally benchmark scans. |
| [`summarize_scans`](#summarize_scans) | Aggregate family scan JSON into research statistics, figures, and optional manual-validation samples. |
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

`scan_diff`, `analyze_family`, and `scan_family` all support:

| Option | Description |
|---|---|
| `--output [DIR]` | Write JSON to `DIR`. If `DIR` is omitted, use `./output`. Existing directories are reused. |
| `--verbose` | Include additional diagnostic detail. |
| `-h`, `--help` | Show command help and exit. |

---

## `scan_diff`

### Purpose

`scan_diff` compares a **base** file with a **derived** file and reports rule-match changes, added or removed security-sensitive evidence, and evidence-based risk indicators. The comparison is directional: the first file is treated as earlier and the second as later.

Top-of-file YAML frontmatter is masked by default **only for files named `SKILL.md`** (case-insensitive), preserving source positions. Other file types are scanned without automatic frontmatter masking.

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
- `rule_match_count` values for both files and their overall delta;
- `rule_deltas` for rules whose match counts changed;
- `evidence_comparison`, with `added` and `removed` extracted evidence records, including rule IDs, source locations, structural context, extraction status, and redacted excerpts; and
- `risk_indicators`, including the policy version, supported indicator categories, distinct finding counts, supporting evidence, uncertain observations, and evidence-coverage status/notes.

Evidence is compared by normalized source constructs, so a change can be reported even if rule-match counts stay the same. The default JSON contains **changed evidence**, not a full inventory of unchanged evidence from both files. Risk indicators are review signals, not an overall risk or maliciousness classification.

With `--verbose`, the JSON also includes the base and derived capability profiles and rule-match totals. Diagnostic logging reports individual rule matches and source lines. Report excerpts are redacted on a best-effort basis; review exported reports before sharing them.

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

**All directionally supported relationships for research:**

```powershell
uv run python -m gitskills.tools.scan_family --input data/validation/families.txt --db C:/data/duckdb/agent_skills_release.db --output output/all-edges --edges all
```

Use separate output directories for `primary` and `all` runs. They describe different populations and should not be combined in one research summary.

### Interpretation

A positive rule delta means the derived file contains more matches for that rule. An introduced capability means a capability category appears in the derived file but not the base file. Added or removed evidence can identify a meaningful source change even when the rule counts are unchanged. Supported risk indicators identify evidence-based changes warranting review; uncertain observations and incomplete coverage are reported separately. None of these results establishes malicious intent, execution, or exploitability.

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
| `--verbose` | Off | Include supplementary group, variant, and provenance diagnostics; standard JSON already includes artifact metadata, pairwise similarities, and relationship evidence. |
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

The default JSON is a complete shared report for SkillTrace and research sampling. It includes the summary, artifact source metadata, full pairwise similarity measurements, clusters, directed and ambiguous relationships, chronology proxies, input counts, and skipped-artifact reasons.

`--verbose` adds supplementary diagnostic data such as artifact groups, skill and bundle variants, and expanded provenance fields.

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

`scan_family` runs family analysis and static security scanning for **one candidate family** or **multiple families from an input file**. By default, it scans only **primary** predecessor relationships selected for the inferred evolution graph. With `--edges all`, it also scans additional related artifact pairs with supported direction. Equivalent, direction-unknown, and unrelated relationships are not treated as base-to-derived comparisons.

The scanner examines the `SKILL.md` body and relevant changed sibling content. It records changes in rule counts, **added or removed extracted evidence**, and supported or uncertain **risk indicators (RI-001–RI-011)**. Indicators are evidence-based review signals, not conclusions that a skill is malicious.

### Synopsis

```bash
scan_family NAME [OPTIONS]
scan_family --input FILE --output [DIR] [OPTIONS]
```

Supply **either** `NAME` **or** `--input FILE`, not both. The first form runs a single family; the second runs a batch.

### Arguments and Options

| Option / argument | Default | Description |
|---|---:|---|
| `NAME` | — | Exact candidate-family skill name, such as `busybox-on-windows` (single-family mode). |
| `--input FILE` | Off | Read UTF-8 candidate-family names from a file, one per line. Blank lines and lines beginning with `#` are ignored. Names must be unique. Requires `--output`. |
| `--limit N` | Off | In `--input` mode, scan only the first `N` names (positive integer); useful for a pilot run. |
| `--edges {primary,all}` | `primary` | `primary` scans edges designated as predecessor relationships in the inferred evolution graph; `all` also scans additional directionally supported related edges. Neither mode includes ambiguous or equivalent pairs as directed changes. |
| `--db PATH` | `$GITSKILLS_DB` | GitSkills DuckDB database path. |
| `--shingle-size N` | `5` | Tokens per similarity shingle. |
| `--min-containment FLOAT` | `0.80` | Minimum directional containment. |
| `--min-jaccard FLOAT` | `0.30` | Minimum Jaccard similarity. |
| `--min-shared-shingles N` | `5` | Minimum shared shingles. |
| `--direction-margin FLOAT` | `0.10` | Minimum containment difference when stronger direction evidence is unavailable. |
| `--json` | Off | In single-family mode, print structured JSON rather than the human-readable report. Batch mode writes JSON files automatically. |
| `--verbose` | Off | Include more direction, similarity, sibling, evidence, and rule-match details. |
| `--output [DIR]` | Off | Save one JSON report per family; special characters in family names are converted to safe, collision-resistant filenames. If `DIR` is omitted, use `./output`. Required in batch mode. |
| `--benchmark` | Off | For either single or batch scans, generate `benchmarks.csv` with per-family elapsed time and success/failure status. |
| `--tracemalloc` | Off | With `--benchmark`, also measure peak **Python-traced allocations** in MiB. Not process RSS or DuckDB native memory; adds measurement overhead. |
| `-h`, `--help` | — | Display full CLI help. |

All family-analysis threshold flags apply equally in single-family and batch mode. Thresholds are exploratory and should be recorded with the results.

### How It Works

For each family, `scan_family`:

1. Loads artifacts, similarity/direction information, and stored sibling records from DuckDB.
2. Selects primary directed evolution edges (default) or primary plus additional directionally supported related edges (`--edges all`), scanning any repeated directed pair only once. Relationships without supported direction are counted separately and are **not** labeled as introduced changes.
3. Runs the rule-based scanner and evidence extractor against the base and derived `SKILL.md` bodies, plus relevant changed sibling files. Scanned content is **not executed**.
4. Compares evidence constructs, including changes that do not alter rule-match counts, and evaluates the 11 evidence-based risk indicators.
5. Preserves distinct coverage information for partial/unsupported extraction, unavailable sibling content, unknown hashes, and incomplete sibling listings.

Top-of-file `SKILL.md` frontmatter is excluded from behavioral scanning. Sibling content is inspected as stored file content.

### Output

**Single-family mode:** Prints a human-readable summary by default; `--json` prints the structured report. With `--output`, also saves a family JSON report, using a safe filename when needed.

**Batch mode:** Requires `--output`, writes one JSON report per successfully scanned family, and prints per-family progress/status rather than a stream of JSON reports. A failed family does not prevent later families from running, but the command returns a nonzero status if any fail. To avoid mixing research cohorts, batch mode rejects an output directory already containing `*.json` reports or `benchmarks.csv`; use a fresh directory for each run.

Every directed pair is labeled `primary` or `additional` in the JSON; reports also record the `edge_selection` setting. Pair counts and indicator findings are not interchangeable with independent historical events, since comparisons can share artifacts.

A **flagged pair** can result from rule/evidence changes or supported/uncertain indicators. A flagged pair is not necessarily a pair with a supported risk indicator. **`Pairs incomplete`** refers to sibling-data limitations; **evidence coverage** also reflects partial or unsupported extraction. Complete evidence coverage does not imply that every security risk can be detected.

With `--benchmark`, the scanner also writes `benchmarks.csv` with columns:

```text
family,seconds,peak_python_memory_mib,status
```

The peak-memory field is empty unless `--tracemalloc` is enabled. In single-family mode, `--benchmark` without `--output` saves the benchmark and family JSON under `./output`.

### Examples

**Single family:**

```powershell
uv run python -m gitskills.tools.scan_family busybox-on-windows --db C:/data/duckdb/agent_skills_release.db
```

**Single family with JSON report and benchmarking:**

```powershell
uv run python -m gitskills.tools.scan_family busybox-on-windows --db C:/data/duckdb/agent_skills_release.db --json --output output/single --benchmark
```

**Example `data/validation/families.txt`:**

```text
# Candidate families selected for the study
busybox-on-windows
```

**Batch pilot with benchmarking:**

```powershell
uv run python -m gitskills.tools.scan_family --input data/validation/families.txt --db C:/data/duckdb/agent_skills_release.db --output output/pilot --limit 2 --benchmark
```

**Complete input list using the default primary edges (no benchmarking):**

```powershell
uv run python -m gitskills.tools.scan_family --input data/validation/families.txt --db C:/data/duckdb/agent_skills_release.db --output output/scans
```

**All directionally supported relationships for research:**

```powershell
uv run python -m gitskills.tools.scan_family --input data/validation/families.txt --db C:/data/duckdb/agent_skills_release.db --output output/all-edges --edges all
```

Use separate output directories for `primary` and `all` runs. They describe different populations and should not be combined in one research summary.

### Interpretation

A positive rule delta means a rule matched more often in the derived content, but does not alone prove an expanded harmful capability. Evidence changes and risk indicators provide additional context. One-sided sibling records are distinguished from sibling content that is genuinely unavailable; a recorded sibling difference does not prove historical introduction or deletion.

Report frequency denominators using **all analyzed directed pairs**, not only flagged pairs. Treat ambiguous direction and incomplete coverage as explicit limitations. Findings are static observations for review, not evidence of execution, exploitability, or malicious intent.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | All requested family scans completed successfully. |
| `1` | One or more family scans, database accesses, or output writes failed. |
| `2` | Invalid command-line arguments, missing database configuration, invalid input list, or output-directory setup failed. |

---

## `summarize_scans`

### Purpose

`summarize_scans` is an **offline research reporting tool**. It reads the JSON files generated by `scan_family`, **not** the DuckDB database. It aggregates **every analyzed directed pair**, including unflagged pairs, to generate reproducible statistics, CSV tables, and a figure.

Manual validation sampling is **optional**. Selecting a sample does not restrict the full scan statistics or indicator-frequency denominators.

### Synopsis

```bash
summarize_scans REPORTS... --output DIR [OPTIONS]
```

### Arguments and Options

| Argument / option | Required | Default | Description |
|---|---:|---:|---|
| `REPORTS...` | Yes | — | One or more `scan_family` JSON files or directories containing those reports. Directory search uses `*.json` (nonrecursive). |
| `--output DIR` | Yes | — | Directory for research results. |
| `--per-stratum N` | No | Off | Additionally select up to `N` directed pairs per manual-review category (positive integer). Without this flag, no validation sample or annotation template is created. |
| `--seed N` | No | `580` | Seed for reproducible sample selection; relevant when `--per-stratum` is set. |
| `--annotations FILE` | No | Off | Adjudicated directed-review CSV for sample-level indicator metrics; requires `--per-stratum`. Use a **copy** of the generated template. |
| `--family-reports FILES...` | No | Off | Matching standard `analyze_family` JSON files for ambiguous/equivalent/no-related-edge validation sampling. |
| `--relationship-annotations FILE` | No | Off | Adjudicated relationship-review CSV; requires matching `--family-reports`. |
| `-h`, `--help` | No | — | Display full CLI help. |

### Input Requirements

Provide JSON reports generated by `scan_family`. The tool rejects duplicate family reports, inconsistent pair counts, and reports generated with different similarity policies, rule catalogs, scanner scopes, or edge-selection modes. Run separate summaries for `--edges primary` and `--edges all`. `benchmarks.csv` may coexist in the input directory; it is not read as a scan report.

Use only the selected family reports, not an entire directory containing extra families. A pair's direction must be supported to enter the directed-pair denominator. Direction-unknown/ambiguous edges are tracked separately as counts rather than treated as negative pairs.

### Output

All runs generate:

| File | Contents |
|---|---|
| `summary.json` | Cohort totals, supported-indicator frequencies, coverage statistics, direction/denominator notes, and optional sampling/annotation metrics. |
| `families.csv` | Counts by scanned family, including loaded/skipped artifacts and ambiguous-edge counts. |
| `directed_pairs.csv` | Every directed pair, including unflagged pairs, with indicator IDs, evidence-change counts, and coverage fields. |
| `edge_types.csv` | Counts of scanned, flagged, indicator-positive, and coverage-limited comparisons by primary versus additional edge type. |
| `indicator_frequency_by_edge_type.csv` | Risk-indicator counts and percentages calculated separately for primary and additional directed pairs. |
| `indicator_frequency.csv` | Counts and percentages for RI-001 through RI-011, using analyzed directed pairs as the denominator. |
| `direction_basis.csv` | Counts grouped by direction-evidence basis. |
| `indicator_frequency.svg` | Reproducible indicator-frequency chart. |

Only when `--per-stratum` is supplied, it also generates:

| File | Contents |
|---|---|
| `validation_sample.csv` | A deterministic, deduplicated sample selected across review categories (indicators, coverage limitations, uncertain cases, sibling changes, other flagged cases, and unflagged directed pairs). |
| `validation_annotations_template.csv` | The sample with blank manual-review fields; copy it before recording review judgments. |

The main summary includes an `edge_type_breakdown` as well as overall cohort totals, and `families.csv` identifies primary and additional counts per family. The `--per-stratum` sample size affects neither.

Each indicator is counted at most once per directed pair; pairs may support more than one indicator. Therefore, indicator percentages can overlap and need not sum to 100%. Review samples should **not** be interpreted as statistically representative prevalence estimates. Multiple directed comparisons may reuse the same artifact and are not independent historical events.

With `--annotations`, `summary.json` also reports reviewed-sample confusion counts and precision/recall by indicator, excluding unresolved categories. These are **review-sample measures**, not corpus-wide accuracy estimates.

### Examples

**Aggregate all scanned pairs without sampling:**

```powershell
uv run python -m gitskills.tools.summarize_scans output/scans --output output/research
```

**Create the same complete research statistics plus a manual-review sample:**

```powershell
uv run python -m gitskills.tools.summarize_scans output/scans --output output/review --per-stratum 5 --seed 580
```

Here, `--per-stratum 5` means **up to five pairs per validation category for human review**. It does **not** limit how many pairs were scanned or included in the research statistics.

**Recalculate reviewed-sample metrics after annotating a copy of the template:**

```powershell
uv run python -m gitskills.tools.summarize_scans output/scans --output output/review --per-stratum 5 --seed 580 --annotations data/validation/validation_annotations_reviewed.csv
```

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Research aggregation completed successfully. |
| `1` | Report loading, schema validation, cohort consistency, or output generation failed. |
| `2` | Invalid command-line arguments. |

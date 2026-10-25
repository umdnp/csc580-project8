# GitSkills Tools

This document describes the project command-line tools and the options most developers need to run them.

## Quick Reference

| Tool | Purpose |
|---|---|
| [`scan_diff`](#scan_diff) | Compare two skill files and report changes in security-sensitive behavior. |
| [`analyze_family`](#analyze_family) | Analyze similarity, clusters, chronology, and inferred relationships for one candidate family or a batch of families. |
| [`scan_family`](#scan_family) | Scan one candidate family or a list of families for security-sensitive evidence changes and risk indicators; optionally benchmark scans. |
| [`summarize_cohort`](#summarize_cohort) | Independently analyze selected families, reuse compatible scans, and generate audited research results and manual-validation samples. |
| [`family_picker`](#family_picker) | Interactively browse candidate families and run [`analyze_family`](#analyze_family). |

Use `<tool> --help` for the complete command-line help. When running directly from the source tree, the equivalent form is `python -m gitskills.tools.<tool>`.

**Console-script migration:** In your existing `pyproject.toml`, replace the old `[project.scripts]` entry `summarize_scans = "gitskills.tools.summarize_scans:main"` with `summarize_cohort = "gitskills.tools.summarize_cohort:main"`, then reinstall the editable package (for example `uv pip install -e .`). The project ZIP supplied for these changes did not contain `pyproject.toml`; it is therefore not overwritten by the archive. Until the entry point is updated, `uv run python -m gitskills.tools.summarize_cohort` works directly. There are no legacy CLI or reporting-module aliases; use `gitskills.tools.summarize_cohort` and `gitskills.reporting.cohort_summary` directly.

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

`analyze_family`, `scan_family`, and `summarize_cohort` use the GitSkills DuckDB database. Pass `--db PATH`, or set `GITSKILLS_DB` when `--db` is omitted.

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

`analyze_family` performs similarity and inferred-evolution analysis for one or more GitSkills **candidate families**. A candidate family contains qualifying artifacts with the same exact skill `name` in `artifact_groupings`.

The tool compares `SKILL.md` bodies, forms similarity clusters, identifies selected predecessor relationships when direction is supported, and preserves equivalent or direction-unknown relationships separately. It does **not** run the security scanner.

### Synopsis

```bash
analyze_family NAME [OPTIONS]
analyze_family --input FILE --output DIR [OPTIONS]
```

Supply either `NAME` or `--input FILE`, not both.

### Arguments

| Argument | Required | Description |
|---|---:|---|
| `NAME` | Single-family mode | Exact candidate-family skill name, such as `busybox-on-windows`. |
| `--input FILE` | Batch mode | UTF-8 file with one exact candidate-family name per line; blank lines and `#` comments are ignored. Requires `--output`. |
| `--limit N` | No | With `--input`, process only the first `N` family names (`N` must be positive). |

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
| `--verbose` | Off | Include the **complete pairwise similarity matrix** plus supplementary group, variant, and provenance diagnostics. For large families this can generate multiple gigabytes of JSON. |
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

The default JSON is the compact lineage report used by SkillTrace. It includes the summary, artifact source metadata, all clusters, primary/related/ambiguous edges and their evidence, chronology proxies, input counts, and skipped-artifact reasons. It **does not include** the exhaustive pairwise similarity matrix or derivable cluster/group counts. JSON remains indented and human-readable.

`--verbose` adds **all pairwise similarities** (including nonqualifying pairs), full family/cluster diagnostics, artifact groups, skill and bundle variants, and expanded provenance. The underlying similarity and lineage calculations are identical in both modes.

When `--output` is used, each report is saved under a Windows-safe filename derived from the exact family name. Single-family mode prints the human-readable report unless `--json` is also used.

Batch mode writes one JSON report per family and prints per-family progress instead of full reports, even with `--json`. As with `scan_family`, batch output must use a fresh directory without existing JSON reports or benchmark files, and duplicate input names are rejected. Individual failures are reported without preventing later families from running; the command exits with status `1` if any family fails.

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

**Analyze a pinned family list:**

```bash
analyze_family --input data/validation/families.txt --output output/family-reports
```

**Analyze only the first five families:**

```bash
analyze_family --input data/validation/families.txt --limit 5 --output output/family-pilot
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
| `2` | Database path, batch-input validation, command-line, or output-directory setup failed. |

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

## `summarize_cohort`

### Purpose

`summarize_cohort` is the **independent research pipeline** for one candidate family or a selected cohort of families. It loads selected names directly from the prepared DuckDB database, reuses shared family-analysis and security-scanner logic, and produces reproducible findings, validation candidates, and source/audit records. It **does not require** reports created by `analyze_family`, `scan_family`, or SkillTrace.

It reports per-family processing progress and may reuse compatible scans from `results/.scans/` to avoid repeating the security scan. When needed, it calculates complete family similarities **in memory**, examines all eligible relationship comparisons for manual-review selection, and releases each family's analysis before proceeding. No temporary verbose family JSON is written. `scan_diff`, `analyze_family`, and `scan_family` remain independent command-line tools.

A **candidate family** consists of same-name artifacts (`artifact_groupings.name`); a **cluster** groups artifacts with related contents within a family; a **cohort** is the selected **one or more families** studied together. `--per-stratum` is applied across the whole cohort, not separately to each family.

### Synopsis

```bash
summarize_cohort NAME --db PATH --output results [OPTIONS]
summarize_cohort --input FILE --db PATH --output results [OPTIONS]
```

`--db` defaults to `$GITSKILLS_DB` when not given. Supply exactly one of `NAME` and `--input FILE`. The notebook uses the same Python API, `gitskills.pipelines.cohort.summarize_cohort(...)`.

### Options

| Option | Default | Description |
|---|---|---|
| `NAME` | — | Exact name of one candidate family, for example `code-review`. |
| `--input FILE` | Off | UTF-8 list of exact family names; blank lines and `#` comments are ignored. Duplicate names are rejected. |
| `--limit N` | Off | With `--input`, process the first `N` names. |
| `--db PATH` | `$GITSKILLS_DB` | Prepared DuckDB database. |
| `--output DIR` | Required | Root of the results directory (for example `--output results`). |
| `--edges {primary,all}` | `all` | Select only inferred predecessor edges (`primary`) or all directionally supported edges (`all`). Must match any reusable scans. |
| `--rescan` | Off | **Always** regenerate scans for all selected families, even if their cache is current. Does **not** override manual-review protections. |
| `--per-stratum N` | `5` | Select up to `N` pairs per directed or relationship-review stratum for manual inspection **across the cohort**. Does not limit the analysis or reported denominators. |
| `--no-sampling` | Off | Skip manual validation sampling; compatible cached scans can then be summarized without rerunning family similarity analysis. |
| `--seed N` | `580` | Deterministic seed for validation selection. |
| `--annotations FILE` | Off | Completed/adjudicated directed-pair review CSV, separate from the generated template. |
| `--relationship-annotations FILE` | Off | Completed/adjudicated relationship review CSV, separate from the generated template. |
| `--approval-reference TEXT` | Off | Optional source of cohort selection approval for the manifest. |
| `--shingle-size N` | `5` | Token shingle width. |
| `--min-containment FLOAT` | `0.80` | Minimum directional containment. |
| `--min-jaccard FLOAT` | `0.30` | Minimum Jaccard similarity. |
| `--min-shared-shingles N` | `5` | Minimum shared shingles. |
| `--direction-margin FLOAT` | `0.10` | Directional-containment margin. |
| `-h`, `--help` | — | Print complete help. |

Thresholds and security scanning are identical to those used by `analyze_family` and `scan_family` for the same configurations. `summarize_cohort` defaults to `--edges all`, whereas the standalone `scan_family` defaults to `primary`; set both explicitly when sharing scans.

### Reusable scan cache

`results/.scans/` contains one plain JSON scan report per family and a separate **`.scan_manifest.json`** for cache bookkeeping. The scan reports themselves retain their scientific evidence and source references without extra cache-specific metadata.

By default, the summarizer:

1. Checks the cached report's family name, input artifacts/skipped records, similarity policy, edge selection, active rules, scanner scope, and internal pair counts.
2. Checks the separate cache manifest's source fingerprint, database identity/size/modification time, implementation fingerprint, and scan-file checksum when a manifest entry exists.
3. Reuses a compatible scan, or regenerates a missing, changed, malformed, or incompatible scan.
4. Adds compatible scans previously generated by an independent `scan_family` invocation to the manifest; no separate `scan_family` cache format is required.
5. Writes each completed family scan and the manifest with atomic file replacements, so successful cache entries survive a later family failing.

`--rescan` unconditionally regenerates scans. A cache hit can skip *security scanning*, but when manual relationship review is enabled, the family similarity analyzer must still run to evaluate nonqualifying pairs not present in scan JSON.

A standalone scan can populate the cache, for example:

```bash
scan_family code-review --db "$GITSKILLS_DB" --edges all --output results/.scans
summarize_cohort code-review --db "$GITSKILLS_DB" --edges all --output results
```

The directory remains flat. In batch mode, `scan_family --input` still requires a fresh output directory without existing JSON reports; that CLI behavior is unchanged.

### Output structure

```text
results/
├── .scans/                          # Ignorable, reusable intermediate scan cache
│   ├── .scan_manifest.json
│   ├── code-review.json
│   └── skill-creator.json
├── manual-review/
│   ├── directed-pairs/
│   │   ├── validation_sample.csv
│   │   └── validation_annotations_template.csv
│   ├── relationship-pairs/
│   │   ├── relationship_validation_sample.csv
│   │   └── relationship_validation_annotations_template.csv
│   └── adjudicated/                # User-managed reviewed copies; never silently overwritten
├── review/
│   ├── summary.json
│   ├── families.csv
│   ├── directed_pairs.csv
│   ├── edge_types.csv
│   ├── indicator_frequency.csv
│   ├── indicator_frequency_by_edge_type.csv
│   └── direction_basis.csv
├── figures/
│   └── indicator_frequency.svg
├── audit/
│   ├── processing_summary.csv
│   └── skipped_artifacts.csv
├── sample_manifest.json
└── execution_summary.json
```

Generated directed and relationship validation samples are stratified research-review aids, **not** the populations used to calculate indicator frequencies. All eligible directed pairs remain in `directed_pairs.csv` and the full statistics. Directed-pair validation examines scanner findings, direction, and coverage; relationship-pair validation examines ambiguous, equivalent, and **no-related-edge** decisions.

Relationships are sampled reproducibly via a **bounded reservoir per stratum** so a large family does not require storing every negative artifact-pair candidate. The strata, source population, thresholds, and cohort-wide sample sizes are preserved. Because the earlier implementation used a full-list shuffle, specific selected IDs for the same seed **can differ** when migrating to this method; existing adjudicated samples are protected from silent changes by the sample manifest.

`sample_manifest.json` records selected families, source identities and coverage, policies, rule configuration, implementation fingerprint, dataset source, review seed, and approval reference. `audit/` records loaded/skipped artifacts and per-family counts. Manual-review files under `manual-review/adjudicated/` are reviewer-owned; the summarizer rejects attempts to silently change an adjudicated sample or replace a differing cached scan.

To exclude only intermediate scans from Git, add:

```gitignore
results/.scans/
```

For notebook-specific runs nested under `notebooks/`, use a matching pattern such as `**/results/.scans/` in `.gitignore`.

### Examples

**One family, using the cache where valid:**

```bash
summarize_cohort code-review --db "$GITSKILLS_DB" --output results --per-stratum 5 --seed 580 --edges all
```

**A reproducible pinned cohort:**

```bash
summarize_cohort --input data/validation/families.txt --db "$GITSKILLS_DB" --output results --edges all
```

**Force a full security rescan:**

```bash
summarize_cohort --input data/validation/families.txt --output results --rescan
```

**Produce population statistics without creating manual-review samples:**

```bash
summarize_cohort code-review --output results --no-sampling
```

**Recalculate metrics after final independent review and adjudication:**

```bash
summarize_cohort --input data/validation/families.txt --output results \
  --annotations results/manual-review/adjudicated/directed.csv \
  --relationship-annotations results/manual-review/adjudicated/relationships.csv
```

### Python API

```python
from pathlib import Path
from gitskills.pipelines.cohort import summarize_cohort

execution = summarize_cohort(
    ["code-review", "skill-creator"],
    database=Path("C:/data/duckdb/agent_skills_release.db"),
    results=Path("results"),
    edges="all",
    per_stratum=5,
    seed=580,
    rescan=False,
)
```

For an independent lineage visualization, run `analyze_family NAME --output apps/skilltrace/reports`. SkillTrace reads those **compact** lineage reports and lazily fetches source detail from DuckDB. Cohort summarization neither reads nor requires them.

### Exit Status

| Status | Meaning |
|---:|---|
| `0` | Cohort completed and research outputs were generated. |
| `1` | Family loading, scanning, cache, consistency checks, or writing failed. |
| `2` | Invalid command-line options, family list, or missing database configuration. |

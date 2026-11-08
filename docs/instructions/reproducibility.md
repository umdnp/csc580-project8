# End-to-end reproduction check

This records the equivalent isolated check for [story #213](https://github.com/umdnp/csc580-project8/issues/213), performed on November 8, 2026. It distinguishes reproducing the historical report from running the same cohort under updated code.

## Scope and result

| Acceptance check | Evidence |
|---|---|
| Setup and execution instructions | This document gives locked installation, a versioned dataset download/checksum, native PowerShell SQL preparation, baseline configuration, output locations, and report commands. |
| Isolated installation and pipeline | Detached committed-source worktrees outside OneDrive, fresh virtual environments, and an initially empty `uv` download cache; no active/global Python packages or scan caches were used. Both revisions installed successfully with `uv sync --locked`. |
| Historical primary results | The historical scanner reproduced the committed summary, all six research CSV tables, and both review samples exactly as parsed values. All four SVG figures were regenerated with matching numerical labels. |
| Report sources | HTML, Word, LaTeX source, and the official 28-page PDF built from committed report sources. The PDF has 13 main-content pages (physical pages 2-14), references on page 15, and Appendices A-F on pages 16-28. |
| Remaining dependencies and limits | The large source download was checksum-verified, not downloaded again; the full DuckDB import was not repeated. A pre-existing prepared snapshot was read-only, and all three preparation SQL scripts were tested on a fresh SQLite fixture. See the limits below. |

This verifies the **provisional Sprint 2 baseline**, not completion of human validation, population prevalence, or optional Sprint 3 experiments.

## Pinned inputs and environments

- Report-source/current-code checkout: `0baeb0fff3e3e8598c5754cdf5637a0799142d8e`.
- Historical scanner checkout: `e1d6b773956c87877c51c8b0faa9ebb39fffdaf3`, as recorded in the [saved manifest](../../notebooks/end_to_end_pipeline/sprint2/results/sample_manifest.json).
- Family input: the committed [30-family list](../../notebooks/end_to_end_pipeline/sprint2/samples/families.txt). Its checked file SHA-256 was `4562ff59808f2b1535d09fd242d8f9b8522885f15e99b1bf33f59c1751898763`; line-ending conversion can change this file hash without changing parsed names.
- Source release: GitSkills **1.0.0**, DOI `10.5281/zenodo.21875637`, SQLite size **44,388,249,600 bytes**, published MD5 `b058631fb1926efac6e82a4706646742`.
- Windows x64, Python **3.12.3**, current locked DuckDB **1.5.6**, historical locked DuckDB **2.0.0**, and DuckDB CLI **1.5.6**. The original manifest recorded Python **3.14.7**; reproducing the numeric results did not require that interpreter.
- Prepared database used in this check: **39,941,320,704 bytes**, rather than the historical manifest's **40,123,510,784 bytes**. All 1,151 cohort artifact IDs, repository/path identities, primary hashes, sibling counts, and sibling hashes matched; group IDs differed after preparation changes. Database file size alone is not an input identity check.
- The four imported table counts matched the public release: `artifacts` **3,797,117**; `artifact_siblings` **7,264,865**; `repos` **282,200**; `mining_runs` **7**.

The dataset URL returned HTTP 200 with the published byte length. The existing SQLite file's computed MD5 matched the public record. No credentials were required. MD5 is used only to check agreement with the release record.

## Equivalent isolated installation

Install Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and the [DuckDB CLI](https://duckdb.org/docs/installation/) before running the PowerShell commands below. Python 3.12 must be available or downloadable by `uv`. Clone the project if needed:

```powershell
git clone https://github.com/umdnp/csc580-project8.git
Set-Location csc580-project8
```

The check used `git worktree add --detach` for each revision, separate environments outside the synced repository, `UV_LINK_MODE=copy`, and a new `UV_CACHE_DIR`. The current checkout downloaded and installed all locked dependencies and built the project from its committed `pyproject.toml`. The historical install used its own lockfile; verified downloads from the first check were reused, but installed packages and the environment were separate.

An equivalent new-user check, from the main checkout in PowerShell, is:

```powershell
git worktree add --detach ..\csc580-reproduction 0baeb0fff3e3e8598c5754cdf5637a0799142d8e
Set-Location ..\csc580-reproduction
$env:UV_PROJECT_ENVIRONMENT = "$env:LOCALAPPDATA\uv\environments\csc580-reproduction"
$env:UV_CACHE_DIR = "$env:LOCALAPPDATA\uv\cache-csc580-reproduction"
$env:UV_LINK_MODE = "copy"
uv sync --locked --python 3.12
```

Choose new worktree/environment/cache paths when repeating a clean check. `uv` may download an interpreter if the requested one is not installed. The checked installation instead specified the absolute installed Python 3.12.3 executable.

The isolated focused validation command was:

```powershell
uv run --locked python -m pytest `
  tests\test_cohort_primary_cache.py `
  tests\pytests\test_cohort_cache.py `
  tests\pytests\test_end_to_end_pipeline.py `
  tests\pytests\test_research_reporting.py `
  tests\pytests\test_pipeline_notebook.py -q
```

Result: **53 passed**. This includes real loaders/scanning on temporary databases and execution of the production notebook on constructed inputs, with and without missing sibling content. It is not a claim that the entire repository test suite was run.

## Obtain and prepare the external database

Allow space for the 44.4 GB SQLite download, approximately 40 GB of prepared DuckDB data, and additional import temporary files and outputs. Internet access is required for dependencies, the dataset, and DuckDB's SQLite extension. No dataset credentials are required. These files are local inputs, not PR deliverables.

From the pinned current-code checkout in PowerShell, download GitSkills 1.0.0 and verify its published checksum:

```powershell
New-Item -ItemType Directory -Force C:\data\sqlite, C:\data\duckdb
if (Test-Path C:\data\sqlite\agent_skills_release.db) { throw "Choose a new download path or verify the existing SQLite file instead" }
curl.exe --fail --location --output C:\data\sqlite\agent_skills_release.db "https://zenodo.org/records/21875637/files/agent_skills_release.db?download=1"
if ($LASTEXITCODE -ne 0) { throw "Dataset download failed" }
$checksum = (Get-FileHash C:\data\sqlite\agent_skills_release.db -Algorithm MD5).Hash
if ($checksum -ne "B058631FB1926EFAC6E82A4706646742") { throw "Dataset checksum mismatch" }
```

The downloaded file is SQLite, not DuckDB. Use a new output path and execute all three committed SQL scripts in order:

```powershell
if (Test-Path C:\data\duckdb\agent_skills_release.db) { throw "Choose a new DuckDB output path before importing" }
$env:GITSKILLS_SQLITE_DB = "C:\data\sqlite\agent_skills_release.db"
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\create_gitskills_duckdb.sql
if ($LASTEXITCODE -ne 0) { throw "SQLite import failed; do not continue with incomplete output" }
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\create_analysis_tables.sql
if ($LASTEXITCODE -ne 0) { throw "Analysis table creation failed" }
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\update_artifact_groupings.sql
if ($LASTEXITCODE -ne 0) { throw "Artifact grouping update failed" }
$env:GITSKILLS_DB = "C:\data\duckdb\agent_skills_release.db"
uv run --locked python -c "import os, duckdb; c = duckdb.connect(os.environ['GITSKILLS_DB'], read_only=True); print(c.execute('SHOW TABLES').fetchall()); c.close()"
if ($LASTEXITCODE -ne 0) { throw "Prepared database access check failed" }
```

Require matching imported/source counts, zero unresolved IDs, and the tables `artifacts`, `artifact_groupings`, `artifact_siblings`, and `repos`. The grouping scripts retain valid frontmatter, bodies longer than 50 characters, non-NULL content/name/description, and exact names occurring at least twice; they also compute available sibling fingerprints. The Sprint 1 sample-view script is not required for this baseline.

Set `GITSKILLS_DB` in every new terminal before running analysis. Close database-writing sessions first. Keep virtual environments outside OneDrive and reapply `UV_PROJECT_ENVIRONMENT` and `UV_LINK_MODE` in each terminal. The native PowerShell commands above do not depend on Git Bash's `/c/...` path conventions.

## Reproduce the historical numerical baseline

The historical revision predates the current location of the committed family list. Pass that list from the main checkout; do not attempt to generate a random substitute.

From the main checkout, after preparing and configuring the external database:

```powershell
$source = (Get-Location).Path
$previousEnvironment = $env:UV_PROJECT_ENVIRONMENT
$env:GITSKILLS_DB = "C:\data\duckdb\agent_skills_release.db"
git worktree add --detach ..\csc580-baseline e1d6b773956c87877c51c8b0faa9ebb39fffdaf3
Set-Location ..\csc580-baseline
$env:UV_PROJECT_ENVIRONMENT = "$env:LOCALAPPDATA\uv\environments\csc580-baseline"
$env:UV_LINK_MODE = "copy"
uv sync --locked --python 3.12
uv run --locked python -m gitskills.tools.summarize_cohort `
  --input "$source\notebooks\end_to_end_pipeline\sprint2\samples\families.txt" `
  --output "$source\output\baseline-e1d6b77" `
  --edges all --rescan --per-stratum 5 --seed 580 `
  --shingle-size 5 --min-containment 0.8 --min-jaccard 0.3 `
  --min-shared-shingles 5 --direction-margin 0.1
Set-Location $source
if ($previousEnvironment) {
  $env:UV_PROJECT_ENVIRONMENT = $previousEnvironment
} else {
  Remove-Item Env:\UV_PROJECT_ENVIRONMENT
}
```

Use a new output directory and do not pass annotation files: independent review remains pending. The historical implementation fingerprint matched the saved value exactly:
`99a121b091b8b9446291af17db8fd2b56e577a7dd5fde0ebcb904a4a37fd308e`.

To run the same configuration under the pinned current code, return to the `0baeb0f` checkout and its environment:

```powershell
uv run --locked python -m gitskills.tools.summarize_cohort `
  --input notebooks\end_to_end_pipeline\sprint2\samples\families.txt `
  --output output\baseline-0baeb0f `
  --edges all --rescan --per-stratum 5 --seed 580 `
  --shingle-size 5 --min-containment 0.8 --min-jaccard 0.3 `
  --min-shared-shingles 5 --direction-margin 0.1
```

Each output directory contains `sample_manifest.json`, `review\summary.json`, `review\tables\` (six CSV tables), `figures\`, and `manual-review\` (directed and relationship samples). Inspect regenerated outputs there rather than replacing committed results. Random sampling and benchmarks are optional experiments, not prerequisites for this fixed-family baseline.

### Numerical comparison

| Measure | Committed / historical rerun | Current-code rerun |
|---|---:|---:|
| Families | 30 | 30 |
| Artifacts loaded / skipped | 1,151 / 0 | 1,151 / 0 |
| Directed comparisons | 3,997 | 3,997 |
| Primary / additional comparisons | 468 / 3,529 | 468 / 3,529 |
| Flagged comparisons | 2,241 | 2,241 |
| Pairs with supported indicators | 588 | 577 |
| Families with supported indicators | 19 | 18 |
| Supported findings | 5,551 | 4,096 |
| Pairs with changed evidence | 1,998 | 1,998 |
| Pairs with changed sibling evidence | 1,199 | 1,199 |
| Pairs with incomplete evidence coverage | 206 | 206 |
| Ambiguous relationships excluded from directed scanning | 2,244 | 2,244 |

Historical `review/summary.json` matched every field of the committed summary. CSV comparison used parsed rows and fields, not rounded plot rates:

- `directed_pairs.csv`: 3,997 rows, exact match.
- `families.csv`: 30 rows, exact match.
- `direction_basis.csv`: five rows, exact match.
- `edge_types.csv`: two rows, exact match.
- `indicator_frequency.csv`: 11 rows, exact match.
- `indicator_frequency_by_edge_type.csv`: 22 rows, exact match.
- Directed review sample: 30 rows, exact match.
- Relationship review sample: 15 rows, exact match.

Current-code differences are not random timing variation. The intervening commits change extraction and RI interpretation, including staged download-and-execute detection, package-install equivalence, package source comparisons, and credential handling. Keep current results separate; do not silently relabel the historical report as a current-code analysis.

### Figure regeneration

The CLI produces `indicator_frequency.svg`. For the other three figures, use the current committed notebook's plot cells on the historical tables:

1. Open the notebook with the **current** project environment.
2. Run imports; choose `SPRINT = 2`, `EDGES = "all"`, seed `580`, and the saved default policy.
3. Set `RESULT_DIR = PROJECT_ROOT / "output" / "baseline-e1d6b77"` and `SCAN_CACHE_DIR = RESULT_DIR / ".scans"`.
4. Run the summary, family-rate, indicator-frequency, and edge-type results cells, **skipping the analysis execution cell**. Do not rescan historical outputs with the current implementation.

The isolated check executed those same trusted notebook source cells noninteractively with Matplotlib's `Agg` backend against each rerun's tables. It did not execute dataset content. All four historical figures had identical numeric/category labels to the committed figures. The frequency SVG also matched after XML normalization. The three Matplotlib SVGs were not byte/geometry-identical across the plotting environment; timestamps, generated IDs, layout, and font rendering are not numerical research results.

## Report build and inspection

In the current-code isolated checkout, these commands succeeded:

```powershell
uv run --locked python bin\setup_report_tools.py
uv run --locked python bin\build_report.py --format html
uv run --locked python bin\build_report.py --format docx
uv run --locked python bin\build_report.py --format latex
uv run --locked python bin\build_report.py --format html --cached-only
uv run --locked python bin\build_report.py --format pdf
```

The portable setup downloaded and checksum-verified the committed toolchain's Pandoc **3.12.1**, PlantUML **1.2026.8**, and Java JRE. Normal rendering and the cached-diagram build both succeeded. HTML had no unresolved citations or external image sources; all three embedded diagrams loaded in the browser. Word contained three embedded media entries. The report contained its results tables, bibliography, conclusion, and all six appendices.

PDF initially failed because XeLaTeX was absent. With permission, user-level **MiKTeX 25.12** was installed:

```powershell
winget install --id MiKTeX.MiKTeX --exact --version 25.12 --scope user `
  --source winget --silent --accept-source-agreements `
  --accept-package-agreements --disable-interactivity
$tex = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"
$env:PATH = "$tex;$env:PATH"
& "$tex\initexmf.exe" "--set-config-value=[MPM]AutoInstall=1"
& "$tex\mpm.exe" --update-db
uv run --locked python bin\build_report.py --format pdf
```

The package database update flag is deprecated in this MiKTeX release but succeeded. MiKTeX fetched required LaTeX packages automatically; internet access is therefore also required for initial TeX package installation. XeTeX reported version **4.16**. These packages are not fully pinned by the project. The build emitted nonfatal MiKTeX reminders to check distribution updates.

The rebuilt PDF had **28 nonempty Letter-size pages**, a bibliography, three diagrams, readable main-result tables, and readable preparation code/diagram pages. It was inspected with MiKTeX's `pdfinfo`, `pdftotext`, and page rendering utilities. The prior committed PDF lagged the Markdown sources' pending draft-annotation status; the regenerated PDF reflects those committed sources. PDF binary equality and identical text line wrapping are not promised.

## External requirements and reproducibility limits

- **Large external input:** the SQLite and prepared DuckDB files are not bundled. The check validated the public release, checksum, imported row counts, and selected artifact identities, but did **not** redo the full 44.4 GB import. Import temporary space can exceed final database size.
- **Preparation equivalent:** all three current SQL scripts were executed in order against a newly created SQLite fixture, using the documented native CLI flags. Imported counts matched, unresolved IDs were zero, and two valid family members received normalized groupings and sibling fingerprints. Full-scale resource use and a cache-free download of the SQLite extension were not validated.
- **Historical snapshot:** its prepared database checksum was not recorded/bundled. The available snapshot has different group IDs and size, even though the cohort content identities and historical numerical outcomes agree. Surrogate IDs created by unordered `row_number()` during a fresh import can differ; compare repository/path and content hashes as well as counts.
- **Environment metadata:** absolute paths, database timestamps/sizes, scan-cache filenames, Python versions, and manifest/sample file checksums affected by line endings can vary. Preserve new manifests; never hide these differences by copying historical metadata.
- **Rendering and timing:** SVG/PDF bytes, layout/font metrics, and timings can vary. Fixed seeds control review selection given stable input/code ordering, not package versions or filesystem metadata.
- **Report synchronization:** report tables are committed Markdown, not live links to newly generated CSVs. Building the report verifies its sources; it does not update research claims to the current scanner. Reconcile results explicitly before changing the reported baseline.
- **Optional work:** random Sprint 3 samples, primary-only comparisons, and timing benchmarks are separate experiments, not covered by this reproduction check. Their locally generated outputs were neither adopted nor overwritten.
- **Human validation:** draft annotation proposals remain pending independent review/adjudication. Reproducing automated counts does not establish scanner precision/recall, malicious intent, or historical ancestry.

No baseline results, annotation drafts, or user-modified notebooks were overwritten during the check. Regenerated analysis outputs and the rebuilt report PDF are local verification outputs, not included in this documentation-only change.

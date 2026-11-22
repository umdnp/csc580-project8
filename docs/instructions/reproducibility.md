# End-to-End Reproducibility

This guide explains how to reproduce the **three Sprint 3 research trials**, inspect their outputs, and build the research report. It also preserves the separate, independently performed **Sprint 2 baseline reproduction check** from November 8, 2026 ([issue #213](https://github.com/umdnp/csc580-project8/issues/213)).

For the final Sprint 3 workflow, use this guide and the [current notebook README](../../notebooks/end_to_end_pipeline/README.md); the separate [October 5 pipeline walkthrough](pipeline-walkthrough.md) records a historical implementation snapshot.

**Verification status:** The team **completed clean-environment reproduction of all three Sprint 3 trials**. This was a separate check from the November 8 Sprint 2 baseline verification and the adjudication-only summary update. The original Sprint 3 check was not documented at the time; its completion is recorded in Section 3.6 below.

## 1. Requirements and source version

Use Git, [uv](https://docs.astral.sh/uv/), Python 3.12 or newer, the [DuckDB CLI](https://duckdb.org/docs/installation/), and JupyterLab. The source dataset is large: allow space for the **44.4 GB SQLite download**, approximately **40 GB for DuckDB**, and additional temporary files. Do not commit the downloaded databases.

Clone the repository and install the locked Python dependencies:

```powershell
git clone https://github.com/umdnp/csc580-project8.git
Set-Location csc580-project8
uv sync --locked --python 3.12
```

For a stable reproduction, check out the intended **Sprint 3 tag or commit** before running the notebook. Do not assume that a later `main` branch will reproduce unchanged historical figures: subsequent scanner fixes may change the reported indicators.

The saved trial manifests record these original code revisions:

| Trial | Recorded code revision | Recorded Python |
| --- | --- | --- |
| 1 | `ae69732ed8988ad7066ff351848f7d2e8ad311a1` | 3.14.7 |
| 2 | `ae69732ed8988ad7066ff351848f7d2e8ad311a1` | 3.14.7 |
| 3 | `66ea452f6fb9d596905a62f9b0fd4546b71927b7` | 3.14.7 |

The three manifests record the same scanner implementation and cohort fingerprints, despite the different Trial 3 Git revision. Exact historical reproduction should respect the recorded inputs, revisions, and rules. Running the three trials with one newer repository version is a **current-code rerun** and may not exactly match the frozen published numbers. Work in a separate clone or detached worktree when checking historical outputs so that generated files do not overwrite the committed evidence.

**Historical-checkout detail:** The original commits above do **not** contain the subsequently committed `sprint3/samples1/`, `samples2/`, or `samples3/` family lists. To rerun an original code revision, first copy the saved `families.txt` (and, where needed, the corresponding `sampling_report.json`) from today's repository into the matching `sprint3/samplesX/` folders of that checkout. Preserve the same lists rather than allowing the older checkout to generate replacements. Trial 1 and Trial 2 use the first revision in the table; Trial 3 uses the second. The simpler three-run procedure in Section 3 assumes the saved lists are already present in your checkout.

## 2. Prepare the GitSkills database

The [GitSkills 1.0.0 dataset](https://zenodo.org/records/21875637) is distributed as **SQLite**; the project builds a separate **DuckDB** database for analysis. The published SQLite file is **44,388,249,600 bytes**, with MD5 checksum `b058631fb1926efac6e82a4706646742` (the checksum is used for release-identity verification, not as a security guarantee).

The following example uses **Windows PowerShell** and `C:\data`. On WSL or other systems, adjust the file paths and shell commands as described in [data/README.md](../../data/README.md).

Download the original dataset and check its published checksum:

```powershell
New-Item -ItemType Directory -Force C:\data\sqlite, C:\data\duckdb
curl.exe --fail --location --output C:\data\sqlite\agent_skills_release.db "https://zenodo.org/records/21875637/files/agent_skills_release.db?download=1"
if ($LASTEXITCODE -ne 0) { throw "Dataset download failed" }
$checksum = (Get-FileHash C:\data\sqlite\agent_skills_release.db -Algorithm MD5).Hash
if ($checksum -ne "B058631FB1926EFAC6E82A4706646742") { throw "Dataset checksum mismatch" }
```

If the downloaded file already exists, verify that file instead of downloading over it. Create the DuckDB database and its derived analysis tables **in this order**, using a new output path:

```powershell
$env:GITSKILLS_SQLITE_DB = "C:\data\sqlite\agent_skills_release.db"
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\create_gitskills_duckdb.sql
if ($LASTEXITCODE -ne 0) { throw "SQLite import failed" }
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\create_analysis_tables.sql
if ($LASTEXITCODE -ne 0) { throw "Analysis table creation failed" }
duckdb -no-init -bail C:\data\duckdb\agent_skills_release.db -f sql\update_artifact_groupings.sql
if ($LASTEXITCODE -ne 0) { throw "Artifact grouping update failed" }
```

**Do not run the import against an existing DuckDB file** unless intentionally rebuilding it from scratch. Set the database path in the terminal that will launch Jupyter:

```powershell
$env:GITSKILLS_DB = "C:\data\duckdb\agent_skills_release.db"
uv run --locked python -c "import os, duckdb; c = duckdb.connect(os.environ['GITSKILLS_DB'], read_only=True); print(c.execute('SHOW TABLES').fetchall()); c.close()"
```

The prepared database must contain `artifacts`, `artifact_groupings`, `artifact_siblings`, and `repos`. Source-release row counts are 3,797,117 `artifacts`, 7,264,865 `artifact_siblings`, 282,200 `repos`, and seven `mining_runs`. Preparation changes can alter derived IDs; compare underlying repository/path identities and content hashes, not surrogate IDs alone. The Sprint 1 sample-view script is **not required** for these trials.

## 3. Run the three Sprint 3 trials

**Run the same notebook three separate times, changing only `SAMPLE` from 1 to 2 to 3.** All three runs use `SPRINT = 3`. Each trial has its own saved list of 100 families and its own results directory.

From the repository root, with `GITSKILLS_DB` set as above, start JupyterLab:

```powershell
uv run --with jupyterlab jupyter lab
```

Open [`notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb`](../../notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb). Select the project's Python environment as the notebook kernel.

### 3.1 Confirm the notebook settings

In the **Set Variables** cell, use:

```python
SPRINT = 3
SAMPLE = 1  # Trial 1; change to 2 and then 3 for later runs
```

In the subsequent family-selection cell, retain the saved-study settings:

```python
POLICY = SimilarityPolicy()
EDGES = "primary"
PER_STRATUM = 5
SEED = 580
FAMILY_SAMPLE_SIZE = 100
FAMILY_SEED = SEED * 10 + SAMPLE  # 5801, 5802, 5803
APPROVAL_REFERENCE = None       # Matches the provisional saved manifests
```

`PER_STRATUM = 5` applies to **manual-review sampling**, not the five family-size groups. The 100-family selection uses five size strata with a **20/55/20/4/1** allocation. The same scanner rules and similarity policy are used across trials. `EDGES = "primary"` includes selected directed predecessor comparisons; ambiguous relationships are not treated as directed changes.

### 3.2 Execute each trial separately

| Run | Set `SPRINT` | Set `SAMPLE` | Family selection seed | Saved family list | Results directory |
| --- | ---: | ---: | ---: | --- | --- |
| Trial 1 | `3` | `1` | `5801` | `sprint3/samples1/families.txt` | `sprint3/results1/` |
| Trial 2 | `3` | `2` | `5802` | `sprint3/samples2/families.txt` | `sprint3/results2/` |
| Trial 3 | `3` | `3` | `5803` | `sprint3/samples3/families.txt` | `sprint3/results3/` |

All paths in this table are relative to `notebooks/end_to_end_pipeline/`.

1. **Trial 1:** Set `SPRINT = 3` and `SAMPLE = 1`. Restart the kernel and run the notebook cells in order **through “Findings for manual review.”** Inspect the outputs in `sprint3/results1/`.
2. **Trial 2:** Change `SAMPLE = 2` and leave `SPRINT = 3`. Restart the kernel and rerun the same notebook cells. Inspect `sprint3/results2/`.
3. **Trial 3:** Change `SAMPLE = 3` and leave `SPRINT = 3`. Restart the kernel and rerun the same notebook cells. Inspect `sprint3/results3/`.

**Important:** Restart and rerun the notebook from the beginning for each sample. Changing `SAMPLE` without rerunning the configuration and analysis cells does not run a different trial. The final **“Independent review and adjudication”** cell is a separate validation-summary step, already completed for all three published trials. It is not part of an automated scan rerun; supply only finalized, matching adjudication files when recalculating validation metrics.

Each saved `samplesX/families.txt` is already committed. The notebook **reuses an existing file** rather than generating a different random sample. If a file is missing, it generates a replacement sample with `family_picker` and saves `sampling_report.json`; later samples require and exclude earlier family lists. A newly generated list is not automatically identical to the committed sample if the database, candidate pool, policy, code, or selection order has changed. For reproduction of the published cohort, **retain the committed family lists**.

The notebook reuses compatible reports in its shared `.scans/` cache; incompatible entries are rebuilt. It is unnecessary to run `analyze_family`, `scan_family`, or `scan_diff` separately before the notebook.

### 3.3 Locate the generated outputs

For each `sprint3/resultsX/` (X is 1, 2, or 3):

```text
resultsX/
├── sample_manifest.json              # Dataset, code/rule identity, settings, family selection
├── execution_summary.json            # Automated execution status and coverage
├── audit/                            # Processing and skipped-artifact records
├── review/
│   ├── summary.json                  # Trial-level numerical results
│   ├── families.csv
│   ├── directed_pairs.csv
│   ├── edge_types.csv
│   ├── direction_basis.csv
│   ├── indicator_frequency.csv
│   └── indicator_frequency_by_edge_type.csv
├── figures/                          # Four generated SVG figures
└── manual-review/                    # Directed and relationship review samples/templates
```

The four notebook-generated figures are `pair_outcomes.svg`, `indicators_by_family.svg`, `indicators_by_edge_type.svg`, and `indicator_frequency.svg`. The report's combined Sprint 3 figures are maintained separately under [`report/figures/`](../../report/figures/) with their [generation script](../../report/figures/generate_sprint3_figures.py).

### 3.4 Compare with the saved Sprint 3 results

Check each regenerated `review/summary.json`, `execution_summary.json`, and `sample_manifest.json` against the corresponding committed versions. The saved automated results are:

| Measure | Trial 1 | Trial 2 | Trial 3 | Combined |
| --- | ---: | ---: | ---: | ---: |
| Families | 100 | 100 | 100 | **300** |
| Artifacts loaded | 2,275 | 2,067 | 2,228 | **6,570** |
| Primary directed comparisons | 665 | 633 | 859 | **2,157** |
| Families with supported indicators | 25 | 18 | 20 | **63 (21.0%)** |
| Comparisons with supported indicators | 113 | 36 | 191 | **340 (15.8%)** |
| Comparisons with incomplete evidence coverage | 123 | 28 | 60 | **211** |

To display key metrics from a rerun in PowerShell:

```powershell
1..3 | ForEach-Object {
    $s = Get-Content "notebooks/end_to_end_pipeline/sprint3/results$_/review/summary.json" -Raw | ConvertFrom-Json
    [pscustomobject]@{
        Trial = $_
        Families = $s.family_count
        Comparisons = $s.directed_pairs_analyzed
        FamiliesWithRI = $s.families_with_supported_indicators
        PairsWithRI = $s.pairs_with_supported_indicators
        IncompleteCoverage = $s.pairs_with_incomplete_evidence_coverage
    }
} | Format-Table -AutoSize
```

Use **parsed numerical values and family identities**, not binary equality of JSON/SVG files: absolute database paths, metadata, timestamps, file ordering, font rendering, and generated IDs can vary. A comparison against committed results must be made **before overwriting them**, ideally using another clone or worktree. If the scanner revision differs from the recorded trial revision, document any numerical differences rather than claiming exact reproduction. The saved manifests have `sample_status: provisional` and no recorded approval reference; do not silently replace that status with an invented approval.

### 3.5 Manual review is a separate step

Each trial generated **30 directed-pair** and **15 relationship-pair** review cases (90 and 45 across the three trials). The team completed adjudication of all **135** cases and preserved the original independent annotations separately from its final decisions. The adjudicated copies are saved under each `sprint3/resultsX/` directory:

```text
resultsX/manual-review/
├── directed-pairs/annotations.csv                   # Original independent judgments
├── relationship-pairs/relationship_annotations.csv  # Original independent judgments
└── adjudicated/
    ├── directed.csv                                 # Final team-agreed directed reviews
    ├── relationships.csv                            # Final team-agreed relationship reviews
    └── adjudication.txt                             # Decision notes and approval provenance
```

The final **“Independent review and adjudication”** notebook cell has already processed both adjudicated CSVs for **all three trials**, updating each `review/summary.json` and `execution_summary.json` without rescanning skills or changing the frozen automated counts. Each execution summary now records `validation_status: "adjudicated results provided"`. The pre-adjudication summaries are preserved as `review/summary.before-adjudication.json` and `execution_summary.before-adjudication.json`.

The computed totals agree with [Appendix C of the final report](../../report/appendices/C-validation-materials.md):

| Measure | Final Sprint 3 result |
| --- | ---: |
| Directed / relationship cases | 90 / 45 |
| Directed `all_assessed` / `not_assessable` | 56 / 34 |
| Excluded among `all_assessed`: direction / evidence coverage | 12 / 15 |
| Directed comparisons eligible for indicator scoring | **29** |
| True positives / false negatives / counted false positives | 13 / 7 / 0 |
| Observed micro-precision / micro-recall | **100% (13/13) / 65.0% (13/20)** |
| Relatedness classification agreement | **42 / 45** |

The observed precision is limited to the 29 eligible comparisons: two adjudicated `mcp-builder` RI-003 false positives were **excluded** because direction was uncertain. These deliberately stratified review cases do not measure accuracy across the full dataset, and independent inter-rater agreement was not calculated.

To verify or repeat the *adjudication-only* summary calculation, use the committed final CSVs, compatible saved inputs and settings, and the last notebook cell separately for `SAMPLE = 1`, `2`, and `3`. Do not rerun the earlier scan cells or overwrite the frozen study results simply to update human-validation metrics. The [Manual Annotation Protocol](manual_annotation_protocol.md) explains review fields and decisions. Never execute untrusted skill instructions or scripts.

### 3.6 Completed Sprint 3 clean-environment verification

The team confirms that it **reproduced all three Sprint 3 trials in a clean environment**. This verification is separate from the adjudication-only update documented in Section 3.5: the latter applies final human judgments to saved results without rescanning. The original automated findings remain the published reference, and later scanner improvements were not substituted into those frozen counts. The original verification run's date, environment, and command transcript were not recorded here; the saved manifests, family lists, and output summaries provide the study inputs and comparison points.

## 4. Previously verified: Sprint 2 baseline (November 8, 2026)

The independent check for [story #213](https://github.com/umdnp/csc580-project8/issues/213) used detached committed-source worktrees, fresh environments and an initially empty uv cache. Both historical and current checkouts installed using `uv sync --locked`. It verified the historical 30-family study and generated the report. **This November 8 check is separate from the completed clean-environment Sprint 3 verification documented in Section 3.6.**

| Pinned input | Value |
| --- | --- |
| Report-source/current-code checkout used in the check | `0baeb0fff3e3e8598c5754cdf5637a0799142d8e` |
| Historical scanner checkout | `e1d6b773956c87877c51c8b0faa9ebb39fffdaf3` |
| Family input | [`sprint2/samples/families.txt`](../../notebooks/end_to_end_pipeline/sprint2/samples/families.txt), 30 families |
| Original family-list SHA-256 | `4562ff59808f2b1535d09fd242d8f9b8522885f15e99b1bf33f59c1751898763` |
| Source release | GitSkills 1.0.0, DOI `10.5281/zenodo.21875637` |
| Isolated environment | Windows x64, Python 3.12.3, DuckDB CLI 1.5.6; locked DuckDB 1.5.6 (current) and 2.0.0 (historical) |

To reproduce the original Sprint 2 **numerical baseline**, check out the historical revision in a separate worktree and invoke its cohort summarizer with the committed family list:

```powershell
# Start at the main checkout with GITSKILLS_DB configured.
$source = (Get-Location).Path
git worktree add --detach ..\csc580-baseline e1d6b773956c87877c51c8b0faa9ebb39fffdaf3
Set-Location ..\csc580-baseline
uv sync --locked --python 3.12
uv run --locked python -m gitskills.tools.summarize_cohort `
  --input "$source\notebooks\end_to_end_pipeline\sprint2\samples\families.txt" `
  --output "$source\output\baseline-e1d6b77" `
  --edges all --rescan --per-stratum 5 --seed 580 `
  --shingle-size 5 --min-containment 0.8 --min-jaccard 0.3 `
  --min-shared-shingles 5 --direction-margin 0.1
Set-Location $source
```

The verified historical summary and six research CSV tables matched the committed versions as parsed values. The two 30/15-case review sample lists matched. Four SVG plots were regenerated with matching numeric/category labels (not byte-identical drawing geometry). The focused isolated tests passed **53/53**, including production notebook execution on constructed inputs. The study's manual-validation findings were **not** independently adjudicated by this test.

The historical and then-current implementations produced different supported-indicator counts on the same cohort, reflecting changed scanner rules rather than nondeterministic timing:

| Metric (30-family baseline) | Historical scanner | November 8 current-code rerun |
| --- | ---: | ---: |
| Artifacts loaded | 1,151 | 1,151 |
| Directed comparisons (`all` edges) | 3,997 | 3,997 |
| Primary / additional comparisons | 468 / 3,529 | 468 / 3,529 |
| Comparisons with supported indicators | 588 | 577 |
| Families with supported indicators | 19 | 18 |
| Supported findings | 5,551 | 4,096 |

The prepared snapshot used in that check was **39,941,320,704 bytes**, whereas the historical manifest recorded **40,123,510,784 bytes**. Content identities matched for all 1,151 study artifacts despite differences in derived group IDs. All three preparation scripts were tested on a fresh SQLite fixture; the **full 44.4 GB import was not repeated** in the isolated check. These facts limit what the original verification establishes.

## 5. Build the research report

Building the report uses committed Markdown, tables, citations, and diagrams. **It does not rerun the notebook or automatically replace the reported numbers with those from a new scan.** See the [report build guide](../../report/README.md) for detailed prerequisites and troubleshooting.

```powershell
uv run --locked python bin/setup_report_tools.py
uv run --locked python bin/build_report.py --format html
uv run --locked python bin/build_report.py --format docx
uv run --locked python bin/build_report.py --format pdf
```

The portable report setup pins Pandoc, PlantUML, and Java components. The PDF build additionally requires XeLaTeX (for example, from MiKTeX or TeX Live); TeX package installation and rendering details can vary. Generated HTML/DOCX files go to `report/generated-report/`; the PDF goes to `report/final.pdf`.

The November 8 check built HTML, Word, LaTeX, and a **28-page PDF** successfully after installing a user-level MiKTeX distribution. It inspected the bibliography, diagrams, main tables, and appendices. PDF and SVG binary identity is not promised because fonts, layout, timestamps, and rendering tools may differ.

## 6. Reproducibility limits and interpretation

- **External dataset:** The downloaded SQLite release and prepared DuckDB are not checked into Git. Exact repetition depends on consistent source data and derived-table preparation. The November 8 Sprint 2 check did not include a full clean import or the three Sprint 3 trials; the team completed a separate clean-environment verification of those trials.
- **Saved cohorts:** Sprint 3 family lists and sampling reports are committed. Reuse these lists to reproduce the analyzed samples. Seeds alone cannot compensate for differences in the database, selection algorithm, or eligibility checks.
- **Code changes:** Trial manifests preserve code revisions and scanner fingerprints. A later scanner or data-preparation change may alter detections, comparisons, or IDs. Keep frozen reported outcomes distinct from revised-code reruns.
- **Incomplete evidence and validation:** Supported risk indicators are static signals, not confirmed vulnerabilities. Team adjudication is complete, but missing sibling-file content, uncertain direction, and the small restricted scoring subset limit conclusions. Sample precision and recall do not establish full-cohort accuracy.
- **Generalizability:** The 300 families were stratified and deliberately oversampled in larger size groups, with eligibility restricted to usable primary directed relationships. Their 21.0% family-level rate is not an unweighted estimate for all GitSkills families.
- **Output metadata:** Absolute paths, timestamps, surrogate IDs, cache filenames, source-file line endings, and SVG/PDF rendering may differ. Compare manifests, selected families, structured counts, and source/content hashes before drawing conclusions.

For methodology and interpretation, see [RDR-013: Sprint 3 Sampling and Edge Selection](../decisions/RDR-013-sprint3-sampling-and-edge-selection.md), [RDR-014: Stratified Family Sampling Method](../decisions/RDR-014-stratified-family-sampling-method.md), and [Threats to Validity](../../THREATS_TO_VALIDITY.md).

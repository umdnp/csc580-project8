# End-to-End Research Pipeline

This notebook studies **one or more GitSkills candidate families**: it infers possible relationships between skills, scans direction-supported changes for security-sensitive evidence, summarizes the findings, and prepares pairs for **human validation**.

**Start here:** Run the notebook once, independently review the two generated spreadsheets, agree on final judgments, and run its last cell to add validation metrics. The pipeline does **not** establish that a skill is malicious or that an inferred relationship is proven ancestry.

## 1. Set up and run

From the project root:

1. Install Python 3.12+ and [`uv`](https://docs.astral.sh/uv/), then run `uv sync`. Select the project environment as your notebook kernel.
2. Prepare the GitSkills DuckDB database using [`data/README.md`](../../data/README.md). The database needs `artifacts`, `artifact_groupings`, `artifact_siblings`, and `repos`. The large dataset is not included in the repository.
3. Set `GITSKILLS_DB` to the prepared DuckDB file, using a path visible to the notebook's Python environment. For example, in WSL:

   ```bash
   export GITSKILLS_DB=/mnt/c/data/duckdb/agent_skills_release.db
   ```

   Without this variable the notebook uses the Windows fallback `C:\data\duckdb\agent_skills_release.db`.
4. Open `notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb` in Jupyter, starting Jupyter from the project root (for example, `uv run --with jupyterlab jupyter lab`).
5. Edit the configuration cell: `candidate_families` (exact skill names), `POLICY`, `EDGES`, `PER_STRATUM`, `SEED`, and `APPROVAL_REFERENCE`. The provided family list is **provisional**, not an approved research sample. Set `APPROVAL_REFERENCE` only after recording the team's approval. `RUN_LABEL` determines the results subdirectory (`sprint2` by default); use a separate label such as `final` for a separately frozen run.
6. Run the notebook cells in order through **Findings for manual review**. The final **Independent review and adjudication** cell is for *after* humans finish reviewing the samples.

The notebook calls **`summarize_cohort()` directly**. You do *not* need to run `analyze_family`, `scan_family`, or `scan_diff` first. For each selected family, the summarizer computes similarity evidence as needed, reuses a compatible cached security scan (or regenerates it), and writes the cohort research outputs. A cohort can contain **one family or several**; a cluster is a group of related artifacts *within* a family.

`PER_STRATUM = 5` means **up to five reviewed pairs in each validation category across the whole cohort**, not five per family. It does **not** reduce the artifacts or pairs used in the full research analysis. The notebook uses `EDGES = "all"`, covering both primary and additional direction-supported edges; ambiguous pairs are not security-scanned as directed changes.

## 2. Find the outputs

With `RUN_LABEL = "sprint2"`, files are under `notebooks/end_to_end_pipeline/results/sprint2/` (called `RESULT_DIR` below):

```text
RESULT_DIR/
├── .scans/                         # Reusable security-scan cache; not review evidence
│   ├── .metadata/
│   │   └── scan-manifest.json      # Cache bookkeeping
│   └── <family>.json               # Scan result for each family
├── manual-review/
│   ├── directed-pairs/
│   │   ├── validation_sample.csv
│   │   └── annotations_template.csv
│   ├── relationship-pairs/
│   │   ├── relationship_validation_sample.csv
│   │   └── relationship_annotations_template.csv
│   └── adjudicated/                # Team-created reviewed copies
├── review/
│   ├── summary.json                # Full-population statistics; later, review metrics
│   ├── families.csv
│   ├── directed_pairs.csv
│   ├── edge_types.csv
│   ├── indicator_frequency.csv
│   ├── indicator_frequency_by_edge_type.csv
│   └── direction_basis.csv
├── figures/indicator_frequency.svg
├── audit/
│   ├── processing_summary.csv
│   └── skipped_artifacts.csv
├── sample_manifest.json           # Source identities, settings, sample checksums
└── execution_summary.json         # Run status and coverage
```

A successful automated run reports `status: "complete"` in `execution_summary.json`. **That does not mean human validation is complete.** The `.scans/` directory is an intermediate cache; the two `manual-review/` sample CSVs and the adjudicated decisions are the review evidence. You can ignore `.scans/` in Git, but retain the research outputs and adjudicated records according to your team's data-management plan.

The run can legitimately contain **zero direction-supported pairs**. This does not establish that a skill is safe. Check `audit/skipped_artifacts.csv` and the coverage columns before drawing conclusions.

## 3. Manual validation: what reviewers actually do

These steps are also summarized in the [Manual Annotation Protocol](../../docs/instructions/manual_annotation_protocol.md).

There are **two different review assignments**. Give each reviewer independent copies of *both* annotation templates; do not edit the originals or each other's judgments.

| Review | File to copy | Question to answer |
|---|---|---|
| **Directed pairs** | `manual-review/directed-pairs/annotations_template.csv` | Is the inferred direction defensible? Did the scanner correctly identify changed commands, files, network or credential-related evidence, risk indicators, and coverage limitations? |
| **Relationship pairs** | `manual-review/relationship-pairs/relationship_annotations_template.csv` | Do these two artifacts appear related, and does the available evidence support a direction (if any)? This includes pairs the algorithm did **not** link. |

**Do not review only flagged rows.** The samples deliberately include less-obvious, incomplete, uncertain, and unflagged examples. `review/directed_pairs.csv` is the full set of analyzed directed pairs; `validation_sample.csv` is only the selected review subset.

### Step A — Prepare independent copies

1. Confirm the intended families, sampling seed, policy, and scan scope in `sample_manifest.json`. Freeze these inputs before review begins.
2. Copy both annotation templates for each reviewer (for example, into a team-controlled review workspace). Keep the generated templates and `*_sample.csv` files unchanged.
3. Open the copies in Excel, LibreOffice, or a CSV editor. **Preserve every row, column heading, artifact ID, and existing sample value**; only fill in the review columns described below. Save as UTF-8 CSV, not just `.xlsx`.
4. Reviewers work **independently first**. Mark a row `complete` only after inspecting the evidence and recording all required review judgments. Keep difficult rows `pending` until resolved.

### Step B — Locate the original evidence

For each row, start with its `family` and artifact IDs:

- **Directed pair:** `base_artifact_id` is the earlier/source side inferred by the tool; `derived_artifact_id` is the later/target side. This ordering is an *inference* to verify, not guaranteed history.
- **Relationship pair:** `artifact_a_id` and `artifact_b_id` are two artifacts being compared; their A/B order **does not imply chronology**.
- In `sample_manifest.json`, find the named entry under `families`, then the artifacts under its `artifacts` list. Match `artifact_id` to find `repo_full_name`, `path`, and `file_sha` so you know exactly which stored sources to inspect.
- In the cached `.scans/<family>.json`, a directed pair's observations provide rule matches, evidence changes, indicators, and sibling coverage; review these alongside the original content. Do not infer that a missing sibling record proves that a file was absent historically.

**Using SkillTrace (optional, especially useful for visual inspection):**

1. If the family is not listed in SkillTrace, create its **compact** lineage report separately from the project root:

   ```bash
   uv run python -m gitskills.tools.analyze_family code-review --output apps/skilltrace/reports
   ```

   Replace `code-review` with the row's family name. Use the **same similarity settings** as your cohort run if you changed the defaults. Do not use `--verbose`; SkillTrace loads the smaller saved reports. These reports are **not required by** `summarize_cohort`.
2. Start SkillTrace with `sh bin/start_skilltrace_server.sh`, open `http://127.0.0.1:8000`, and select the family from the **Report** dropdown. It needs the prepared DuckDB for source inspection.
3. Search for an artifact ID, select it in the graph, and inspect the **raw `SKILL.md`**, repository/path metadata, chronology, and sibling files. For direction-supported relationships, compare the base and derived contents in the side-by-side diff. **Run scan** and **Inspect evidence** can help inspect rules and source locations.
4. Check the original lines, not just redacted excerpts or highlighted matches. SkillTrace's on-demand scans **do not reproduce the full `scan_family` sibling assessment**, and its graph does not necessarily provide a direct comparison for an unlinked (`no-related-edge`) pair. For those, locate and read **both** artifacts individually using their IDs and the database/source references.

SkillTrace is an inspection aid, **not** the final adjudicator. Never execute skill commands, scripts, linked installers, or downloaded code during validation. Do not publish unredacted credentials or private source content.

### Step C — Review *relationship* pairs

Open your copy of `relationship_annotations_template.csv`. The generated columns describe the tool's assessment and should remain unchanged:

- `relationship_status` / `sampling_stratum`: `ambiguous`, `equivalent`, or `no-related-edge` (the last means the pair failed the configured relatedness criteria; it does not establish independence).
- `similarity_jaccard`, `similarity_containment`, `similarity_shared_shingles`: numerical similarity evidence to help guide inspection, **not** a human judgment.
- `direction_basis` and `change_type`: the tool's explanation, where available.

For **each pair**, inspect both raw skill bodies, important instructions and commands, available metadata, and chronology/provenance evidence. Then fill the review columns:

| Column | What to enter |
|---|---|
| `reviewer` | Your initials or reviewer ID. |
| `review_phase` | `independent` in your own copy; **`adjudicated`** in the final team-agreed file. |
| `review_status` | `pending` while unresolved; `complete` when judged. Pending rows are not counted in metrics. |
| `review_date` | Date of the decision; use `YYYY-MM-DD` for consistency. |
| `manual_relatedness` | `related` if substantive source/instruction similarity supports a relationship; `not_related` if not; `uncertain` if evidence is insufficient. The shared family name alone is not enough. |
| `direction_basis_review` | `supported` if provenance or defensible chronology supports a direction; `unsupported` if the proposed direction lacks support or is contradicted; `uncertain` if unresolved; `not_applicable` when no direction is proposed or relevant. |
| `notes` | Brief evidence and reasoning: specific commands, content similarities/differences, repository/path clues, and chronology limitations. |

**Example (illustrative):** A `no-related-edge` pair shares a name but its instructions describe unrelated workflows. Enter `manual_relatedness=not_related`, `direction_basis_review=not_applicable`, and explain the difference in `notes`. If instead the two skills clearly repeat substantive instructions despite low shingle similarity, enter `related` and document that observation. Do not invent a source or a direction.

### Step D — Review *directed/security* pairs

Open your copy of `annotations_template.csv`. Keep the generated fields (`base_artifact_id`, `derived_artifact_id`, `edge_type`, `indicator_ids`, `uncertain_indicator_ids`, `coverage_status`, `sampling_stratum`, counts, etc.) **unchanged**. The scanner's `indicator_ids` are its predictions; your separate `manual_*` fields contain **your** conclusions.

Inspect the original base and derived instructions, all relevant changed source evidence and sibling files, and the stated direction evidence. Ask:

1. Are the two artifacts meaningfully related, and is base → derived supported by available provenance/chronology?
2. Did the tool correctly extract and classify the rules/changes? Are matches real instructions or just examples, quoted text, or negated warnings? Were any important changes missed?
3. For **each RI-001 through RI-011**, is the indicator supported by the *change* between these artifacts, uncertain, or absent? Consider **false negatives**, not just the indicators predicted by the scanner.
4. Is the evidence complete enough to make those decisions? Check missing sibling text, unknown hashes, partial/unsupported extraction, and whether content was available on both sides.

Fill the following review columns:

| Column | Enter one of these values (or free text as indicated) |
|---|---|
| `reviewer`, `review_phase`, `review_status`, `review_date` | Same rules as the relationship review. |
| `manual_relatedness` | `related`, `not_related`, `uncertain`. |
| `direction_basis_review` | `supported`, `unsupported`, `uncertain`, `not_applicable`. |
| `scanner_rule_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable`. Overall assessment of the scanner's rule matches. |
| `manual_rule_judgments` | Optional detailed rule decisions, separated by semicolons: `FS-001=correct;NET-002=false_positive`. Allowed judgments: `correct`, `false_positive`, `false_negative`, `uncertain`, `not_applicable`. Use actual rule IDs from the scan's active rules/findings; do not repeat a rule ID. |
| `manual_change_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable`. Overall assessment of detected evidence changes. |
| `manual_change_judgments` | Optional per-indicator change notes in `RI-###=value` format; choices: `introduced`, `removed`, `retained`, `mixed`, `none_detected`, `direction_unknown`, `uncertain`, `not_applicable`. Separate multiple entries with `;`; do not repeat an ID. |
| `indicator_review_scope` | `all_assessed` **only if you could independently assess all eleven RI categories** for this pair; otherwise `not_assessable`. |
| `manual_supported_indicator_ids` | Semicolon-separated indicator IDs **you** confirm, e.g. `RI-006;RI-010`; leave blank if none is supported. Only `RI-001` through `RI-011` are valid. |
| `manual_uncertain_indicator_ids` | Semicolon-separated indicator IDs you cannot decide, e.g. `RI-010`; blank if none. An ID cannot appear in both supported and uncertain fields. |
| `sibling_coverage_review` | `complete`, `incomplete`, `uncertain`, `not_applicable` based on the *available evidence*, not only the scanner's label. |
| `missed_observations` | Free text: relevant commands, files, URLs, or other evidence the tool missed, with source locations. |
| `false_positive_notes` | Free text: why any scanner findings are unsupported (for example, a quoted warning rather than an executable instruction). |
| `notes` | Free text: reasoning, source references, limits and unresolved questions. |

**Example (illustrative):** The base skill has no deletion instruction; the derived skill instructs `rm -rf ./cache`. After inspecting both source texts, a reviewer might mark `manual_relatedness=related`, `direction_basis_review=supported`, `scanner_rule_review=correct`, `manual_rule_judgments=FS-001=correct`, `manual_change_review=correct`, `manual_supported_indicator_ids=RI-006`, `manual_change_judgments=RI-006=introduced`, and explain the changed line in `notes`. Mark `indicator_review_scope=all_assessed` **only after reviewing the other RI categories too**. If sibling data is missing and you cannot assess them all, use `not_assessable` or an uncertain judgment rather than guessing.

**Important for metrics:** A directed pair contributes to the calculated indicator precision/recall only if its manual relatedness is `related`, direction is `supported`, scanner `coverage_status` **and** your `sibling_coverage_review` are both `complete`, and `indicator_review_scope=all_assessed`. Otherwise it remains a reviewed example but is excluded from assessable-pair indicator metrics. `manual_uncertain_indicator_ids` are excluded from individual indicator judgments. These statistics describe the **reviewed sample**, not the full corpus.

### Step E — Adjudicate disagreements

1. Collect each reviewer's independently completed CSVs. Preserve them separately as evidence of disagreement; don't merge overwriting one reviewer's judgments.
2. Compare decisions for every sampled pair, especially disagreements about relatedness, direction, detected risk indicators, and coverage.
3. Reinspect the relevant source text and scanner evidence together. Record a **single final team decision per sampled pair**, with an explanation in `notes`. If the evidence is genuinely insufficient, choose `uncertain` or `not_assessable` where permitted rather than forcing agreement.
4. Create the following **team-owned** CSVs by copying the generated templates and filling in the agreed judgments, retaining **all original sample identifiers and headers**:

   ```text
   RESULT_DIR/manual-review/adjudicated/directed.csv
   RESULT_DIR/manual-review/adjudicated/relationships.csv
   ```

5. For every final accepted row, enter `review_phase=adjudicated`, `review_status=complete`, a nonempty `reviewer` (for example `team-review`), and `review_date`. **Populate the required enumerated review fields** listed above even when the answer is `uncertain` or `not_applicable`. Leave unfinished rows `pending` until they can be resolved; the metrics ignore them. Preserve CSV formatting and the exact artifact IDs. Never write decisions into `*_sample.csv` or the generated templates.

## 4. Incorporate adjudicated results (fast rerun)

Once **both** final adjudicated CSVs exist, execute the notebook's last cell, **Independent review and adjudication (team action)**. It calls `summarize_cohort()` again with `directed_annotations` and `relationship_annotations`, while keeping the **same** candidate families, DuckDB, policy, `EDGES`, `PER_STRATUM`, seed and results directory.

With compatible saved outputs **and without `rescan=True`**, this is a lightweight operation: it verifies the manifest, scan cache, sample checksums, implementation and research summary, reads your completed CSVs, and updates:

- `RESULT_DIR/review/summary.json` → `manual_validation` (directed-pair indicator metrics) and `relationship_validation` (relatedness agreement counts and direction-review breakdown).
- `RESULT_DIR/execution_summary.json` → validation status.

It **does not re-run family similarity analysis or security scans**. If only one adjudicated CSV is available, the notebook's last cell will defer; the Python API/CLI can process an individual supplied annotation file separately, but team review should ultimately complete both.

**Check the results:** open `review/summary.json`. Confirm `manual_validation.reviewed_pairs` and `relationship_validation.reviewed_pairs` match the expected number of `complete` adjudicated rows. Review `assessable_pairs`, exclusions, precision/recall (where calculable), and relationship agreements/disagreements. Investigate errors or exclusions before reporting findings. Do not present validation-sample metrics as prevalence estimates.

If a cache, dataset, selected family, sampling setting, rule/policy, or implementation has changed, **the fast rerun refuses to reuse stale evidence**. Preserve the previous result directory and adjudications and start a newly labeled cohort run rather than overwriting reviewed samples. Use `--rescan` / `rescan=True` only when you deliberately want to regenerate security scans—not when simply adding human judgments.

## 5. Automated checks and interpretation

Run the notebook integration test from the repository root:

```bash
uv run pytest tests/pytests/test_pipeline_notebook.py -v
```

The test runs the notebook's code cells using synthetic DuckDB records and temporary outputs. It checks processing, coverage and reproducibility paths, **not** the accuracy of real-world results or the quality of human judgments.

When writing the report, distinguish the *full analyzed population* (`review/directed_pairs.csv`, summary tables and figure) from the *stratified human-review samples*. Directional edges are inferred, multiple pairs may share artifacts, risk indicators are static **review signals**, and unavailable sibling content limits what can be concluded. Never execute stored scripts or treat uncertain/missing evidence as proof of safety or malicious intent.

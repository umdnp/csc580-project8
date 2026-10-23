# End-to-End Family Pipeline

This notebook connects the existing GitSkills family analysis, directed security scanning, research summaries, and manual-review sampling. It supersedes the **Sprint 1** `notebooks/end-to-end_pipeline/` demonstration without changing it.

## Prerequisites

1. From a fresh checkout, install Python 3.12+ and [`uv`](https://docs.astral.sh/uv/); run `uv sync` from the repository root. Use the project virtual environment as the notebook kernel.
2. Obtain the [GitSkills Zenodo dataset](https://zenodo.org/records/21875637) and prepare the project DuckDB with the repository's database setup instructions in [`data/README.md`](../../data/README.md). The database must contain `artifacts`, `artifact_groupings`, `artifact_siblings`, and `repos`. The large source dataset stays outside Git.
3. Set `GITSKILLS_DB` to the **prepared DuckDB** path accessible to your Python interpreter, for example `export GITSKILLS_DB=/mnt/c/data/duckdb/agent_skills_release.db` under WSL. Without this variable, notebooks default to `C:\data\duckdb\agent_skills_release.db` (Windows).
4. Open `end_to_end_pipeline.ipynb` from the repository or run `uv run --with jupyterlab jupyter lab` from the root. Use its Python kernel and execute cells in order.

## Run and outputs

Select `candidate_families` in the notebook. The example list is **provisional**; approve/freeze the cohort and its dataset preparation before independent validation. Set `APPROVAL_REFERENCE` to a recorded team decision/date to mark the generated manifest approved; otherwise it is marked provisional. Change `RUN_LABEL` to `final` only for the final analysis. The notebook processes families independently through `run_family()`; you may analyze subsets in separate sessions. To summarize, include every intended family name in `candidate_families` and ensure each has a current scan. The summary rejects missing reports and different input snapshots, policies, rules, scopes, or edge settings.

- `apps/skilltrace/reports/<family>.json`: canonical `analyze_family` reports, refreshed when missing or incompatible. **Not duplicated** in the notebook directory. These reports are shared with SkillTrace; preserve/report their source fingerprints when publishing results.
- `notebooks/end_to_end_pipeline/results/sprint2/scans/*.json` (or `final/scans/`): one security report per processed family, with edge scope `all` and explicit skipped-artifact reasons.
- `results/<run>/sample_manifest.json`: selected family names, provenance, exact artifact IDs, file hashes, inclusion/exclusion rules, and matching source/implementation fingerprints.
- `results/<run>/execution_summary.json` and `audit/*.csv`: family and pair counts, skipped records/reasons, incomplete coverage, and execution status.
- `results/<run>/review/`: `summary.json`, research tables, `indicator_frequency.svg`, directed/security and relationship samples, and independent-review templates.

The workflow completes successfully when `execution_summary.json` reports `status=complete`, selected families match `sample_manifest.json`, and both review templates exist. **Zero directed pairs** is a valid outcome for a family without defensible direction; it is not equivalent to a negative security finding. A missing family or incompatible report is an error, not an implicit exclusion.

## Human validation

Copy the two review templates for independent team reviewers and follow [`docs/validation/manual_validation_protocol.md`](../../docs/validation/manual_validation_protocol.md). Preserve individual judgments, resolve disagreements separately, and place final adjudicated copies at `review/adjudicated/directed.csv` and `review/adjudicated/relationships.csv` if you want the optional notebook cell to calculate sample-level metrics. Generated outputs do not contain human judgments. Never execute scripts or commands found inside GitSkills artifacts.

A new dataset, changed family list, changed rules, or changed policy requires a new research snapshot. Preserve previous validation materials before rerunning a changed cohort; the pipeline prevents overwriting a selected sample when adjudicated CSVs exist under the designated review directory. The project repository contains setup instructions, but the full multi-GB DuckDB is not bundled with this notebook.

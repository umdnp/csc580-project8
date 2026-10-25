# Manual Annotation Protocol

## Purpose

Human reviewers check the relationships and security findings produced by `summarize_cohort`. The automated results are **evidence to inspect**, not verified ancestry or proof of malicious behavior. Reviewers make independent judgments first; the team then agrees on an adjudicated record.

This protocol defines the required judgments and how to record them. For a step-by-step walkthrough, including practical SkillTrace instructions, see the [End-to-End Pipeline README](../../notebooks/end_to_end_pipeline/README.md).

## Generate Review Samples

From the repository root, with `GITSKILLS_DB` pointing to the prepared DuckDB database:

```bash
uv run python -m gitskills.tools.summarize_cohort busybox-on-windows \
  --output results --edges all --per-stratum 5 --seed 580
```

For multiple families, replace the family name with `--input FILE`, where `FILE` lists one exact family name per line. `summarize_cohort` performs the required analysis and scanning itself; it does **not** need saved `analyze_family` or `scan_family` reports. It reuses compatible scans under `results/.scans/` when available.

Two separate review samples are generated:

| Review | Annotation template | What to check |
|---|---|---|
| **Directed pairs** | `results/manual-review/directed-pairs/validation_annotations_template.csv` | Relatedness, inferred direction, scanner matches, changed evidence, risk indicators, and coverage |
| **Relationship pairs** | `results/manual-review/relationship-pairs/relationship_validation_annotations_template.csv` | Whether pairs are related and whether direction is supported, including ambiguous, equivalent, and *no-related-edge* cases |

`--per-stratum 5` selects **up to five pairs per review category across the selected families**, not five per family. Sampling is for human review only: all eligible relationships and directed security comparisons are still included in the research analysis. An empty category remains empty.

The generated sample CSVs and templates are research evidence. Preserve them along with `sample_manifest.json`; do not alter their source IDs or automated results. See the [Tools Guide](../../TOOLS.md) for additional execution options.

## Review Each Pair

1. Give each reviewer **separate copies** of both annotation templates. Leave the generated originals unchanged.
2. Locate the artifacts by their IDs. Read both stored `SKILL.md` files and relevant sibling content. Inspect the tool's similarity, chronology, detection, and coverage evidence—not only its conclusions.
3. Judge **relatedness and direction** separately. The same name or a high similarity score does not prove copying or order; artifact IDs do not establish chronology.
4. For directed pairs, check actual source instructions against the scanner's rule matches, reported changes, and **all applicable risk indicators**. Consider missed evidence and false positives as well as flagged matches. Missing sibling content or uncertain extraction is not a negative security finding. Complete scan coverage does not guarantee that every risk was detected.
5. Fill in only the human-review columns below. Explain disagreements and uncertain decisions in `notes`, using source locations when helpful. Mark a row `complete` only when you have finished its review; otherwise leave it `pending`.

**SkillTrace can help:** Generate a separate **compact** family report with `analyze_family NAME --output apps/skilltrace/reports`, open SkillTrace, select the family, and search for each artifact ID. View the stored content, metadata, lineage graph, and available diffs; use its focused scan for an additional check where supported. SkillTrace is an inspection aid, not a substitute for reading the underlying source or for full sibling-file scanning. An unlinked relationship pair may require opening both artifacts separately. Do **not** execute commands or scripts from the dataset.

### Directed Review Fields

| Field | Values | Meaning |
| --- | --- | --- |
| `reviewer`, `review_date` | Reviewer identifier; date | Attribution of the review |
| `review_phase` | `independent`, `adjudicated` | Independent judgment or agreed final judgment |
| `review_status` | `pending`, `complete` | Whether the row has been reviewed |
| `manual_relatedness` | `related`, `not_related`, `uncertain` | Whether the pair is meaningfully comparable |
| `direction_basis_review` | `supported`, `unsupported`, `uncertain`, `not_applicable` | Whether base/derived direction is defensible |
| `scanner_rule_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable` | Overall assessment of detected constructs |
| `manual_rule_judgments` | `RULE_ID=judgment` entries separated by `;`; judgments: `correct`, `false_positive`, `false_negative`, `uncertain`, `not_applicable` | Rule-level evidence when needed |
| `manual_change_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable` | Overall assessment of reported changes |
| `manual_change_judgments` | `RI-###=judgment` entries separated by `;`; judgments: `introduced`, `removed`, `retained`, `mixed`, `none_detected`, `direction_unknown`, `uncertain`, `not_applicable` | Indicator-level change judgment; use `mixed` and notes when several outcomes apply |
| `indicator_review_scope` | `all_assessed`, `not_assessable` | Explicit confirmation of whether all active indicators were checked within the reviewed scope |
| `manual_supported_indicator_ids` | Semicolon-separated `RI-###` values | Indicators supported by manual evidence review |
| `manual_uncertain_indicator_ids` | Semicolon-separated `RI-###` values | Indicators that cannot be assessed reliably |
| `sibling_coverage_review` | `complete`, `incomplete`, `uncertain`, `not_applicable` | Reviewer's assessment of covered content |
| `missed_observations`, `false_positive_notes`, `notes` | Short free text | Context for errors, gaps, and uncertainty |

For `manual_rule_judgments`, write separate complete assignments, such as `NET-001=correct;FS-001=false_positive`. For `manual_change_judgments`, an example is `RI-003=introduced;RI-005=removed`. A changed command can be meaningful even when the count of rule matches stays the same.

The `manual_supported_indicator_ids` and `manual_uncertain_indicator_ids` fields must not overlap. Empty supported and uncertain lists mean **all other indicators were assessed as absent only when** `indicator_review_scope=all_assessed`. Otherwise, no negative judgment is implied. Reviewers should use `not_assessable` when they cannot examine the necessary evidence.

### Relationship Review Fields

The relationship template retains the artifact IDs, similarity measurements, relationship status, direction basis, and selection stratum. Reviewers complete `reviewer`, `review_date`, `review_phase`, `review_status`, `manual_relatedness`, `direction_basis_review`, and `notes`.

For an ambiguous pair, `direction_basis_review=supported` means the reviewer found defensible ordering that the automated method did not establish. For a no-related-edge pair, `manual_relatedness=related` indicates a potential false negative in relationship discovery. These are review judgments, not verified copying histories.

## Independent Review and Adjudication

Keep every reviewer's completed CSV. Compare judgments and resolve disagreements as a team, inspecting the source evidence again when necessary. Do not overwrite reviewers' original copies. If the evidence is insufficient, record `uncertain` or `not_assessable` rather than inventing a conclusion.

Create final team-agreed copies of the generated templates here:

```text
results/manual-review/adjudicated/directed.csv
results/manual-review/adjudicated/relationships.csv
```

For each completed final row, set `review_phase=adjudicated`, `review_status=complete`, and a nonempty `reviewer` and `review_date`. Fill the applicable review fields with one of the permitted values above. Include concise reasoning in `notes`. Keep any unresolved rows `pending`; only complete, adjudicated rows contribute to the computed metrics.

Run the same cohort command and settings as the original sample run, this time supplying the completed CSVs:

```bash
uv run python -m gitskills.tools.summarize_cohort busybox-on-windows \
  --output results --edges all --per-stratum 5 --seed 580 \
  --annotations results/manual-review/adjudicated/directed.csv \
  --relationship-annotations results/manual-review/adjudicated/relationships.csv
```

When the saved cohort, samples, settings, and cache still match—and `--rescan` is not used—this rerun **only calculates manual-review metrics**. It does not repeat family similarity analysis or scanning. If the saved evidence has changed, the tool stops rather than silently replacing reviewed samples. Preserve the old run and start a separate results directory for a new cohort snapshot.

## Read the Validation Results

Open `results/review/summary.json`:

- `manual_validation` reports directed-pair review counts, exclusions, and indicator precision/recall where assessable. Relatedness, direction, indicator coverage, and sibling coverage affect which reviewed pairs can be scored.
- `relationship_validation` reports agreements, disagreements, and uncertain decisions about the inferred relationships and direction. These do not count as directed risk-indicator judgments.

Confirm the reviewed-pair counts against the adjudicated CSVs. **Review-sample metrics are not full-dataset prevalence estimates.** Document limitations and recurring errors in the research report and [Threats to Validity](../../THREATS_TO_VALIDITY.md).

The fixed Sprint 1 sample under [`data/validation/archive/`](../../data/validation/archive/) is historical and is not a second active review procedure.

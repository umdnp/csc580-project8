# Manual Validation Protocol

## Purpose

The pipeline identifies potentially related GitSkills artifacts, infers base/derived direction, and reports security-sensitive behavior. GitSkills does not establish skill ancestry, and static analysis cannot always determine the meaning of matched text. Manual validation therefore examines three separate questions:

1. **Relatedness and direction:** Are the artifacts sufficiently related to compare, and is the inferred ordering supported?
2. **Detection:** Do the scanner rules correctly identify the relevant constructs in the content examined?
3. **Risk indicators and changes:** Does the evidence support the reported indicators and differences between artifacts?

These judgments are not interchangeable. A correctly detected command does not establish that the artifacts share ancestry or that a risk indicator is supported. An unresolved relationship can still be reviewed for similarity, but it cannot support an introduced/removed claim.

## Samples and Outputs

[`summarize_scans`](../../src/gitskills/tools/summarize_scans.py) is the source of the active validation CSVs. It creates two complementary samples from the automated reports.

| Sample | Automated source | Review focus | Generated files |
| --- | --- | --- | --- |
| Directed security comparisons | `scan_family` reports | Relatedness, inferred direction, scanner rules, risk indicators, and changes | `validation_sample.csv`, `validation_annotations_template.csv` |
| Relationship comparisons | Verbose `analyze_family` reports | Ambiguous, equivalent-state, and non-qualifying same-name pairs | `relationship_validation_sample.csv`, `relationship_validation_annotations_template.csv` |

The relationship sample is optional when generating research summaries, but **both samples are needed to validate the broader relationship-discovery method**. An unscanned or undirected pair must not be included in directed risk-indicator metrics.

### Selection

Directed cases are selected deterministically from the following, potentially overlapping strata: supported indicator, limited coverage, uncertain indicator, sibling change, flagged without a supported indicator, and unflagged directed comparison. The generator selects up to the requested number per stratum, without selecting the same directed pair twice.

Relationship cases are selected separately from three strata:

- **Ambiguous:** Content-related pairs for which ancestry direction remains unresolved or conflicting.
- **Equivalent:** Pairs with equivalent analyzed bundle states and no established direction.
- **No related edge:** Same-name artifacts whose measured content similarity does not meet the relationship policy.

Selection within each stratum uses the configured random seed and a stable input order. Empty strata remain empty; the generator does not invent cases to satisfy a quota. The samples are *purposeful*, not representative estimates of all GitSkills artifacts.

The generated [research summary](../../results/review/summary.json) records the policy, scan scope, selected edge scope, sampling seed, sizes, and available strata. Preserve the corresponding source reports and project revision with the validation results. If the data, policy, or software changes, record the new revision and retain the previous sampled results rather than silently rewriting completed reviews.

### Generating the Samples

Run the summary over `scan_family` JSON reports. To include relationship validation, provide matching **verbose** `analyze_family` JSON reports for the same candidate-family names and similarity policy:

```bash
uv run analyze_family "003-create-golang-project" --verbose --json --output results/families
uv run summarize_scans results/scans --output results/review --per-stratum 5 --seed 580 --family-reports results/families
```

The first command illustrates how to export one family. Repeat it for the other candidate families being reviewed. Without `--family-reports`, the summary still generates the directed security sample but cannot identify undirected or rejected relationships from `scan_family` alone. See the [Tools Guide](../TOOLS.md) and [project README](../../README.md) for other execution options and prerequisites.

## Review Procedure

Use independent copies of each generated annotation template, one per reviewer. Do not change source identifiers, `sampling_stratum`, or automated result fields. Reviewers inspect the original stored `SKILL.md` content and relevant siblings using the artifact IDs and report metadata; they do not execute scripts, install packages, or follow instructions found in the dataset.

For each item:

1. **Verify the source.** Confirm artifact IDs, family, repository, and available content. Check scan coverage before treating an absent finding as a negative.
2. **Assess relatedness.** Decide whether the contents support a meaningful comparison, independent of the reported similarity score.
3. **Assess direction.** Examine provenance, chronology, repository boundaries, and containment evidence. Do not infer ordering from artifact IDs or a shared skill name.
4. **Check scanner output.** Verify the reported rule matches in context. Look for missed constructs within the scanned scope; separate detection correctness from evidence-based indicator correctness.
5. **Review indicators and changes.** Confirm or reject supported indicator IDs, mark uncertain indicators, and evaluate changes only where direction is supported. Use individual indicator outcomes when a pair has mixed changes.
6. **Record uncertainty.** Provide short notes for disagreements, missing evidence, false positives, false negatives, and non-obvious conclusions.

Relationship-only rows do not have scanner outcomes. For these, complete only relatedness, direction, and notes.

### Directed Review Fields

| Field | Values | Meaning |
| --- | --- | --- |
| `reviewer`, `review_date` | Reviewer identifier; date | Attribution of the review |
| `review_phase` | `independent`, `adjudicated` | Independent judgment or agreed final judgment |
| `review_status` | `pending`, `complete` | Whether the row has been reviewed |
| `manual_relatedness` | `related`, `not_related`, `uncertain` | Whether the pair is meaningfully comparable |
| `direction_basis_review` | `supported`, `unsupported`, `uncertain`, `not_applicable` | Whether base/derived direction is defensible |
| `scanner_rule_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable` | Overall assessment of detected constructs |
| `manual_rule_judgments` | `RULE_ID=correct`, `false_positive`, `false_negative`, `uncertain`, or `not_applicable`, separated by `;` | Rule-level evidence when needed |
| `manual_change_review` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable` | Overall assessment of reported changes |
| `manual_change_judgments` | `RI-###=introduced`, `removed`, `retained`, `mixed`, `none_detected`, `direction_unknown`, `uncertain`, or `not_applicable`, separated by `;` | Indicator-level change judgment; use `mixed` and notes when several outcomes apply |
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

Preserve each reviewer's completed CSV. Resolve disagreements in a **separate adjudicated copy** of the same template; do not overwrite the original judgments. Set `review_phase=adjudicated`, identify the reviewer or reviewing team, and mark `review_status=complete` only when the relevant fields have been completed. Record the resolution and its rationale in `notes`. Unresolved disagreements remain `uncertain`.

Only an adjudicated CSV is accepted for calculated validation results. For example:

```bash
uv run summarize_scans results/scans --output results/review --per-stratum 5 --seed 580 \
  --annotations data/validation/direct-review-adjudicated.csv \
  --family-reports results/families \
  --relationship-annotations data/validation/relationship-review-adjudicated.csv
```

The tool checks that completed rows refer to sampled cases, have unique identifiers, include a reviewer/date, and contain valid controlled labels. Independent reviewer copies remain separate and can be compared during adjudication.

## Interpreting Validation Results

The two validation populations have separate denominators:

- **Directed risk-indicator metrics** count only adjudicated sample pairs marked related, with supported direction, explicitly assessed indicators, and complete scan/review coverage. Uncertain indicator judgments are omitted individually. Unrelated pairs, unresolved direction, and incomplete coverage are reported as exclusions rather than counted as negatives.
- **Relationship validation** reports agreement or disagreement with automated relatedness, together with uncertain judgments and direction-review counts. It does not contribute to the directed risk-indicator precision/recall calculations.

A completed review row is not automatically an assessable indicator row. The `manual_validation` section of `summary.json` reports assessable and excluded pair counts, along with true positives, false positives, false negatives, true negatives, precision, and recall **for the assessed sample only**. These metrics are not population estimates, and review selection can affect their interpretation.

Record recurring error patterns, proposed corrections, and remaining uncertainty in the research results and [Threats to Validity](../../THREATS_TO_VALIDITY.md). Changes to rules, relationship thresholds, or interpretation should be tested and traced to a [Research Decision Record](../decisions/) when significant.

The original fixed Sprint 1 sample is preserved under [`data/validation/archive/`](../../data/validation/archive/). It is historical material, not a second active validation procedure.

# RDR-006: Sprint 1 Sample Design and Selection Dimensions

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-09-26 |
| **Revised** | 2026-09-27 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 1, RDR-001 through RDR-005, `artifact_groupings`, `sample_selections` |
| **Evidence** | Selection queries in `data/sample-population/sample_population_query_rationale.md`; ten saved family reports under `work/`; previously recorded manual inspection of selected comparisons |
| **Supersedes** | Earlier sampling decision within this RDR for immediate Sprint 1 tool validation; the earlier sample may remain useful for later work |

## Context

The project addresses MSR 2027 Mining Challenge Question 4: risky skill instructions. Sprint 1 needs a manageable sample for checking family analysis, inferred relationships, and scanner comparisons before broader analysis.

The previous design combined purposeful lineage, content-screening, and sibling-variation cases with 75 random artifact seeds, followed by family expansion. It produced approximately 1,400 artifact-selection rows, which was too large for immediate manual validation. Its frozen manifest and successful stable-key reconstruction checks apply to that earlier sample, not automatically to the revised sample.

The revised selection aimed for approximately 50 artifacts or fewer. The ten current reports contain 43 artifacts and 17 directed comparisons. These are report-based totals, not evidence that a revised sample manifest has been frozen or successfully rebuilt.

## Decision Drivers

- Keep the sample small enough for focused tool validation and selected manual inspection.
- Exercise supported direction evidence, ambiguous relationships, and families with no inferred relationships.
- Include positive, negative, and zero scanner-count deltas, plus newly detected capabilities.
- Retain cases exposing scanner coverage gaps and normalization bugs.
- Preserve family context and distinguish screening heuristics from observed tool output and validated findings.
- Use deterministic `artifact_id` values to record sample selection and reconstruct membership for the project's dataset.

## Decision

> Sprint 1 will use a small, purposeful tool-validation sample of ten exact-name families. The current saved reports contain 43 artifacts and 17 directed comparisons. The revised sample has no separate random component and does not support population-level risk estimates.

This revision replaces the earlier three-dimension sampling matrix and random expansion for immediate validation. It does not imply that the earlier sample was deleted or permanently abandoned. Repository distribution remains excluded as a primary selection dimension: repeated file hashes establish identical content, not evolution, provenance, or historical copying.

### Family scope and analysis workflow

`artifact_groupings` groups artifacts by exact name and normalized description. The current `analyze_family` tool loads all qualifying artifacts sharing an exact name, including multiple description groups. Revised family selection follows that exact-name scope; some SQL screening steps are narrower because they compare within a name-and-description group.

`analyze_family` compares body-token shingles, forms similarity clusters, and infers relationships. Jaccard similarity, containment, and minimum shared-shingle counts establish candidate relatedness. Resolved declared provenance, chronology, and asymmetric containment provide direction evidence. A `similarity-only` relationship indicates relatedness without supported direction. These relationships are inferences, not proof of historical copying.

`analyze_family_diffs` loads a family, runs family analysis, and scans the `SKILL.md` content on selected directed edges using the same scanning functions as `scan_diff`. Ambiguous relationships are listed separately without directional scanning. Sibling-file contents are not compared by this wrapper; a sibling-only relationship with no scanner delta does not establish that sibling changes are harmless.

### Selection procedure

The three queries documented in `data/sample-population/sample_population_query_rationale.md` supported iterative candidate screening:

1. **Package-installation variation:** identify small exact-name families with different file hashes and differing package-installation counts within a description group. The displayed configuration uses 5–15 artifact-grouping rows and prioritizes qualifying pairs with distinct parseable commit dates. Earlier settings differed. Neither count variation nor chronology alone establishes lineage.
2. **Declared provenance:** locate field-like references to `derived_from`, `upstream_skill`, `source_repo`, and `upstream_source`, prioritizing smaller families. The query searches the whole document rather than parsing YAML frontmatter. Matches require follow-up to establish recognized metadata and source resolution within the loaded exact-name family; the generic `source` field is not supported.
3. **Additional rule variation:** screen bounded batches of small families for rules not yet demonstrated by selected cases. The saved version has four active patterns: NET-002, FS-002, EXT-001, and SYS-001; FS-001 is commented out despite the retained comment referring to five rules. The omitted exclusion list must be restored before execution. SQL patterns approximate the Python rules and perform no similarity or direction analysis.

SQL counts were selection heuristics. Candidate families were checked through the Python workflow, and selected comparisons were inspected manually in Mergely. Not every comparison was manually validated. Searching stopped because further screening was becoming time-consuming, not because selection was exhaustive or statistically optimized.

## Sample Size and Selection Rationale

The revised sample contains **43 artifacts across 10 families**, producing **17 directed comparisons** in the saved analysis reports. This keeps the sample below the approximate 50-artifact target and manageable for focused tool validation.

Families were selected purposefully to exercise different analysis outcomes: relationships with supported direction, ambiguous relationships, cases with no inferred relationship, and positive, negative, or unchanged scanner counts. Additional cases distinguish increased matches within an existing capability from newly detected capabilities and test known scanner limitations.

The number of directed comparisons is smaller than the number of artifacts because the workflow scans selected relationships with supported direction, rather than every possible artifact pair. Ambiguous relationships are recorded without directional scanning. A family with no directed comparisons therefore does not establish an absence of scanner matches or risk.

These totals describe the saved tool output. They do not establish that every comparison was manually validated or that the revised sample has been frozen and rebuilt successfully. The sample supports tool validation, not representative or population-level risk estimates.

### Manual observations and regression cases

Selected manual inspections identified uneven scanner coverage: equivalent types of operations can produce different match counts when only some command forms are recognized. Such differences can reflect detection limitations rather than changes in risk.

A separate regression case exposed sensitivity to line-ending formats. Normalizing line endings before scanning removed the artificial count difference. The corrected comparison remains useful for checking that formatting differences do not introduce misleading scanner deltas.

Another case highlighted limitations in declared-source resolution and exact-name candidate generation. The declared source was not located by the lookup performed, but this does not establish its absence from the dataset. The candidate pair also failed similarity criteria, so the result cannot be attributed solely to source resolution. Naming differences may further prevent related artifacts from being considered together.

These observations come from selected inspections and do not constitute manual validation of every comparison.

### Rule coverage and interpretation

The saved reports show nonzero count deltas for 10 of the scanner's 12 rules: CMD-001, CMD-002, NET-001, NET-002, FS-001, FS-002, CRED-001, CRED-002, EXT-002, and SYS-002. EXT-001 and SYS-001 remain without confirmed delta examples in this sample.

Rule presence, a count change, and an introduced capability are distinct outcomes. A missing entry in `rule_deltas` does not establish that the rule never matched. Positive and negative deltas describe detected matches, not increased or decreased risk. Coverage here means observed count variation, not complete validation of the rules or their accuracy.

## Reproducibility and Output Scope

The revised sample uses `artifact_id` to select artifacts and identify comparison endpoints. The product owner confirmed that these IDs are deterministic for the project's dataset, so they serve as the identifiers for recording and reconstructing sample membership.

The earlier sample's frozen manifest and reconstruction checks do not validate the revised selection. Freezing the revised artifact-ID list, reconciling membership, and verifying reconstruction remain follow-up work until confirmed by current files.

While potential licensing concerns are being considered, reports use artifact IDs, omit text diffs, and serialize scanner comparisons with `verbose=False`. This limits exported content but does not guarantee anonymity or resolve licensing questions. This record includes no source bodies, repository identities, or provenance values.

## Alternatives Considered

| Alternative | Outcome and reason |
| --- | --- |
| Continue immediate validation with the approximately 1,400-row sample | Deferred; too large for the current manual-validation effort, but potentially useful later. |
| Retain a random component in the revised sample | Not selected; immediate priority is compact, purposeful tool validation. |
| Select isolated artifacts | Not selected; exact-name family context is needed to exercise relationship inference. |
| Continue searching until every rule has a delta example | Deferred; screening was time-consuming and two rule gaps remain explicit. |
| Keep sibling diversity as a required selection dimension | Not retained as a primary requirement; sibling-only cases remain useful, but the wrapper scans only `SKILL.md`. |
| Use repository distribution as a primary dimension | Not selected; identical-content distribution does not establish evolution, and sibling-composition coverage is uneven. |

## Consequences and Limitations

- Purposeful selection favors informative cases and cannot estimate population-wide risk prevalence.
- Exact-name candidate generation can miss related skills with different names; shared names do not prove lineage.
- SQL screening and exploratory similarity thresholds can miss cases or produce candidates that do not yield directed comparisons.
- Scanner coverage gaps, formatting sensitivity, and unvalidated matches limit risk interpretation.
- Ambiguous pairs are not directionally scanned, and sibling-file contents remain outside the wrapper's scan scope.
- Only selected comparisons have documented manual inspection; saved reports are tool output rather than independent ground truth.
- Report-based totals do not establish a frozen, reproducible revised sample.

## Follow-up Actions

- Reconcile the selected exact-name families and artifact membership with the revised sample manifest and construction SQL.
- Freeze the selected `artifact_id` list under the project's current content-export constraints, then validate bidirectional reconstruction against that list.
- Update dataset, study-design, and threats-to-validity documentation to distinguish this sample from the earlier design.
- Retain the line-ending regression case and record manual validation separately from automated output.
- Carry forward EXT-001 and SYS-001 delta gaps and the lack of sibling-content scanning as explicit limitations.

## Revisit Criteria

Revisit this decision when broader or population-level analysis is required, candidate-generation or direction rules change, scanner revisions alter the observed coverage, sibling-content scanning becomes available, or validation reveals important cases not exercised by these ten families.